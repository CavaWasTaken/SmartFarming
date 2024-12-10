import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber

# humidity management component is a MQTT subscriber and it receives the humidity and soil moisture values
class HumidityManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("../logs/HumidityManagement.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received message on {msg.topic}: {message}\n")
            if message["bn"] == "greenhouse_1/sensors/DTH22/Humidity":    # check the topic of the message
                humidity = message["v"] # get the value of the message
                if humidity < 60:   # check if the value is lower than a threshold
                    log_file.write(f"Humidity is low: {humidity}\n")    # write on the log file what it has understand
                    # take action
                else:
                    log_file.write(f"Humidity is high: {humidity}\n")
                    # take action
            elif message["bn"] == "greenhouse_1/sensors/SoilMoisture":
                soil_moisture = message["v"]    # get the value of the message
                if soil_moisture < 40:  # check if the value is lower than a threshold
                    log_file.write(f"Soil moisture is low: {soil_moisture}\n")
                    # take action
                else:
                    log_file.write(f"Soil moisture is high: {soil_moisture}\n")
                    # take action
            elif message["bn"] == "greenhouse_1/schedules/irrigation":
                log_file.write(f"Irrigation scheduled: {message["e"]}\n")
                # take action
            elif message["bn"] == "greenhouse_1/schedules/humidity":
                log_file.write(f"Humidity scheduled: {message["e"]}\n")
                # take action

if __name__ == "__main__":
    broker = "mqtt.eclipseprojects.io"  # broker address
    port = 1883
    topics = ["greenhouse_1/sensors/DTH22/Humidity", "greenhouse_1/sensors/SoilMoisture", "greenhouse_1/schedules/irrigation", "greenhouse_1/schedules/humidity"]    # nutrient values

    subscriber = HumidityManagement(broker, port, topics)
    subscriber.connect()