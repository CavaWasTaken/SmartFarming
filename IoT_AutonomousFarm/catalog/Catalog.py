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
        if device_name == "DeviceConnector" or device_name == "DataAnalysis" or device_name == "ThingSpeakAdaptor":    # device connector is interested in all the sensors connected to the greenhouse
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
            'thingspeak_channel_read_key': greenhouse[4],
            'thingspeak_channel_write_key': greenhouse[5],
            'token': greenhouse[6]
        }
        
        return greenhouse_dict


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
        elif uri[0] == 'get_greenhouse_info':
            return get_greenhouse_info(self.catalog_connection, params['greenhouse_id'], params['device_id'])
        elif uri[0] == 'get_device_info':
            return get_device_info(self.catalog_connection, params['device_id'], params['device_name'])
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        
    @cherrypy.tools.json_out()  # automatically convert return value
    def POST(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')
        
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
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
    cherrypy.tree.mount(catalogClient, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()