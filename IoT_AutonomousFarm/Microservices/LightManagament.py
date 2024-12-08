import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber

# light management component is a MQTT subscriber and it receives the light and temperature values
class LightManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("../logs/logs_LightManagement.txt", "a") as log_file:
            log_file.write(f"Received message on {msg.topic}: {msg.payload}\n")
            message = json.loads(msg.payload.decode())
            print(message)
            if message["bn"] == "greenhouse/sensors/LightIntensity":
                light_intensity = message["v"]
                if light_intensity < 100:
                    log_file.write(f"Light intensity is low: {light_intensity}\n")
                else:
                    log_file.write(f"Light intensity is high: {light_intensity}\n")
            elif message["bn"] == "greenhouse/sensors/DTH22/Temperature":
                temperature = message["v"]
                if temperature < 20:
                    log_file.write(f"Temperature is low: {temperature}\n")
                else:
                    log_file.write(f"Temperature is high: {temperature}\n")

if __name__ == "__main__":
    broker = "mqtt.eclipseprojects.io"  # broker address
    port = 1883
    topics = ["greenhouse/sensors/LightIntensity", "greenhouse/sensors/DTH22/Temperature"]    # nutrient values

    subscriber = LightManagement(broker, port, topics)
    subscriber.connect()