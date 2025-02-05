import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests
import threading
from functools import partial

# each time that the device starts, we clear the log file
with open("./logs/LightManagement.log", "w") as log_file:
    pass

# read the device_id and mqtt information of the broker from the json file
with open("./LightManagement_config.json", "r") as config_fd:
    config = json.load(config_fd)
    catalog_url = config["catalog_url"]
    dataAnalysis_url = config["dataAnalysis_url"]
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
    mqtt_port = config["mqtt_connection"]["mqtt_port"]
    keep_alive = config["mqtt_connection"]["keep_alive"]

expected_value = {
    "LightIntensity": None,
    "Temperature": None
}

timers = {
    "LightIntensity": None,
    "Temperature": None
}

def handle_message(topic, val, unit, timestamp):
    with open("./logs/LightManagement.log", "a") as log_file:

        def Send_alert(sendor_id, sensor_type, expected_timestamp):
            with open("./logs/LightManagement.log", "a") as log_file:
                log_file.write(f"WARNING: Was expecting a value of {sensor_type} from sensor_{sensor_id} at time {expected_timestamp}, but it didn't arrive\n")

        def Severity(distance, value_type):
            severity = None
            if value_type == "LightIntensity":
                max_humidity = 1000
                min_humidity = 0
                severity = distance / max_humidity - min_humidity
            elif value_type == "Temperature":
                max_soil_moisture = 40
                min_soil_moisture = -10
                severity = distance / max_soil_moisture - min_soil_moisture

            return severity
        
        def Is_inside(min_treshold, val, max_treshold):   # function that checks if the value is in the accepted range
            return min_treshold <= val <= max_treshold
        
        def Check_value(value_type, min_treshold, max_treshold, sensor_id):
                
            # evaluate the next expected value
            response = requests.get(f"{dataAnalysis_url}/get_next_value", params={'value_type': value_type, 'timestamp': timestamp, 'sensor_type': sensor_type})    # get the expected humidity from the data analysis
            if response.status_code == 200:
                expected_val = response.json()["next_value"]
                if expected_val is not None:
                    log_file.write(f"Next expected {value_type}: {expected_val}\n")
                else:   # if the response is None, we consider the prediction lost
                    log_file.write(f"WARNING: Failed to get the next expected value of {value_type} from the DataAnalysis\n")
                    return
            else:
                log_file.write(f"Failed to get the next expected value of {value_type} from the DataAnalysis\nResponse: {response.reason}\n")
                exit(1)

            if expected_value[value_type] is None:  # if it is the first value, just update the expected value and terminate the function
                expected_value[value_type] = expected_val   # update the next expected value
                return

            # we use the previous expected value to check if the measured value is unexpected
            if abs(val - expected_value[value_type]) > 5:    # if the value was unexpected, alert the user and wait for the next value
                log_file.write(f"WARNING: The measured value {val} of {value_type} is unexpected. (Expected value: {expected_val})\tWaiting for the next value\n")
            
            else:   # if the value was expected
                if not Is_inside(min_treshold, val, max_treshold):  # if the value is outside the range of accepted values, alert the user
                    log_file.write(f"WARNING: The measured value {val} {unit} of {value_type} went outside the range [{min_treshold}, {max_treshold}]\n")

                    # evaluate how far the value is from the interval
                    if val > max_treshold:  # if the value is higher than the max treshold
                        distance = (val - max_treshold)
                    else:   # val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_t
                        distance = (min_treshold - val)
                    severity = Severity(distance, value_type)   # evaluate the severity of the problem
                    if severity is None:
                        log_file.write(f"Failed to calculate the severity of the problem\n")
                        exit(1)

                    # if the value was expected
                    if severity > 0.5:  # if the severity is high enough, action is needed
                        # take preventive action by following the expected severity
                        log_file.write(f"WARNING: Action needed for sensor_{sensor_id}\n")
                    else:   # if the severity isn't high enough
                        # get the updated mean
                        response = requests.get(f"{dataAnalysis_url}/get_mean_value", params={'value_type':value_type, 'timestamp': timestamp, 'sensor_type': sensor_type})
                        if response.status_code == 200:
                            mean_value = response.json()["mean_value"]
                            if mean_value is not None:
                                log_file.write(f"Mean {value_type}: {mean_value}\n")
                            else:   # if the response is None, we consider the evaluation lost
                                log_file.write(f"Failed to get mean of {value_type} from the DataAnalysis\n")
                                return
                            if not Is_inside(min_treshold, mean_value, max_treshold):    # if the mean value is outside the range, action is needed
                                # take preventive action by following the expected severity
                                log_file.write(f"WARNING: Action needed for sensor_{sensor_id}\n")
                            else:   # if the mean value is inside the range
                                if abs(val - mean_value) > 5:    # if the value is far from the mean, action is needed
                                    # take preventive action by following the expected severity
                                    log_file.write(f"WARNING: Action needed for sensor_{sensor_id}\n")
                                else:   # if the value is near the mean, check if the next expected value is in the range
                                    if not Is_inside(min_treshold, expected_val, max_treshold):    # if the expected value is outside the range, action is needed
                                        # take preventive action by following the expected severity
                                        log_file.write(f"WARNING: Action needed for sensor_{sensor_id}\n")
                        else:
                            log_file.write(f"Failed to get mean of {value_type} from the DataAnalysis\nResponse: {response.reason}\n")
                            exit(1)

                else:   # if the value is inside the range
                    if not Is_inside(min_treshold, expected_val, max_treshold):    # if the next expected value is outside the range, action is needed
                        log_file.write(f"WARNING: The next expected value of {value_type} is outside the range [{min_treshold}, {max_treshold}]\n")

                        if expected_val > max_treshold: # if the expected value is higher than the max treshold
                            distance = (expected_val - max_treshold)
                        else:   # expected_value < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_treshold
                            distance = (min_treshold - expected_val)
                        severity = Severity(distance, value_type)
                        # take preventive action by following the expected severity
                        log_file.write(f"WARNING: Preventine action needed for sensor_{sensor_id}\n")
                    else:   # if the next expected value is inside the range
                        log_file.write(f"INFO: The measured value ({val} {unit}) and the next prediction ({expected_val}, {unit}) of {value_type} are inside the range [{min_treshold}, {max_treshold}]\n")
            
            expected_value[value_type] = expected_val   # update the next expected value

        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        # i have all the information about the sensor but i don't know its id, so i need to ask the catalog. I need the id cause i use it to access to its tresholds
        response = requests.get(f"{catalog_url}/get_sensor_id", params={'device_id': device_id, 'device_name': 'LightManagement', 'greenhouse_id': greenhouse.split("_")[1], 'plant_id': plant.split("_")[1], 'sensor_name': sensor_name, 'sensor_type': sensor_type})    # get the sensor id from the catalog
        if response.status_code == 200:
            sensor_id = response.json()["sensor_id"]
            log_file.write(f"New value collected by sensor {sensor_id}\n")
        else:
            log_file.write(f"Failed to get sensor id from the Catalog\nResponse: {response.reason}\n")
            exit(1) # if the request fails, the device connector stops

        treshold = tresholds[f"sensor_{sensor_id}"]    # get the treshold for the sensor
        min_treshold = treshold["min"]
        max_treshold = treshold["max"]

        # get from the DataAnalysis the next expected timestamp
        response = requests.get(f"{dataAnalysis_url}/get_next_timestamp", params={'sensor_type': sensor_type, 'timestamp': timestamp})
        if response.status_code == 200:
            next_timestamp = response.json()["next_timestamp"]
            if next_timestamp is not None:
                log_file.write(f"Next expected timestamp: {next_timestamp}\n")
            else:   # if the response is None, we consider the prediction lost
                log_file.write(f"WARNING: Failed to get the next expected timestamp from the DataAnalysis\n")
                return
        else:
            log_file.write(f"Failed to get the next expected timestamp from the DataAnalysis\nResponse: {response.reason}\n")
            exit(1)

        if next_timestamp is not None:  # when the data analysis make prediction with just 1 value, it can't predict the next value so it is None
            if timers[sensor_type] is not None:  # if there is a timer running, stop it
                timers[sensor_type].cancel()

            timers[sensor_type] = threading.Timer(next_timestamp + 5 - timestamp, partial(Send_alert, sensor_id, sensor_type, next_timestamp)) # timer that will wait the next timestamp
            timers[sensor_type].start()   # start the timer


        Check_value(sensor_type, min_treshold, max_treshold, sensor_id)

class LightManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("./logs/LightManagement.log", "a") as log_file: # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"\nReceived: {message}\n")   # write on the log file the message received
            log_file.flush()    # flush the buffer of the log file
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    unit = message["u"]
                    timestamp = message["t"]
                    handle_message(topic, val, unit, timestamp)

if __name__ == "__main__":
    response = requests.get(f"{catalog_url}/get_sensors", params={"device_id": device_id, 'device_name': 'LightManagement'})
    if response.status_code == 200:
        sensors = response.json()["sensors"]  # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("./logs/LightManagement.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("./logs/LightManagement.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # array of topics where the microservice is subscribed
    global tresholds    # global variable that contains the tresholds of the sensors
    tresholds = {}  # dictionary of tresholds for each sensor
    for sensor in sensors:  # for each sensor, build the topic and append it to the mqtt_topic array
        mqtt_topic.append(f"greenhouse_{sensor["greenhouse_id"]}/plant_{sensor["plant_id"] if sensor["plant_id"] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")
        tresholds[f"sensor_{sensor['sensor_id']}"] = sensor['threshold']    # associate the treshold to the sensor id in the dictionary

    # the mqtt susbcriber subscribes to the topics
    subscriber = LightManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()