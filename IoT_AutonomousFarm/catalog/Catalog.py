import cherrypy
import psycopg2
from psycopg2 import sql
import jinja2
import bcrypt
import json
import os
from cherrypy_cors import CORS 


# Setup jinja2 
Template_path = "/Users/thatsnegar/SmartFarming/IoT_AutonomousFarm/ui/webApp"
env = jinja2.Environment(loader=jinja2.FileSystemLoader(Template_path))


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


# get all the greenhouses 

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

# given the id of the device connector and the name of the device, return the information of the device
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
    
# given the id of the greenhouse, return the location of the greenhouse
def get_greenhouse_location(conn, greenhouse_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT location FROM greenhouses WHERE greenhouse_id = %s"), [greenhouse_id,])
        location = cur.fetchone()[0]
        if location is None:
            raise cherrypy.HTTPError(404, "Greenhouse not found")
        return {'location': location}

# given the id of the device connector, return the list of sensors connected to it
def get_sensors(conn, device_id, device_name):
    with conn.cursor() as cur: # create a cursor to execute queries
        # the first query is to get the greenhouse_id of the device
        cur.execute(sql.SQL("SELECT greenhouse_id FROM devices WHERE device_id = %s AND name = %s"), [device_id, device_name])
        # then the second one returns the list of sensors connected to the greenhouse
        greenhouse_id = cur.fetchone()[0]
        if greenhouse_id is None:   # if the greenhouse does not exist, return error 404
            raise cherrypy.HTTPError(404, "Greenhouse not found")
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
            raise cherrypy.HTTPError(404, "No sensors found")
        
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
@cherrypy.tools.json_out()
@cherrypy.tools.json_in()
@cherrypy.tools.allow(methods=['POST'])
def register(conn, username, email, password):
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    with conn.cursor() as cur:
        # check if the username already exists
        cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
        user = cur.fetchone()
        if user is not None:
            raise cherrypy.HTTPError(409, "Username already exists")
        # insert the new user in the db
        try:
            # salt hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur.execute(sql.SQL("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"), [username, email, hashed_password])
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            raise cherrypy.HTTPError(409, "Username already exists")
        except psycopg2.errors.NotNullViolation:
            raise cherrypy.HTTPError(400, "Username, email or password not provided")
        except:
            raise cherrypy.HTTPError(500, "Internal error")
        
        cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
        user = cur.fetchone()

        if user is None:
            raise cherrypy.HTTPError(401, "Incorrect username")
        
        return json.dumps({
            'message': 'User registered successfully',
              'user_id': user[0],
                'username': user[1],
                  'email': user[2]
                  }),201
    
# function to perform user login
def login(conn, username, password):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
        user = cur.fetchone()

        if user is None:
            raise cherrypy.HTTPError(401, "Incorrect username")

        stored_hash = bytes(user[3])  # Convert memoryview to bytes

        # Check the hashed password
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            raise cherrypy.HTTPError(401, "Incorrect password")

        return {'message': 'Login successful', 'user_id': user[0], 'username': user[1], 'email': user[2]}

# function to return the greenhouses of a user
def get_user_greenhouses(conn, user_id):
    with conn.cursor() as cur:
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
            raise cherrypy.HTTPError(409, "Plant already in the greenhouse")
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

class CatalogREST(object):
    exposed = True

    def __init__(self, catalog_connection):
        self.catalog_connection = catalog_connection

    # @cherrypy.tools.json_out()  # automatically convert return value
    def GET(self, *uri, **params):
        if len(uri) == 0:
           return get_all_greenhouses(conn=self.catalog_connection)
        elif uri[0] == 'get_sensors':
            return get_sensors(self.catalog_connection, params['device_id'], params['device_name'])
        elif uri[0] == 'get_greenhouse_info':
            return get_greenhouse_info(self.catalog_connection, params['greenhouse_id'], params['device_id'])
        elif uri[0] == 'get_device_info':
            return get_device_info(self.catalog_connection, params['device_id'], params['device_name'])
        elif uri[0] == 'get_greenhouse_location':
            return get_greenhouse_location(self.catalog_connection, params['greenhouse_id'])
        elif uri[0] == 'get_user_greenhouses':
            return get_user_greenhouses(self.catalog_connection, params['user_id'])
        elif uri[0] == 'get_greenhouse_configurations':
            return get_greenhouse_configurations(self.catalog_connection, params['greenhouse_id'])
        elif uri[0] == 'get_all_plants':
            return get_all_plants(self.catalog_connection)
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        
    @cherrypy.tools.json_out()  # automatically convert return value
    # @cherrypy.tools.json_in()  # automatically convert return value
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
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')

    @cherrypy.tools.json_out()  # automatically convert return value        
    def PUT(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')
        
    @cherrypy.tools.json_out()  # automatically convert return value
    def DELETE(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')
    
    


if __name__ == "__main__":
    # configuration of the server
    catalogClient = CatalogREST(get_db_connection())
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        },
        '/ui':{
            'tools.staticdir.on': True,
             'tools.staticdir.dir': os.path.abspath("/Users/thatsnegar/SmartFarming/IoT_AutonomousFarm/ui/webApp")
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
    cherrypy.tree.mount(catalogClient, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()