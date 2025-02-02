import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests
import cherrypy

# each time that the device starts, we clear the log file
with open("./logs/DataAnalysis.log", "w") as log_file:
    pass
    
# MQTT Sub

# read the device_id and mqtt information of the broker from the json file
with open("./DataAnalysis_config.json", "r") as config_fd:
    config = json.load(config_fd)
    catalog_url = config["catalog_url"]
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
    mqtt_port = config["mqtt_connection"]["mqtt_port"]
    keep_alive = config["mqtt_connection"]["keep_alive"]

global N

def handle_message(topic, val):
    with open("./logs/DataAnalysis.log", "a") as log_file:
        global mean_temperature, mean_humidity, mean_light, mean_soil_moisture, mean_pH, mean_N, mean_P, mean_K
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        # log_file.write(f"Received message from {greenhouse} - {plant} - {sensor_name} - {sensor_type}\n")

        if sensor_type == "Temperature":    # keeps track of the mean temperature
            if len(temperatures) == N_values:    # if the list of temperatures is N_values, remove the first element (the oldest)
                temperatures.pop(0)
            temperatures.append(val)    # append the new temperature to the list
            mean_temperature = sum(temperatures) / len(temperatures)    # calculate the mean temperature
            log_file.write(f"Mean temperature: {mean_temperature}\n")
        elif sensor_type == "Humidity":   # keeps track of the mean humidity
            if len(humidities) == N_values:
                humidities.pop(0)
            humidities.append(val)
            mean_humidity = sum(humidities) / len(humidities)
            log_file.write(f"Mean humidity: {mean_humidity}\n")
        elif sensor_type == "LightIntensity":    # keeps track of the mean light
            if len(light_intensities) == N_values:
                light_intensities.pop(0)
            light_intensities.append(val)
            mean_light = sum(light_intensities) / len(light_intensities)
            log_file.write(f"Mean light intensity: {mean_light}\n")
        elif sensor_type == "SoilMoisture":    # keeps track of the mean soil moisture
            if len(soil_moistures) == N_values:
                soil_moistures.pop(0)
            soil_moistures.append(val)
            mean_soil_moisture = sum(soil_moistures) / len(soil_moistures)
            log_file.write(f"Mean soil moisture: {mean_soil_moisture}\n")
        elif sensor_type == "pH":   # keeps track of the mean pH
            if len(pH_values) == N_values:
                pH_values.pop(0)
            pH_values.append(val)
            mean_pH = sum(pH_values) / len(pH_values)
            log_file.write(f"Mean pH: {mean_pH}\n")
        elif sensor_type == "NPK":    # keeps track of the mean NPK
            if len(N_values) == N_values:
                N_values.pop(0)
            N_values.append(val["N"])
            mean_N = sum(N_values) / len(N_values)
            log_file.write(f"Mean N: {mean_N}\n")
            if len(P_values) == N_values:
                P_values.pop(0)
            P_values.append(val["P"])
            mean_P = sum(P_values) / len(P_values)
            log_file.write(f"Mean P: {mean_P}\n")
            if len(K_values) == N_values:
                K_values.pop(0)
            K_values.append(val["K"])
            mean_K = sum(K_values) / len(K_values)
            log_file.write(f"Mean K: {mean_K}\n")
            

class DataAnalysis(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("./logs/DataAnalysis.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)

temperatures = []   # list of the last N temperatures received
humidities = [] # list of the last N humidities received
light_intensities = []  # list of the last N light intensities received
soil_moistures = [] # list of the last N soil moistures received
pH_values = []  # list of the last N pH values received
N_values = []   # list of the last N N values received
P_values = []   # list of the last N P values received
K_values = []   # list of the last N K values received

# REST API

# methods called from management components to get the mean statistics on the last N values received
def get_mean_temperature():
    global mean_temperature
    return {'mean_temperature': mean_temperature}

def get_mean_humidity():
    global mean_humidity
    return {'mean_humidity': mean_humidity}

def get_mean_light():
    global mean_light
    return {'mean_light': mean_light}

def get_mean_soil_moisture():
    global mean_soil_moisture
    return {'mean_soil_moisture': mean_soil_moisture}

def get_mean_pH():
    global mean_pH
    return {'mean_pH': mean_pH}

def get_mean_N():
    global mean_N
    return {'mean_N': mean_N}

def get_mean_P():
    global mean_P
    return {'mean_P': mean_P}

def get_mean_K():
    global mean_K
    return {'mean_K': mean_K}

# REST API exposed by the DataAnalysis microservice
class DataAnalysisREST(object):
    exposed = True

    def __init__(self, data_analysis_connection):
        self.data_analysis_connection = data_analysis_connection

    # handles all the different HTTP methods
    @cherrypy.tools.json_out()  # automatically convert return value
    def GET(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        elif uri[0] == 'get_mean_temperature':
            return get_mean_temperature()
        elif uri[0] == 'get_mean_humidity':
            return get_mean_humidity()
        elif uri[0] == 'get_mean_light':
            return get_mean_light()
        elif uri[0] == 'get_mean_soil_moisture':
            return get_mean_soil_moisture()
        elif uri[0] == 'get_mean_pH':
            return get_mean_pH()
        elif uri[0] == 'get_mean_N':
            return get_mean_N()
        elif uri[0] == 'get_mean_P':
            return get_mean_P()
        elif uri[0] == 'get_mean_K':
            return get_mean_K()
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
    # RESR API
    dataAnalysisClient = DataAnalysisREST(None)
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8081})
    cherrypy.tree.mount(dataAnalysisClient, '/', conf)
    cherrypy.engine.start()

    response = requests.get(f"{catalog_url}/get_device_info", params={'device_id': device_id, 'device_name': 'DataAnalysis'})    # get the device information from the catalog
    if response.status_code == 200:
        device_info = response.json()    # device_info is a dictionary with the information of the device
        with open("./logs/DataAnalysis.log", "a") as log_file:
            log_file.write(f"Received device information: {device_info}\n")
    else:
        with open("./logs/DataAnalysis.log", "a") as log_file:
            log_file.write(f"Failed to get device information from the Catalog\nResponse: {response.reason}\n")
            exit(1) # if the request fails, the device connector stops

    N = device_info["params"]['N']    # get the number of values to keep track of from the device information

    # MQTT Sub
    # instead of reading the topics like this, i would like to change it and make that the microservices build the topics by itself by knowing the greenhouse where it is connected and the plant that it contains
    response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'DataAnalysis'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("./logs/DataAnalysis.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("./logs/DataAnalysis.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topic.append(f"greenhouse_{sensor['greenhouse_id']}/plant_{sensor['plant_id'] if sensor['plant_id'] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")

    # the mqtt subscriber subscribes to the topics
    subscriber = DataAnalysis(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()