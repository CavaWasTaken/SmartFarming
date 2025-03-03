import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests

# each time that the device starts, we clear the log file
with open("./logs/ThingSpeakAdaptor.log", "w") as log_file:
    pass


# read the device_id and mqtt information of the broker from the json file
with open("./ThingSpeakAdaptor_config.json", "r") as config_fd:
    config = json.load(config_fd)
    catalog_url = config["catalog_url"]
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
    mqtt_port = config["mqtt_connection"]["mqtt_port"]
    keep_alive = config["mqtt_connection"]["keep_alive"]

fields = {}
read_API = ""
write_API = ""

def handle_message(topic, sensor_type, val):
    with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
        greenhouse, sensor = topic.split("/")  # split the topic and get all the information contained
        greenhouse_id = greenhouse.split("_")[1]    # extract the id of the greenhouse from the topic
        sensor_id = sensor.split("_")[1]    # extract the id of the sensor from the topic

        url = f"https://api.thingspeak.com/update"  # url of the ThingSpeak API

        fields[f"greenhouse_{greenhouse_id}"][f"sensor_{sensor_id}"] = val

        if any(value == "" for value in fields[f"greenhouse_{greenhouse_id}"].values()):  # if there are missing values in the fields, write a log message and return
            with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
                log_file.write(f"Missing values in {f"greenhouse_{greenhouse_id}"}\n")
            return
        
        payload = { # payload to send to the ThingSpeak API
            "api_key": write_API,   # write api key of the channel
            **{f"field{i+1}": value for i, value in enumerate(fields[f"greenhouse_{greenhouse_id}"].values())}    # add the values of the fields to the payload
        }

        response = requests.post(url, data=payload)    # send the request to the ThingSpeak API
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:    
            if response.status_code == 200:
                log_file.write(f"Successfully updated ThingSpeak channel {channel_data['channel_id']} with payload: {payload}\n")
            else:
                log_file.write(f"Failed to update ThingSpeak. Response: {response.reason}\n")

        fields[key] = {k: "" for k in fields[key]}  # reset the fields of the key to empty strings

class ThingSpeakAdaptor(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    message = message["e"]
                    sensor_type = message["n"]
                    val = message["v"]
                    handle_message(topic, sensor_type, val)
                    break   # if the message is processed, break the loop

if __name__ == "__main__":
    # instead of reading the topics like this, i would like to change it and make that the microservices build the topics by itself by knowing the greenhouse where it is connected and the plant that it contains
    response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'ThingSpeakAdaptor'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops
        
    response = requests.get(f"{catalog_url}/get_greenhouse_info", params={'greenhouse_id': sensors[0]["greenhouse_id"], 'device_id': device_id})    # get the greenhouse information from the catalog
    if response.status_code == 200:
        greenhouse_info = response.json()    # greenhouse_info is a dictionary with the information of the greenhouse
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Received greenhouse information: {greenhouse_info}\n")
            read_API = greenhouse_info["thingspeak_channel_read_key"]
            write_API = greenhouse_info["thingspeak_channel_write_key"]
    else:
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Failed to get greenhouse information from the Catalog\nResponse: {response.reason}\n")
            exit(1)


    mqtt_topic = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topic.append(f"greenhouse_{sensor['greenhouse_id']}/sensor_{sensor['sensor_id']}")
        fields[f"greenhouse_{sensor['greenhouse_id']}"][f"sensor_{sensor['sensor_id']}"] = ""    # initialize the fields of the sensor to empty strings

    # the mqtt subscriber subscribes to the topics
    subscriber = ThingSpeakAdaptor(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()