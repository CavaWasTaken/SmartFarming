import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber

# light management component is a MQTT subscriber and it receives the light and temperature values
class LightManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("../logs/LightManagement.log", "a") as log_file: # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received message on {msg.topic}: {message}\n")   # write on the log file the message received
            if message["bn"] == "greenhouse_0/sensors/LightIntensity":    # check the topic of the message
                light_intensity = message["v"]  # get the light intensity value
                if light_intensity < 100:
                    log_file.write(f"Light intensity is low: {light_intensity}\n")
                else:
                    log_file.write(f"Light intensity is high: {light_intensity}\n")
            elif message["bn"] == "greenhouse_0/sensors/DTH22/Temperature":   # check the topic of the message
                temperature = message["v"]
                if temperature < 20:
                    log_file.write(f"Temperature is low: {temperature}\n")
                else:
                    log_file.write(f"Temperature is high: {temperature}\n")
            elif message["bn"] == "greenhouse_0/schedules/lighting":  # check the topic of the message
                log_file.write(f"Received lighting schedule: {message["e"]}\n")

if __name__ == "__main__":
    broker = "mqtt.eclipseprojects.io"  # broker address
    port = 1883
    topics = ["greenhouse_0/sensors/LightIntensity", "greenhouse_0/sensors/DTH22/Temperature", "greenhouse_0/schedules/lighting"]    # nutrient values

    subscriber = LightManagement(broker, port, topics)
    subscriber.connect()