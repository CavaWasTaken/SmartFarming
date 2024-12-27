import paho.mqtt.client as mqtt
import time
import random
import json
import requests
import math

# device connector is a MQTT publisher that reads data from the sensors connected to RaspberryPi and publishes it to the MQTT broker


# read the device_id and mqtt information of the broker from the json file
with open("./DeviceConnector_config.json", "r") as config_fd:
    config = json.load(config_fd)
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_broker"]
    mqtt_port = config["mqtt_port"]
    keep_alive = config["keep_alive"]

# REST API calls to the Catalog to get the list of sensors connected to this device connector
response = requests.get('http://localhost:8080/get_sensors', params={'device_id': device_id, 'device_name': 'DeviceConnector'})    # read the list of sensors from the Catalog
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

# this are simulation functions of real sensors, they generate  only random values without a logic
# DTH22 is the sensor that measures temperature and humidity
def get_DTH22_Humidity():
    # real simulation of humidity sensor
    global current_humidity, start_time

    # simulate time passage
    elapsed_time = time.time() - start_time  # returns the seconds passed since the device connector started
    hours = (elapsed_time / 3600) % 24  # every 24 hours the humidity pattern repeats

    # simulate daily humidity variation using a sinusoidal pattern
    daily_variation = 20 * math.sin(math.pi * hours / 12)  # 20% variation over 24 hours

    # add some random noise
    noise = random.uniform(-5.0, 5.0)

    # update the current humidity
    current_humidity += daily_variation + noise

    # ensure humidity stays within realistic bounds (0 to 100 percent)
    current_humidity = max(0.0, min(100.0, current_humidity))

    return current_humidity

def get_DTH22_Temperature():
    # real simulation of temperature sensor
    global current_temperature, start_time

    # simulate time passage
    elapsed_time = time.time() - start_time # returns the seconds passed since the device connector started
    hours = (elapsed_time / 3600) % 24  # every 24 hours the temperature pattern repeats
    
    # simulate daily temperature variation using a sinusoidal pattern
    daily_variation = 10 * math.sin(math.pi * hours / 12)  # 10 degree variation over 24 hours
    
    # add some random noise
    noise = random.uniform(-1.0, 1.0)
    
    # update the current temperature
    current_temperature += daily_variation + noise

    # ensure temperature stays within realistic bounds (10 to 35 degrees Celsius)
    current_temperature = max(10.0, min(35.0, current_temperature))
    
    return current_temperature

    # temperature = random.uniform(10.0, 35.0)  # Read data from the sensors
    # if temperature is not None:
    #     return temperature
    # else:
    #     return None
    
# grove NPK sensor is the sensor that measures NPK values
def get_NPK_Values():
    # real simulation of NPK sensor
    global current_npk, start_time
    
    # simulate time passage
    elapsed_time = time.time() - start_time
    
    # add some random noise
    noise = {
        'N': random.uniform(-5.0, 5.0),
        'P': random.uniform(-3.0, 3.0),
        'K': random.uniform(-4.0, 4.0)
    }
    
    # introduce gradual decrease
    trend = {
        'N': -0.01 * elapsed_time / 3600,  # small decrease over time
        'P': -0.01 * elapsed_time / 3600,  # small decrease over time
        'K': -0.01 * elapsed_time / 3600   # small decrease over time
    }
    
    # update the current NPK values
    current_npk['N'] += noise['N'] + trend['N']
    current_npk['P'] += noise['P'] + trend['P']
    current_npk['K'] += noise['K'] + trend['K']

    # ensure NPK values stay within realistic bounds (0 to 1000)
    current_npk['N'] = max(0.0, min(1000.0, current_npk['N']))
    current_npk['P'] = max(0.0, min(1000.0, current_npk['P']))
    current_npk['K'] = max(0.0, min(1000.0, current_npk['K']))
    
    return current_npk

    # NPK = random.uniform(0.0, 1000.0)  # Read data from the sensors
    # if NPK is not None:
    #     return NPK
    # else:
    #     return None
    
