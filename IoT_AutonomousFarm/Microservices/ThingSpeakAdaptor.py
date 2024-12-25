import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests

# data analysis component is a MQTT subscriber to all the topics of the sensors of the greenhouse


# read the device_id and mqtt information of the broker from the json file
with open("./ThingSpeakAdaptor_config.json", "r") as config_fd:
    config = json.load(config_fd)
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_broker"]
    mqtt_port = config["mqtt_port"]
    keep_alive = config["keep_alive"]

def handle_message(topic, val):
    with open("../logs/ThingSpeakAdaptor.log", "a") as log_file:
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        log_file.write(f"Received message from {greenhouse} - {plant} - {sensor_name} - {sensor_type}\n")

class ThingSpeakAdaptor(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("../logs/ThingSpeakAdaptor.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)

if __name__ == "__main__":
    # instead of reading the topics like this, i would like to change it and make that the microservices build the topics by itself by knowing the greenhouse where it is connected and the plant that it contains
    response = requests.get(f"http://localhost:8080/get_sensors", params={'device_id': device_id, 'device_name': 'ThingSpeakAdaptor'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("../logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("../logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # array of topics where the microservice is subscribed
    # to do, thing speak adaptor should understand how to share data with ThingSpeak
    # global channels
    # channels = {}
    # for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
    #     mqtt_topic.append(f"greenhouse_{sensor['greenhouse_id']}/plant_{sensor['plant_id'] if sensor['plant_id'] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")
    #     greenhouse_key = f"greenhouse_{sensor['greenhouse_id']}"    # the key of the greenhouse in the dictionary of channels
    #     plant_key = f"plant_{sensor['plant_id']}" if sensor['plant_id'] is not None else 'ALL'  # the key of the plant in the dictionary of channels
    #     if greenhouse_key not in channels:  # if the greenhouse is not in the dictionary, add it
    #         channels[greenhouse_key] = {}
    #     if plant_key not in channels[greenhouse_key]:   # if the plant is not in the dictionary, add it
    #         channels[greenhouse_key][plant_key] = {}
    #     channels[greenhouse_key][plant_key][f"sensor_{sensor['sensor_id']}"] = sensor['thing_speak_channel_id']    # add the channel where the data of the sensor will be sent to ThingSpeak
    # print(channels)
    # the mqtt subscriber subscribes to the topics
    subscriber = ThingSpeakAdaptor(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()