import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests
import cherrypy
from scipy.stats import linregress

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

global N   # N is the number of values to keep track of

def handle_message(topic, val, timestamp):

    def weighted_mean(values, weights):    # calculate the weighted mean of a list of values
        return sum([v*w for v,w in zip(values, weights)]) / sum(weights)
    
    def linear_regression(times, values):
        if len(times) > 1 and len(set(times)) > 1 and len(set(values)) > 1:  # ensure there are enough unique points
            slope, intercept, r_value, p_value, std_err = linregress(times, values)    # calculate the linear regression of the values
            slope = round(slope, 2)    # round the slope to 2 decimal places
            if slope > 0:   # if the slope is positive, the values are increasing
                trend = "increasing of " + str(slope)
            elif slope < 0: # if the slope is negative, the values are decreasing
                trend = "decreasing of " + str(slope)
            else:   # if the slope is 0, the values are constant
                trend = "stable"

            # predict the timestamp of the next value by evaluating the mean difference between two consecutive timestamps
            next_timestamp = sum([times[i] - times[i-1] for i in range(1, len(times))]) / (len(times) - 1) + times[-1]

            # predict the value of the next value by evaluating the linear regression of the values (y = mx + q)
            next_value = slope * next_timestamp + intercept
        else:
            next_timestamp = None
            next_value = None
            trend = None

        return next_timestamp, next_value, trend
    
    def update_timestamps(times, timestamp):    # update the timestamps of the last N values received
        if len(times) >= N:    # if the length of the list of timestamps is N, remove the first element (the oldest)
            times.pop(0)
        times.append(timestamp)    # append the timestamp of the new value to the list of timestamps 
    
    def update_statistics(times, values, val):    # update the statistics of the last N values received
        if len(values) >= N:    # if the length of the list of values is N, remove the first element (the oldest)
            values.pop(0)
        values.append(val)    # append the new value to the list
        weights = list(range(1, len(values)+1))    # create a list of weights from 1 to N to calculate the weighted mean
        mean = weighted_mean(values, weights)    # calculate the weighted mean of the values

        # evaluate predictions
        next_times, next_val, trend = linear_regression(times, values)    # calculate the linear regression of the values
        next_timestamp[sensor_type] = next_times
        next_value[sensor_type] = next_val

        return mean, trend


    with open("./logs/DataAnalysis.log", "a") as log_file:  # open the log file to write on it logs
        global mean_temperature, mean_humidity, mean_light, mean_soil_moisture, mean_pH, mean_N, mean_P, mean_K   # global variables to keep track of the mean values
        global trend_temperature, trend_humidity, trend_light, trend_soil_moisture, trend_pH, trend_N, trend_P, trend_K   # global variables to keep track of the trend of the values
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained

        if sensor_type == "Temperature":    # keeps track of the mean temperature
            update_timestamps(timestamps[sensor_type], timestamp)
            mean_temperature, trend_temperature = update_statistics(timestamps[sensor_type], temperatures, val)
            log_file.write(f"Weighted mean temperature: {mean_temperature}\n")
            log_file.write(f"Trend of temperature: {trend_temperature}\n")

            if next_timestamp[sensor_type] is not None and next_value[sensor_type] is not None:
                log_file.write(f"Next timestamp: {next_timestamp[sensor_type]}\n")
                log_file.write(f"Next value: {next_value[sensor_type]}\n")

        elif sensor_type == "Humidity":   # keeps track of the mean humidity
            update_timestamps(timestamps[sensor_type], timestamp)
            mean_humidity, trend_humidity = update_statistics(timestamps[sensor_type], humidities, val)
            log_file.write(f"Weighted mean humidity: {mean_humidity}\n")
            log_file.write(f"Trend of humidity: {trend_humidity}\n")

            if next_timestamp[sensor_type] is not None and next_value[sensor_type] is not None:
                log_file.write(f"Next timestamp: {next_timestamp[sensor_type]}\n")
                log_file.write(f"Next value: {next_value[sensor_type]}\n")

        elif sensor_type == "LightIntensity":    # keeps track of the mean light
            update_timestamps(timestamps[sensor_type], timestamp)
            mean_light, trend_light = update_statistics(timestamps[sensor_type], light_intensities, val)
            log_file.write(f"Weighted mean light intensity: {mean_light}\n")
            log_file.write(f"Trend of light intensity: {trend_light}\n")

            if next_timestamp[sensor_type] is not None and next_value[sensor_type] is not None:
                log_file.write(f"Next timestamp: {next_timestamp[sensor_type]}\n")
                log_file.write(f"Next value: {next_value[sensor_type]}\n")

        elif sensor_type == "SoilMoisture":    # keeps track of the mean soil moisture
            update_timestamps(timestamps[sensor_type], timestamp)
            mean_soil_moisture, trend_soil_moisture = update_statistics(timestamps[sensor_type], soil_moistures, val)
            log_file.write(f"Weighted mean soil moisture: {mean_soil_moisture}\n")
            log_file.write(f"Trend of soil moisture: {trend_soil_moisture}\n")

            if next_timestamp[sensor_type] is not None and next_value[sensor_type] is not None:
                log_file.write(f"Next timestamp: {next_timestamp[sensor_type]}\n")
                log_file.write(f"Next value: {next_value[sensor_type]}\n")

        elif sensor_type == "pH":   # keeps track of the mean pH
            update_timestamps(timestamps[sensor_type], timestamp)
            mean_pH, trend_pH = update_statistics(timestamps[sensor_type], pH_values, val)
            log_file.write(f"Weighted mean pH: {mean_pH}\n")
            log_file.write(f"Trend of pH: {trend_pH}\n")

            if next_timestamp[sensor_type] is not None and next_value[sensor_type] is not None:
                log_file.write(f"Next timestamp: {next_timestamp[sensor_type]}\n")
                log_file.write(f"Next value: {next_value[sensor_type]}\n")

        elif sensor_type == "NPK":    # keeps track of the mean NPK
            update_timestamps(timestamps[sensor_type], timestamp)
            mean_N, trend_N = update_statistics(timestamps[sensor_type], N_values, val["N"])
            log_file.write(f"Weighted mean Nitrogen: {mean_N}\n")
            log_file.write(f"Trend of Nitrogen: {trend_N}\n")

            mean_P, trend_P = update_statistics(timestamps[sensor_type], P_values, val["P"])
            log_file.write(f"Weighted mean Phosphorus: {mean_P}\n")
            log_file.write(f"Trend of Phosphorus: {trend_P}\n")

            mean_K, trend_K = update_statistics(timestamps[sensor_type], K_values, val["K"])
            log_file.write(f"Weighted mean K(Potassium): {mean_K}\n")
            log_file.write(f"Trend of K(Potassium): {trend_K}\n")

            if next_timestamp[sensor_type] is not None and next_value["N"] is not None and next_value["P"] is not None and next_value["K"] is not None:
                log_file.write(f"Next timestamp: {next_timestamp[sensor_type]}\n")
                log_file.write(f"Next value N: {next_value['N']}\n")
                log_file.write(f"Next value P: {next_value['P']}\n")
                log_file.write(f"Next value K: {next_value['K']}\n")
            

