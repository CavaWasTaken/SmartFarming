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
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_broker"]
    mqtt_port = config["mqtt_port"]
    keep_alive = config["keep_alive"]

fields = {}

def handle_message(topic, val):
    with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        greenhouse_id = greenhouse.split("_")[1]    # extract the id of the greenhouse from the topic
        plant_id = plant.split("_")[1]  # extract the id of the plant from the topic
        with open("./ThingSpeak_config.json", "r") as config_fd:    # read from the json file the configuration of the ThingSpeak channels
            config = json.load(config_fd)   # load the configuration in a dictionary

        url = f"https://api.thingspeak.com/update"  # url of the ThingSpeak API

        # these sensors are general for the greenhouse, so they are not associated with a specific plant. We have to update the channel of the greenhouse
        if sensor_type in ["Temperature", "Humidity", "LightIntensity"]:
            channel_data = config["greenhouses"][greenhouse_id] # get the configuration of the greenhouse
            key = f"greenhouse_{greenhouse_id}"  # key of the fields of the greenhouse
        elif sensor_type in ["SoilMoisture", "NPK", "pH"]:
            channel_data = config["greenhouses"][greenhouse_id]["plants"][plant_id]
            key = f"plant_{plant_id}_{greenhouse_id}"   # key of the fields of the plant in the greenhouse
        else:
            raise ValueError(f"Unknown sensor type: {sensor_type}")
        
        if key not in fields:   # if the key is new and is not in the fields dictionary, add it
            fields[key] = channel_data["fields"]

        if sensor_type == "NPK":    # if the sensor type is NPK, we have to split the value in the three nutrients
            for nutrient in ["N", "P", "K"]:
                fields[key][nutrient] = val.get(nutrient, "")
        else:   # if the sensor type is not NPK, we just have to update the value of the sensor
            fields[key][sensor_type] = val

        if any(value == "" for value in fields[key].values()):  # if there are missing values in the fields, write a log message and return
            with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
                log_file.write(f"Missing values for {sensor_type} in {key}\n")
            return
        
        payload = { # payload to send to the ThingSpeak API
            "api_key": channel_data["write_api_key"],   # write api key of the channel
            **{f"field{i+1}": value for i, value in enumerate(fields[key].values())}    # add the values of the fields to the payload
        }

        response = requests.get(url, params=payload)    # send the request to the ThingSpeak API
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
                    val = message["v"]
                    handle_message(topic, val)

if __name__ == "__main__":
    # instead of reading the topics like this, i would like to change it and make that the microservices build the topics by itself by knowing the greenhouse where it is connected and the plant that it contains
    response = requests.get(f"http://localhost:8080/get_sensors", params={'device_id': device_id, 'device_name': 'ThingSpeakAdaptor'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topic.append(f"greenhouse_{sensor['greenhouse_id']}/plant_{sensor['plant_id'] if sensor['plant_id'] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")

    # the mqtt subscriber subscribes to the topics
    subscriber = ThingSpeakAdaptor(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()