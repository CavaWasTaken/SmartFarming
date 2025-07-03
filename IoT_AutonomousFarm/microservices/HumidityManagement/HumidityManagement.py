import json
import requests
import threading
from functools import partial
import time
import Management
from datetime import datetime, timedelta
import os

from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/HumidityManagement.log", "a") as log_file:
        log_file.write(f"{message}\n")

os.makedirs("./logs", exist_ok=True)  # create the logs directory if it doesn't exist

# each time that the device starts, we clear the log file
with open("./logs/HumidityManagement.log", "w") as log_file:
    pass

try:
    # read the info from the json file
    with open("./HumidityManagement_config.json", "r") as config_fd:
        config = json.load(config_fd)   # load the configuration from the file as a dictionary
        catalog_url = config["catalog_url"] # get the url of the catalog
        dataAnalysis_url = config["dataAnalysis_url"]   # get the url of the data analysis
        greenhouse_id = config["greenhouse_id"] # get the id of the device
        mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # mqtt broker
        mqtt_port = config["mqtt_connection"]["mqtt_port"]  # mqtt port
        keep_alive = config["mqtt_connection"]["keep_alive"]    # keep alive time
        telegram_token = config["telegram_token"]  # telegram token for the bot

except FileNotFoundError:
    write_log("HumidityManagement_config.json file not found")
    exit(1)   # exit the program if the file is not found
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)

def checkSensors():
    # check for updates in the list of sensors in the Catalog
    try:
        response = requests.get(f'{catalog_url}/get_sensors', params={'greenhouse_id': greenhouse_id, 'device_name': 'HumidityManagement'})  # read the list of sensors from the Catalog
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
                    client.unsubscribe(f"greenhouse_{removed_sensor['greenhouse_id']}/area_{removed_sensor['area_id']}/event/sensor_{removed_id}")  # unsubscribe from the event topic to stop receiving events for the removed sensor
                    client.unsubscribe(f"greenhouse_{removed_sensor['greenhouse_id']}/area_{removed_sensor['area_id']}/sensor_{removed_id}")  # unsubscribe from the topic to stop receiving actions for the removed sensor

                # add topics for new sensors
                for added_id in new_sensor_ids - old_sensor_ids:
                    added_sensor = next((s for s in new_sensors if s["sensor_id"] == added_id), None)
                    client.subscribe(f"greenhouse_{added_sensor['greenhouse_id']}/area_{added_sensor['area_id']}/event/sensor_{added_id}")  # subscribe to the event topic to receive events for the new sensor
                    client.subscribe(f"greenhouse_{added_sensor['greenhouse_id']}/area_{added_sensor['area_id']}/sensor_{added_id}")
                    tresholds[added_sensor['sensor_id']] = added_sensor['threshold']    # associate the threshold to the sensor id into the dictionary
                    domains[added_sensor['sensor_id']] = added_sensor['domain']    # associate the domain to the sensor id into the dictionary  
                    expected_value[added_sensor['sensor_id']] = None
                    timers[added_sensor['sensor_id']] = None
 
                sensors = new_sensors  # update the list of sensors

    except Exception as e:
        write_log(f"Error checking for updates in the Catalog: {e}")

expected_value = {} # dictionary to save the next expected value for each sensor
timers = {} # dictionary to save the timer (interval of time for waiting the next value of that sensor) for each sensor
tresholds = {}  # dictionary to save the treshold interval for each sensor
domains = {}    # dictionary  to save the domain of the values collectable by each sensor

liveValue = {}  # dictionary to save the last value received for each sensor

