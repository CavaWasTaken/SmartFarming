import cherrypy
import psycopg2
from psycopg2 import sql
import bcrypt
import json
import os
import jwt
import datetime
import time
import requests

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/Catalog.log", "a") as log_file:
        log_file.write(f"{message}\n")

os.makedirs("./logs", exist_ok=True)  # create the logs directory if it doesn't exist

# each time that the catalog starts, we clear the log file
with open("./logs/Catalog.log", "w") as log_file:
    pass

try:
    # read the mqtt information of the broker from the json file
    with open("./Catalog_config.json", "r") as config_fd:
        config = json.load(config_fd)   # read the configuration from the json file
        telegram_token = config["telegram_token"]  # read the token of the telegram bot

except FileNotFoundError:
    write_log("Catalog_config.json file not found")
    exit(1)   # exit the program if the file is not found
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)

# class that implements the REST API of the Catalog

# method to get a connection to the database
def get_db_connection():
    for _ in range(5):  # try to connect to the database 5 times
        try:
            write_log("Database connection estabilished")
            return psycopg2.connect(
                dbname="smartfarm_db",  # db name
                user="iotproject",  # username postgre sql
                password="WeWillDieForIoT", # password postgre sql
                host="db",    # host,
                port="5432" # port
            )
        
        except psycopg2.Error as e:
            write_log(f"Error connecting to database: {e}")
            if _ == 4:  # if this is the last attempt
                write_log("Failed to connect to the database after 5 attempts")
                raise Exception("Unable to connect to the database")
            
            time.sleep(60)  # wait for 60 seconds before trying again

def cors():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

cherrypy.tools.cors = cherrypy.Tool('before_handler', cors)

# used
# given the id of the greenhouse, return its location
def get_greenhouse_location(conn, greenhouse_id):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT location FROM greenhouses WHERE greenhouse_id = %s"), [greenhouse_id,])
            result = cur.fetchone()
            if result is None:
                cherrypy.response.status = 404
                return {"error": "Greenhouse not found"}
            
            location = result[0]  # get the location from the result
            return {'location': location}
        
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

# used
# given the id of the device, return the list of sensors connected to the greenhouse where it is working
def get_sensors(conn, greenhouse_id, device_name):
    try: 
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur: # create a cursor to execute queries
            # check if the device exists
            if device_name is not None and device_name != "WebApp":  # if the device name is not WebApp, we check if it exists in the db
                cur.execute(sql.SQL("SELECT * FROM devices WHERE greenhouse_id = %s AND name = %s"), [greenhouse_id, device_name])
                result = cur.fetchone()
                if result is None:  # if the device doesn't exist
                    cherrypy.response.status = 404
                    return {"error": "Unexisting device"}
                
                device_id = result[0]  # get the device id from the result
            else:
                device_id = None  # if the device name is WebApp, we don't need the device id
                
            write_log(device_name)
            # personalize the query based on the device name, cause each device connector is interested in different sensors
            authorized_devices = ["DeviceConnector", "DataAnalysis", "ThingSpeakAdaptor", "TelegramBot", "TimeShift", "WebApp"]  # these devices are interested in all the sensors connected to the greenhouse
            if device_name in authorized_devices:    # device connector is interested in all the sensors connected to the greenhouse
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s"),  [greenhouse_id,])
            elif device_name == "HumidityManagement":   # humidity management is interested in humidity and soil moisture sensors
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'Humidity' OR type = 'SoilMoisture'"), [greenhouse_id,])
            elif device_name == "LightManagement":  # light management is interested in light intensity and temperature sensors
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'LightIntensity' OR type = 'Temperature'"), [greenhouse_id,])
            elif device_name == "NutrientManagement":   # nutrient management is interested in NPK and pH sensors
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'NPK' OR type = 'pH' OR type = 'SoilMoisture'"), [greenhouse_id,])
            sensors = cur.fetchall()    # sensors is a list of values (tuples)
            if sensors is None: # if there are no sensors connected to the greenhouse, return error 404
                cherrypy.response.status = 404
                return {"error": "No sensors found"}
            
            # convert the list of sensors to a list of dictionaries, associating the values to the keys (columns of the db)
            sensors_list = []
            for sensor in sensors:  # for each sensor in the list
                sensor_dict = { # associate the values to the keys
                    'sensor_id': sensor[0],
                    'area_id': sensor[1],
                    'type': sensor[2],
                    'name': sensor[3],
                    'unit': sensor[4],
                    'threshold': sensor[5],
                    'domain': sensor[6],
                    'greenhouse_id': sensor[7]
                }
                sensors_list.append(sensor_dict)    # create a dictionary containing the information of each sensor
            write_log(sensors_list)
            return {
                'device_id': device_id,
                'sensors': sensors_list
            }
        
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
    
# used
# return the info about the greenhouse by greenhouse_id. The device id is used to see if who made the request is connected to the greenhouse
def get_greenhouse_info(conn, greenhouse_id):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}

        with conn.cursor() as cur: # create a cursor to execute queries
            # the first query is to get the greenhouse info of the greenhouse
            cur.execute(sql.SQL("SELECT * FROM greenhouses WHERE greenhouse_id = %s"), [greenhouse_id,])
            greenhouse = cur.fetchone() # greenhouse is a tuple
            if greenhouse is None:  # if the greenhouse does not exist, return error 404
                raise cherrypy.HTTPError(404, "Greenhouse not found")
            greenhouse_dict = { # associate the values to the keys
                'greenhouse_id': greenhouse[0],
                'user_id': greenhouse[1],
                'name': greenhouse[2],
                'location': greenhouse[3],
                'thingSpeak_config': greenhouse[4]
            }
            
            return greenhouse_dict
    
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
    
