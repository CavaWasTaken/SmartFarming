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
        topic = topic.split("/")[-1]
        if topic == "Humidity":
            if val < 60:
                log_file.write(f"Humidity is low: {val}\n")
                # take action
            else:
                log_file.write(f"Humidity is high: {val}\n")
                # take action
        elif topic == "SoilMoisture":
            if val < 40:
                log_file.write(f"Soil moisture is low: {val}\n")
                # take action
            else:
                log_file.write(f"Soil moisture is high: {val}\n")
                # take action


class HumidityManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("../logs/HumidityManagement.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received message on {msg.topic}: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)


if __name__ == "__main__":
    response = requests.get(f"http://localhost:8080/get_topics", params={'device_id': device_id, 'device_type': 'HumidityManagement'})    # get the device information from the catalog
    if response.status_code == 200:
        mqtt_topic = response.json()    # obtain the data from the response in json format
        mqtt_topic = mqtt_topic["topics"][0]   # obtain the array of topics
        with open("../logs/HumidityManagement.log", "a") as log_file:
            log_file.write(f"Received mqtt_topic: {mqtt_topic}\n")
    else:
        with open("../logs/HumidityManagement.log", "a") as log_file:
            log_file.write(f"Failed to get topics from the Catalog\nResponse: {response.reason}\n") # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    subscriber = HumidityManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()