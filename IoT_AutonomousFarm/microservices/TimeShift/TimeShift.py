import time
import json
import requests
from datetime import datetime, timedelta
from MqttClient import MqttClient   # import the MqttClient class
import os

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/TimeShift.log", "a") as log_file:
        log_file.write(f"{message}\n")

def reconnectClient(client):
    while True:
        try:
            client.reconnect()
            write_log("MQTT client reconnected")

            # re-subscribe to all topics
            if sensors != []:
                for sensor in sensors:  # iterate over the list of sensors
                    topic = f"greenhouse_{sensor['greenhouse_id']}/area_{sensor['area_id']}/action/sensor_{sensor['sensor_id']}"  # create the topic to subscribe to
                    client.subscribe(topic)    # subscribe to the topic to receive actions from the Catalog

            break

        except Exception as e:
            write_log(f"Error reconnecting MQTT client: {e}")
            time.sleep(30)  # wait for 30 seconds before trying to reconnect

os.makedirs("./logs", exist_ok=True)   # create the logs directory if it doesn't exist

# each time that the device starts, we clear the log file
with open("./logs/TimeShift.log", "w") as log_file:
    pass

try:
    # read the device_id and mqtt information of the broker from the json file
    with open("./TimeShift_config.json", "r") as config_fd:
        config = json.load(config_fd)
        catalog_url = config["catalog_url"]
        dataAnalysis_url = config["dataAnalysis_url"]
        greenhouse_id = config["greenhouse_id"] # get the id of the greenhouse
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
            write_log(f"Failed to get sensors from the Catalog\t(Response: {response.json()['error']})\nTrying again in 30 seconds...")    # in case of error, write the reason of the error in the log file
            time.sleep(30)

    except Exception as e:
        write_log(f"Error getting sensors from the Catalog: {e}\nTrying again in 30 seconds...")
        time.sleep(30)   # wait for 30 seconds before trying again

while True:
    try:
        # MQTT Client setup
        client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"TimeShift_{device_id}", None, write_log)    # create a MQTT client object
        client.start()  # start the MQTT client
        break   # exit the loop if the client is started successfully

    except Exception as e:
        write_log(f"Error starting MQTT client: {e}\nTrying again in 30 seconds...")    # in case of error, write the reason of the error in the log file
        time.sleep(30)   # wait for 30 seconds before trying again

while True:
    current_time = datetime.now() + timedelta(hours=2)  # get the current time in UTC+2 (Italy time zone)
    write_log(f"\nCurrent time: {current_time}")
    try:
        response = requests.get(f'{catalog_url}/get_sensors', params={'greenhouse_id': greenhouse_id, 'device_name': 'TimeShift'})    # read the list of sensors from the Data Analysis service
        if response.status_code == 200: # if the request is successful
            new_sensors = response.json()["sensors"]  # new_sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
            if new_sensors != sensors:  # if the list of sensors has changed
                write_log("Sensors list updated")
                # find sensors to add and remove
                new_sensor_ids = {s["sensor_id"] for s in new_sensors}
                old_sensor_ids = {s["sensor_id"] for s in sensors}

                # remove topics for sensors that are no longer present
                for removed_id in old_sensor_ids - new_sensor_ids:
                    removed_sensor = next((s for s in sensors if s["sensor_id"] == removed_id), None)
                    client.unsubscribe(f"greenhouse_{removed_sensor['greenhouse_id']}/area_{removed_sensor['area_id']}/event/sensor_{removed_id}")  # unsubscribe from the event topic to stop receiving events for the removed sensor
                    client.unsubscribe(f"greenhouse_{removed_sensor['greenhouse_id']}/area_{removed_sensor['area_id']}/sensor_{removed_id}")  # unsubscribe from the topic to stop receiving actions for the removed sensor

                # add topics for new sensors
                for added_id in new_sensor_ids - old_sensor_ids:
                    added_sensor = next((s for s in new_sensors if s["sensor_id"] == added_id), None)
                    client.subscribe(f"greenhouse_{added_sensor['greenhouse_id']}/area_{added_sensor['area_id']}/event/sensor_{added_id}")  # subscribe to the event topic to receive events for the new sensor
                    client.subscribe(f"greenhouse_{added_sensor['greenhouse_id']}/area_{added_sensor['area_id']}/sensor_{added_id}")
 
                sensors = new_sensors  # update the list of sensors

    except Exception as e:
        write_log(f"Error checking for updates in the Catalog: {e}")
        # check if the client is still connected, otherwise try to reconnect
        if not client.is_connected():
            write_log("MQTT client disconnected, trying to reconnect...")
            reconnectClient(client)

    try:
        response = requests.get(f'{catalog_url}/get_scheduled_events', params={'device_id': device_id, 'device_name': 'TimeShift', 'greenhouse_id': greenhouse_id})    # read the list of sensors from the Catalog
        if response.status_code == 200:
            events = response.json()['events']   # events is a dictionary of scheduled events for this greenhouse
            write_log(f"Received {len(events)} events: {events}")

        else:
            write_log(f"Failed to get events from the Catalog\t(Response: {response.json()['error']})")    # in case of error, write the reason of the error in the log file
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
                # select the sensor given the event sensor_id
                sensor = next((s for s in sensors if s["sensor_id"] == event["sensor_id"]), None)
                senML = json.dumps({"bn": f"greenhouse_{greenhouse_id}/area_{sensor['area_id']}/event/sensor_{event['sensor_id']}", "e": event})   # create the senML message
                senML_dictionary = json.loads(senML)
                client.publish(senML_dictionary["bn"], senML)   # publish the senML message to the MQTT broker

            if event_time < current_time:
                # if the event time is in the past, we remove it from the list of events
                write_log(f"Event {event['event_id']} is in the past: {event_time}")
                response = requests.delete(f"{catalog_url}/delete_event", params={'device_id': device_id, 'event_id': event['event_id']})
                if response.status_code == 200:
                    write_log(f"Event {event['event_id']} deleted from the Catalog")
                
                else:
                    write_log(f"WARNING: Failed to delete the event {event['event_id']} from the Catalog\t(Response: {response.json()['error']})")
    
    except Exception as e:
        write_log(f"Error processing events: {e}")
        # check if the client is still connected, otherwise try to reconnect
        if not client.is_connected():
            write_log("MQTT client disconnected, trying to reconnect...")
            reconnectClient(client)

    time.sleep(60)   # repeat every 60 seconds