def sendTelegramMessage(msg):
    # get greenhouse information by passing the greenhouse_id and device_id
    try:
        response = requests.get(f"{catalog_url}/get_greenhouse_info", params={'greenhouse_id': greenhouse_id, 'device_id': device_id})
        if response.status_code == 200:
            greenhouse_info = response.json()
            greenhouse_name = greenhouse_info["name"]
        else:
            write_log(f"Failed to get greenhouse info from the Catalog\t(Response: {response.json()['error']})")
            return
    except Exception as e:
        write_log(f"Error getting greenhouse info from the Catalog: {e}")
        return

    msg = f"{greenhouse_name}:\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n" + msg
    # get the telegram user ID from the catalog
    try:
        response = requests.get(f"{catalog_url}/get_telegram_chat_id", params={'greenhouse_id': greenhouse_id})
        if response.status_code == 200:
            telegram_chat_id = response.json()["telegram_chat_id"]  # get the telegram user ID from the response
            if not telegram_chat_id:
                write_log("No Telegram user found for this greenhouse")
                return
            
        else:
            write_log(f"Failed to get Telegram user from the Catalog\t(Response: {response.json()['error']})")
            return
        
    except Exception as e:
        write_log(f"Error getting Telegram user from the Catalog: {e}")
        return
    
    # send to telegram bot the user ID
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": msg
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.ok:
            write_log(f"Telegram message sent successfully to user {telegram_chat_id}")
        else:
            write_log(f"Failed to send Telegram message: {response.text}")

    except Exception as e:
        write_log(f"Failed to send Telegram message: {e}")

# function that handles the received message from the broker
def handle_message(sensor_type, val, unit, timestamp, area_id, sensor_id):
    # function that sends an alert to the user when the expected value doesn't arrive (timer expiration)
    def TimerExpiration(sensor_id, expected_timestamp):
        write_log(f"WARNING: Was expecting a value of {sensor_type} from sensor_{sensor_id} at time {expected_timestamp}, but it didn't arrive")   # ALERT TO BE SENT TO THE UI
        sendTelegramMessage(
            f"⚠️ *Sensor Data Missing!*\n\n"
            f"*Sensor Type:* {sensor_type}\n"
            f"*Sensor ID:* {sensor_id}\n"
            f"*Expected Time:* {expected_timestamp}\n\n"
            "No data was received from this sensor as expected. Please check the device or connection."
        )
        
    def sendAction(msg):
        msg = json.dumps({"message": msg, "sensor_type": sensor_type, "timestamp": timestamp})
        client.publish(f"greenhouse_{greenhouse_id}/area_{area_id}/action/sensor_{sensor_id}", msg)
        
    treshold = tresholds[sensor_id]    # get the treshold for the sensor
    min_treshold = treshold["min"]
    max_treshold = treshold["max"]

    liveValue[sensor_id] = val  # save the last value received for the sensor

    # get from the DataAnalysis the next expected timestamp
    response = requests.get(f"{dataAnalysis_url}/get_next_timestamp", params={'sensor_id': sensor_id, 'sensor_type': sensor_type, 'timestamp': timestamp})
    if response.status_code == 200:
        next_timestamp = response.json()["next_timestamp"]
        if next_timestamp is not None:
            # evaluate the datetime of when the next value is expected to arrive
            write_log(f"The next value of {sensor_type} (sensor_{sensor_id}) is expected to be received at: {next_timestamp}")
        else:   # if the response is None, we consider the prediction lost
            write_log(f"WARNING: Failed to get when the next value of {sensor_type} (sensor_{sensor_id}) is expected to arrive")
            next_timestamp = None

    else:
        write_log(f"WARNING: A problem with DataAnalysis component occured while getting when the next value of {sensor_type} (sensor_{sensor_id}) is expected to arrive\t(Response: {response.json()['error']})")
        next_timestamp = None
    
    if next_timestamp is not None:  # when the data analysis make prediction with just 1 value, it can't predict the next value so it is None
        if timers[sensor_id] is not None:  # if there is a timer running, stop it
            timers[sensor_id].cancel()

        # create a new timer that will wait for the next message. I add 5 seconds to permit a delay in the message arrival
        timers[sensor_id] = threading.Timer(next_timestamp + 5 - timestamp, partial(TimerExpiration, sensor_id, next_timestamp)) # timer that will wait the next timestamp
        timers[sensor_id].start()   # start the timer

    Management.checkValue(dataAnalysis_url, sensor_id, sensor_type, val, unit, timestamp, min_treshold, max_treshold, expected_value, domains, write_log, sendTelegramMessage, sendAction)

