import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests
import cherrypy
from scipy.stats import linregress
import time

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

            # predict the timestamp of the next value by evaluating the mean difference between two consecutive timestamps
            next_timestamp = sum([times[i] - times[i-1] for i in range(1, len(times))]) / (len(times) - 1) + times[-1]

            # predict the value of the next value by evaluating the linear regression of the values (y = mx + q)
            next_value = slope * next_timestamp + intercept
        else:
            next_timestamp = None
            next_value = None
            slope = None

        return next_timestamp, next_value, slope
    
    def update_timestamps(times, timestamp):    # update the timestamps of the last N values received
        if len(times) >= N:    # if the length of the list of timestamps is N, remove the first element (the oldest)
            times.pop(0)
        times.append(timestamp)    # append the timestamp of the new value to the list of timestamps 
    
    def update_statistics(times, vals, val, value_type):    # update the statistics of the last N values received
        if len(vals) >= N:    # if the length of the list of values is N, remove the first element (the oldest)
            vals.pop(0)
        vals.append(val)    # append the new value to the list
        weights = list(range(1, len(vals)+1))    # create a list of weights from 1 to N to calculate the weighted mean
        mean = weighted_mean(vals, weights)    # calculate the weighted mean of the values

        # evaluate predictions
        next_times, next_val, trend = linear_regression(times, vals)    # calculate the linear regression of the values
        next_timestamp[sensor_type] = next_times
        next_value[value_type] = next_val

        return mean, trend
    
    def handle_sensor(value_type, val):
        ts = timestamps[sensor_type].copy()    # copy the list of timestamps of the last N values received
        if value_type != "P" and value_type != "K":    # otherwise we add three times the same timestamp for N, P, K
            update_timestamps(ts, timestamp)
        mean_value[value_type], trend[value_type] = update_statistics(ts, values[value_type], val, value_type)
        log_file.write(f"Weighted mean {value_type}: {mean_value[value_type]}\n")
        log_file.write(f"Trend of {value_type}: {trend[value_type]}\n")
        log_file.write(f"Expected next timestamp of {value_type}: {next_timestamp[sensor_type]}\n")
        log_file.write(f"Expected next value of {value_type}: {next_value[value_type]}\n")
        timestamps[sensor_type] = ts    # update the list of timestamps of the last N values received

    with open("./logs/DataAnalysis.log", "a") as log_file:  # open the log file to write on it logs
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained

        if sensor_type != "NPK":    # keeps track of the mean of the other sensors
            handle_sensor(sensor_type, val)
        else:    # keeps track of the mean NPK
            handle_sensor("N", val["N"])
            handle_sensor("P", val["P"])
            handle_sensor("K", val["K"])