# used
# function to perform user registration
def register(conn, username, email, password):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # check if the username already exists
            cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
            user = cur.fetchone()
            if user is not None:
                cherrypy.response.status = 409
                return {"error": "Username already exists"}
        
            # if the username is new, insert it in the db
            # salt hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur.execute(sql.SQL("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"), [username, email, hashed_password])
            conn.commit()

            # check if the user was inserted correctly
            cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
            user = cur.fetchone()
            if user is None:
                cherrypy.response.status = 500
                return {"error": "Internal error"}
        
            return {
                'message': 'User registered successfully',
                'user_id': user[0],
                'username': user[1],
                'email': user[2]
            }
        
    except psycopg2.errors.NotNullViolation:
        cherrypy.response.status = 400
        return {"error": "Missing required fields"}
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
    
# secret key for JWT encoding and decoding
SECRET_KEY = config["SECRET_KEY"]
# function to generate a JWT token for the logged in user    
def generate_token(user_id, username):
    try:
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": int(expiration.timestamp()),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    
    except Exception as e:
        print(f"Error generating token: {e}")
        raise cherrypy.HTTPError(500, "Internal error")
    
# used
# function to perform user login
def login(conn, username, password):
    try:
        # Check DB connection
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}

        with conn.cursor() as cur:
            # Fetch user by username
            cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
            user = cur.fetchone()

            if user is None:
                cherrypy.response.status = 401
                return {"error": "Incorrect username"}

            stored_hash_raw = user[3]

            # If password is missing
            if stored_hash_raw is None or stored_hash_raw == "":
                cherrypy.response.status = 401
                return {"error": "Password not set"}

            # Convert to correct bcrypt bytes
            if isinstance(stored_hash_raw, memoryview):  
                stored_hash_bytes = bytes(stored_hash_raw)
            elif isinstance(stored_hash_raw, str) and stored_hash_raw.startswith("\\x"):
                # Decode Postgres hex (\x...)
                stored_hash_bytes = bytes.fromhex(stored_hash_raw[2:])
            elif isinstance(stored_hash_raw, (bytes, bytearray)):
                stored_hash_bytes = stored_hash_raw
            else:
                stored_hash_bytes = stored_hash_raw.encode('utf-8') if isinstance(stored_hash_raw, str) else bytes(stored_hash_raw)

            # Check password depending on format
            try:
                if stored_hash_bytes.startswith(b"$2b$"):
                    # bcrypt hash
                    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes):
                        cherrypy.response.status = 401
                        return {"error": "Incorrect password"}
                else:
                    # fallback: treat as plaintext
                    db_pass = stored_hash_bytes.decode('utf-8', errors='ignore').strip()
                    if password.strip() != db_pass:
                        cherrypy.response.status = 401
                        return {"error": "Incorrect password"}
            except ValueError as ve:
                print("LOGIN ERROR: bcrypt invalid salt or corrupted hash:", ve)
                cherrypy.response.status = 401
                return {"error": "Invalid password format"}

            # Generate JWT token
            token = generate_token(user[0], user[1])
            cherrypy.response.headers['Authorization'] = f"Bearer {token}"

            return {
                'message': 'Login successful',
                'user_id': user[0],
                'username': user[1],
                'email': user[2],
                'token': token
            }

    except Exception as e:
        print("LOGIN ERROR TRACE:", e)
        cherrypy.response.status = 500
        return {"error": "Internal error"}

# used
# function to return the greenhouses of a user
def get_user_greenhouses(conn, user_id, username):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # chech if the user exists
            cur.execute(sql.SQL("SELECT * FROM users WHERE user_id = %s AND username = %s"), [user_id, username])
            user = cur.fetchone()
            if user is None:
                cherrypy.response.status = 404
                return {"error": "User not found"}
            # get the greenhouses of the user
            cur.execute(sql.SQL("SELECT * FROM greenhouses WHERE user_id = %s"), [user_id])
            greenhouses = cur.fetchall()
            if greenhouses is None:
                return {'greenhouses': []}
            
            greenhouses_list = []
            for greenhouse in greenhouses:
                greenhouse_dict = {
                    'greenhouse_id': greenhouse[0],
                    'user_id': greenhouse[1],
                    'name': greenhouse[2],
                    'location': greenhouse[3],
                    'thingSpeak_config': greenhouse[4]
                }
                greenhouses_list.append(greenhouse_dict)
            
            return {'greenhouses': greenhouses_list}
        
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
    
# used
# function to return everything about a greenhouse (plants, sensors, devices)
def get_devices(conn, greenhouse_id):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # get devices of the greenhouse
            cur.execute(sql.SQL("SELECT * FROM devices WHERE greenhouse_id = %s"), [greenhouse_id])
            devices = cur.fetchall() or [] # fall back to empty list if no devices are found
            if devices is None:
                cherrypy.response.status = 404
                return {"error": "No devices found"}
            
            devices_list = []
            for device in devices:
                device_dict = {
                    'device_id': device[0],
                    'greenhouse_id': device[1],
                    'name': device[2],
                    'type': device[3],
                }
                devices_list.append(device_dict)

            return { 'devices': devices_list}
        
    except Exception:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
    
# used
# function used by the user to change the threshold of a sensor
def set_sensor_threshold(conn, sensor_id, threshold):
    threshold = json.dumps(threshold)
    with conn.cursor() as cur:
        try:
            cur.execute(sql.SQL("UPDATE sensors SET threshold_range = %s WHERE sensor_id = %s"), [threshold, sensor_id])
            conn.commit()
            return {'message': 'Threshold set'}
        
        except psycopg2.errors.NotNullViolation:
            raise cherrypy.HTTPError(400, "Threshold not provided")
        except:
            raise cherrypy.HTTPError(500, "Internal error")
        
