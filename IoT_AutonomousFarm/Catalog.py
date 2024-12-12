import cherrypy
import psycopg2
from psycopg2 import sql
import json

# configuration for the connection to the MQTT broker
configuration = {
    "mqtt_broker": "mqtt.eclipseprojects.io",
    "mqtt_port": 1883,
    "mqtt_topic": "",
    "keep_alive": 60
}

# class that implements the REST API of the Catalog
class CatalogService:
    # method to get a connection to the database
    def get_db_connection(self):
        conn = psycopg2.connect(
            dbname="smartfarm_db",  # db name
            user="iotproject",  # username postgre sql
            password="WeWillDieForIoT", # password postgre sql
            host="localhost"    # host
        )
        return conn

    # method called by a device to register itself in the system
    # i have used this method to register devices on the DB
    # @cherrypy.expose
    # @cherrypy.tools.json_out()  # automatically convert return value to JSON
    # def register_device(self, device_id, device_name, device_type, greenhouse_id):
    #     configuration["mqtt_topic"] = "greenhouse_" + str(greenhouse_id) + "/sensors"
    #     conn = self.get_db_connection()
    #     cur = conn.cursor()
    #     cur.execute("INSERT INTO devices (device_id, greenhouse_id, name, type, configuration) VALUES (%s, %s, %s, %s, %s)", 
    #         (device_id, greenhouse_id, device_name, device_type, json.dumps(configuration)))
    #     conn.commit()
    #     cur.close()
    #     conn.close()
    #     return "OK"
    
    # at the beginnig of the system each device should read from the Catalog the information about the system itself
    @cherrypy.expose
    @cherrypy.tools.json_out()  # automatically convert return value to JSON
    def get_device_configurations(self, device_id):
        if cherrypy.request.method == "GET":    # this method can be called only with GET
            conn = self.get_db_connection() # get the connection to the database
            cur = conn.cursor() # create a cursor to execute queries
            cur.execute("SELECT configuration FROM devices WHERE device_id = %s", (device_id, ))    # select from the db the configuration json file of the device
            configurations = cur.fetchone()
            cur.close()
            conn.close()

            return configurations[0]    # configuration is an array, return the first element
        else:    # if the method is called with other methods, return error 405
            raise cherrypy.HTTPError(405, "Invalid request method")
    
    # given the id of the device connector, return the list of sensors connected to it
    @cherrypy.expose
    @cherrypy.tools.json_out()  # automatically convert return value
    def get_sensors(self, device_id):
        if cherrypy.request.method == "GET":    # this method can be called only with GET
            conn = self.get_db_connection() # get the connection to the database
            cur = conn.cursor() # create a cursor to execute queries
            # the first query is to get the greenhouse_id of the device connector
            cur.execute("SELECT greenhouse_id FROM devices WHERE device_id = %s", (device_id,))
            # then the second one returns the list of sensors connected to the greenhouse
            cur.execute("SELECT * FROM sensors WHERE greenhouse_id = %s", (str(cur.fetchone()[0])))
            sensors = cur.fetchall()    # sensors is a list of values (tuples)
            cur.close()
            conn.close()
            
            # convert the list of sensors to a list of dictionaries, associating the values to the keys (columns of the db)
            sensors_list = []
            for sensor in sensors:  # for each sensor in the list
                sensor_dict = { # associate the values to the keys
                    'sensor_id': sensor[0],
                    'greenhouse_id': sensor[1],
                    'plant_id': sensor[2],
                    'type': sensor[3],
                    'thing_speak_channel_id': sensor[4],
                    'description': sensor[5],
                    'name': sensor[6],
                    'unit': sensor[7]
                }
                sensors_list.append(sensor_dict)    # create a dictionary containing the information of each sensor

            return {'sensors': sensors_list}
        else:   # if the method is called with other methods, return error 405
            raise cherrypy.HTTPError(405, "Invalid request method")
    
if __name__ == "__main__":
    # configuration of the server
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
    cherrypy.quickstart(CatalogService())