class DataAnalysis(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("./logs/DataAnalysis.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"\nReceived: {message}\n")
            log_file.flush()    # flush the buffer of the log file to write the message immediately
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

values = {
    "Temperature": [],  # list of the last N temperatures received
    "Humidity": [], # list of the last N humidities received
    "LightIntensity": [],   # list of the last N light intensities received
    "SoilMoisture": [], # list of the last N soil moistures received
    "pH": [],   # list of the last N pH values received
    "N": [],   # list of the last N N values received
    "P": [],   # list of the last N P values received
    "K": []   # list of the last N K values received
}

mean_value = {  # dictionary of the mean value of each sensor
    "Temperature": None,  # mean value of the temperature
    "Humidity": None,  # mean value of the humidity
    "LightIntensity": None,    # mean value of the light intensity
    "SoilMoisture": None,  # mean value of the soil moisture
    "pH": None,    # mean value of the pH
    "N": None,    # mean value of the Nitrogen
    "P": None,    # mean value of the Phosphorus
    "K": None    # mean value of the Potassium
}

trend = { # dictionary of the trend of each sensor
    "Temperature": None,  # trend of the temperature
    "Humidity": None,  # trend of the humidity
    "LightIntensity": None,    # trend of the light intensity
    "SoilMoisture": None,  # trend of the soil moisture
    "pH": None,    # trend of the pH
    "N": None,    # trend of the Nitrogen
    "P": None,    # trend of the Phosphorus
    "K": None    # trend of the Potassium
}

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
def get_mean_value(value_type, timestamp, sensor_type):
    with open("./logs/DataAnalysis.log", "a") as log_file:
        log_file.write(f"Received request for the mean value of {value_type} at timestamp {timestamp}\n{timestamps[sensor_type]}\n")
        log_file.write(f"{float(timestamps[sensor_type][-1])} == {float(timestamp)} : {float(timestamps[sensor_type][-1]) == float(timestamp)}\n")
        count = 0   # count how many seconds we are waiting
        if float(timestamps[sensor_type][-1]) == float(timestamp):  # if the timestamp is the same as the last received, return the mean value
            log_file.write(f"I AM IN\n")
            return {'mean_value': mean_value[value_type]}   # the value has been updated, so we can return it
        else:   # the value has not been updated yet, so we wait for it
            log_file.write(f"I AM OUT\n")
            while float(timestamps[sensor_type][-1]) != float(timestamp):   # wait for the value to be updated
                log_file.write(f"{float(timestamps[sensor_type][-1])} != {float(timestamp)} : {float(timestamps[sensor_type][-1]) != float(timestamp)}\n")
                if count < 60:  # wait for a maximum of 60 seconds
                    time.sleep(1)   # wait for 1 second
                else:   # if we waited for 60 seconds, return None
                    return {'mean_value': None}
                count += 1  # increment the counter
            return {'mean_value': mean_value[value_type]}   # the value has been updated, so we can return it
            
# methods called from management components to get the trend of the last N values received
def get_trend(value_type, timestamp, sensor_type):
    with open("./logs/DataAnalysis.log", "a") as log_file:
        log_file.write(f"Received request for the trend of {value_type} at timestamp {timestamp}\n{timestamps[sensor_type]}\n")
        count = 0   # count how many seconds we are waiting
        if float(timestamps[sensor_type][-1]) == float(timestamp):  # if the timestamp is the same as the last received, return the mean value
            return {'trend': trend[value_type]}   # the value has been updated, so we can return it
        else:   # the value has not been updated yet, so we wait for it
            while float(timestamps[sensor_type][-1]) == float(timestamp):   # wait for the value to be updated
                if count < 60:  # wait for a maximum of 60 seconds
                    time.sleep(1)   # wait for 1 second
                else:   # if we waited for 60 seconds, return None
                    return {'trend': None}
                count += 1  # increment the counter
            return {'trend': trend[value_type]}  # the value has been updated, so we can return it
    
# methods called from management components to get the predictions of the sensor
def get_next_timestamp(sensor_type, timestamp):
    with open("./logs/DataAnalysis.log", "a") as log_file:
        log_file.write(f"Received request for the next timestamp of {sensor_type} at timestamp {timestamp}\n{timestamps[sensor_type]}\n")
        log_file.write(f"{float(timestamps[sensor_type][-1])} == {float(timestamp)} : {float(timestamps[sensor_type][-1]) == float(timestamp)}\n")
        count = 0   # count how many seconds we are waiting
        if float(timestamps[sensor_type][-1]) == float(timestamp):  # if the timestamp is the same as the last received, return the mean value
            log_file.write(f"I AM IN\n")
            return {'next_timestamp': next_timestamp[sensor_type]}   # the value has been updated, so we can return it
        else:   # the value has not been updated yet, so we wait for it
            log_file.write(f"I AM OUT\n")
            while float(timestamps[sensor_type][-1]) != float(timestamp):   # wait for the value to be updated
                log_file.write(f"{float(timestamps[sensor_type][-1])} != {float(timestamp)} : {float(timestamps[sensor_type][-1]) != float(timestamp)}\n")
                if count < 60:  # wait for a maximum of 60 seconds
                    time.sleep(1)   # wait for 1 second
                else:   # if we waited for 60 seconds, return None
                    return {'next_timestamp': None}
                count += 1  # increment the counter
            return {'next_timestamp': next_timestamp[sensor_type]}   # the value has been updated, so we can return it

def get_next_value(value_type, timestamp, sensor_type):
    with open("./logs/DataAnalysis.log", "a") as log_file:
        log_file.write(f"Received request for the next value of {value_type} at timestamp {timestamp}\n{timestamps[sensor_type]}\n")
        log_file.write(f"{float(timestamps[sensor_type][-1])} == {float(timestamp)} : {float(timestamps[sensor_type][-1]) == float(timestamp)}\n")
        count = 0   # count how many seconds we are waiting
        if float(timestamps[sensor_type][-1]) == float(timestamp):  # if the timestamp is the same as the last received, return the mean value
            log_file.write(f"I AM IN\n")
            return {'next_value': next_value[value_type]}   # the value has been updated, so we can return it
        else:   # the value has not been updated yet, so we wait for it
            log_file.write(f"I AM OUT\n")
            while float(timestamps[sensor_type][-1]) != float(timestamp):   # wait for the value to be updated
                log_file.write(f"{float(timestamps[sensor_type][-1])} != {float(timestamp)} : {float(timestamps[sensor_type][-1]) != float(timestamp)}\n")
                if count < 60:  # wait for a maximum of 60 seconds
                    time.sleep(1)   # wait for 1 second
                else:   # if we waited for 60 seconds, return None
                    return {'next_value': None}
                count += 1  # increment the counter
            return {'next_value': next_value[value_type]}   # the value has been updated, so we can return it

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
        elif uri[0] == 'get_mean_value':
            return get_mean_value(params['value_type'], params['timestamp'], params['sensor_type'])
        elif uri[0] == 'get_trend':
            return get_trend(params['value_type'], params['timestamp'], params['sensor_type'])
        elif uri[0] == 'get_next_timestamp':
            return get_next_timestamp(params['sensor_type'], params['timestamp'])
        elif uri[0] == 'get_next_value':
            return get_next_value(params['value_type'], params['timestamp'], params['sensor_type'])
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