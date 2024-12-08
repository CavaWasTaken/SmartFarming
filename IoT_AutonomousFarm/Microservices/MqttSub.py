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
        print(f"Received message on {msg.topic}: {msg.payload}")

    def connect(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker, self.port)
        self.client.loop_forever()