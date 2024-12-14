import paho.mqtt.client as mqtt
import time
import random
import json
import requests
import socket

# device connector is a MQTT publisher that reads data from the sensors connected to RaspberryPi and publishes it to the MQTT broker
device_id = socket.gethostname()    # get the name of the device running

# on the same device are running DeviceConnector and all the MicroServices, so all these components are sharing the same device_id. 
# This is why in the devices table of the DB (where all the microservices and device connectors are saved), the primay key is made by the device_id and the type of device. 
# Cause i think that in our system we cannot have more than one of the same device on the same greenhouse. (At each raspberry is connected just one device connector, not more. The same for management components)

# REST API calls to the Catalog to get the configuration
response = requests.get('http://localhost:8080/get_device_configurations', params={'device_id': device_id, 'device_type': 'DeviceConnector'})    # read the configuration from the Catalog
if response.status_code == 200: # if the request is successful
    configuration = response.json() # configutation is a dictionary
else:
    with open("./logs/DeviceConnector.log", "a") as log_file:
        log_file.write(f"Failed to get configuration from the Catalog\n")
        exit(1) # if the request fails, the device connector stops
# extract information from the configuration dictionary
mqtt_broker = configuration["mqtt_broker"]
mqtt_port = configuration["mqtt_port"]
mqtt_topic = configuration["mqtt_topic"]
keep_alive = configuration["keep_alive"]

# REST API calls to the Catalog to get the list of sensors connected to this device connector
response = requests.get('http://localhost:8080/get_sensors', params={'device_id': device_id, 'device_type': 'DeviceConnector'})    # read the list of sensors from the Catalog
if response.status_code == 200: # if the request is successful
    sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor connected to the device connector
else:
    sensors = []    # if the request fails, the list of sensors is empty
    with open("./logs/DeviceConnector.log", "a") as log_file:
        log_file.write(f"Failed to get sensors from the Catalog\n")
        exit(1) # if the request fails, the device connector stops

# MQTT Client setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, keep_alive)  # connection to the MQTT broker with the read configuration

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

    # this commented code is the old mqtt architecture
    # temperature, humidity = get_DTH22_Values()
    # NPK = get_NPK_Values()
    # soil_moisture = get_SoilMoisture_Values()
    # pH = get_pH_Values()
    # light_intensity = get_LightIntensity_Values()
    
    # Create SenML records for each sensor value
    # temperature_senml = json.dumps({"bn": f"{mqtt_topic}/DTH22/Temperature", "n": "temperature", "u": "Cel", "v": temperature, "t": timestamp})
    # humidity_senml = json.dumps({"bn": f"{mqtt_topic}/DTH22/Humidity", "n": "humidity", "u": "%RH", "v": humidity, "t": timestamp})
    # NPK_senml = json.dumps({"bn": f"{mqtt_topic}/NPK", "n": "NPK", "u": "mg/L", "v": NPK, "t": timestamp})
    # soil_moisture_senml = json.dumps({"bn": f"{mqtt_topic}/SoilMoisture", "n": "soil_moisture", "u": "%", "v": soil_moisture, "t": timestamp})
    # pH_senml = json.dumps({"bn": f"{mqtt_topic}/Ph", "n": "pH", "v": pH, "t": timestamp})
    # light_intensity_senml = json.dumps({"bn": f"{mqtt_topic}/LightIntensity", "n": "light_intensity", "u": "lux", "v": light_intensity, "t": timestamp})
    
    # # Publish the sensor values to the MQTT broker
    # client.publish(f"{mqtt_topic}/DTH22/Temperature", temperature_senml)
    # client.publish(f"{mqtt_topic}/DTH22/Humidity", humidity_senml)
    # client.publish(f"{mqtt_topic}/NPK", NPK_senml)
    # client.publish(f"{mqtt_topic}/SoilMoisture", soil_moisture_senml)
    # client.publish(f"{mqtt_topic}/Ph", pH_senml)
    # client.publish(f"{mqtt_topic}/LightIntensity", light_intensity_senml)

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
        senML = json.dumps({"bn": f"{mqtt_topic}/{sensor['name']}/{sensor['type']}", "n": sensor["type"], "v": val, "t": timestamp})
        client.publish(f"{mqtt_topic}/{sensor['name']}/{sensor['type']}", senML)
        # write in a log file the value published
        with open("./logs/DeviceConnector.log", "a") as log_file:
            log_file.write(f"Published: {senML}\n")
    
    # old code
    # with open("./logs/DeviceConnector.log", "a") as log_file:
    #     log_file.write(f"Published: {temperature_senml}\n")
    #     log_file.write(f"Published: {humidity_senml}\n")
    #     log_file.write(f"Published: {NPK_senml}\n")
    #     log_file.write(f"Published: {soil_moisture_senml}\n")
    #     log_file.write(f"Published: {pH_senml}\n")
    #     log_file.write(f"Published: {light_intensity_senml}\n")
    
    time.sleep(10)  # publish sensor values every 10 seconds