# used
# function to get the entire list of plants
def get_all_plants(conn):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM plants"))
            plants = cur.fetchall()
            if plants is None:
                cherrypy.response.status = 404
                return {"error": "No plants found"}
            
            plants_list = []
            for plant in plants:
                plant_dict = {
                    'plant_id': plant[0],
                    'name': plant[1],
                    'species': plant[2],
                    'desired_thresholds': plant[3]
                }
                plants_list.append(plant_dict)
            
            return {'plants': plants_list}
        
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
    
# used
# function to add a plant to a greenhouse
def add_plant_to_greenhouse(conn, greenhouse_id, plant_id, area_id):
    with conn.cursor() as cur:
        # check if the plant is already in the greenhouse
        cur.execute(sql.SQL("SELECT * FROM area_plants WHERE greenhouse_id = %s AND plant_id = %s AND area_id=%s"), [greenhouse_id, plant_id, area_id])
        plant = cur.fetchone()
        if plant is not None:
            raise cherrypy.HTTPError(404, "Plant already in the greenhouse")
        # insert the new plant in the greenhouse
        try:
            cur.execute(sql.SQL("INSERT INTO area_plants (greenhouse_id, plant_id, area_id) VALUES (%s, %s,%s)"), [greenhouse_id, plant_id, area_id])
            conn.commit()
            # return the updated list of plants in the greenhouse
            cur.execute(sql.SQL("SELECT plant_id FROM area_plants WHERE greenhouse_id = %s AND area_id=%s"), [greenhouse_id, area_id])
            plants = cur.fetchall()
            if plants is None:
                raise cherrypy.HTTPError(404, "No plants found")
            
            plants_list = []
            for plant in plants:
                cur.execute(sql.SQL("SELECT * FROM plants WHERE plant_id = %s"), [plant[0]])
                plant = cur.fetchone()
                plant_dict = {
                    'plant_id': plant[0],
                    'name': plant[1],
                    'species': plant[2],
                    'desired_thresholds': plant[3]
                }
                plants_list.append(plant_dict)

            return plants_list
        except:
            raise cherrypy.HTTPError(500, "Internal error")
        
# used
# function to remove a plant from the greenhouse
def remove_plant_from_greenhouse(conn, area_id, plant_id):
    with conn.cursor() as cur:
        # check if the plant is in the greenhouse
        cur.execute(sql.SQL("SELECT * FROM area_plants WHERE area_id = %s AND plant_id = %s"), [area_id, plant_id])
        plant = cur.fetchone()
        if plant is None:
            raise cherrypy.HTTPError(404, "Plant not in the greenhouse")
        # remove the plant from the greenhouse
        try:
            cur.execute(sql.SQL("DELETE FROM area_plants WHERE area_id = %s AND plant_id = %s"), [area_id, plant_id])
            conn.commit()
            # return the updated list of plants in the greenhouse
            cur.execute(sql.SQL("SELECT plant_id FROM area_plants WHERE area_id = %s"), [area_id])
            cur.execute(sql.SQL("SELECT plant_id FROM area_plants WHERE area_id = %s"), [area_id])
            plants = cur.fetchall()
            if plants is None:
                raise cherrypy.HTTPError(404, "No plants found")
            
            plants_list = []
            for plant in plants:
                cur.execute(sql.SQL("SELECT * FROM plants WHERE plant_id = %s"), [plant[0]])
                plant = cur.fetchone()
                plant_dict = {
                    'plant_id': plant[0],
                    'name': plant[1],
                    'species': plant[2],
                    'desired_thresholds': plant[3]
                }
                plants_list.append(plant_dict)

            return plants_list
        except:
            raise cherrypy.HTTPError(500, "Internal error")
        
# used
# delete sensor from greenhouse function
def remove_sensor_from_greenhouse(conn, area_id, sensor_id):
    with conn.cursor() as cur:
        # check if the sensor is in the greenhouse
        cur.execute("SELECT * FROM sensors WHERE area_id = %s AND sensor_id = %s", [area_id, sensor_id])
        sensor = cur.fetchone()
        if sensor is None:
            raise cherrypy.HTTPError(404, "Sensor is not in the greenhouse")
        # remove the plant from the greenhouse
        try:
            cur.execute("DELETE FROM sensors WHERE area_id = %s AND sensor_id = %s", [area_id, sensor_id])
           

            conn.commit()
            # return the updated list of sensors in the greenhouse
            cur.execute("SELECT sensor_id FROM sensors WHERE area_id = %s", [area_id])
            sensors = cur.fetchall()
            if sensors is None:
                raise cherrypy.HTTPError(404, "No sensors found")
            
            sensor_list = []
            for sensor in sensors:
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE sensor_id = %s"), [sensor[0]])
                sensor = cur.fetchone()
                sensor_dict = {
                    'sensor_id': sensor[0],
                    'name': sensor[1],
                    'type': sensor[2],
                    'domain': sensor[3]
                }
                sensor_list.append(sensor_dict)

            return sensor_list
        except:
            raise cherrypy.HTTPError(500, "Internal error")
        
