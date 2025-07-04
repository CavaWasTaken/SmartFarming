import json
import requests
import cherrypy
import time
import os

from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
        log_file.write(f"{message}\n")

os.makedirs("./logs", exist_ok=True)   # create the logs directory if it doesn't exist

# each time that the device starts, we clear the log file
with open("./logs/ThingSpeakAdaptor.log", "w") as log_file:
    pass

try:
    # read the info from the json file
    with open("./ThingSpeakAdaptor_config.json", "r") as config_fd:
        config = json.load(config_fd)   # load the configuration from the file as a dictionary
        catalog_url = config["catalog_url"] # get the url of the catalog
        greenhouse_id = config["greenhouse_id"] # get the id of the greenhouse
        mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # mqtt broker
        mqtt_port = config["mqtt_connection"]["mqtt_port"]  # mqtt port
        keep_alive = config["mqtt_connection"]["keep_alive"]    # keep alive time
        write_url = config["write_url"] # url to write data to the ThingSpeak channel
        read_url = config["read_url"]   # url to read data from the ThingSpeak channel

except FileNotFoundError:
    write_log("ThingSpeakAdaptor_config.json file not found")
    exit(1)
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)

thingSpeak_config = {}  # dictionary containing the configuration of the ThingSpeak channel

fields = {}
field_map = {}  # (parameter, area_id) -> field number mapping

def checkSensors():
    # check for updates in the list of sensors in the Catalog
    try:
        response = requests.get(f'{catalog_url}/get_sensors', params={'greenhouse_id': greenhouse_id, 'device_name': 'ThingSpeakAdaptor'})  # read the list of sensors from the Catalog
        if response.status_code == 200:
            new_sensors = response.json()["sensors"]
            global sensors
            if new_sensors != sensors:  # if the list of sensors has changed
                write_log("Sensors list updated")
                # find sensors to add and remove
                new_sensor_ids = {s["sensor_id"] for s in new_sensors}
                old_sensor_ids = {s["sensor_id"] for s in sensors}

                # remove topics for sensors that are no longer present
                for removed_id in old_sensor_ids - new_sensor_ids:
                    removed_sensor = next((s for s in sensors if s["sensor_id"] == removed_id), None)
                    client.unsubscribe(f"greenhouse_{removed_sensor['greenhouse_id']}/area_{removed_sensor['area_id']}/sensor_{removed_id}")  # unsubscribe from the topic to stop receiving actions for the removed sensor

                # add topics for new sensors
                for added_id in new_sensor_ids - old_sensor_ids:
                    added_sensor = next((s for s in new_sensors if s["sensor_id"] == added_id), None)
                    client.subscribe(f"greenhouse_{added_sensor['greenhouse_id']}/area_{added_sensor['area_id']}/sensor_{added_id}")

                sensors = new_sensors  # update the list of sensors
        
        else:
            write_log(f"Failed to get sensors from the Catalog\t(Response: {response.json()['error']})")

        response = requests.get(f"{catalog_url}/get_greenhouse_info", params={'greenhouse_id': greenhouse_id, 'device_id': device_id})    # get the greenhouse information from the catalog
        if response.status_code == 200:
            greenhouse_info = response.json()    # greenhouse_info is a dictionary with the information of the greenhouse
            write_log(f"Received greenhouse information: {greenhouse_info}")
            global thingSpeak_config
            thingSpeak_config = greenhouse_info["thingSpeak_config"]
        
        else:
            write_log(f"Failed to get greenhouse information from the Catalog\nResponse: {response.reason}")

    except Exception as e:
        write_log(f"Error checking for updates in the Catalog: {e}")

def handle_message(timestamp, area_id, sensor_type, val):
    global fields, field_map
    if timestamp not in fields.keys():
        fields[timestamp] = {}

    if sensor_type == "NPK":
        if "Nitrogen" not in fields[timestamp].keys():
            fields[timestamp]["Nitrogen"] = {}
        if "Phosphorus" not in fields[timestamp].keys():
            fields[timestamp]["Phosphorus"] = {}
        if "Potassium" not in fields[timestamp].keys():
            fields[timestamp]["Potassium"] = {}
    else:
        if sensor_type not in fields[timestamp].keys():
            fields[timestamp][sensor_type] = {}

    if sensor_type == "NPK":
        fields[timestamp]["Nitrogen"][area_id] = val["N"]
        fields[timestamp]["Phosphorus"][area_id] = val["P"]
        fields[timestamp]["Potassium"][area_id] = val["K"]
    else:
        fields[timestamp][sensor_type][area_id] = val

    # if at the given timestamp there there is at least one field missing, return
    for sensor in sensors:
        if sensor["type"] == "NPK":
            if (
                "Nitrogen" not in fields[timestamp].keys() or
                "Phosphorus" not in fields[timestamp].keys() or
                "Potassium" not in fields[timestamp].keys()
            ):
                return
            
            elif (sensor["area_id"] not in fields[timestamp]["Nitrogen"].keys() or
                  sensor["area_id"] not in fields[timestamp]["Phosphorus"].keys() or
                  sensor["area_id"] not in fields[timestamp]["Potassium"].keys()):
                return
            
        elif (sensor["type"] not in fields[timestamp].keys() or
              sensor["area_id"] not in fields[timestamp][sensor["type"]].keys()):
            return
        
    # if at the given timestamp tall the fields are filled, send the data to ThingSpeak
    payload = {"write_key": thingSpeak_config["write_key"]}
    payload.update({
        f"{type}": json.dumps(fields[timestamp][type])
        for i, type in enumerate(fields[timestamp].keys())
    })

    response = requests.post(write_url, data=payload)
    if response.status_code == 200:
        write_log(f"Successfully updated ThingSpeak channel {thingSpeak_config['channel_id']} with payload: {payload}")
    else:
        write_log(f"Failed to update ThingSpeak. Response: {response.reason}")

    write_log("")

    fields[timestamp] = {}  # clear the fields for the next timestamp

