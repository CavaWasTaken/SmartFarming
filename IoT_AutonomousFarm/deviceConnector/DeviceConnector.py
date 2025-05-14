from datetime import datetime
import time
import json
import requests
import os

from sensors import Temperature, Humidity, Light, NPK, pH, SoilMoisture, Sensor # import the classes of the sensors
from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/DeviceConnector.log", "a") as log_file:
        log_file.write(f"{message}\n")

# function for the device connector to receive the needed action and perform it
def ActionReceived(client, userdata, message):
    msg = json.loads(message.payload.decode())    # decode the message received
    write_log(f"Received action: {msg}")    # write in the log file the action received
    try:
        sensor_type = msg['sensor_type']    # get the sensor type from the action
        action = msg['message']['action']    # get the action from the action
        # get the sensor id from the topic
        sensor_id = message.topic.split("/")[-1].split("_")[-1]    # get the sensor id from the topic
        if action == "increase":

            if sensor_type == "NPK":  # inject fertilizer
                nutrient = msg['message']['nutrient']
            
                if nutrient == "N":
                    sensorClasses[sensor_id].goalN = goal
                    sensorClasses[sensor_id].nitrogenIncrease = True
                    sensorClasses[sensor_id].nitrogenDecrease = False
                    write_log(f"Nitrogen increase action received")
            
                elif nutrient == "P":
                    sensorClasses[sensor_id].goalP = goal
                    sensorClasses[sensor_id].phosphorusIncrease = True
                    sensorClasses[sensor_id].phosphorusDecrease = False
                    write_log(f"Phosphorus increase action received")
            
                elif nutrient == "K":
                    sensorClasses[sensor_id].goalK = goal
                    sensorClasses[sensor_id].potassiumIncrease = True
                    sensorClasses[sensor_id].potassiumDecrease = False
                    write_log(f"Potassium increase action received")

            else:
                sensorClasses[sensor_id].goal = msg['message']['min_treshold']    # get the goal from the action
                sensorClasses[sensor_id].increase = True
                sensorClasses[sensor_id].decrease = False
            
        elif action == "decrease":
            goal = msg['message']['max_treshold']    # get the goal from the action

            if sensor_type == "NPK":  # soil dilution
                nutrient = msg['message']['nutrient']
        
                if nutrient == "N":
                    sensorClasses[sensor_id].goalN = goal
                    sensorClasses[sensor_id].nitrogenDecrease = True
                    sensorClasses[sensor_id].nitrogenIncrease = False
                    write_log(f"Nitrogen decrease action received")
        
                elif nutrient == "P":
                    sensorClasses[sensor_id].goalP = goal
                    sensorClasses[sensor_id].phosphorusDecrease = True
                    sensorClasses[sensor_id].phosphorusIncrease = False
                    write_log(f"Phosphorus decrease action received")
        
                elif nutrient == "K":
                    sensorClasses[sensor_id].goalK = goal
                    sensorClasses[sensor_id].potassiumDecrease = True
                    sensorClasses[sensor_id].potassiumIncrease = False
                    write_log(f"Potassium decrease action received")
            
            else:
                sensorClasses[sensor_id].goal = goal
                sensorClasses[sensor_id].decrease = True
                sensorClasses[sensor_id].increase = False
    
    except Exception as e:
        write_log(f"Error processing action: {e}")


os.makedirs("./logs", exist_ok=True)   # create the logs directory if it doesn't exist

# each time that the device starts, we clear the log file
with open("./logs/DeviceConnector.log", "w") as log_file:
    pass

sensorClasses = {}

try:
    # read the greenhouse_id and mqtt information of the broker from the json file
    with open("./DeviceConnector_config.json", "r") as config_fd:
        config = json.load(config_fd)   # read the configuration from the json file
        catalog_url = config["catalog_url"] # read the url of the Catalog
        greenhouse_id = config["greenhouse_id"] # read the greenhouse id where the device connector is connected
        mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # read the mqtt broker address
        mqtt_port = config["mqtt_connection"]["mqtt_port"]  # read the mqtt broker port
        keep_alive = config["mqtt_connection"]["keep_alive"]    # read the keep alive time of the mqtt connection

except FileNotFoundError:
    write_log("DeviceConnector_config.json file not found")
    exit(1)   # exit the program if the file is not found
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)

