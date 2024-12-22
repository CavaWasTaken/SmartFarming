import paho.mqtt.client as mqtt
import time
import random
import json
import requests

# device connector is a MQTT publisher that reads data from the sensors connected to RaspberryPi and publishes it to the MQTT broker


# read the device_id and mqtt information of the broker from the json file
with open("./DeviceConnector_config.json", "r") as config_fd:
    config = json.load(config_fd)
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_broker"]
    mqtt_port = config["mqtt_port"]
    keep_alive = config["keep_alive"]

# REST API calls to the Catalog to get the configuration
response = requests.get('http://localhost:8080/get_topics', params={'device_id': device_id, 'device_type': 'DeviceConnector'})    # read the topics from the Catalog
if response.status_code == 200: # if the request is successful read the mqtt topic
    mqtt_topic = response.json()    # obtain the data from the response in json format
    mqtt_topic = mqtt_topic["topics"][0]   # obtain the array of topics
    with open("./logs/DeviceConnector.log", "a") as log_file:   # to be more clear, we write everything in a log file
        log_file.write(f"Received mqtt_topic: {mqtt_topic}\n")
else:
    with open("./logs/DeviceConnector.log", "a") as log_file:
        log_file.write(f"Failed to get topics from the Catalog\nResponse: {response.reason}\n") # in case of error, write the reason of the error in the log file
        exit(1) # if the request fails, the device connector stops

# REST API calls to the Catalog to get the list of sensors connected to this device connector
response = requests.get('http://localhost:8080/get_sensors', params={'device_id': device_id, 'device_type': 'DeviceConnector'})    # read the list of sensors from the Catalog
if response.status_code == 200: # if the request is successful
    sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor connected to the device connector
    with open("./logs/DeviceConnector.log", "a") as log_file:   # to be more clear, we write everything in a log file
        log_file.write(f"Received sensors: {sensors}\n")
else:
    with open("./logs/DeviceConnector.log", "a") as log_file:
        log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
        exit(1) # if the request fails, the device connector stops

# MQTT Client setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, keep_alive)  # connection to the MQTT broker with the read configuration
with open("./logs/DeviceConnector.log", "a") as log_file:
    log_file.write(f"Connected to the MQTT broker\n")    # write in the log file that the connection is successful

# this are simulation functions of real sensors, they generate  only random values without a logic
# DTH22 is the sensor that measures temperature and humidity
def get_DTH22_Humidity():
    humidity = random.uniform(0.0, 100.0)  # Read data from the sensors
    if humidity is not None:
        return humidity
    else:
        return None

def get_DTH22_Temperature():
    temperature = random.uniform(10.0, 35.0)  # Read data from the sensors
    if temperature is not None:
        return temperature
    else:
        return None
    
# grove NPK sensor is the sensor that measures NPK values
def get_NPK_Values():
    NPK = random.uniform(0.0, 1000.0)  # Read data from the sensors
    if NPK is not None:
        return NPK
    else:
        return None
    
# capacitive soil moisture sensor is the sensor that measures soil moisture
def get_SoilMoisture_Values():
    soil_moisture = random.uniform(0.0, 100.0)  # Read data from the sensors
    if soil_moisture is not None:
        return soil_moisture
    else:
        return None
    
# analog pH sensor is the sensor that measures pH values of the soil
def get_pH_Values():
    pH = random.uniform(3.0, 9.0)  # Read data from the sensors
    if pH is not None:
        return pH
    else:
        return None
    
# ldr sensor is the sensor that measures light intensity
def get_LightIntensity_Values():
    light_intensity = random.uniform(0.0, 1000.0)  # Read data from the sensors
    if light_intensity is not None:
        return light_intensity
    else:
        return None

start_time = int(time.time())   # get the time when the device connector starts

while True:
    timestamp = int(time.time()-start_time) # get the time since the device connector started

    for sensor in sensors:  # iterate over the list of sensors
        val = -1    # default value read from the sensor
        # check the sensor name, if its knwon we read its value
        if(sensor["name"] == "DTH22"):  
            # DTH22 is the only senosor in our system that collects two values, temperature and humidity, so we need to handle both
            if(sensor["type"] == "Temperature"):
                val = get_DTH22_Temperature()
            elif(sensor["type"] == "Humidity"):
                val = get_DTH22_Humidity()
        elif(sensor["name"] == "NPK"):
            val = get_NPK_Values()
        elif(sensor["name"] == "SoilMoisture"):
            val = get_SoilMoisture_Values()
        elif(sensor["name"] == "Ph"):
            val = get_pH_Values()
        elif(sensor["name"] == "LightIntensity"):
            val = get_LightIntensity_Values()
        else:
            # not recognized sensor, write the error in the log file
            with open("./logs/DeviceConnector.log", "a") as log_file:
                log_file.write(f"Sensor not recognized: {sensor['name']}\n")
            continue    # skip to the next iteration, so at the next sensor
        
        # we want to pusblish values with senML format, so we create a dictionary of the value read from the sensor
        senML = json.dumps({"bn": f"{mqtt_topic[0]}/{sensor['name']}/{sensor['type']}", "n": sensor["type"], "v": val, "t": timestamp})
        client.publish(f"{mqtt_topic[0]}/{sensor['name']}/{sensor['type']}", senML)
        # write in a log file the value published
        with open("./logs/DeviceConnector.log", "a") as log_file:
            log_file.write(f"Published: {senML}\n")

    time.sleep(60)  # publish sensor values every 60 seconds