def on_message(client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
    try:
        message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
        write_log(f"Received: {message}")
        for topic in mqtt_topics:
            if message["bn"] == topic:
                try:
                    message = message["e"]
                    sensor_type = message["n"]
                    val = message["v"]
                    timestamp = message["t"] 

                    area_id = int(topic.split("/")[1].split("_")[1])  # extract the area id from the topic

                    checkSensors()  # check for updates in the list of sensors

                    if thingSpeak_config.get("write_key") == "" or thingSpeak_config.get("channel_id") == "":
                        write_log("ThingSpeak configuration is missing. Please check the configuration file.")
                        return
                    
                    handle_message(timestamp, area_id, sensor_type, val)

                except KeyError as e:
                    write_log(f"Missing key in the message: {e}")
                except Exception as e:
                    write_log(f"Error processing the message: {e}")
                finally:
                    break  # if the message is processed, exit the loop

    except json.JSONDecodeError:
        write_log("Error decoding the MQTT message payload")
    except Exception as e:
        write_log(f"Unexpected error in on_message: {e}")

if __name__ == "__main__":

    while True:   # try to get the device information from the Catalog for 5 times
        try: 
            # get the list of sensors connected to this device connector from the Catalog
            response = requests.get(f'{catalog_url}/get_sensors', params={'greenhouse_id': greenhouse_id, 'device_name': 'TimeShift'})    # read the list of sensors from the Catalog
            if response.status_code == 200: # if the request is successful
                response = response.json()  # convert the response to a dictionary
                device_id = response["device_id"]    # get the device id from the response
                write_log(f"Device id: {device_id}")
                sensors = response["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
                write_log(f"Received {len(sensors)} sensors: {sensors}")
                break

            else:
                write_log(f"Failed to get sensors from the Catalog\t(Response: {response.json()['error']})\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
                time.sleep(60)

        except Exception as e:
            write_log(f"Error getting sensors from the Catalog: {e}\nTrying again in 60 seconds...")
            time.sleep(60)   # wait for 60 seconds before trying again

    for _ in range(5):
        try:
            response = requests.get(f"{catalog_url}/get_greenhouse_info", params={'greenhouse_id': greenhouse_id, 'device_id': device_id})    # get the greenhouse information from the catalog
            if response.status_code == 200:
                greenhouse_info = response.json()    # greenhouse_info is a dictionary with the information of the greenhouse
                write_log(f"Received greenhouse information: {greenhouse_info}")
                thingSpeak_config = greenhouse_info["thingSpeak_config"]
                break

            else:
                write_log(f"Failed to get greenhouse information from the Catalog\nResponse: {response.reason}")
                if _ == 4:
                    write_log("Failed to get greenhouse information from the Catalog after 5 attempts")
                    exit(1)
                
                time.sleep(60)  # wait 60 seconds before retrying

        except Exception as e:
            write_log(f"Error getting greenhouse information from the Catalog: {e}")
            if _ == 4:
                write_log("Failed to get greenhouse information from the Catalog after 5 attempts")
                exit(1)
            
            time.sleep(60)

    mqtt_topics = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topics.append(f"greenhouse_{greenhouse_id}/area_{sensor['area_id']}/sensor_{sensor['sensor_id']}")

    write_log("")

    for _ in range(5):
        try:
            # create the mqtt client
            client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"ThingSpeakAdaptor_{device_id}", on_message, write_log)
            client.start()
            break

        except Exception as e:
            write_log(f"Error starting MQTT client: {e}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
            if _ == 4:  # if it is the last attempt
                write_log("Failed to start MQTT client after 5 attempts")
                exit(1)  # exit the program if the device information is not found
            
            time.sleep(60)   # wait for 60 seconds before trying again

    for topic in mqtt_topics:
        for _ in range(5):
            try:
                client.subscribe(topic)
                break

            except Exception as e:
                write_log(f"Error subscribing the client to the topic ({topic}): {e}\nTrying again in 60 seconds...")
                if _ == 4:  # if it is the last attempt
                    write_log(f"Failed to subscribe the client to the topic ({topic}) after 5 attempts")
                else:
                    time.sleep(60)  # wait for 60 seconds before trying again

    while True:
        time.sleep(1)
    client.stop()