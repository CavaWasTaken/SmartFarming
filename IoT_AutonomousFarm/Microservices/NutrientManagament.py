import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import socket
import requests

# nutrient management component is a MQTT subscriber and it receives the NPK, pH and soil moisture values from the sensors
device_id = socket.gethostname()

def handle_message(topic, val):
    with open("../logs/NutrientManagement.log", "a") as log_file:
        topic = topic.split("/")[-1]
        if topic == "NPK":
            if val < 100:
                log_file.write(f"NPK is low: {val}\n")
                # take action
            else:
                log_file.write(f"NPK is high: {val}\n")
                # take action
        elif topic == "Ph":
            if val < 7:
                log_file.write(f"pH is low: {val}\n")
                # take action
            else:
                log_file.write(f"pH is high: {val}\n")
                # take action
        elif topic == "Soil Moisture":
            if val < 50:
                log_file.write(f"Soil moisture is low: {val}\n")
                # take action
            else:
                log_file.write(f"Soil moisture is high: {val}\n")
                # take action

class NutrientManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("../logs/NutrientManagement.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode()) # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received message on {msg.topic}: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)
            
            # if message["bn"] == "greenhouse_0/sensors/NPK":   # check the topic of the message
            #     npk = message["v"]
            #     if npk < 100:
            #         log_file.write(f"NPK is low: {npk}\n")
            #     else:
            #         log_file.write(f"NPK is high: {npk}\n")

            # elif message["bn"] == "greenhouse_0/sensors/Ph":
            #     ph = message["v"]
            #     if ph < 7:
            #         log_file.write(f"pH is low: {ph}\n")
            #     else:
            #         log_file.write(f"pH is high: {ph}\n")
                    
            # elif message["bn"] == "greenhouse_0/sensors/SoilMoisture":
            #     soil_moisture = message["v"]
            #     if soil_moisture < 50:
            #         log_file.write(f"Soil moisture is low: {soil_moisture}\n")
            #     else:
            #         log_file.write(f"Soil moisture is high: {soil_moisture}\n")
            # elif message["bn"] == "greenhouse_0/schedules/fertilization":
            #     log_file.write(f"Received fertilization schedule: {message["e"]}\n")

if __name__ == "__main__":
    response = requests.get(f"http://localhost:8080/get_device_configurations", params={'device_id': device_id, 'device_type': 'NutrientManagement'})    # get the device information from the catalog
    if response.status_code == 200:
        configuration = response.json()
    else:
        with open("../logs/NutrientManagement.log", "a") as log_file:
            log_file.write("Failed to get configuration from the Catalog\n")
            exit(1)

    mqtt_broker = configuration["mqtt_broker"]
    mqtt_port = configuration["mqtt_port"]
    mqtt_topic = configuration["mqtt_topic"]

    subscriber = NutrientManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()