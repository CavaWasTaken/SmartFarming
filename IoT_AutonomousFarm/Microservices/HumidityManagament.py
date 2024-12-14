import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import socket
import requests

# humidity management component is a MQTT subscriber and it receives the humidity and soil moisture values
device_id = socket.gethostname()

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

            # if message["bn"] == "greenhouse_0/sensors/DTH22/Humidity":    # check the topic of the message
            #     humidity = message["v"] # get the value of the message
            #     if humidity < 60:   # check if the value is lower than a threshold
            #         log_file.write(f"Humidity is low: {humidity}\n")    # write on the log file what it has understand
            #         # take action
            #     else:
            #         log_file.write(f"Humidity is high: {humidity}\n")
            #         # take action
            # elif message["bn"] == "greenhouse_0/sensors/SoilMoisture":
            #     soil_moisture = message["v"]    # get the value of the message
            #     if soil_moisture < 40:  # check if the value is lower than a threshold
            #         log_file.write(f"Soil moisture is low: {soil_moisture}\n")
            #         # take action
            #     else:
            #         log_file.write(f"Soil moisture is high: {soil_moisture}\n")
            #         # take action
            # elif message["bn"] == "greenhouse_0/schedules/irrigation":
            #     log_file.write(f"Irrigation scheduled: {message["e"]}\n")
            #     # take action
            # elif message["bn"] == "greenhouse_0/schedules/humidity":
            #     log_file.write(f"Humidity scheduled: {message["e"]}\n")
            #     # take action

if __name__ == "__main__":
    # broker = "mqtt.eclipseprojects.io"  # broker address
    # port = 1883
    # topics = ["greenhouse_0/sensors/DTH22/Humidity", "greenhouse_0/sensors/SoilMoisture", "greenhouse_0/schedules/irrigation", "greenhouse_0/schedules/humidity"]    # nutrient values

    response = requests.get(f"http://localhost:8080/get_device_configurations", params={'device_id': device_id, 'device_type': 'HumidityManagement'})    # get the device information from the catalog
    if response.status_code == 200:
        configuration = response.json()
    else:
        with open("../logs/HumidityManagement.log", "a") as log_file:
            log_file.write("Failed to get configuration from the Catalog\n")
            exit(1)

    mqtt_broker = configuration["mqtt_broker"]
    mqtt_port = configuration["mqtt_port"]
    mqtt_topic = configuration["mqtt_topic"]

    subscriber = HumidityManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()