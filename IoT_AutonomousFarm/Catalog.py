import cherrypy
import psycopg2
from psycopg2 import sql
import json
import datetime

configuration = {
    "mqtt_broker": "mqtt.eclipseprojects.io",
    "mqtt_port": 1883,
    "mqtt_topic": "",
    "keep_alive": 60
}

class CatalogService:
    def get_db_connection(self):
        conn = psycopg2.connect(
            dbname="smartfarm_db",
            user="iotproject",
            password="WeWillDieForIoT",
            host="localhost"
        )
        return conn

    # method called by a device to register itself in the system
    @cherrypy.expose
    @cherrypy.tools.json_out()  # automatically convert return value to JSON
    def register_device(self, device_id, device_name, device_type, greenhouse_id):
        configuration["mqtt_topic"] = "greenhouse_" + str(greenhouse_id) + "/sensors"
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO devices (device_id, greenhouse_id, name, type, configuration) VALUES (%s, %s, %s, %s, %s)", 
            (device_id, greenhouse_id, device_name, device_type, json.dumps(configuration)))
        conn.commit()
        cur.close()
        conn.close()
        return "OK"
    
    # at the beginnig of the system each device should read from the Catalog the information about the system itself
    @cherrypy.expose
    @cherrypy.tools.json_out()  # automatically convert return value to JSON
    def get_device_configurations(self, device_id):
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT configuration FROM devices WHERE device_id = %s", (device_id, ))
        configurations = cur.fetchone()
        cur.close()
        conn.close()

        return configurations[0]
    
    # given the id of the device connector, return the list of sensors connected to it
    @cherrypy.expose
    @cherrypy.tools.json_out()  # automatically convert return value
    def get_sensors(self, device_id):
        conn = self.get_db_connection()
        cur = conn.cursor()
        # the first query is to get the greenhouse_id of the device connector
        cur.execute("SELECT greenhouse_id FROM devices WHERE device_id = %s", (device_id,))
        # then the second one returns the list of sensors connected to the greenhouse
        cur.execute("SELECT * FROM sensors WHERE greenhouse_id = %s", (str(cur.fetchone()[0])))
        sensors = cur.fetchall()
        cur.close()
        conn.close()
        
        # convert the list of sensors to a list of dictionaries
        sensors_list = []
        for sensor in sensors:
            sensor_dict = {
                'sensor_id': sensor[0],
                'greenhouse_id': sensor[1],
                'plant_id': sensor[2],
                'type': sensor[3],
                'thing_speak_channel_id': sensor[4],
                'description': sensor[5],
                'name': sensor[6],
                'unit': sensor[7]
            }
            sensors_list.append(sensor_dict)

        return {'sensors': sensors_list}
    
if __name__ == "__main__":
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
    cherrypy.quickstart(CatalogService())