# capacitive soil moisture sensor is the sensor that measures soil moisture
def get_SoilMoisture_Values():
    # real simulation of soil moisture sensor
    global current_soil_moisture, start_time
    
    # simulate time passage
    elapsed_time = time.time() - start_time
    
    # add some random noise
    noise = random.uniform(-1.0, 1.0)
    
    # introduce gradual decrease
    trend = -0.05 * elapsed_time / 3600  # small decrease over time
    
    # update the current soil moisture value
    current_soil_moisture += noise + trend
    
    # ensure soil moisture stays within realistic bounds (0 to 100)
    current_soil_moisture = max(0.0, min(100.0, current_soil_moisture))
    
    return current_soil_moisture

    # soil_moisture = random.uniform(0.0, 100.0)  # Read data from the sensors
    # if soil_moisture is not None:
    #     return soil_moisture
    # else:
    #     return None
    
# analog pH sensor is the sensor that measures pH values of the soil
def get_pH_Values():
    # real simulation of pH sensor
    global current_pH, start_time
    
    # simulate time passage
    elapsed_time = time.time() - start_time
    
    # add some random noise
    noise = random.uniform(-0.1, 0.1)
    
    # introduce gradual change
    trend = -0.001 * elapsed_time / 3600  # small decrease over time
    
    # update the current pH value
    current_pH += noise + trend
    
    # ensure pH stays within realistic bounds (3.0 to 9.0)
    current_pH = max(3.0, min(9.0, current_pH))
    
    return current_pH

    # pH = random.uniform(3.0, 9.0)  # Read data from the sensors
    # if pH is not None:
    #     return pH
    # else:
    #     return None
    
# ldr sensor is the sensor that measures light intensity
def get_LightIntensity_Values():
    # real simulation of light intensity sensor
    global current_light_intensity, start_time
    
    # simulate time passage
    elapsed_time = time.time() - start_time
    
    # add some random noise
    noise = random.uniform(-10.0, 10.0)
    
    # introduce gradual change
    trend = 0.1 * math.sin(math.pi * elapsed_time / 43200)  # simulate daily light intensity variation
    
    # update the current light intensity value
    current_light_intensity += noise + trend
    
    # ensure light intensity stays within realistic bounds (0 to 1000)
    current_light_intensity = max(0.0, min(1000.0, current_light_intensity))
    
    return current_light_intensity

    # light_intensity = random.uniform(0.0, 1000.0)  # Read data from the sensors
    # if light_intensity is not None:
    #     return light_intensity
    # else:
    #     return None

start_time = time.time()   # get the time when the device connector starts
current_humidity = 50.0  # default humidity value for the simulation
current_temperature = 22.0  # default temperature value for the simulation
current_npk = {"N": 500.0, "P": 500.0, "K": 500.0}  # default NPK values for the simulation
current_soil_moisture = 50.0  # default soil moisture value for the simulation
current_pH = 7.0  # default pH value for the simulation
current_light_intensity = 500.0  # default light intensity value for the simulation

while True:
    timestamp = int(time.time()-int(start_time)) # get the time since the device connector started

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
        elif(sensor["name"] == "pH"):
            val = get_pH_Values()
        elif(sensor["name"] == "LightIntensity"):
            val = get_LightIntensity_Values()
        else:
            # not recognized sensor, write the error in the log file
            with open("./logs/DeviceConnector.log", "a") as log_file:
                log_file.write(f"Sensor not recognized: {sensor['name']}\n")
            continue    # skip to the next iteration, so at the next sensor
        
        # we want to pusblish values with senML format, so we create a dictionary of the value read from the sensor
        senML = json.dumps({"bn": f"greenhouse_{sensor["greenhouse_id"]}/plant_{sensor["plant_id"] if sensor["plant_id"] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}", "n": sensor["type"], "v": val, "t": timestamp})
        senML_dictionary = json.loads(senML)
        client.publish(senML_dictionary["bn"], senML)  # publish the value read from the sensor to the MQTT broker
        # write in a log file the value published
        with open("./logs/DeviceConnector.log", "a") as log_file:
            log_file.write(f"Published: {senML}\n")

    time.sleep(60)  # publish sensor values every 60 seconds