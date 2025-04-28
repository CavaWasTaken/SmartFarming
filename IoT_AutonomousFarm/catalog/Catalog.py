import cherrypy
import psycopg2
from psycopg2 import sql
import jinja2
import bcrypt
import json
import os
from cherrypy_cors import CORS 
import jwt
import datetime
import secrets

from MqttClient import MqttClient   # import the MqttClient class

# Setup jinja2 
# relative path to the template directory
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '../ui/webApp')
env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH))

# read the mqtt information of the broker from the json file
with open("./Catalog_config.json", "r") as config_fd:
    config = json.load(config_fd)   # read the configuration from the json file
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # read the mqtt broker address
    mqtt_port = config["mqtt_connection"]["mqtt_port"]  # read the mqtt broker port
    keep_alive = config["mqtt_connection"]["keep_alive"]    # read the keep alive time of the mqtt connection

# class that implements the REST API of the Catalog

# method to get a connection to the database
def get_db_connection():
    return psycopg2.connect(
        dbname="smartfarm_db",  # db name
        user="iotproject",  # username postgre sql
        password="WeWillDieForIoT", # password postgre sql
        host="localhost",    # host,
        port="5433" # port
    )

def cors():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

cherrypy.tools.cors = cherrypy.Tool('before_handler', cors)

# function to write in a log file messages from MQTT client
def write_log(message):
    with open("./MQTT_Catalog.log", "a") as log_file:
        log_file.write(f"{message}\n")

# function triggered when a message of interest is received by the Catalog
# Because the Catalog is only a publisher, this function should never be used
def on_message(client, userdata, message):
    write_log(f"Received message: {message.payload.decode()}")    # write in the log file the action received

# method to get all the greenhouses in the system
def get_all_greenhouses(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM greenhouses")
        greenhouses = cur.fetchall()
        if not greenhouses:
            raise cherrypy.HTTPError(404, "no greenhouses found")

        greenhouse_list = []
        for greenhouse in greenhouses:
            thingspeak_config = greenhouse[4]  # Column where JSON is stored

            # Convert JSON string to dictionary if needed
            if isinstance(thingspeak_config, str) and thingspeak_config.strip():
                try:
                    thingspeak_config = json.loads(thingspeak_config)
                except json.JSONDecodeError:
                    print(f"ERROR: Invalid JSON in greenhouse ID {greenhouse[0]}")  
                    thingspeak_config = {}  

            # Ensure fields exist
            if not isinstance(thingspeak_config, dict):
                thingspeak_config = {}

            # Debug: Print actual values before sending to Jinja
            print(f"Greenhouse ID: {greenhouse[0]} | thingspeak_config: {json.dumps(thingspeak_config, indent=2)}")

            greenhouse_dict = {
                'greenhouse_id': greenhouse[0],
                'user_id': greenhouse[1],
                'name': greenhouse[2],
                'location': greenhouse[3],
                'thingspeak_config': thingspeak_config  
            }

            greenhouse_list.append(greenhouse_dict)

        # Debugging: Print full list
        print("Final greenhouse_list:\n", json.dumps(greenhouse_list, indent=2))

        template = env.get_template("greenhouses.html")
        return template.render(greenhouse_list=greenhouse_list)

# given the id of the device and its name, return its information
def get_device_info(conn, device_id, device_name):
    with conn.cursor() as cur: # create a cursor to execute queries
        cur.execute(sql.SQL("SELECT * FROM devices WHERE device_id = %s AND name = %s"), [device_id, device_name])    # the query is to get the device info of the device
        device = cur.fetchone() # device is a tuple
        if device is None:  # if the device does not exist, return error 404
            raise cherrypy.HTTPError(404, "Device not found")
        device_dict = { # associate the values to the keys
            'device_id': device[0],
            'greenhouse_id': device[1],
            'name': device[2],
            'type': device[3],
            'params': device[4]
        }

        return device_dict
    
# given the id of the greenhouse, return its location
def get_greenhouse_location(conn, greenhouse_id):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        # check if the greenhouse exists
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

# given the id of the device, return the list of sensors connected to it
def get_sensors(conn, device_id, device_name):
    try: 
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur: # create a cursor to execute queries
            # check if the device exists
            cur.execute(sql.SQL("SELECT * FROM devices WHERE device_id = %s AND name = %s"), [device_id, device_name])
            result = cur.fetchone()
            if result is None:  # if the device doesn't exist
                cherrypy.response.status = 404
                return {"error": "Unexisting device"}

            # the first query is to get the greenhouse_id of the device
            cur.execute(sql.SQL("SELECT greenhouse_id FROM devices WHERE device_id = %s AND name = %s"), [device_id, device_name])
            # then the second one returns the list of sensors connected to the greenhouse
            result = cur.fetchone()
            if result is None:   # if the greenhouse does not exist, return error 404
                cherrypy.response.status = 404
                return {"error": "Greenhouse not found"}
            greenhouse_id = result[0]
            
            # personalize the query based on the device name, cause each device connector is interested in different sensors
            authorized_devices = ["DeviceConnector", "DataAnalysis", "ThingSpeakAdaptor", "WebApp", "TelegramBot"]
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
                    'greenhouse_id': sensor[1],
                    'type': sensor[2],
                    'name': sensor[3],
                    'unit': sensor[4],
                    'threshold': sensor[5],
                    'domain': sensor[6]
                }
                sensors_list.append(sensor_dict)    # create a dictionary containing the information of each sensor

            return {'sensors': sensors_list}
        
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}
    
