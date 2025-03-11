import json
import requests
import threading
from functools import partial
import time
import Management

from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/NutrientManagement.log", "a") as log_file:
        log_file.write(f"{message}\n")

# each time that the device starts, we clear the log file
with open("./logs/NutrientManagement.log", "w") as log_file:
    pass

# read the info from the json file
with open("./NutrientManagement_config.json", "r") as config_fd:
    config = json.load(config_fd)   # load the configuration from the file as a dictionary
    catalog_url = config["catalog_url"] # get the url of the catalog
    dataAnalysis_url = config["dataAnalysis_url"]   # get the url of the data analysis
    device_id = config["device_id"] # get the id of the device
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # mqtt broker
    mqtt_port = config["mqtt_connection"]["mqtt_port"]  # mqtt port
    keep_alive = config["mqtt_connection"]["keep_alive"]    # keep alive time

expected_value = {} # dictionary to save the next expected value for each sensor
timers = {} # dictionary to save the timer (interval of time for waiting the next value of that sensor) for each sensor
tresholds = {}  # dictionary to save the treshold interval for each sensor
domains = {}    # dictionary  to save the domain of the values collectable by each sensor

# function that handles the received message from the broker
def handle_message(topic, sensor_type, val, unit, timestamp):
    # function that sends an alert to the user when the expected value doesn't arrive (timer expiration)
    def TimerExpiration(sensor_id, expected_timestamp):
        write_log(f"WARNING: Was expecting a value of {sensor_type} from sensor_{sensor_id} at time {expected_timestamp}, but it didn't arrive")   # ALERT TO BE SENT TO THE UI
        SendAlert(f"WARNING: Was expecting a value of {sensor_type} from sensor_{sensor_id} at time {expected_timestamp}, but it didn't arrive")

    def SendAlert(msg):
        client.publish(f"greenhouse_{greenhouse_id}/alert", msg)

    def SendInfo(msg):
        client.publish(f"greenhouse_{greenhouse_id}/info", msg)

    def SendAction(msg):
        client.publish(f"greenhouse_{greenhouse_id}/sensor_{sensor_id}/action", msg)

    def Severity(distance):
        max = domains[sensor_id]["max"]
        min = domains[sensor_id]["min"]
        severity = distance / max - min

        return severity
    
    def Is_inside(min_treshold, val, max_treshold):   # function that checks if the value is in the accepted range
        return min_treshold <= val <= max_treshold
    
    greenhouse, sensor = topic.split("/")  # split the topic and get all the information contained
    
    greenhouse_id = int(greenhouse.split("_")[1])
    sensor_id = int(sensor.split("_")[1])

    treshold = tresholds[sensor_id]    # get the treshold for the sensor

     # get from the DataAnalysis the next expected timestamp
    response = requests.get(f"{dataAnalysis_url}/get_next_timestamp", params={'sensor_id': sensor_id, 'sensor_type': sensor_type, 'timestamp': timestamp})
    if response.status_code == 200:
        next_timestamp = response.json()["next_timestamp"]
        if next_timestamp is not None:
            write_log(f"Next expected timestamp of sensor_{sensor_id} ({sensor_type}): {next_timestamp}")  # THIS INFO CAN BE SENT TO THE UI
            SendInfo(f"Next expected timestamp of sensor_{sensor_id} ({sensor_type}): {next_timestamp}")
        else:   # if the response is None, we consider the prediction lost
            write_log(f"WARNING: Next expected timestamp of sensor_{sensor_id} ({sensor_type}) not found")   # ALERT TO BE SENT TO THE UI
            SendAlert(f"WARNING: Next expected timestamp of sensor_{sensor_id} ({sensor_type}) not found")
            return
    else:
        write_log(f"WARNING: Impossible to get the next expected timestamp of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis\t(Response: {response.reason})")  # ALERT TO BE SENT TO THE UI
        SendAlert(f"WARNING: Impossible to get the next expected timestamp of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis\t(Response: {response.reason})")
        return

    if next_timestamp is not None:  # when the data analysis make prediction with just 1 value, it can't predict the next value so it is None
        if timers[sensor_id] is not None:  # if there is a timer running, stop it
            timers[sensor_id].cancel()

        timers[sensor_id] = threading.Timer(next_timestamp + 5 - timestamp, partial(TimerExpiration, sensor_id, next_timestamp)) # timer that will wait the next timestamp
        timers[sensor_id].start()   # start the timer

    if sensor_type == "NPK":
        min_treshold_N = treshold["N"]["min"]
        max_treshold_N = treshold["N"]["max"]
        min_treshold_P = treshold["P"]["min"]
        max_treshold_P = treshold["P"]["max"]
        min_treshold_K = treshold["K"]["min"]
        max_treshold_K = treshold["K"]["max"]

        Management.Check_value(dataAnalysis_url, sensor_id, sensor_type, val, unit, timestamp, {"N": min_treshold_N, "P": min_treshold_P, "K": min_treshold_K}, {"N": max_treshold_N, "P": max_treshold_P, "K": max_treshold_K}, expected_value, domains, write_log, SendAlert, SendInfo, SendAction)
    else:
        min_treshold = treshold["min"]
        max_treshold = treshold["max"]

        Management.Check_value(dataAnalysis_url, sensor_id, sensor_type, val, unit, timestamp, min_treshold, max_treshold, expected_value, domains, write_log, SendAlert, SendInfo, SendAction)


def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode()) # decode the message from JSON format, so we can access the values of the message as a dictionary
    write_log(f"\nReceived: {message}")
    for topic in mqtt_topics:
        if message["bn"] == topic:
            message = message["e"]
            sensor_type = message["n"]
            val = message["v"]
            unit = message["u"]
            timestamp = message["t"]
            handle_message(topic, sensor_type, val, unit, timestamp)
            break   # if the message is processed, exit the loop

if __name__ == "__main__":
    response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'NutrientManagement'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]   # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        write_log(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        write_log(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
        exit(1) # if the request fails, the device connector stops

    mqtt_topics = [] # array of topics where the device is subscribed
    for sensor in sensors:  # for each sensor build the topic where the device is subscribed and build the dictionary of tresholds
        mqtt_topics.append(f"greenhouse_{sensor["greenhouse_id"]}/sensor_{sensor['sensor_id']}")
        tresholds[sensor['sensor_id']] = sensor['threshold']    # associate the threshold to the sensor id into the dictionary
        domains[sensor['sensor_id']] = sensor['domain']    # associate the domain to the sensor id into the dictionary
        expected_value[sensor['sensor_id']] = None
        timers[sensor['sensor_id']] = None

     # create the mqtt client
    client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"NutrientManagement_{device_id}", on_message, write_log)
    client.start()
    for topic in mqtt_topics:
        client.subscribe(topic)

    while True:
        time.sleep(1)   # keep the microservice running
    client.stop()