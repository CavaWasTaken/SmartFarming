import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import sys
import os
import socket
import requests


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Catalog import CatalogService 

# light management component is a MQTT subscriber and it receives the light and temperature values
catalog = CatalogService()
device_id = socket.gethostname()

def handle_message(topic, val):
    with open("../logs/LightManagement.log", "a") as log_file:
        topic = topic.split("/")[-1]
        if topic == "LightIntensity":
            if val < 100:
                log_file.write(f"Light intensity is low: {val}\n")
            else:
                log_file.write(f"Light intensity is high: {val}\n")
        elif topic == "Temperature":
            if val < 20:
                log_file.write(f"Temperature is low: {val}\n")
            else:
                log_file.write(f"Temperature is high: {val}\n")
        elif topic == "lighting":
            log_file.write(f"Received lighting schedule: {val}\n")

class LightManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("../logs/LightManagement.log", "a") as log_file: # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received message on {msg.topic}: {message}\n")   # write on the log file the message received
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)
            
            # if message["bn"] == "greenhouse_0/sensors/LightIntensity":    # check the topic of the message
            #     light_intensity = message["v"]  # get the light intensity value
            #     if light_intensity < 100:
            #         log_file.write(f"Light intensity is low: {light_intensity}\n")
            #     else:
            #         log_file.write(f"Light intensity is high: {light_intensity}\n")
            # elif message["bn"] == "greenhouse_0/sensors/DTH22/Temperature":   # check the topic of the message
            #     temperature = message["v"]
            #     if temperature < 20:
            #         log_file.write(f"Temperature is low: {temperature}\n")
            #     else:
            #         log_file.write(f"Temperature is high: {temperature}\n")
            # elif message["bn"] == "greenhouse_0/schedules/lighting":  # check the topic of the message
            #     log_file.write(f"Received lighting schedule: {message["e"]}\n")

if __name__ == "__main__":
    response = requests.get(f"http://localhost:8080/get_device_configurations", params={"device_id": device_id, 'device_type': 'LightManagement'})
    if response.status_code == 200:
        response = response.json()
    else:
        with open("../logs/LightManagement.log", "a") as log_file:
            log_file.write("Failed to get configuration from the Catalog\n")
            exit(1)

    mqtt_broker = response["mqtt_broker"]
    mqtt_port = response["mqtt_port"]
    mqtt_topic = response["mqtt_topic"]

    subscriber = LightManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()