# return the info about the greenhouse by greenhouse_id. The device id is used to see if who made the request is connected to the greenhouse
def get_greenhouse_info(conn, greenhouse_id, device_id):
    with conn.cursor() as cur: # create a cursor to execute queries
        # check if the device is connected to the greenhouse
        cur.execute(sql.SQL("SELECT * FROM devices WHERE device_id = %s AND greenhouse_id = %s"), [device_id, greenhouse_id])
        device = cur.fetchone() # device is a tuple
        if device is None:  # if the device is not connected to the greenhouse, return error 404
            raise cherrypy.HTTPError(404, "Device not connected to the greenhouse")
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
    
# instead of using a json, think to use an env variable
with open("Catalog_config.json", "r") as config_file:
    config = json.load(config_file)
    
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
    
# function to perform user login
def login(conn, username, password):
    try:
        # check if the connection is closed
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        
        with conn.cursor() as cur:
            # check if the username exists
            cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
            user = cur.fetchone()

            if user is None:
                cherrypy.response.status = 401
                return {"error": "Incorrect username"}

            stored_hash = bytes(user[3])  # convert memoryview to bytes

            # Check the hashed password
            if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                cherrypy.response.status = 401
                return {"error": "Incorrect password"}
            
            # generate JWT token
            token = generate_token(user[0], user[1])
            cherrypy.response.headers['Authorization'] = f"Bearer {token}"
            # return the user info

            return {
                'message': 'Login successful', 
                'user_id': user[0],
                'username': user[1],
                'email': user[2],
                'token': token
            }
                    
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

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
    
# function to return everything about a greenhouse (plants, sensors, devices)
def get_greenhouse_configurations(conn, greenhouse_id):
    with conn.cursor() as cur:
        # get sensors of the greenhouse
        cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s"), [greenhouse_id])
        sensors = cur.fetchall()
        if sensors is None:
            raise cherrypy.HTTPError(404, "No sensors found")

        sensors_list = []
        for sensor in sensors:
            sensor_dict = {
                'sensor_id': sensor[0],
                'greenhouse_id': sensor[1],
                'type': sensor[2],
                'name': sensor[3],
                'unit': sensor[4],
                'threshold': sensor[5],
                'domain': sensor[6]
            }
            sensors_list.append(sensor_dict)

        # get devices of the greenhouse
        cur.execute(sql.SQL("SELECT * FROM devices WHERE greenhouse_id = %s"), [greenhouse_id])
        devices = cur.fetchall()
        if devices is None:
            raise cherrypy.HTTPError(404, "No devices found")
        
        devices_list = []
        for device in devices:
            device_dict = {
                'device_id': device[0],
                'greenhouse_id': device[1],
                'name': device[2],
                'type': device[3],
                'params': device[4]
            }
            devices_list.append(device_dict)

        # get plants of the greenhouse
        cur.execute(sql.SQL("SELECT plant_id FROM greenhouse_plants WHERE greenhouse_id = %s"), [greenhouse_id])
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
                'desired_thresholds': plant[3],
            }
            plants_list.append(plant_dict)

        return {'sensors': sensors_list, 'devices': devices_list, 'plants': plants_list}
    
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
        
# function to get the entire list of plants
def get_all_plants(conn):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM plants"))
        plants = cur.fetchall()
        if plants is None:
            raise cherrypy.HTTPError(404, "No plants found")
        
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
    
# function to add a plant to a greenhouse
def add_plant_to_greenhouse(conn, greenhouse_id, plant_id):
    with conn.cursor() as cur:
        # check if the plant is already in the greenhouse
        cur.execute(sql.SQL("SELECT * FROM greenhouse_plants WHERE greenhouse_id = %s AND plant_id = %s"), [greenhouse_id, plant_id])
        plant = cur.fetchone()
        if plant is not None:
            raise cherrypy.HTTPError(404, "Plant already in the greenhouse")
        # insert the new plant in the greenhouse
        try:
            cur.execute(sql.SQL("INSERT INTO greenhouse_plants (greenhouse_id, plant_id) VALUES (%s, %s)"), [greenhouse_id, plant_id])
            conn.commit()
            # return the updated list of plants in the greenhouse
            cur.execute(sql.SQL("SELECT plant_id FROM greenhouse_plants WHERE greenhouse_id = %s"), [greenhouse_id])
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
        