class DataAnalysis(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("./logs/DataAnalysis.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    timestamp = message["t"]    # get the timestamp of the message
                    val = message["v"]  # get the value of the message
                    handle_message(topic, val, timestamp)

timestamps = {
    "Temperature": [],  # list of the timestamps of the last N temperatures received
    "Humidity": [], # list of the timestamps of the last N humidities received
    "LightIntensity": [],   # list of the timestamps of the last N light intensities received
    "SoilMoisture": [], # list of the timestamps of the last N soil moistures received
    "pH": [],   # list of the timestamps of the last N pH values received
    "NPK": []   # list of the timestamps of the last N NPK values received
}
temperatures = []   # list of the last N temperatures received
humidities = [] # list of the last N humidities received
light_intensities = []  # list of the last N light intensities received
soil_moistures = [] # list of the last N soil moistures received
pH_values = []  # list of the last N pH values received
N_values = []   # list of the last N N values received
P_values = []   # list of the last N P values received
K_values = []   # list of the last N K values received

next_timestamp = { # dictionary of the next expected timestamp of each sensor
    "Temperature": None,  # timestamp of the next expected temperature
    "Humidity": None,  # timestamp of the next expected humidity
    "LightIntensity": None,    # timestamp of the next expected light intensity
    "SoilMoisture": None,  # timestamp of the next expected soil moisture
    "pH": None,    # timestamp of the next expected pH
    "NPK": None    # timestamp of the next expected NPK
}
next_value = {  # dictionary of the next expected value of each sensor
    "Temperature": None,  # value of the next expected temperature
    "Humidity": None,  # value of the next expected humidity
    "LightIntensity": None,    # value of the next expected light intensity
    "SoilMoisture": None,  # value of the next expected soil moisture
    "pH": None,    # value of the next expected pH
    "N": None,    # value of the next expected Nitrogen
    "P": None,    # value of the next expected Phosphorus
    "K": None    # value of the next expected Potassium
}

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

    # RESR API exposed by the DataAnalysis microservice and used by management components to get statistics
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

    # it has to read the parameter N from the catalog
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
    # it has to read the sensors from the catalog
    response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'DataAnalysis'})
    if response.status_code == 200:
        sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("./logs/DataAnalysis.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("./logs/DataAnalysis.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # initialize the array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topic.append(f"greenhouse_{sensor['greenhouse_id']}/plant_{sensor['plant_id'] if sensor['plant_id'] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")

    # the mqtt subscriber subscribes to the topics
    subscriber = DataAnalysis(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()