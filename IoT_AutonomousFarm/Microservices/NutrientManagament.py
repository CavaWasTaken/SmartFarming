import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber

# nutrient management component is a MQTT subscriber and it receives the NPK, pH and soil moisture values from the sensors
class NutrientManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("../logs/NutrientManagement.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode()) # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received message on {msg.topic}: {message}\n")
            if message["bn"] == "greenhouse_0/sensors/NPK":   # check the topic of the message
                npk = message["v"]
                if npk < 100:
                    log_file.write(f"NPK is low: {npk}\n")
                else:
                    log_file.write(f"NPK is high: {npk}\n")

            elif message["bn"] == "greenhouse_0/sensors/Ph":
                ph = message["v"]
                if ph < 7:
                    log_file.write(f"pH is low: {ph}\n")
                else:
                    log_file.write(f"pH is high: {ph}\n")
                    
            elif message["bn"] == "greenhouse_0/sensors/SoilMoisture":
                soil_moisture = message["v"]
                if soil_moisture < 50:
                    log_file.write(f"Soil moisture is low: {soil_moisture}\n")
                else:
                    log_file.write(f"Soil moisture is high: {soil_moisture}\n")
            elif message["bn"] == "greenhouse_0/schedules/fertilization":
                log_file.write(f"Received fertilization schedule: {message["e"]}\n")

if __name__ == "__main__":
    broker = "mqtt.eclipseprojects.io"  # broker address
    port = 1883
    topics = ["greenhouse_0/sensors/NPK", "greenhouse_0/sensors/Ph", "greenhouse_0/sensors/SoilMoisture", "greenhouse_0/schedules/fertilization"]    # nutrient values

    subscriber = NutrientManagement(broker, port, topics)
    subscriber.connect()