import paho.mqtt.client as mqtt
from datetime import datetime
import time
import json
import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sensors import DTH22, NPK, soilMoisture, pH, light
# each time that the device starts, we clear the log file
with open("./logs/DeviceConnector.log", "w") as log_file:
    pass

# read the device_id and mqtt information of the broker from the json file
with open("./DeviceConnector_config.json", "r") as config_fd:
    config = json.load(config_fd)
    catalog_url = config["catalog_url"]
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
    mqtt_port = config["mqtt_connection"]["mqtt_port"]
    keep_alive = config["mqtt_connection"]["keep_alive"]

# REST API calls to the Catalog to get the list of sensors connected to this device connector
response = requests.get(f'{catalog_url}/get_sensors', params={'device_id': device_id, 'device_name': 'DeviceConnector'})    # read the list of sensors from the Catalog
if response.status_code == 200: # if the request is successful
    sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor connected to the device connector
    with open("./logs/DeviceConnector.log", "a") as log_file:   # to be more clear, we write everything in a log file
        log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
else:
    with open("./logs/DeviceConnector.log", "a") as log_file:
        log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
        exit(1) # if the request fails, the device connector stops

# MQTT Client setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, keep_alive)  # connection to the MQTT broker with the read configuration
with open("./logs/DeviceConnector.log", "a") as log_file:
    log_file.write(f"Connected to the MQTT broker\n")    # write in the log file that the connection is successful

start_time = datetime.now() # get the current time
start_time = (start_time.hour*3600 + start_time.minute*60 + start_time.second)/3600  # convert the time to hours

while True:
    timestamp = datetime.now() 
    timestamp = (timestamp.hour*3600 + timestamp.minute*60 + timestamp.second)/3600  # convert the time to hours
    timestamp -= start_time  # calculate the time passed since the start of the simulation

    for sensor in sensors:  # iterate over the list of sensors
        val = -1    # default value read from the sensor
        # check the sensor name, if its knwon we read its value
        if(sensor["name"] == "DTH22"):  
            # DTH22 is the only senosor in our system that collects two values, temperature and humidity, so we need to handle both
            if(sensor["type"] == "Temperature"):
                val = DTH22.get_DTH22_Temperature()
            elif(sensor["type"] == "Humidity"):
                val = DTH22.get_DTH22_Humidity()
        elif(sensor["name"] == "NPK"):
            val = NPK.get_NPK_Values(timestamp)
        elif(sensor["name"] == "SoilMoisture"):
            val = soilMoisture.get_SoilMoisture_Values(timestamp)
        elif(sensor["name"] == "pH"):
            val = pH.get_pH_Values(timestamp)
        elif(sensor["name"] == "LightIntensity"):
            val = light.get_LightIntensity_Values()
        else:
            # not recognized sensor, write the error in the log file
            with open("./logs/DeviceConnector.log", "a") as log_file:
                log_file.write(f"Sensor not recognized: {sensor['name']}\n")
            continue    # skip to the next iteration, so at the next sensor
        
        # we want to pusblish values with senML format, so we create a dictionary of the value read from the sensor
        senML = json.dumps({"bn": f"greenhouse_{sensor["greenhouse_id"]}/plant_{sensor["plant_id"] if sensor["plant_id"] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}", "n": sensor["type"], "v": val, "t": int(timestamp*3600)})
        senML_dictionary = json.loads(senML)
        client.publish(senML_dictionary["bn"], senML)  # publish the value read from the sensor to the MQTT broker
        # write in a log file the value published
        with open("./logs/DeviceConnector.log", "a") as log_file:
            log_file.write(f"Published: {senML}\n")
        
    time.sleep(60)   # wait for 1 minute before reading the sensors again