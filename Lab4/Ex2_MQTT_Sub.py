import json
import paho.mqtt.client as PahoMQTT

class MqttSubscriber:
    def __init__(self, broker, port, topics):
        self.client = PahoMQTT.Client()
        self.broker = broker
        self.port = port
        self.topics = topics

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        for topic in self.topics:
            self.client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        topic = msg.topic.split("/")[-1]
        payload = json.loads(msg.payload.decode())
        # print(payload)
        value = payload["e"][0]["v"]
        # print(value)
        t = payload["e"][0]["t"]
        # print(t)
        u = payload["e"][0]["u"]
        # print(u)
        print(f"group/DTH11 measured {'a' if topic == 'temperature' else 'an'} {topic} of {value} {u} at the time {t}")

    def connect(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker, self.port)
        self.client.loop_forever()

if __name__ == "__main__":
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    topics = ["group/DTH11/temperature", "group/DTH11/humidity"]

    subscriber = MqttSubscriber(broker, port, topics)
    subscriber.connect()
