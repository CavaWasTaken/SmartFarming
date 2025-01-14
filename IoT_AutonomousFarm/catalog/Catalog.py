import cherrypy
import psycopg2
from psycopg2 import sql

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

# given the id of the device connector, return the list of sensors connected to it
def get_sensors(conn, device_id, device_name):
    with conn.cursor() as cur: # create a cursor to execute queries
        # the first query is to get the greenhouse_id of the device connector
        cur.execute(sql.SQL("SELECT greenhouse_id FROM devices WHERE device_id = %s AND name = %s"), [device_id, device_name])
        # then the second one returns the list of sensors connected to the greenhouse
        greenhouse_id = cur.fetchone()[0]
        # personalize the query based on the device name, cause each device connector is interested in different sensors
        if device_name == "DeviceConnector" or device_name == "DataAnalysis" or device_name == "ThingSpeakAdaptor":    # device connector is interested in all the sensors connected to the greenhouse
            cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s"),  [greenhouse_id,])
        elif device_name == "HumidityManagement":   # humidity management is interested in humidity and soil moisture sensors
            cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'Humidity' OR type = 'SoilMoisture'"), [greenhouse_id,])
        elif device_name == "LightManagement":  # light management is interested in light intensity and temperature sensors
            cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'LightIntensity' OR type = 'Temperature'"), [greenhouse_id,])
        elif device_name == "NutrientManagement":   # nutrient management is interested in NPK and pH sensors
            cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'NPK' OR type = 'pH' OR type = 'SoilMoisture'"), [greenhouse_id,])
        sensors = cur.fetchall()    # sensors is a list of values (tuples)
        
        # convert the list of sensors to a list of dictionaries, associating the values to the keys (columns of the db)
        sensors_list = []
        for sensor in sensors:  # for each sensor in the list
            sensor_dict = { # associate the values to the keys
                'sensor_id': sensor[0],
                'greenhouse_id': sensor[1],
                'plant_id': sensor[2],
                'type': sensor[3],
                'name': sensor[4],
                'unit': sensor[5],
                'threshold': sensor[6],
                'thing_speak_channel_id': sensor[7]
            }
            sensors_list.append(sensor_dict)    # create a dictionary containing the information of each sensor

        return {'sensors': sensors_list}

# given the information of the sensor, return the id of the sensor
def get_sensor_id(conn, device_id, device_name, greenhouse_id, plant_id, sensor_name, sensor_type):
    with conn.cursor() as cur: # create a cursor to execute queries
        cur.execute(sql.SQL("SELECT * FROM devices WHERE device_id = %s AND name = %s"), [device_id, device_name])    # check if the device connector exists
        if cur.rowcount == 0:   # if the device connector does not exist, return error 404
            raise cherrypy.HTTPError(404, "Device not found")
        # the query is to get the sensor id of the sensor
        if plant_id == 'ALL':
            cur.execute(sql.SQL("SELECT sensor_id FROM sensors WHERE greenhouse_id = %s AND plant_id IS NULL AND name = %s AND type = %s"), [greenhouse_id, sensor_name, sensor_type])
        else:
            cur.execute(sql.SQL("SELECT sensor_id FROM sensors WHERE greenhouse_id = %s AND plant_id = %s AND name = %s AND type = %s"), [greenhouse_id, plant_id, sensor_name, sensor_type])
        sensor_id = cur.fetchone()[0]
        return {'sensor_id': sensor_id}

class CatalogREST(object):
    exposed = True

    def __init__(self, catalog_connection):
        self.catalog_connection = catalog_connection

    @cherrypy.tools.json_out()  # automatically convert return value
    def GET(self, *uri, **params):
        if len(uri) == 0:
           raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        elif uri[0] == 'get_sensors':
            return get_sensors(self.catalog_connection, params['device_id'], params['device_name'])
        elif uri[0] == 'get_sensor_id':
            return get_sensor_id(self.catalog_connection, params['device_id'], params['device_name'], params['greenhouse_id'], params['plant_id'], params['sensor_name'], params['sensor_type'])
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        
    @cherrypy.tools.json_out()  # automatically convert return value
    def POST(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        
    @cherrypy.tools.json_out()  # automatically convert return value        
    def PUT(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        
    @cherrypy.tools.json_out()  # automatically convert return value
    def DELETE(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        
if __name__ == "__main__":
    # configuration of the server
    catalogClient = CatalogREST(get_db_connection())
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
    cherrypy.tree.mount(catalogClient, '/', conf)
    cherrypy.engine.start()