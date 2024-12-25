import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests

# nutrient management component is a MQTT subscriber and it receives the NPK, pH and soil moisture values from the sensors


# read the device_id and mqtt information of the broker from the json file
with open("./NutrientManagement_config.json", "r") as config_fd:
    config = json.load(config_fd)
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_broker"]
    mqtt_port = config["mqtt_port"]
    keep_alive = config["keep_alive"]

def handle_message(topic, val):
    with open("../logs/NutrientManagement.log", "a") as log_file:

        def check_val(sensor_id, param, unit, val, min_treshold, max_treshold):   # function that checks if the value is in the accepted range
            if val < min_treshold:
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} {unit} is low\taccepted range {min_treshold}-{max_treshold}\n")
            elif val > max_treshold:
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} is high\taccepted range {min_treshold}-{max_treshold}\n")
            else:
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} is in the accepted range {min_treshold}-{max_treshold}\n")

        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        response = requests.get(f"http://localhost:8080/get_sensor_id", params={'device_id': device_id, 'device_name': 'NutrientManagement', 'greenhouse_id': greenhouse.split("_")[1], 'plant_id': plant.split("_")[1], 'sensor_name': sensor_name, 'sensor_type': sensor_type})    # get the sensor id from the catalog
        if response.status_code == 200:
            sensor_id = response.json()["sensor_id"]
            log_file.write(f"New value collected by sensor {sensor_id}\n")
        else:
            log_file.write(f"Failed to get sensor id from the Catalog\nResponse: {response.reason}\n")
            exit(1) # if the request fails, the device connector stops

        treshold = tresholds[f"sensor_{sensor_id}"]    # get the treshold for the sensor

        if sensor_type == "NPK":    # check the values of NPK
            check_val(sensor_id, "N", "mg/L", val["N"], treshold["N"]["min"], treshold["N"]["max"])  # check if the values are in the accepted range
            check_val(sensor_id, "P", "mg/L", val["P"], treshold["P"]["min"], treshold["P"]["max"])
            check_val(sensor_id, "K", "mg/L", val["K"], treshold["K"]["min"], treshold["K"]["max"])

        elif sensor_type == "pH":   # check the value of pH
            check_val(sensor_id, "pH", "", val, treshold["min"], treshold["max"])

        elif sensor_type == "SoilMoisture":   # check the value of soil moisture
            check_val(sensor_id, "soil moisture", "%", val, treshold["min"], treshold["max"])

class NutrientManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("../logs/NutrientManagement.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode()) # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)

if __name__ == "__main__":
    response = requests.get(f"http://localhost:8080/get_sensors", params={'device_id': device_id, 'device_name': 'NutrientManagement'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]   # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("../logs/NutrientManagement.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("../logs/NutrientManagement.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # array of topics where the device is subscribed
    global tresholds    # global variable that contains the tresholds for each sensor
    tresholds = {}  # dictionary that contains the tresholds for each sensor
    for sensor in sensors:  # for each sensor build the topic where the device is subscribed and build the dictionary of tresholds
        mqtt_topic.append(f"greenhouse_{sensor["greenhouse_id"]}/plant_{sensor["plant_id"] if sensor["plant_id"] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")
        tresholds[f"sensor_{sensor['sensor_id']}"] = sensor['threshold']    # associate the threshold to the sensor id into the dictionary

    # the mqtt subscriber subscribes to the topics
    subscriber = NutrientManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()