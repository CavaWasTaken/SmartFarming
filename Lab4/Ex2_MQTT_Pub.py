import json
import time
import random

import paho.mqtt.client as PahoMQTT

class MqttPublisher:
    def __init__(self, broker, port, topic):
        self.client = PahoMQTT.Client()
        self.broker = broker
        self.port = port
        self.topic = topic

    def connect(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def publish(self, message, t):
        topic = message.split()[0]
        value = message.split()[1]
        if(topic == "temperature"):
            response = {
                "bn": "group/DHT11/temperature",    # base name
                "e": [  # array of data
                    {
                        "n": "temperature", # name of the data
                        "u": "Cel", # celsius
                        "t": t, # time of the data
                        "v": value    # value of the data
                    }
                ]
            }
        elif(topic == "humidity"):
            response = {
                "bn": "group/DHT11/humidity",
                "e": [
                    {
                        "n": "humidity",
                        "u": "%RH",   # relative humidity
                        "t": t,
                        "v": value
                    }
                ]
            }
        # print("Publishing message: ", json.dumps(response))
        self.client.publish(self.topic, json.dumps(response), 2)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

def generate_temperature():
        return round(random.uniform(20.0, 25.0), 2)

def generate_humidity():
    return round(random.uniform(30.0, 50.0), 2)

if __name__ == "__main__":
    broker = "mqtt.eclipseprojects.io"  # public broker
    port = 1883 # default port for mqtt
    temp_topic = "group/DTH11/temperature"    
    hum_topic = "group/DTH11/humidity"

    temp_publisher = MqttPublisher(broker, port, temp_topic)
    hum_publisher = MqttPublisher(broker, port, hum_topic)

    temp_publisher.connect()
    hum_publisher.connect()

    start_t = int(time.time())

    try:    
        while True: # every 5 seconds publish a new message about temperature and humidity
            temp_message = "temperature "+ str(generate_temperature())
            hum_message = "humidity "+ str(generate_humidity())

            t = int(time.time()) - start_t
            temp_publisher.publish(temp_message, t)
            hum_publisher.publish(hum_message, t)

            time.sleep(5)
    except KeyboardInterrupt:   # if the user press ctrl+c, the program will stop
        temp_publisher.disconnect()
        hum_publisher.disconnect()
    finally:
        temp_publisher.disconnect()
        hum_publisher.disconnect()