import paho.mqtt.client as mqtt
import time
import json
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
        
        # Query: select * from schedules where start_date <= current_date and (end_date >= current_date or end_date is NULL) and start_time >= current_time and recurrence like 'daily' or recurrence like 'weekly:%current_day%' order by start_time
        
        for event in schedule:
            topic = mqtt_topic+"/"+event["event"]
            # result in senml format
            result = json.dumps({"bn": topic, "e": [{"n": "start_date", "u": "date", "v": event["start_date"]}, {"n": "end_date", "u": "date", "v": event["end_date"]}, {"n": "start_time", "u": "time", "v": event["start_time"]}, {"n": "end_time", "u": "time", "v": event["end_time"]}, {"n": "recurrence", "u": "text", "v": event["recurrence"]}]})
            client.publish(topic, result)
            with open("./logs/TimeShift.log", "a") as f:
                f.write(f"Published: {result}\n")            
    time.sleep(5)   # check every 5 seconds