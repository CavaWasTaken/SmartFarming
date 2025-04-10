import os
import bcrypt
import jinja2
import cherrypy
import psycopg2
from psycopg2 import sql
import json


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '/Users/thatsnegar/SmartFarming/IoT_AutonomousFarm/ui/webApp')  # Path to templates directory
env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH))


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

def getregister():
  cherrypy.response.headers['Content-Type'] = 'text/html'  # Set the Content-Type header
  template = env.get_template('registerform.html')
  return template.render().encode('utf-8')

def getlogin():
  cherrypy.response.headers['Content-Type'] = 'text/html'  # Set the Content-Type header
  template = env.get_template('loginform.html')
  return template.render().encode('utf-8')
    
def register(conn, username, email, password):
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
        
        return {
            'message': 'User registered successfully',
            'user_id': user[0],
            'username': user[1],
            'email': user[2]
        }


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
    
# function to get all the greenhouses

def get_all_greenhouses(conn):
    cherrypy.response.headers['Content-Type'] = 'text/html'  # Set the Content-Type header

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

        # return json.dumps(greenhouse_list, indent=2)  # Return JSON response

        template = env.get_template("greenhouses.html")
        return template.render(greenhouse_list=greenhouse_list)


# get all the greenhouses sensors
def get_all_sensors(conn, greenhouse_id):
     cherrypy.response.headers['Content-Type'] = 'text/html'  # Set the Content-Type header

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

        template = env.get_template("GHSensors.html")
        return template.render(sensors_list=sensors_list)
        # return json.dumps(sensors_list, indent=2)  # Return JSON response
  

# Get all palnts 
def get_all_plants(conn):
    cherrypy.response.headers['Content-Type'] = 'text/html'  # Set the Content-Type header
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
        
        # return json.dumps(plants_list, indent=2)  # Return JSON response
        template = env.get_template("plants.html")
        return template.render(plants_list=plants_list)


# function used by the user to change the threshold of a sensor
def set_sensor_threshold(conn, sensor_id, threshold):
    
    input_json = cherrypy.request.json
    print(f"📌 Received JSON: {input_json}")

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
        

        
class CatalogREST(object):
    exposed = True

    def __init__(self, catalog_connection):
        self.catalog_connection = catalog_connection

    @cherrypy.tools.encode(encoding='utf-8')
    def GET(self, *uri, **params):
        if len(uri) == 0:
           return 'notfound'
        elif uri[0] == 'getregister':
            return getregister()
        elif uri[0] == 'getlogin':
            return getlogin()
        elif uri[0] == 'greenhouses':
             return get_all_greenhouses(conn=self.catalog_connection)
        elif uri[0] == 'get_all_sensors':
            return get_all_sensors(self.catalog_connection, params['greenhouse_id'])
        elif uri[0] == 'get_all_plants':
            return get_all_plants(self.catalog_connection)
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        
    @cherrypy.tools.cors()
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    @cherrypy.tools.allow(methods=['POST'])
    def POST(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        elif uri[0] == 'register':
            input_json = cherrypy.request.json
            return register(self.catalog_connection, input_json['username'], input_json['email'], input_json['password'])
        elif uri[0] == 'login':
            input_json = cherrypy.request.json
            return login(self.catalog_connection, input_json['username'], input_json['password'])
        elif uri[0] == 'set_sensor_threshold':
            input_json = json.loads(cherrypy.request.body.read())
            return set_sensor_threshold(self.catalog_connection, input_json['sensor_id'], input_json['threshold'])
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')

    @cherrypy.tools.cors()
    def OPTIONS(self, *args, **kwargs):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return ''

    @cherrypy.tools.json_out()
    def PUT(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')
        
    @cherrypy.tools.json_out()
    def DELETE(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')

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
            'tools.staticdir.dir': '/Users/thatsnegar/SmartFarming/IoT_AutonomousFarm/ui/webApp'

        },
         '/ui':{
             'tools.staticdir.on': True,
             'tools.staticdir.dir': os.path.abspath("webApp")
         }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 5004})
    cherrypy.tree.mount(catalogClient, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()