# function to remove a plant from the greenhouse
def remove_plant_from_greenhouse(conn, greenhouse_id, plant_id):
    with conn.cursor() as cur:
        # check if the plant is in the greenhouse
        cur.execute(sql.SQL("SELECT * FROM greenhouse_plants WHERE greenhouse_id = %s AND plant_id = %s"), [greenhouse_id, plant_id])
        plant = cur.fetchone()
        if plant is None:
            raise cherrypy.HTTPError(404, "Plant not in the greenhouse")
        # remove the plant from the greenhouse
        try:
            cur.execute(sql.SQL("DELETE FROM greenhouse_plants WHERE greenhouse_id = %s AND plant_id = %s"), [greenhouse_id, plant_id])
            conn.commit()
            # return the updated list of plants in the greenhouse
            cur.execute(sql.SQL("SELECT plant_id FROM greenhouse_plants WHERE greenhouse_id = %s"), [greenhouse_id])
            cur.execute(sql.SQL("SELECT plant_id FROM greenhouse_plants WHERE greenhouse_id = %s"), [greenhouse_id])
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
        
#function to get all scheduled events where current time is between start_time and end_time for a greenhouse
def get_all_scheduled_events(conn):
    with conn.cursor() as cur:
        # Get current timestamp
        current_time = datetime.datetime.now()
        # Select only columns without any timestamp because seems that python cannot convert psql timestamps to JSON
        cur.execute(sql.SQL("SELECT greenhouse_id, event_type, frequency, status FROM scheduled_events WHERE %s >= start_time AND (%s <= end_time or end_time is NULL)"), [current_time, current_time])
        events = cur.fetchall()
        if not events:
            raise cherrypy.HTTPError(404, f"No events found")
        
        event_list = []
        for event in events:
            event_list.append({'greenhouse_id': event[0],'event_type':event[1], 'frequency':event[2], 'status':event[3]})
        
        return event_list

# Function to add one event in the DB
def add_event(conn, greenhouse_id, event_type, start_time, end_time, frequency):
    with conn.cursor() as cur:
        try:
            # Add the new event in the DB
            cur.execute(sql.SQL("INSERT INTO scheduled_events (greenhouse_id, event_type, start_time, end_time, frequency, status) VALUES (%s, %s, %s, %s, %s, %s)"), \
                        [greenhouse_id, event_type, start_time, end_time, frequency, "Pending"])
            conn.commit()
        except:
            raise cherrypy.HTTPError(500, "Internal error")

# add new greenhouse 
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
                [name, location, user_id, json.dumps(thingspeak_config) if thingspeak_config else None]
            )
            greenhouse = cur.fetchone()
            conn.commit()

            return {
                'message': 'Greenhouse added successfully',
                'greenhouse_id': greenhouse[0],
                'name': greenhouse[1],
                'location': greenhouse[2]
            }

    except psycopg2.errors.NotNullViolation as e:
        conn.rollback()
        cherrypy.response.status = 400
        return {"error": f"Missing required fields: {str(e)}"}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}


# function to get the entire list of sensors
def get_all_sensors(conn):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM availablesensors;"))
        sensors = cur.fetchall()
        if sensors is None:
            raise cherrypy.HTTPError(404, "No sensors found")
        
        sensors_list = []
        for sensor in sensors:
            psensor_dict = {
                'sensor_id': sensor[0],
                'name': sensor[1],
                'type': sensor[2],
            }
            sensors_list.append(psensor_dict)
        
        return {'sensors': sensors_list}
    

