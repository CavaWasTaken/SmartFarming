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
        topic = topic.split("/")[-1]
        if topic == "LightIntensity":
            if val < 100:
                log_file.write(f"Light intensity is low: {val}\n")
                # take action
            else:
                log_file.write(f"Light intensity is high: {val}\n")
                # take action
        elif topic == "Temperature":
            if val < 20:
                log_file.write(f"Temperature is low: {val}\n")
                # take action
            else:
                log_file.write(f"Temperature is high: {val}\n")
                # take action
        elif topic == "lighting":
            log_file.write(f"Received lighting schedule: {val}\n")
            # take action

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

    mqtt_topic = []
    for sensor in sensors:
        mqtt_topic.append(f"greenhouse_{sensor["greenhouse_id"]}/plant_{sensor["plant_id"] if sensor["plant_id"] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")


    subscriber = LightManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()