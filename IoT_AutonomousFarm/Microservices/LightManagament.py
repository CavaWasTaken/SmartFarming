import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests

# light management component is a MQTT subscriber and it receives the light and temperature values


# read the device_id and mqtt information of the broker from the json file
with open("./LightManagement_config.json", "r") as config_fd:
    config = json.load(config_fd)
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_broker"]
    mqtt_port = config["mqtt_port"]
    keep_alive = config["keep_alive"]

def handle_message(topic, val):
    with open("../logs/LightManagement.log", "a") as log_file:

        def check_val(sensor_id, param, unit, val, min_treshold, max_treshold):   # function that checks if the value is in the accepted range
            if val < min_treshold:
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} {unit} is low\taccepted range {min_treshold}-{max_treshold}\n")
            elif val > max_treshold:
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} is high\taccepted range {min_treshold}-{max_treshold}\n")
            else:
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} is in the accepted range {min_treshold}-{max_treshold}\n")

        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        response = requests.get(f"http://localhost:8080/get_sensor_id", params={'device_id': device_id, 'device_name': 'LightManagement', 'greenhouse_id': greenhouse.split("_")[1], 'plant_id': plant.split("_")[1], 'sensor_name': sensor_name, 'sensor_type': sensor_type})    # get the sensor id from the catalog
        if response.status_code == 200:
            sensor_id = response.json()["sensor_id"]
            log_file.write(f"New value collected by sensor {sensor_id}\n")
        else:
            log_file.write(f"Failed to get sensor id from the Catalog\nResponse: {response.reason}\n")
            exit(1) # if the request fails, the device connector stops

        treshold = tresholds[f"sensor_{sensor_id}"]    # get the treshold for the sensor
        min_treshold = treshold["min"]
        max_treshold = treshold["max"]

        if sensor_type == "LightIntensity":   # check the values of light intensity
            check_val(sensor_id, "light intensity", "Lux", val, min_treshold, max_treshold)

        elif sensor_type == "Temperature":  # check the value of temperature
            check_val(sensor_id, "temperature", "Celsius", val, min_treshold, max_treshold)

class LightManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("../logs/LightManagement.log", "a") as log_file: # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")   # write on the log file the message received
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)

if __name__ == "__main__":
    response = requests.get(f"http://localhost:8080/get_sensors", params={"device_id": device_id, 'device_name': 'LightManagement'})
    if response.status_code == 200:
        sensors = response.json()["sensors"]  # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("../logs/LightManagement.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("../logs/LightManagement.log", "a") as log_file:
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