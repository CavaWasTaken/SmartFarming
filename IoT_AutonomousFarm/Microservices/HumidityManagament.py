import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests

# humidity management component is a MQTT subscriber and it receives the humidity and soil moisture values


# read the device_id and mqtt information of the broker from the json file
with open("./HumidityManagement_config.json", "r") as config_fd:
    config = json.load(config_fd)
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_broker"]
    mqtt_port = config["mqtt_port"]
    keep_alive = config["keep_alive"]

def handle_message(topic, val):
    with open("../logs/HumidityManagement.log", "a") as log_file:
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        response = requests.get(f"http://localhost:8080/get_sensor_id", params={'device_id': device_id, 'device_name': 'HumidityManagement', 'greenhouse_id': greenhouse.split("_")[1], 'plant_id': plant.split("_")[1], 'sensor_name': sensor_name, 'sensor_type': sensor_type})    # get the sensor id from the catalog
        if response.status_code == 200:
            sensor_id = response.json()["sensor_id"]
            log_file.write(f"New value collected by sensor {sensor_id}\n")
        else:
            log_file.write(f"Failed to get sensor id from the Catalog\nResponse: {response.reason}\n")
            exit(1) # if the request fails, the device connector stops

        treshold = tresholds[f"sensor_{sensor_id}"]    # get the treshold for the sensor
        min_treshold = treshold["min"]
        max_treshold = treshold["max"]

        if sensor_type == "Humidity":
            if val < min_treshold:
                log_file.write(f"Humidity is low: {val}\n")
                # take action
            elif val > max_treshold:
                log_file.write(f"Humidity is high: {val}\n")
                # take action
            else:
                log_file.write(f"Humidity is in the accepted range {treshold}: {val}\n")
        elif sensor_type == "SoilMoisture":
            if val < min_treshold:
                log_file.write(f"Soil moisture is low: {val}\n")
                # take action
            elif val > max_treshold:
                log_file.write(f"Soil moisture is high: {val}\n")
                # take action
            else:
                log_file.write(f"Soil moisture is in the accepted range {treshold}: {val}\n")


class HumidityManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("../logs/HumidityManagement.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)


if __name__ == "__main__":
    # instead of reading the topics like this, i would like to change it and make that the microservices build the topics by itself by knowing the greenhouse where it is connected and the plant that it contains
    response = requests.get(f"http://localhost:8080/get_sensors", params={'device_id': device_id, 'device_name': 'HumidityManagement'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("../logs/HumidityManagement.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("../logs/HumidityManagement.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # array of topics where the microservice is subscribed
    global tresholds    # global variable that contains the tresholds for each sensor
    tresholds = {}  # dictionary of tresholds for each sensor used by the microservice
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topic.append(f"greenhouse_{sensor['greenhouse_id']}/plant_{sensor['plant_id'] if sensor['plant_id'] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")
        tresholds[f"sensor_{sensor['sensor_id']}"] = sensor['threshold']    # associate the threshold to the sensor id into the dictionary
    with open("../logs/HumidityManagement.log", "a") as log_file:
        log_file.write(f"Tresholds: {tresholds}\n")

    # the mqtt subscriber subscribes to the topics
    subscriber = HumidityManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()