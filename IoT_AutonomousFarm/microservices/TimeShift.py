import time
import json
import requests
from datetime import datetime, timedelta
from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/TimeShift.log", "a") as log_file:
        log_file.write(f"{message}\n")

# each time that the device starts, we clear the log file
with open("./logs/TimeShift.log", "w") as log_file:
    pass

try:
    # read the device_id and mqtt information of the broker from the json file
    with open("./TimeShift_config.json", "r") as config_fd:
        config = json.load(config_fd)
        catalog_url = config["catalog_url"]
        dataAnalysis_url = config["dataAnalysis_url"]
        device_id = config["device_id"]
        mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
        mqtt_port = config["mqtt_connection"]["mqtt_port"]
        keep_alive = config["mqtt_connection"]["keep_alive"]

except FileNotFoundError:
    write_log("TimeShift_config.json file not found")
    exit(1)   # exit the program if the file is not found
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)

for _ in range(5):  # try 5 times to start the MQTT client
    try:
        # MQTT Client setup
        client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"TimeShift_{device_id}", None, write_log)    # create a MQTT client object
        client.start()  # start the MQTT client
        break   # exit the loop if the client is started successfully

    except Exception as e:
        write_log(f"Error starting MQTT client: {e}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
        if _ == 4:  # if this is the last attempt
            write_log("Failed to start MQTT client after 5 attempts")
            exit(1)

        time.sleep(60)   # wait for 60 seconds before trying again

for _ in range(5):  # try 5 times to get the list of sensors connected to this device connector
    try:
        # get the list of sensors connected to this device connector from the Catalog
        response = requests.get(f'{catalog_url}/get_sensors', params={'device_id': device_id, 'device_name': 'TimeShift'})    # read the list of sensors from the Catalog
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

while True:
    current_time = datetime.now()   # get the current time
    try:
        greenhouse_id = sensors[0]['greenhouse_id']   # get the greenhouse id from the first sensor
        response = requests.get(f'{catalog_url}/get_scheduled_events', params={'device_id': device_id, 'device_name': 'TimeShift', 'greenhouse_id': greenhouse_id})    # read the list of sensors from the Catalog
        if response.status_code == 200:
            events = response.json()['events']   # events is a dictionary of scheduled events for this greenhouse
            write_log(f"Received {len(events)} events: {events}")

        else:
            write_log(f"Failed to get events from the Catalog\t(Response: {response.json()["error"]})")    # in case of error, write the reason of the error in the log file
            time.sleep(60)   # repeat every 60 seconds
            continue   # if the request fails, we continue to the next iteration of the loop

    except Exception as e:
        write_log(f"Error getting events from the Catalog: {e}")
        time.sleep(60)   # repeat every 60 seconds
        continue

    if events == []:
        write_log(f"No events scheduled for the greenhouse {greenhouse_id}")
        time.sleep(60)   # repeat every 60 secondsù 
        continue

    try:
        # check which events are scheduled for the current time
        for event in events:

            event_time = datetime.strptime(event['execution_time'], '%Y-%m-%d %H:%M:%S')   # convert the event time to a datetime object  
            # extract the events that are scheduled for the current time and the next minute
            if current_time <= event_time <= current_time + timedelta(minutes=1):
                write_log(f"Event {event['event_id']} scheduled for the current time: {event_time}")
                senML = json.dumps({"bn": f"greenhouse_{greenhouse_id}/event/sensor_{event['sensor_id']}", "e": event})   # create the senML message
                senML_dictionary = json.loads(senML)
                client.publish(senML_dictionary["bn"], senML)   # publish the senML message to the MQTT broker

            if event_time < current_time:
                # if the event time is in the past, we remove it from the list of events
                write_log(f"Event {event['event_id']} is in the past: {event_time}")
                response = requests.delete(f"{catalog_url}/delete_event", params={'device_id': device_id, 'event_id': event['event_id']})
                if response.status_code == 200:
                    write_log(f"Event {event['event_id']} deleted from the Catalog")
                
                else:
                    write_log(f"WARNING: Failed to delete the event {event['event_id']} from the Catalog\t(Response: {response.json()["error"]})")
    
    except Exception as e:
        write_log(f"Error processing events: {e}")
        
    time.sleep(60)   # repeat every 60 seconds