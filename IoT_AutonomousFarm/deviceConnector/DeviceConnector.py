import paho.mqtt.client as mqtt
from datetime import datetime
import time
import json
import requests
import sys
import os
# add the path of the parent directory to the sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) # we can import the sensors classes

from sensors import DTH22, Light, NPK, pH, SoilMoisture, Sensor

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/DeviceConnector.log", "a") as log_file:
        log_file.write(f"{message}")

# each time that the device starts, we clear the log file
with open("./logs/DeviceConnector.log", "w") as log_file:
    pass

# read the device_id and mqtt information of the broker from the json file
with open("./DeviceConnector_config.json", "r") as config_fd:
    config = json.load(config_fd)   # read the configuration from the json file
    catalog_url = config["catalog_url"] # read the url of the Catalog
    device_id = config["device_id"] # read the device_id of the device connector
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # read the mqtt broker address
    mqtt_port = config["mqtt_connection"]["mqtt_port"]  # read the mqtt broker port
    keep_alive = config["mqtt_connection"]["keep_alive"]    # read the keep alive time of the mqtt connection

# REST API calls to the Catalog to get the list of sensors connected to this device connector
response = requests.get(f'{catalog_url}/get_sensors', params={'device_id': device_id, 'device_name': 'DeviceConnector'})    # read the list of sensors from the Catalog
if response.status_code == 200: # if the request is successful
    sensors = response.json()["sensors"]    # sensors is a dictionary of sensors connected to the device connector
    write_log(f"Received {len(sensors)} sensors: {sensors}\n")
else:
    write_log(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
    exit(1) # if we fail to get the sensor list, the device connector stops

# get the location of the greenhouse from the Catalog
response = requests.get(f'{catalog_url}/get_greenhouse_location', params={'greenhouse_id': sensors[0]["greenhouse_id"]})    # read the greenhouse location from the Catalog
if response.status_code == 200: # if the request is successful
    greenhouse_location = response.json()["location"]    # get the location from the response
    write_log(f"Received greenhouse location: {greenhouse_location}\n")
    classSensor = Sensor.Sensor(location=greenhouse_location)    # create a sensor object with the location of the greenhouse
    classDTH22 = DTH22.DTH22(classSensor)    # create a DTH22 object with the sensor object
    classLight = Light.Light(classSensor)  # create a LightIntensity object with the sensor object
    classNPK = NPK.NPK(classSensor)  # create a NPK object with the sensor object
    classpH = pH.pH(classSensor)    # create a pH object with the sensor object
    classSoilMoisture = SoilMoisture.SoilMoisture(classSensor)  # create a SoilMoisture object with the sensor object
else:
    write_log(f"Failed to get greenhouse location from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
    exit(1)

# MQTT Client setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, keep_alive)  # connection to the MQTT broker with the read configuration
write_log(f"Connected to the MQTT broker\n")    # write in the log file that the connection is successful

start_time = datetime.now() # get the current time
start_time = (start_time.hour*3600 + start_time.minute*60 + start_time.second)/3600  # convert the time to hours

while True:
    timestamp = datetime.now()  # get the current time
    timestamp = (timestamp.hour*3600 + timestamp.minute*60 + timestamp.second)/3600  # convert the time to hours
    timestamp -= start_time  # calculate the time passed since the start of the simulation

    write_log("\n")
    for sensor in sensors:  # iterate over the list of sensors
        val = -1    # default value read from the sensor
        # check the sensor name, if its knwon we read its value
        if(sensor["name"] == "DTH22"):  
            # DTH22 is the only senosor in our system that collects two values, temperature and humidity, so we need to handle both
            if(sensor["type"] == "Temperature"):
                val = classDTH22.get_DTH22_Temperature()
            elif(sensor["type"] == "Humidity"):
                val = classDTH22.get_DTH22_Humidity()
        elif(sensor["name"] == "NPK"):
            val = classNPK.get_NPK_Values(timestamp)
        elif(sensor["name"] == "SoilMoisture"):
            val = classSoilMoisture.get_SoilMoisture_Values(timestamp)
        elif(sensor["name"] == "pH"):
            val = classpH.get_pH_Values(timestamp)
        elif(sensor["name"] == "PAR"):
            val = classLight.get_LightIntensity_Values()
        else:
            # not recognized sensor, write the error in the log file
            write_log(f"Sensor not recognized: {sensor['name']}\n")
            continue    # skip to the next iteration, so at the next sensor
        
        # we want to pusblish values with senML format, so we create a dictionary of the value read from the sensor
        senML = json.dumps({"bn": f"greenhouse_{sensor["greenhouse_id"]}/sensor_{sensor['sensor_id']}", "e": {"n": sensor["type"], "v": val, "u": sensor["unit"], "t": int(timestamp*3600)}})
        senML_dictionary = json.loads(senML)
        client.publish(senML_dictionary["bn"], senML)  # publish the value read from the sensor to the MQTT broker
        # write in a log file the value published
        write_log(f"Published: {senML}\n")

    time.sleep(120)   # wait for 2 minutes before reading the sensors again