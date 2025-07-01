import paho.mqtt.client as PahoMQTT

class MqttClient:
    def __init__(self, broker, port, keep_alive, clientID, on_message, log_function):
        self.broker = broker
        self.port = port
        self.keep_alive = keep_alive
        self.clientID = clientID
        self.paho = PahoMQTT.Client(client_id=clientID, clean_session=True)
        self.paho.on_connect = self.on_connect
        self.paho.on_message = on_message
        self.log_function = log_function
        self.subs = []

    def start(self):
        self.paho.connect(self.broker, self.port, self.keep_alive)
        self.paho.loop_start()

    def stop(self):
        for topic in self.subs:
            self.unsubscribe(topic)
        self.paho.loop_stop()
        self.paho.disconnect()

    def subscribe(self, topic):
        if topic not in self.subs:
            self.subs.append(topic)
            self.paho.subscribe(topic, 2)
            self.log_function(f"Subscribed to {topic}")
        else:
            self.log_function(f"Impossible to subscribe to {topic} because it is already subscribed")

    def unsubscribe(self, topic):
        if topic in self.subs:
            self.subs.remove(topic)
            self.paho.unsubscribe(topic)
            self.log_function(f"Unsubscribed from {topic}")
        else:
            self.log_function(f"Impossible to unsubscribe from {topic} because it is not subscribed")

    def publish(self, topic, message):
        self.paho.publish(topic, message, 2)
        self.log_function(f"Published to {topic}: {message}")

    def on_connect(self, client, userdata, flags, rc):
        self.log_function(f"Connected to {self.broker} with result code {rc}")
        print(f"Connected to {self.broker} with result code {rc}")