from datetime import datetime
import time
import json
import requests

from sensors import DTH22, Light, NPK, pH, SoilMoisture, Sensor # import the classes of the sensors
from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/DeviceConnector.log", "a") as log_file:
        log_file.write(f"{message}\n")

# function for the device connector to receive the needed action and perform it
def ActionReceived(client, userdata, message):
    write_log(f"Received action: {message.payload.decode()}")    # write in the log file the action received

# each time that the device starts, we clear the log file
with open("./logs/DeviceConnector.log", "w") as log_file:
    pass

try:
    # read the device_id and mqtt information of the broker from the json file
    with open("./DeviceConnector_config.json", "r") as config_fd:
        config = json.load(config_fd)   # read the configuration from the json file
        catalog_url = config["catalog_url"] # read the url of the Catalog
        device_id = config["device_id"] # read the device_id of the device connector
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
        response = requests.get(f'{catalog_url}/get_sensors', params={'device_id': device_id, 'device_name': 'DeviceConnector'})    # read the list of sensors from the Catalog
        if response.status_code == 200: # if the request is successful
            sensors = response.json()["sensors"]    # sensors is a dictionary of sensors connected to the device connector
            write_log(f"Received {len(sensors)} sensors: {sensors}")
            break   # exit the loop if the request is successful

        else:
            write_log(f"Failed to get sensors from the Catalog\nResponse: {response.json()["error"]}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
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
        response = requests.get(f'{catalog_url}/get_greenhouse_location', params={'greenhouse_id': sensors[0]["greenhouse_id"]})    # read the greenhouse location from the Catalog
        if response.status_code == 200: # if the request is successful
            greenhouse_location = response.json()["location"]    # get the location from the response
            write_log(f"Received greenhouse location: {greenhouse_location}")
            classSensor = Sensor.Sensor(location=greenhouse_location)    # create a sensor object with the location of the greenhouse
            classDTH22 = DTH22.DTH22(classSensor)    # create a DTH22 object with the sensor object
            classLight = Light.Light(classSensor)  # create a LightIntensity object with the sensor object
            classNPK = NPK.NPK(classSensor)  # create a NPK object with the sensor object
            classpH = pH.pH(classSensor)    # create a pH object with the sensor object
            classSoilMoisture = SoilMoisture.SoilMoisture(classSensor)  # create a SoilMoisture object with the sensor object
            break   # exit the loop if the request is successful

        else:
            write_log(f"Failed to get greenhouse location from the Catalog\nResponse: {response.reason}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
            if _ == 4:  # if this is the last attempt
                write_log("Failed to get greenhouse location from the Catalog after 5 attempts")
                exit(1)

            time.sleep(60)   # wait for 60 seconds before trying again

    except Exception as e:
        write_log(f"Error getting greenhouse location from the Catalog: {e}\nTrying again in 60 seconds...")
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
            client.subscribe(f"greenhouse_{sensor['greenhouse_id']}/sensor_{sensor['sensor_id']}/action")    # subscribe to the topic to receive actions from the Catalog
            break

        except Exception as e:
            write_log(f"Error subscribing the client to the topic ({f"greenhouse_{sensor['greenhouse_id']}/sensor_{sensor['sensor_id']}/action"}): {e}\nTrying again in 60 seconds...")
            if _ == 4:  # if this is the last attempt
                write_log(f"Failed to subscribe the client to the topic ({f"greenhouse_{sensor['greenhouse_id']}/sensor_{sensor['sensor_id']}/action"}) after 5 attempts")
            else:
                time.sleep(60)  # wait for 60 seconds before trying again            

start_time = datetime.now() # get the current time
start_time = start_time.hour + start_time.minute / 60 + start_time.second / 3600  # convert the time to hours

while True:
    timestamp = datetime.now()  # get the current time
    timestamp = timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600  # convert the time to hours
    timestamp -= start_time  # calculate the time elapsed since the start of the simulation

    write_log("")
    for sensor in sensors:  # iterate over the list of sensors
        try:
            val = None   # default value read from the sensor
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
                write_log(f"Sensor not recognized: {sensor['name']}")
                continue    # skip to the next iteration, so at the next sensor

            if val is None:
                # if the value is None, write the error in the log file
                write_log(f"Error reading value from sensor {sensor['name']}")
                continue

        except Exception as e:
            write_log(f"Error reading value from sensor {sensor['name']}: {e}")    # in case of error, write the reason of the error in the log file
            continue    # skip to the next iteration, so at the next sensor
            
        try:
            # we want to pusblish values with senML format, so we create a dictionary of the value read from the sensor
            senML = json.dumps({"bn": f"greenhouse_{sensor["greenhouse_id"]}/sensor_{sensor['sensor_id']}", "e": {"n": sensor["type"], "v": val, "u": sensor["unit"], "t": int(timestamp*3600)}})
            senML_dictionary = json.loads(senML)
            client.publish(senML_dictionary["bn"], senML)  # publish the value read from the sensor to the MQTT broker
            
        except Exception as e:
            write_log(f"Error publishing value from sensor {sensor['name']}: {e}")
            continue

    time.sleep(10)   # wait for 2 minutes before reading the sensors again

client.stop()   # stop the MQTT client