# add sensors for greenhouses 
def add_sensor_from_available(conn, greenhouse_id, sensor_id):
    with conn.cursor() as cur:
        try:
            # Step 1: Get sensor info from availablesensors table
            cur.execute(
                sql.SQL("SELECT type, name, unit, threshold_range, domain FROM availablesensors WHERE sensor_id = %s"),
                [sensor_id]
            )
            sensor = cur.fetchone()

            if sensor is None:
                raise cherrypy.HTTPError(404, "Sensor not found in available sensors")

            sensor_type, name, unit, threshold_range, domain = sensor


            if isinstance(threshold_range, dict):
                threshold_range = json.dumps(threshold_range)

            if isinstance(domain, dict):
                domain = json.dumps(domain)

            # Step 2: Insert into sensors table
            cur.execute(
                sql.SQL("""
                    INSERT INTO sensors (greenhouse_id, type, name, unit, threshold_range, domain)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING sensor_id
                """),
                [greenhouse_id, sensor_type, name, unit, threshold_range, domain]
            )
            new_sensor_id = cur.fetchone()[0]
            conn.commit()

            return {
                'message': 'Sensor added successfully',
                'sensor_id': new_sensor_id,
                'greenhouse_id': greenhouse_id,
                'type': sensor_type,
                'name': name,
                'unit': unit,
                'threshold_range': threshold_range,
                'domain': domain
            }

        except psycopg2.Error as e:
            conn.rollback()
            raise cherrypy.HTTPError(500, f"Database error: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise cherrypy.HTTPError(500, f"Internal error: {str(e)}")

class CatalogREST(object):
    exposed = True

    def __init__(self, catalog_connection):
        self.catalog_connection = catalog_connection

    @cherrypy.tools.cors()  # enable CORS for POST requests
    @cherrypy.tools.json_out()  # output JSON response
    def GET(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        elif uri[0] == 'get_sensors':
            return get_sensors(self.catalog_connection, params['device_id'], params['device_name'])
        elif uri[0] == 'get_greenhouse_info':
            return get_greenhouse_info(self.catalog_connection, params['greenhouse_id'], params['device_id'])
        elif uri[0] == 'get_device_info':
            return get_device_info(self.catalog_connection, params['device_id'], params['device_name'])
        elif uri[0] == 'get_greenhouse_location':
            return get_greenhouse_location(self.catalog_connection, params['greenhouse_id'])
        elif uri[0] == 'get_user_greenhouses':
            return get_user_greenhouses(self.catalog_connection, params['user_id'], params['username'])
        elif uri[0] == 'get_greenhouse_configurations':
            return get_greenhouse_configurations(self.catalog_connection, params['greenhouse_id'])
        elif uri[0] == 'get_all_plants':
            return get_all_plants(self.catalog_connection)
        elif uri[0] == 'get_all_scheduled_events':
            return get_all_scheduled_events(self.catalog_connection)
        elif uri[0] == 'get_all_sensors':
            return get_all_sensors(self.catalog_connection)
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
    
    @cherrypy.tools.cors()  # enable CORS for POST requests
    @cherrypy.tools.encode(encoding='utf-8')    # encode the request body
    @cherrypy.tools.json_out()  # output JSON response
    def POST(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        elif uri[0] == 'register':
            input_json = json.loads(cherrypy.request.body.read())
            return register(self.catalog_connection, input_json['username'], input_json['email'], input_json['password'])
        elif uri[0] == 'login':
            input_json = json.loads(cherrypy.request.body.read())
            return login(self.catalog_connection, input_json['username'], input_json['password'])
        elif uri[0] == 'set_sensor_threshold':
            input_json = json.loads(cherrypy.request.body.read())
            return set_sensor_threshold(self.catalog_connection, input_json['sensor_id'], input_json['threshold'])
        elif uri[0] == 'add_plant_to_greenhouse':
            input_json = json.loads(cherrypy.request.body.read())
            return add_plant_to_greenhouse(self.catalog_connection, input_json['greenhouse_id'], input_json['plant_id'])
        elif uri[0] == 'remove_plant_from_greenhouse':
            input_json = json.loads(cherrypy.request.body.read())
            return remove_plant_from_greenhouse(self.catalog_connection, input_json['greenhouse_id'], input_json['plant_id'])
        elif uri[0] == 'add_event':
            input_json = json.loads(cherrypy.request.body.read())
            return add_event(self.catalog_connection, input_json['greenhouse_id'], input_json['event_type'], input_json['start_time'], input_json['end_time'], input_json['frequency'])
        elif uri[0] == 'add_greenhouse':
            input_json = json.loads(cherrypy.request.body.read())
            return add_greenhouse(self.catalog_connection, input_json['user_id'], input_json['name'], input_json['location'], input_json['thingspeak_config'])
        elif uri[0] == 'add_sensor_from_available':
            input_json = json.loads(cherrypy.request.body.read())
            return add_sensor_from_available(self.catalog_connection, input_json['greenhouse_id'], input_json['sensor_id'])
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')

    def PUT(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')
        
    def DELETE(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')

    @cherrypy.tools.cors()
    def OPTIONS(self, *args, **kwargs):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return ''
    
if __name__ == "__main__":
    # configuration of the server
    catalogClient = CatalogREST(get_db_connection())
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')],
            'tools.cors.on': True,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.abspath('../ui/webApp')
        },
        '/ui':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.abspath("../ui/webApp")
        }
    }
    cherrypy.config.update({'server.socket_host': '127.0.0.1', 'server.socket_port': 8080})
    cherrypy.tree.mount(catalogClient, '/', conf)
    cherrypy.engine.start()

    # Initialize MQTT client
    # client = MqttClient(mqtt_broker, mqtt_port, keep_alive, "Catalog", on_message, write_log)    # create a MQTT client object
    # client.start()  # start the MQTT client

    # cherrypy.engine.block()