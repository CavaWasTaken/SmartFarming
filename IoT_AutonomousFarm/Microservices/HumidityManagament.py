import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber

# humidity management component is a MQTT subscriber and it receives the humidity and soil moisture values
class HumidityManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("../logs/logs_HumidityManagement.txt", "a") as log_file:
            log_file.write(f"Received message on {msg.topic}: {msg.payload}\n")
            message = json.loads(msg.payload.decode())
            print(message)
            if message["bn"] == "greenhouse/sensors/DTH22/Humidity":
                humidity = message["v"]
                if humidity < 60:
                    log_file.write(f"Humidity is low: {humidity}\n")
                else:
                    log_file.write(f"Humidity is high: {humidity}\n")
            elif message["bn"] == "greenhouse/sensors/SoilMoisture":
                soil_moisture = message["v"]
                if soil_moisture < 40:
                    log_file.write(f"Soil moisture is low: {soil_moisture}\n")
                else:
                    log_file.write(f"Soil moisture is high: {soil_moisture}\n")

if __name__ == "__main__":
    broker = "mqtt.eclipseprojects.io"  # broker address
    port = 1883
    topics = ["greenhouse/sensors/DTH22/Humidity", "greenhouse/sensors/SoilMoisture"]    # nutrient values

    subscriber = HumidityManagement(broker, port, topics)
    subscriber.connect()