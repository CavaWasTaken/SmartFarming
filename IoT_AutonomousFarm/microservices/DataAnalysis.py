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

global N, weights   # N is the number of values to keep track of, weights is a list of weights from 1 to N to calculate the weighted mean

def handle_message(topic, val):

    def weighted_mean(values, weights):    # calculate the weighted mean of a list of values
        return sum([v*w for v,w in zip(values, weights)]) / sum(weights)
    
    def update_statistics(values, val):    # update the statistics of the last N values received
        if len(values) >= N:    # if the list of values is N, remove the first element (the oldest)
            values.pop(0)
        values.append(val)    # append the new value to the list
        mean = weighted_mean(values, weights)    # calculate the weighted mean of the values
        return mean

    with open("./logs/DataAnalysis.log", "a") as log_file:  # open the log file to write on it logs
        global mean_temperature, mean_humidity, mean_light, mean_soil_moisture, mean_pH, mean_N, mean_P, mean_K   # global variables to keep track of the mean values
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained

        if sensor_type == "Temperature":    # keeps track of the mean temperature
            mean_temperature = update_statistics(temperatures, val)
            log_file.write(f"Weighted mean temperature: {mean_temperature}\n")

        elif sensor_type == "Humidity":   # keeps track of the mean humidity
            mean_humidity = update_statistics(humidities, val)
            log_file.write(f"Weighted mean humidity: {mean_humidity}\n")

        elif sensor_type == "LightIntensity":    # keeps track of the mean light
            mean_light = update_statistics(light_intensities, val)
            log_file.write(f"Weighted mean light intensity: {mean_light}\n")

        elif sensor_type == "SoilMoisture":    # keeps track of the mean soil moisture
            mean_soil_moisture = update_statistics(soil_moistures, val)
            log_file.write(f"Weighted mean soil moisture: {mean_soil_moisture}\n")

        elif sensor_type == "pH":   # keeps track of the mean pH
            mean_pH = update_statistics(pH_values, val)
            log_file.write(f"Weighted mean pH: {mean_pH}\n")

        elif sensor_type == "NPK":    # keeps track of the mean NPK
            mean_N = update_statistics(N_values, val["N"])
            log_file.write(f"Weighted mean N: {mean_N}\n")

            mean_P = update_statistics(P_values, val["P"])
            log_file.write(f"Weighted mean P: {mean_P}\n")

            mean_K = update_statistics(K_values, val["K"])
            log_file.write(f"Weighted mean K: {mean_K}\n")
            

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
    weights = list(range(1, N+1))    # create a list of weights from 1 to N to calculate the weighted mean

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