for _ in range(5):  # try 5 times to get the list of sensors connected to this device connector
    try:
        # get the list of sensors connected to this device connector from the Catalog
        response = requests.get(f'{catalog_url}/get_sensors', params={'greenhouse_id': greenhouse_id, 'device_name': 'DeviceConnector'})    # read the list of sensors from the Catalog
        if response.status_code == 200: # if the request is successful
            response = response.json()    # get the response in json format
            device_id = response["device_id"]    # get the device id from the response
            write_log(f"Received device id: {device_id}")    # write the device id in the log file
            sensors = response["sensors"]    # sensors is a dictionary of sensors connected to the device connector
            write_log(f"Received {len(sensors)} sensors: {sensors}")
            break   # exit the loop if the request is successful

        else:
            write_log(f"Failed to get sensors from the Catalog\nResponse: {response.json()["error"]}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
            if _ == 4:  # if this is the last attempt
                write_log("Failed to get sensors from the Catalog after 5 attempts")
                exit(1)   # exit the program if the request fails after 5 attempts
            
            time.sleep(60)   # wait for 60 seconds before trying again

    except Exception as e:
        write_log(f"Error getting sensors from the Catalog: {e}\nTrying again in 60 seconds...")
        if _ == 4:  # if this is the last attempt
            write_log("Failed to get sensors from the Catalog after 5 attempts")
            exit(1)   # exit the program if the request fails after 5 attempts

        time.sleep(60)   # wait for 60 seconds before trying again

for _ in range(5):  # try 5 times to get the location of the greenhouse
    try:
        # get the location of the greenhouse from the Catalog
        response = requests.get(f'{catalog_url}/get_greenhouse_location', params={'greenhouse_id': greenhouse_id})    # read the greenhouse location from the Catalog
        if response.status_code == 200: # if the request is successful
            greenhouse_location = response.json()["location"]    # get the location from the response
            write_log(f"Received greenhouse location: {greenhouse_location}")

            # create for each sensor its class object
            classSensor = Sensor.Sensor(location=greenhouse_location)    # create a sensor object with the location of the greenhouse
            for sensor in sensors:  # iterate over the list of sensors
                if sensor["type"] == "Temperature":  # if the sensor is a temperature sensor
                    sensorClasses[sensor["sensor_id"]] = Temperature.Temperature(classSensor)  # create a Temperature object with the sensor object 
                
                elif sensor["type"] == "Humidity":  # if the sensor is a humidity sensor
                    sensorClasses[sensor["sensor_id"]] = Humidity.Humidity(classSensor)  # create a Humidity object with the sensor object
                
                elif sensor["type"] == "LightIntensity":  # if the sensor is a light intensity sensor
                    sensorClasses[sensor["sensor_id"]] = Light.Light(classSensor)  # create a LightIntensity object with the sensor object
                
                elif sensor["type"] == "NPK":  # if the sensor is a NPK sensor
                    sensorClasses[sensor["sensor_id"]] = NPK.NPK(classSensor)  # create a NPK object with the sensor object
                
                elif sensor["type"] == "pH":  # if the sensor is a pH sensor
                    sensorClasses[sensor["sensor_id"]] = pH.pH(classSensor)  # create a pH object with the sensor object
                
                elif sensor["type"] == "SoilMoisture":  # if the sensor is a soil moisture sensor
                    sensorClasses[sensor["sensor_id"]] = SoilMoisture.SoilMoisture(classSensor)  # create a SoilMoisture object with the sensor object
                
                else:
                    write_log(f"Sensor not recognized: {sensor['name']}")
                    continue    # skip to the next iteration, so at the next sensor

            break   # exit the loop if the request is successful

        else:
            write_log(f"Failed to get greenhouse location from the Catalog\nResponse: {response.reason}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
            if _ == 4:  # if this is the last attempt
                write_log("Failed to get greenhouse location from the Catalog after 5 attempts")
                exit(1)

            time.sleep(60)   # wait for 60 seconds before trying again

    except Exception as e:
        write_log(f"Error getting greenhouse location from the Catalog: {e}\nTrying again in 60 seconds...")
        if _ == 4:  # if this is the last attempt
            write_log("Failed to get greenhouse location from the Catalog after 5 attempts")
            exit(1)
        
        time.sleep(60)

for _ in range(5):  # try 5 times to start the MQTT client
    try:
        # MQTT Client setup
        client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"DeviceConnector_{device_id}", ActionReceived, write_log)    # create a MQTT client object
        client.start()  # start the MQTT client
        break   # exit the loop if the client is started successfully

    except Exception as e:
        write_log(f"Error starting MQTT client: {e}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
        if _ == 4:  # if this is the last attempt
            write_log("Failed to start MQTT client after 5 attempts")
            exit(1)

        time.sleep(60)   # wait for 60 seconds before trying again

write_log("")

# connection to topics to receive needed action
for sensor in sensors:  # iterate over the list of sensors
    for _ in range(5):
        try:
            client.subscribe(f"greenhouse_{sensor['greenhouse_id']}/area_{sensor["area_id"]}/action/sensor_{sensor['sensor_id']}")    # subscribe to the topic to receive actions from the Catalog
            break

        except Exception as e:
            write_log(f"Error subscribing the client to the topic ({f"greenhouse_{sensor['greenhouse_id']}/action/sensor_{sensor['sensor_id']}"}): {e}\nTrying again in 60 seconds...")
            if _ == 4:  # if this is the last attempt
                write_log(f"Failed to subscribe the client to the topic ({f"greenhouse_{sensor['greenhouse_id']}/action/sensor_{sensor['sensor_id']}"}) after 5 attempts")
            else:
                time.sleep(60)  # wait for 60 seconds before trying again            

start_time = datetime.now() # get the current time
start_time = start_time.hour + start_time.minute / 60 + start_time.second / 3600  # convert the time to hours

while True:
    # cal set method to update the status on the Catalog

    timestamp = datetime.now()  # get the current time
    timestamp = timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600  # convert the time to hours
    timestamp -= start_time  # calculate the time elapsed since the start of the simulation

    write_log("")
    for sensor in sensors:  # iterate over the list of sensors
        try:
            val = sensorClasses[sensor["sensor_id"]].getValue(timestamp)

        except Exception as e:
            write_log(f"Error reading value from sensor {sensor['name']}: {e}")    # in case of error, write the reason of the error in the log file
            continue    # skip to the next iteration, so at the next sensor
            
        try:
            # we want to pusblish values with senML format, so we create a dictionary of the value read from the sensor
            senML = json.dumps({"bn": f"greenhouse_{sensor["greenhouse_id"]}/area_{sensor["area_id"]}/sensor_{sensor['sensor_id']}", "e": {"n": sensor["type"], "v": val, "u": sensor["unit"], "t": int(timestamp*3600)}})
            senML_dictionary = json.loads(senML)
            client.publish(senML_dictionary["bn"], senML)  # publish the value read from the sensor to the MQTT broker
            
        except Exception as e:
            write_log(f"Error publishing value from sensor {sensor['name']}: {e}")
            continue

    time.sleep(20)   # wait for 2 minutes before reading the sensors again

client.stop()   # stop the MQTT client