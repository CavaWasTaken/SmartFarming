import paho.mqtt.client as mqtt
import time
import json
import requests
from datetime import datetime, timedelta

# each time that the device starts, we clear the log file
with open("./logs/TimeShift.log", "w") as log_file:
    pass

# read the device_id and mqtt information of the broker from the json file
with open("./TimeShift_config.json", "r") as config_fd:
    config = json.load(config_fd)
    catalog_url = config["catalog_url"]
    dataAnalysis_url = config["dataAnalysis_url"]
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
    mqtt_port = config["mqtt_connection"]["mqtt_port"]
    keep_alive = config["mqtt_connection"]["keep_alive"]

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/TimeShift.log", "a") as log_file:
        log_file.write(f"{message}\n")

# MQTT Client setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, keep_alive)

start_time = int(time.time())
last_query = start_time
flag = 1

while True:
    current_time = int(time.time())
    if((current_time - last_query) >= 60 or (last_query == start_time and flag)):  # for simulation we simulate of appling the query every minute or at the start of the program
        if flag:
            flag = 0   # to avoid querying the database multiple times at the start of the program
        last_query = current_time
        
        # Query: get all events. Only events active in the current date are selected
        response = requests.get(f'{catalog_url}/get_all_scheduled_events')
        if response.status_code == 200:
            schedule = response.json() # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
            write_log(f"Received {len(schedule)} schedule: {schedule}")
        else:
            write_log(f"Failed to get events from the Catalog\t(Response: {response.reason})")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops
        print(schedule)
        for event in schedule:
            # Don't send any event that is "In action" or "Compleated", to avoid duplication or useless messages
            if (event["status"] == "Pending"):
                topic = f"greenhouse_{event["greenhouse_id"]}"+"/"+event["event_type"]
                # result in senml format
                result = json.dumps({"bn": topic, "e": [{"n": "frequency", "u": "text", "v": event["frequency"]}]})
                client.publish(topic, result)
                with open("./logs/TimeShift.log", "a") as f:
                    f.write(f"Published: {result}\n")            
    time.sleep(5)   # check every 5 seconds