# used
#function to get all scheduled events where current time is between start_time and end_time for a greenhouse
def get_scheduled_events(conn, device_id, device_name, greenhouse_id):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # # check if the device is connected to the greenhouse
            # cur.execute(sql.SQL("SELECT * FROM devices WHERE device_id = %s AND name = %s AND greenhouse_id = %s"), [device_id, device_name, greenhouse_id])
            # device = cur.fetchone() # device is a tuple
            # if device is None:  # if the device doesn't exist
            #     cherrypy.response.status = 404
            #     return {"error": "Device not found"}

            # get all the scheduled events for the greenhouse
            cur.execute(sql.SQL("SELECT * FROM scheduled_events WHERE greenhouse_id = %s"), [greenhouse_id])
            events = cur.fetchall() # events is a list of values (tuples)
            
            # convert the list of events to a list of dictionaries, associating the values to the keys (columns of the db)
            events_list = []
            for event in events:  # for each event in the list
                event_dict = { # associate the values to the keys
                    'event_id': event[0],
                    'frequency': event[1],
                    'execution_time': str(event[2]),
                    'sensor_id': event[3],
                    'greenhouse_id': event[4],
                    'parameter': event[5],
                    'value': str(event[6])
                }
                events_list.append(event_dict)    # create a dictionary containing the information of each event

            return {'events': events_list}
            
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": "Internal error: " + str(e)}

# used
# method to add one event in the DB
def schedule_event(conn, greenhouse_id, device_id, sensor_id, parameter, frequency, value, execution_time):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # # check if the device is connected to the greenhouse
            # cur.execute(sql.SQL("SELECT * FROM devices WHERE device_id = %s AND greenhouse_id = %s"), [device_id, greenhouse_id])
            # device = cur.fetchone() # device is a tuple
            # if device is None:  # if the device doesn't exist
            #     cherrypy.response.status = 404
            #     return {"error": "Device not found"}

            # insert the event in the DB
            cur.execute(sql.SQL("INSERT INTO scheduled_events (greenhouse_id, frequency, sensor_id, parameter, execution_time, value) VALUES (%s, %s, %s, %s, %s, %s)"), [greenhouse_id, frequency, sensor_id, parameter, execution_time, value])
            conn.commit()

            # check if the event was inserted
            cur.execute(sql.SQL("SELECT * FROM scheduled_events WHERE greenhouse_id = %s AND frequency = %s AND sensor_id = %s AND parameter = %s AND execution_time = %s AND value = %s"), [greenhouse_id, frequency, sensor_id, parameter, execution_time, value])
            event = cur.fetchone()
            if event is None:
                cherrypy.response.status = 500
                return {"error": "Event not inserted"}
            
            cherrypy.response.status = 201
            return {
                'event_id': event[0],
                'frequency': event[1],
                'execution_time': str(event[2]),
                'sensor_id': event[3],
                'greenhouse_id': event[4],
                'parameter': event[5],
                'value': str(event[6])
            }
                            
    except psycopg2.errors.NotNullViolation as e:
        cherrypy.response.status = 400
        return {"error": f"Missing required fields: {str(e)}"}
    
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}
        
