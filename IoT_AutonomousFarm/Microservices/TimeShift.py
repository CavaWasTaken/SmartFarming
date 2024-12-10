import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime, timedelta

# device connector is a MQTT publisher that reads data from the sensors connected to RaspberryPi and publishes it to the MQTT broker

# MQTT configuration
mqtt_broker = "mqtt.eclipseprojects.io" # broker address
mqtt_port = 1883    # broker port
mqtt_topic = "greenhouse_1/schedules"   # topic to publish scheduled events
keep_alive = 60

# MQTT Client setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, keep_alive)

start_time = int(time.time())
last_query = start_time
flag = 1

# we must think about different type of plants or we handle all the plants in the same way?

# our system is sensor-driven, so even if we have scheduled events, we must check the sensor values to decide if we need to perform the scheduled event or not
# this check must be done by the management component that handle the scheduled event

# we perform scheduled events by time
# the scheduled events are correlated to the actions that the system must perform, so we must define the actions that the system must perform, for example: irrigation, fertilization, lighting
schedule = [
    {"event": "irrigation", "start_date": "2024-12-10", "end_date": None, "start_time": "08:00:00", "end_time": "8:15:00", "recurrence": "daily"},
    {"event": "fertilization", "start_date": "2024-12-10", "end_date": None, "start_time": "10:00:00", "end_time": "10:15:00", "recurrence": "weekly:Mon,Wed,Fri"},
    {"event": "lighting", "start_date": "2024-12-10", "end_date": None, "start_time": "18:00:00", "end_time": "20:00:00", "recurrence": "daily"},
    {"event": "humidity", "start_date": "2024-12-10", "end_date": None, "start_time": "12:00:00", "end_time": "12:15:00", "recurrence": "weekly:Tue,Thu,Sat"},
]
# there could be events that are not scheduled as recurring events, so they are one-time events

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
            with open("../logs/TimeShift.log", "a") as f:
                f.write(f"Published: {result}\n")            
    time.sleep(5)   # check every 5 seconds