def handle_event(event_id, greenhouse_id, sensor_id, parameter, frequency, desired_value, execution_time, area_id):
    def SendAction(msg, sensor_type):
        msg = json.dumps({"message": msg, "sensor_type": sensor_type, "timestamp": execution_time})
        client.publish(f"greenhouse_{greenhouse_id}/area_{area_id}/action/sensor_{sensor_id}", msg)

    # check if the action needed to reach the desired value is to increase or decrease the value
    if desired_value < liveValue[sensor_id]:
        SendAction({
            "action": "decrease",
            "val": liveValue[sensor_id],
            "max_treshold": desired_value,
        }, parameter)

    elif desired_value > liveValue[sensor_id]:
        SendAction({
            "action": "increase",
            "val": liveValue[sensor_id],
            "min_treshold": desired_value,
        }, parameter)

    else:
        write_log(f"WARNING: The desired value of {parameter} is equal to the current value. No action needed.")

    # depending on the frequency, we can schedule the next event
    # first we always delete the event from the catalog
    response = requests.delete(f"{catalog_url}/delete_event", json={'device_id': device_id, 'event_id': event_id})
    if response.status_code == 200:
        write_log(f"Event {event_id} deleted from the Catalog")
    
    else:
        write_log(f"WARNING: Failed to delete the event {event_id} from the Catalog\t(Response: {response.json()['error']})")
    
    if frequency == "Daily":
    
        # schedule the next event for the next day
        response = requests.post(f"{catalog_url}/schedule_event", json={
            "device_id": device_id,
            "greenhouse_id": greenhouse_id,
            "sensor_id": sensor_id,
            "parameter": parameter,
            "frequency": frequency,
            "desired_value": desired_value,
            "execution_time": (datetime.strptime(execution_time, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        })
        if response.status_code == 200:
            write_log(f"Event {sensor_id} scheduled for the next day")
        
        else:
            write_log(f"WARNING: Failed to schedule the event {sensor_id} for the next day\t(Response: {response.json()['error']})")
    
    elif frequency == "Weekly":
        
        # schedule the next event for the next week
        response = requests.post(f"{catalog_url}/schedule_event", json={
            "device_id": device_id,
            "greenhouse_id": greenhouse_id,
            "sensor_id": sensor_id,
            "parameter": parameter,
            "frequency": frequency,
            "desired_value": desired_value,
            "execution_time": (datetime.strptime(execution_time, "%Y-%m-%d %H:%M:%S") + timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M:%S")
        })
        if response.status_code == 200:
            write_log(f"Event {sensor_id} scheduled for the next week")
        
        else:
            write_log(f"WARNING: Failed to schedule the event {sensor_id} for the next week\t(Response: {response.json()['error']})")
    
    elif frequency == "Monthly":
    
        # schedule the next event for the next month
        response = requests.post(f"{catalog_url}/schedule_event", json={
            "device_id": device_id,
            "greenhouse_id": greenhouse_id,
            "sensor_id": sensor_id,
            "parameter": parameter,
            "frequency": frequency,
            "desired_value": desired_value,
            "execution_time": (datetime.strptime(execution_time, "%Y-%m-%d %H:%M:%S") + timedelta(weeks=4)).strftime("%Y-%m-%d %H:%M:%S")
        })
        if response.status_code == 200:
            write_log(f"Event {sensor_id} scheduled for the next month")
        
        else:
            write_log(f"WARNING: Failed to schedule the event {sensor_id} for the next month\t(Response: {response.json()['error']})")
    
    elif frequency != "Once":
        write_log(f"WARNING: Frequency {frequency} not supported. Event not scheduled.")
        return

def on_message(client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
    try:
        message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
        write_log(f"\nReceived: {message}")
        for topic in mqtt_topics:
            if message["bn"] == topic:
                try:
                    if "event" in topic:    # if the message is referred to a scheduled event
                        event = message["e"]
                        event_id = event["event_id"]
                        greenhouse_id = event["greenhouse_id"]
                        sensor_id = event["sensor_id"]
                        parameter = event["parameter"]
                        frequency = event["frequency"]
                        desired_value = event["value"]
                        execution_time = event["execution_time"]

                        area_id = int(topic.split("/")[1].split("_")[1])  # extract from the topic the area_id

                        checkSensors()  # check if the sensors list has been updated

                        handle_event(event_id, greenhouse_id, sensor_id, parameter, frequency, desired_value, execution_time, area_id)

                    else:
                        message = message["e"]
                        sensor_type = message["n"]
                        val = message["v"]
                        unit = message["u"]
                        timestamp = message["t"]

                        # extract from the topic the area_id and the sensor_id
                        area_id = int(topic.split("/")[1].split("_")[1])
                        sensor_id = int(topic.split("/")[2].split("_")[1])

                        handle_message(sensor_type, val, unit, timestamp, area_id, sensor_id)

                except KeyError as e:
                    write_log(f"Missing key in the message: {e}")
                except Exception as e:
                    write_log(f"Error processing the message: {e}")
                finally:
                    break  # if the message is processed, exit the loop
                    
    except json.JSONDecodeError:
        write_log("Error decoding the MQTT message payload")
    except Exception as e:
        write_log(f"Unexpected error on handling the message: {e}")

if __name__ == "__main__":
    # try to get the sensors from the catalog for 5 times
    for _ in range(5):
        try:
            response = requests.get(f"{catalog_url}/get_sensors", params={'greenhouse_id': greenhouse_id, 'device_name': 'HumidityManagement'})    # get the device information from the catalog
            if response.status_code == 200:
                response = response.json()  # convert the response to a dictionary
                device_id = response["device_id"]    # get the device id from the response
                write_log(f"Device id: {device_id}")
                sensors = response["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
                write_log(f"Received {len(sensors)} sensors: {sensors}")
                break

            else:
                write_log(f"Failed to get sensors from the Catalog\t(Response: {response.json()['error']})\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
                if _ == 4:  # if it is the last attempt
                    write_log("Failed to get sensors from the Catalog after 5 attempts")
                    exit(1)  # exit the program if the device information is not found
                
                time.sleep(60)

        except Exception as e:
            write_log(f"Error getting sensors from the Catalog: {e}\nTrying again in 60 seconds...")
            if _ == 4:  # if it is the last attempt
                write_log("Failed to get sensors from the Catalog after 5 attempts")
                exit(1)

            time.sleep(60)   # wait for 60 seconds before trying again

    mqtt_topics = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        try:
            mqtt_topics.append(f"greenhouse_{sensor['greenhouse_id']}/area_{sensor['area_id']}/sensor_{sensor['sensor_id']}")   # topic where receive live data
            mqtt_topics.append(f"greenhouse_{sensor['greenhouse_id']}/area_{sensor['area_id']}/event/sensor_{sensor['sensor_id']}") # topic where receive scheduled events
            tresholds[sensor['sensor_id']] = sensor['threshold']    # associate the threshold to the sensor id into the dictionary
            domains[sensor['sensor_id']] = sensor['domain']    # associate the domain to the sensor id into the dictionary  
            expected_value[sensor['sensor_id']] = None
            timers[sensor['sensor_id']] = None

        except Exception as e:
            write_log(f"Unexpected error in building the topic: {e}")
            exit(1)

    for _ in range(5):  # try to start the MQTT client for 5 times
        try:
            client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"HumidityManagement_{device_id}", on_message, write_log)
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
        time.sleep(1)   # keep the microservice running
    client.stop()