# used
# method to delete the scheduled event from the DB
def delete_event(conn, device_id, event_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # check if the device is connected to the greenhouse
            cur.execute(sql.SQL("SELECT * FROM devices WHERE device_id = %s"), [device_id])
            device = cur.fetchone() # device is a tuple
            if device is None:  # if the device doesn't exist
                cherrypy.response.status = 404
                return {"error": "Device not found"}

            # delete the event from the DB
            cur.execute(sql.SQL("DELETE FROM scheduled_events WHERE event_id = %s"), [event_id])
            conn.commit()

            # # check if the event was deleted
            # cur.execute(sql.SQL("SELECT * FROM scheduled_events WHERE event_id = %s"), [event_id])
            # event = cur.fetchone()
            # if event is not None:
            #     cherrypy.response.status = 500
            #     return {"error": "Event not deleted"}
            
            cherrypy.response.status = 200
            return
                            
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

# used
# method called through the web app to initialize a new greenhouse with default areas and devices
def add_greenhouse(conn, user_id, name, location, thingspeak_config):
    try:
        # Check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # Check if the greenhouse already exists for the same user
            cur.execute(
                sql.SQL("SELECT * FROM greenhouses WHERE name = %s AND user_id = %s"),
                [name, user_id]
            )
            if cur.fetchone():
                cherrypy.response.status = 409
                return {"error": "Greenhouse with this name already exists for the user"}

            # Insert the new greenhouse
            cur.execute(
                sql.SQL("""
                    INSERT INTO greenhouses (name, location, user_id, thingspeak_config)
                    VALUES (%s, %s, %s, %s)
                    RETURNING greenhouse_id, name, location
                """),
                [name, location, user_id, json.dumps(thingspeak_config) if thingspeak_config else json.dumps({"write_key": "", "read_key": "", "channel_id": ""})]
            )
            greenhouse = cur.fetchone()

            # add default area 
            cur.execute(
                sql.SQL("""
                    INSERT INTO areas (greenhouse_id, name)
                    VALUES (%s, %s)
                    RETURNING area_id
                """),
                [greenhouse[0], "Main Area"]
            )

            main_area_id = cur.fetchone()[0]

            # add default devices 
            default_devices = [
                ("DeviceConnector", "DeviceConnector"),
                ("HumidityManagement", "Microservices"),
                ("LightManagement", "Microservices"),
                ("NutrientManagement", "Microservices"),
                ("DataAnalysis", "Microservices"),
                ("TimeShift", "Microservices"),
                ("ThingSpeakAdaptor", "ThingSpeakAdaptor"),
                ("TelegramBot", "UI")
            ]

            for name, dev_type in default_devices:
                cur.execute(
                    """
                    INSERT INTO devices (greenhouse_id, name, type)
                    VALUES (%s, %s, %s)
                    """,
                    (greenhouse[0], name, dev_type)
                )

            conn.commit()

            return {
                'message': 'Greenhouse added successfully',
                'greenhouse_id': greenhouse[0],
                'name': greenhouse[1],
                'location': greenhouse[2],
                'area_id': main_area_id
            }

    except psycopg2.errors.NotNullViolation as e:
        conn.rollback()
        cherrypy.response.status = 400
        return {"error": f"Missing required fields: {str(e)}"}
    
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

# used
# function to get the entire list of sensors
def get_all_sensors(conn):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM availablesensors;"))
        sensors = cur.fetchall()
        if sensors is None:
            raise cherrypy.HTTPError(404, "No sensors found")
        
        sensors_list = []
        for sensor in sensors:
            sensor_dict = {
                'sensor_id': sensor[0],
                'name': sensor[1],
                'type': sensor[2],
            }
            sensors_list.append(sensor_dict)
        
        return {'sensors': sensors_list}

# used
# add sensors for greenhouses 
def add_sensor_from_available(conn, greenhouse_id, sensor_id, area_id):
    with conn.cursor() as cur:
        try:
            # Step 1: Get sensor info from availablesensors table
            cur.execute(
                sql.SQL("SELECT type, name, unit, threshold_range, domain FROM availablesensors WHERE sensor_id = %s"),
                [sensor_id]
            )
            sensor = cur.fetchone()

            if sensor is None:
                cherrypy.response.status = 404
                return {"error": "Sensor not found in available sensors"}

            sensor_type, name, unit, threshold_range, domain = sensor


            if isinstance(threshold_range, dict):
                threshold_range = json.dumps(threshold_range)

            if isinstance(domain, dict):
                domain = json.dumps(domain)

            try:
                # Step 2: Insert into sensors table
                cur.execute(
                    sql.SQL("""
                        INSERT INTO sensors (greenhouse_id, type, name, unit, threshold_range, domain, area_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING greenhouse_id
                    """),
                    [greenhouse_id, sensor_type, name, unit, threshold_range, domain, area_id]
                )
                new_sensor_id = cur.fetchone()[0]
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                cherrypy.response.status = 409
                return {"error": "Sensor already exists in this greenhouse"}

            return {
                'message': 'Sensor added successfully',
                'sensor_id': new_sensor_id,
                'greenhouse_id': greenhouse_id,
                'type': sensor_type,
                'name': name,
                'unit': unit,
                'threshold_range': threshold_range,
                'domain': domain,
                'area_id': area_id
            }

        except psycopg2.Error as e:
            conn.rollback()
            raise cherrypy.HTTPError(500, f"Database error: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise cherrypy.HTTPError(500, f"Internal error: {str(e)}")

# used
# method to get the areas contained in the greenhouse
def get_areas_by_greenhouse(conn, greenhouse_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}

        with conn.cursor() as cur:
            cur.execute("""
                SELECT area_id, name
                FROM areas
                WHERE greenhouse_id = %s
            """, (greenhouse_id,))

            areas = cur.fetchall() or []

            area_list = [
                {"area_id": row[0], "name": row[1]}
                for row in areas
            ]

            return {"areas": area_list}

    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

# used
# method to add new area for existing greenhouse
def add_area(conn, greenhouse_id, name):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}

        with conn.cursor() as cur:
            # Check if the greenhouse exists
            cur.execute("SELECT greenhouse_id FROM greenhouses WHERE greenhouse_id = %s", [greenhouse_id])
            if not cur.fetchone():
                cherrypy.response.status = 404
                return {"error": "Greenhouse not found"}

            # Insert new area
            cur.execute(
                """
                INSERT INTO areas (name, greenhouse_id)
                VALUES (%s, %s)
                RETURNING area_id
                """,
                (name, greenhouse_id)
            )
            area_id = cur.fetchone()[0]
            conn.commit()

            return {
                "message": "Area added successfully",
                "area_id": area_id,
                "greenhouse_id": greenhouse_id,
                "name": name
            }

    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

# used
# get the sensors of each area of the greenhouse
def get_sensors_area(conn, greenhouse_id, area_id):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # get sensors of the greenhouse
            cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s and area_id = %s"), [greenhouse_id, area_id])
            sensors = cur.fetchall() or [] # fall back to empty list if no sensors are found
            if sensors is None:
                cherrypy.response.status = 404
                return {"error": "No sensors found"}

            sensors_list = []
            for sensor in sensors:
                sensor_dict = {
                    'sensor_id': sensor[0],
                    'greenhouse_id': sensor[1],
                    'type': sensor[2],
                    'name': sensor[3],
                    'unit': sensor[4],
                    'threshold': sensor[5],
                    'domain': sensor[6],
                    'area_id': sensor[7]
                }
                sensors_list.append(sensor_dict)

            return {'sensors': sensors_list}
    except Exception:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
    
# used
# get the plants of each area of the greenhouse
def get_plants_area(conn, greenhouse_id, area_id):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # get plants of the greenhouse
            cur.execute(sql.SQL("SELECT plant_id FROM area_plants WHERE greenhouse_id = %s and area_id = %s"), [greenhouse_id, area_id])
            plants = cur.fetchall() or [] # fall back to empty list if no plants are found
            
            plants_list = []
            for plant in plants:
                cur.execute(sql.SQL("SELECT * FROM plants WHERE plant_id = %s"), [plant[0]])
                plant = cur.fetchone() or [] # fall back to empty list if no plants are found
                if plant: # if the plant exists
                    plant_dict = {
                    'plant_id': plant[0],
                    'name': plant[1],
                    'species': plant[2],
                    'desired_thresholds': plant[3],
                }
                plants_list.append(plant_dict)

            return {'plants': plants_list}
    except Exception:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
        
# used
# method to remove an area from the greenhouse
def remove_area_from_greenhouse(conn, greenhouse_id, area_id):
    with conn.cursor() as cur:
        # check if the area is in the greenhouse
        cur.execute(sql.SQL("SELECT * FROM areas WHERE greenhouse_id = %s AND area_id = %s"), [greenhouse_id, area_id])
        area = cur.fetchone()
        if area is None:
            raise cherrypy.HTTPError(404, "area is not in the greenhouse")
        # remove the area from the greenhouse
        try:
            cur.execute(sql.SQL("DELETE FROM areas WHERE greenhouse_id = %s AND area_id = %s"), [greenhouse_id, area_id])
            conn.commit()
            # return the updated list of areas in the greenhouse
            cur.execute(sql.SQL("SELECT area_id FROM areas WHERE area_id = %s"), [area_id])
            areas = cur.fetchall()
            if areas is None:
                raise cherrypy.HTTPError(404, "No areas found")
            
            area_list = []
            for area in areas:
                cur.execute(sql.SQL("SELECT * FROM areas WHERE area_id = %s"), [area[0]])
                area = cur.fetchone()
                area_dict = {
                    'area_id': area[0],
                    'name': area[1],
                }
                area_list.append(area_dict)

            return area_list
        except:
            raise cherrypy.HTTPError(500, "Internal error")

# used
# method to get the username and email of a logged user
def get_user_info(conn, user_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT username, email FROM users WHERE user_id = %s;"), [user_id])  
        user = cur.fetchone()  # Use fetchone() for a single user

        if user is None:
            raise cherrypy.HTTPError(404, "No user found")
        
        user_dict = {
            'username': user[0],
            'email': user[1]
        }

        return user_dict  # Just return the dictionary, not a list
    
# used
# method to read get the telegram chat id associated to the greenhouse
def get_telegram_chat_id(conn, greenhouse_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        # check if the greenhouse exists and get its Telegram chat ID
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT user_id FROM greenhouses WHERE greenhouse_id = %s;"), [greenhouse_id])  
            chat_id = cur.fetchone()

            if chat_id is None:
                cherrypy.response.status = 404
                return {"error": "No greenhouse found with this ID"}
            
            # use the user_id to get the Telegram chat ID
            cur.execute(sql.SQL("SELECT telegram_user_id FROM users WHERE user_id = %s;"), [chat_id[0]])
            chat_id = cur.fetchone()

            if chat_id is None:
                cherrypy.response.status = 404
                return {"error": "No Telegram chat ID found for this user"}

            return {
                'telegram_chat_id': chat_id[0]
            }

    except Exception as e:
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

# used
# method to save the updated info of the user (username, email, new_pass)
def update_user_info(conn, user_id, username, email, new_password=None):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute(sql.SQL("SELECT * FROM users WHERE user_id = %s"), [user_id])
            user = cur.fetchone()
            if not user:
                cherrypy.response.status = 404
                return {"error": "User not found"}

            # Update username and email
            cur.execute(
                sql.SQL("UPDATE users SET username = %s, email = %s WHERE user_id = %s"),
                [username, email, user_id]
            )

            # Optionally update password
            if new_password:
                hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute(
                    sql.SQL("UPDATE users SET password_hash = %s WHERE user_id = %s"),
                    [hashed_pw, user_id]
                )

            conn.commit()

            return {"message": "User information updated successfully"}
    
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cherrypy.response.status = 409
        return {"error": "Username or email already in use"}
    
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}
    
# used 
# method to associate an otp code to a telegram chat
def otp(conn, telegram_chat_id, otp_code):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # if the user has already an OTP code, update it, otherwise create a new one
            cur.execute(sql.SQL("SELECT * FROM otps WHERE telegram_user_id = %s"), [telegram_chat_id])
            user = cur.fetchone()
            if not user:
                cur.execute(sql.SQL("INSERT INTO otps (telegram_user_id, otp) VALUES (%s, %s)"), [telegram_chat_id, otp_code])

            else:
                cur.execute(sql.SQL("UPDATE otps SET otp = %s WHERE telegram_user_id = %s"), [otp_code, telegram_chat_id])

            conn.commit()

            return {"message": "OTP code updated successfully"}
    
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

# used
# method to associate the otp to an user
def verify_telegram_otp(conn, user_id, otp_code):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # check if the OTP code exists
            cur.execute(sql.SQL("SELECT telegram_user_id FROM otps WHERE otp = %s"), [otp_code])
            telegramUser = cur.fetchone()
            if not telegramUser:
                cherrypy.response.status = 404
                return {"error": "OTP code not found"}
            
            # delete the OTP code from the database
            cur.execute(sql.SQL("DELETE FROM otps WHERE otp = %s"), [otp_code])
            
            # get the username and email of the user
            cur.execute(sql.SQL("SELECT username, email FROM users WHERE user_id = %s"), [user_id])
            user_info = cur.fetchone()
            if not user_info:
                cherrypy.response.status = 404
                return {"error": "User not found"}
            
            try:
                # associate the user to the Telegram user ID
                cur.execute(sql.SQL("UPDATE users SET telegram_user_id = %s WHERE user_id = %s"), [telegramUser[0], user_id])
                conn.commit()

            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                cherrypy.status = 409   # conflict
                return {"error": f"Unique violation {str(e)}"}

            # send to telegram bot the user ID
            message = f"Welcome {user_info[0]}!"
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {
                "chat_id": telegramUser[0],
                "text": message
            }
            try:
                response = requests.post(url, json=payload, timeout=5)
                if response.ok:
                    write_log(f"Telegram message sent successfully to user {telegramUser[0]}")
                else:
                    write_log(f"Failed to send Telegram message: {response.text}")

            except Exception as e:
                write_log(f"Failed to send Telegram message: {e}")

            # if found, return the user ID
            return {"telegram_user_id": telegramUser[0]}
    
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

# used
# method to remove the association between the telegram chat and the greenhouse
def logout_telegram(conn, user_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:

            # remove the Telegram user ID from the user
            cur.execute(sql.SQL("UPDATE users SET telegram_user_id = NULL WHERE telegram_user_id = %s"), [user_id])
            conn.commit()

            return {"message": "User logged out successfully"}
    
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}
    
# used
# method to update the thingspeak configuration of a greenhouse
def update_thingspeak_config(conn, greenhouse_id, channel_id, write_key, read_key):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # Check if the greenhouse exists
            cur.execute(sql.SQL("SELECT * FROM greenhouses WHERE greenhouse_id = %s"), [greenhouse_id])
            greenhouse = cur.fetchone()
            if not greenhouse:
                cherrypy.response.status = 404
                return {"error": "Greenhouse not found"}

            # Update the ThingSpeak configuration
            cur.execute(
                sql.SQL("UPDATE greenhouses SET thingspeak_config = %s WHERE greenhouse_id = %s"),
                [json.dumps({"channel_id": channel_id, "write_key": write_key, "read_key": read_key}), greenhouse_id]
            )
            conn.commit()

            return {"message": "ThingSpeak configuration updated successfully"}
    
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}
    
# used
# method to get area information by greenhouse_id and area_id
def get_area_info(conn, greenhouse_id, area_id):
    try:
        greenhouse_id = int(greenhouse_id)
        area_id = int(area_id)

        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:          
            # get area information
            cur.execute(sql.SQL("SELECT * FROM areas WHERE greenhouse_id = %s AND area_id = %s"), [greenhouse_id, area_id])
            area = cur.fetchone()
            if not area:
                cherrypy.response.status = 404
                return {"error": "Area not found"}
            
            area_info = {
                'area_id': area[0],
                'name': area[1],
                'greenhouse_id': area[2]
            }
            return area_info
            
    except ValueError:
        cherrypy.response.status = 400
        return {"error": "Invalid greenhouse_id or area_id. Must be integers."}
    except psycopg2.Error as e:
        cherrypy.response.status = 500
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": f"Internal server error: {str(e)}"}

class CatalogREST(object):
    exposed = True

    def __init__(self, catalog_connection):
        self.catalog_connection = catalog_connection

    @cherrypy.tools.cors()  # enable CORS for POST requests
    @cherrypy.tools.json_out()  # output JSON response
    def GET(self, *uri, **params):
        if len(uri) == 0:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}
        
        elif uri[0] == 'get_sensors':
            # check the existence of the parameters
            if 'greenhouse_id' in params and 'device_name' in params:
                return get_sensors(self.catalog_connection, params['greenhouse_id'], params['device_name'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
            
        elif uri[0] == 'get_greenhouse_info':
            # check the existence of the parameters
            if 'greenhouse_id' in params:
                return get_greenhouse_info(self.catalog_connection, params['greenhouse_id'])

            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
            
        elif uri[0] == 'get_greenhouse_location':
            # check the existence of the parameters
            if 'greenhouse_id' in params:
                return get_greenhouse_location(self.catalog_connection, params['greenhouse_id'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
            
        elif uri[0] == 'get_user_greenhouses':
            # check the existence of the parameters
            if 'user_id' in params and 'username' in params:
                return get_user_greenhouses(self.catalog_connection, params['user_id'], params['username'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
            
        elif uri[0] == 'get_devices':
            # check the existence of the parameters
            if 'greenhouse_id' in params:
                return get_devices(self.catalog_connection, params['greenhouse_id'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
            
        elif uri[0] == 'get_all_plants':
            # check that no parameters are passed
            if len(params) > 0:
                cherrypy.response.status = 400
                return {"error": "No parameters allowed"}
            
            return get_all_plants(self.catalog_connection)
        
        elif uri[0] == 'get_scheduled_events':
            # check the existence of the parameters
            if 'device_id' in params and 'device_name' in params and 'greenhouse_id' in params:
                return get_scheduled_events(self.catalog_connection, params["device_id"], params["device_name"], params["greenhouse_id"])
            
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
        
        elif uri[0] == 'get_all_sensors':
            # check that no parameters are passed
            if len(params) > 0:
                cherrypy.response.status = 400
                return {"error": "No parameters allowed"}
            
            return get_all_sensors(self.catalog_connection)
        
        elif uri[0] == 'get_areas_by_greenhouse':
            # check the existence of the parameters
            if 'greenhouse_id' in params:
                return get_areas_by_greenhouse(self.catalog_connection, params['greenhouse_id'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
        
        elif uri[0] == 'get_sensors_area':
            # check the existence of the parameters
            if 'greenhouse_id' in params and 'area_id' in params:
                return get_sensors_area(self.catalog_connection, params['greenhouse_id'], params['area_id'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
        
        elif uri[0] == 'get_plants_area':
            # check the existence of the parameters
            if 'greenhouse_id' in params and 'area_id' in params:
                return get_plants_area(self.catalog_connection, params['greenhouse_id'], params['area_id'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}

        elif uri[0] == 'get_user_info':
            # check the existence of the parameters
            if 'user_id' in params:
                return get_user_info(self.catalog_connection, params['user_id'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}     
   
        elif uri[0] == 'get_telegram_chat_id':
            # check the existence of the parameters
            if 'greenhouse_id' in params:
                return get_telegram_chat_id(self.catalog_connection, params['greenhouse_id'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
            
        elif uri[0] == 'get_area_info':
            # check the existence of the parameters
            if 'greenhouse_id' in params and 'area_id' in params:
                return get_area_info(self.catalog_connection, params['greenhouse_id'], params['area_id'])
                
            else:
                cherrypy.response.status = 400
                return {"error": "Missing parameters"}
        
        else:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}

    @cherrypy.tools.cors()  # enable CORS for POST requests
    @cherrypy.tools.encode(encoding='utf-8')    # encode the request body
    @cherrypy.tools.json_out()  # output JSON response
    def POST(self, *uri, **params):
        if len(uri) == 0:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}
        
        elif uri[0] == 'register':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'username' not in input_json or 'email' not in input_json or 'password' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return register(self.catalog_connection, input_json['username'], input_json['email'], input_json['password'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
        
        elif uri[0] == 'login':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'username' not in input_json or 'password' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return login(self.catalog_connection, input_json['username'], input_json['password'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
        
        elif uri[0] == 'set_sensor_threshold':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'sensor_id' not in input_json or 'threshold' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                if not isinstance(input_json['threshold'], dict):
                    cherrypy.response.status = 400
                    return {"error": "Threshold must be a dictionary"}
                
                return set_sensor_threshold(self.catalog_connection, input_json['sensor_id'], input_json['threshold'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
        
        elif uri[0] == 'add_plant_to_greenhouse':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'greenhouse_id' not in input_json or 'plant_id' not in input_json or 'area_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return add_plant_to_greenhouse(self.catalog_connection, input_json['greenhouse_id'], input_json['plant_id'], input_json['area_id'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'remove_plant_from_greenhouse':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'area_id' not in input_json or 'plant_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return remove_plant_from_greenhouse(self.catalog_connection, input_json['area_id'], input_json['plant_id'])

            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
        
        elif uri[0] == 'remove_sensor_from_greenhouse':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'sensor_id' not in input_json or 'area_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return remove_sensor_from_greenhouse(self.catalog_connection, input_json['area_id'], input_json['sensor_id'])

            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        elif uri[0] == 'schedule_event':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'device_id' not in input_json or 'greenhouse_id' not in input_json or 'sensor_id' not in input_json or 'parameter' not in input_json or 'frequency' not in input_json or 'desired_value' not in input_json or 'execution_time' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return schedule_event(self.catalog_connection, input_json['greenhouse_id'], input_json['device_id'], input_json['sensor_id'], input_json['parameter'], input_json['frequency'], input_json['desired_value'], input_json['execution_time'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'add_greenhouse':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json or 'name' not in input_json or 'location' not in input_json or 'thingspeak_config' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return add_greenhouse(self.catalog_connection, input_json['user_id'], input_json['name'], input_json['location'], input_json['thingspeak_config'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
  
        elif uri[0] == 'add_sensor_from_available':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'greenhouse_id' not in input_json or 'sensor_id' not in input_json or 'area_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return add_sensor_from_available(self.catalog_connection, input_json['greenhouse_id'], input_json['sensor_id'], input_json['area_id'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        elif uri[0] == 'add_area':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'greenhouse_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return add_area(self.catalog_connection, input_json['greenhouse_id'], input_json['name'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'remove_area_from_greenhouse':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'area_id' not in input_json or 'greenhouse_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return remove_area_from_greenhouse(self.catalog_connection, input_json['greenhouse_id'], input_json['area_id'])

            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"} 
            
        elif uri[0] == 'update_user_info':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json or 'username' not in input_json or 'email' not in input_json or 'new_password' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return update_user_info(self.catalog_connection, input_json['user_id'], input_json['username'], input_json['email'], input_json['new_password'])

            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"} 
            
        elif uri[0] == 'otp':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json or 'otp_code' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return otp(self.catalog_connection, input_json['user_id'], input_json['otp_code'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        elif uri[0] == 'verify_telegram_otp':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json or 'otp' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return verify_telegram_otp(self.catalog_connection, input_json['user_id'], input_json['otp'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        elif uri[0] == 'logout_telegram':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return logout_telegram(self.catalog_connection, input_json['user_id'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        elif uri[0] == 'update_thingspeak_config':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                write_log(f"Received input JSON: {input_json}")
                if 'greenhouse_id' not in input_json or 'channel_id' not in input_json or 'writeKey' not in input_json or 'readKey' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                
                return update_thingspeak_config(self.catalog_connection, input_json['greenhouse_id'], input_json['channel_id'], input_json['writeKey'], input_json['readKey'])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        else:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}

    def PUT(self, *uri, **params):
        cherrypy.response.status = 405
        return {"error": "METHOD NOT ALLOWED"}

    def DELETE(self, *uri, **params):
        if uri[0] == 'delete_event':
            try:
                if "device_id" not in params and "event_id" not in params:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}

                return delete_event(self.catalog_connection, params["device_id"], params["event_id"])
            
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        else:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}

    @cherrypy.tools.cors()
    def OPTIONS(self, *args, **kwargs):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return ''
    
if __name__ == "__main__":
    try:
        write_log("Catalog service starting...")

        # configuration of the server
        catalogClient = CatalogREST(get_db_connection())
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True,
                'tools.response_headers.on': True,
                'tools.response_headers.headers': [('Content-Type', 'application/json')],
                'tools.cors.on': True,
            },
        }
        cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
        cherrypy.tree.mount(catalogClient, '/', conf)
        cherrypy.engine.start()

    except Exception as e:
        write_log(f"Error starting the REST API: {e}")
        exit(1)