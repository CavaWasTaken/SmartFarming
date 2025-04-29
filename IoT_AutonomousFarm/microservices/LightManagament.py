import json
import requests
import threading
from functools import partial
import time
import Management

from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/LightManagement.log", "a") as log_file:
        log_file.write(f"{message}\n")

# each time that the device starts, we clear the log file
with open("./logs/LightManagement.log", "w") as log_file:
    pass

try:
    # read the info from the json file
    with open("./LightManagement_config.json", "r") as config_fd:
        config = json.load(config_fd)   # load the configuration from the file as a dictionary
        catalog_url = config["catalog_url"] # get the url of the catalog
        dataAnalysis_url = config["dataAnalysis_url"]   # get the url of the data analysis
        device_id = config["device_id"] # get the id of the device
        mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # mqtt broker
        mqtt_port = config["mqtt_connection"]["mqtt_port"]  # mqtt port
        keep_alive = config["mqtt_connection"]["keep_alive"]    # keep alive time

except FileNotFoundError:
    write_log("LightManagement_config.json file not found")
    exit(1)
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)

expected_value = {} # dictionary to save the next expected value for each sensor
timers = {} # dictionary to save the timer (interval of time for waiting the next value of that sensor) for each sensor
tresholds = {}  # dictionary to save the treshold interval for each sensor
domains = {}    # dictionary  to save the domain of the values collectable by each sensor

# function that handles the received message from the broker
def handle_message(topic, sensor_type, val, unit, timestamp):
    # function that sends an alert to the user when the expected value doesn't arrive (timer expiration)
    def TimerExpiration(sensor_id, expected_timestamp):
        write_log(f"WARNING: Was expecting a value of {sensor_type} from sensor_{sensor_id} at time {expected_timestamp}, but it didn't arrive")   # ALERT TO BE SENT TO THE UI
        SendAlert(f"WARNING: Was expecting a value of {sensor_type} from sensor_{sensor_id} at time {expected_timestamp}, but it didn't arrive")

    def SendAlert(msg):
        msg = json.dumps({"message": msg, "timestamp": timestamp})
        client.publish(f"greenhouse_{greenhouse_id}/alert/device_{device_id}", msg)

    def SendInfo(msg):
        msg = json.dumps({"message": msg, "timestamp": timestamp})
        client.publish(f"greenhouse_{greenhouse_id}/info/device_{device_id}", msg)

    def SendAction(msg):
        msg = json.dumps({"message": msg, "timestamp": timestamp})
        client.publish(f"greenhouse_{greenhouse_id}/action/device_{device_id}/sensor_{sensor_id}", msg)

    greenhouse, sensor = topic.split("/")  # split the topic and get all the information contained

    greenhouse_id = int(greenhouse.split("_")[1])
    sensor_id = int(sensor.split("_")[1])

    treshold = tresholds[sensor_id]    # get the treshold for the sensor
    min_treshold = treshold["min"]
    max_treshold = treshold["max"]

    # get from the DataAnalysis the next expected timestamp
    response = requests.get(f"{dataAnalysis_url}/get_next_timestamp", params={'sensor_id': sensor_id, 'sensor_type': sensor_type, 'timestamp': timestamp})
    if response.status_code == 200:
        next_timestamp = response.json()["next_timestamp"]
        if next_timestamp is not None:
            write_log(f"Next expected timestamp of sensor_{sensor_id} ({sensor_type}): {next_timestamp}")  # THIS INFO CAN BE SENT TO THE UI
            SendInfo(f"Next expected timestamp of sensor_{sensor_id} ({sensor_type}): {next_timestamp}")
        else:   # if the response is None, we consider the prediction lost
            write_log(f"WARNING: Next expected timestamp of sensor_{sensor_id} ({sensor_type}) not found")   # ALERT TO BE SENT TO THE UI
            SendAlert(f"WARNING: Next expected timestamp of sensor_{sensor_id} ({sensor_type}) not found")
            return
    else:
        write_log(f"WARNING: Impossible to get the next expected timestamp of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis\t(Response: {response.reason})")  # ALERT TO BE SENT TO THE UI
        SendAlert(f"WARNING: Impossible to get the next expected timestamp of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis\t(Response: {response.reason})")
        return

    if next_timestamp is not None:  # when the data analysis make prediction with just 1 value, it can't predict the next value so it is None
        if timers[sensor_id] is not None:  # if there is a timer running, stop it
            timers[sensor_id].cancel()

        timers[sensor_id] = threading.Timer(next_timestamp + 5 - timestamp, partial(TimerExpiration, sensor_id, next_timestamp)) # timer that will wait the next timestamp
        timers[sensor_id].start()   # start the timer

    Management.Check_value(dataAnalysis_url, sensor_id, sensor_type, val, unit, timestamp, min_treshold, max_treshold, expected_value, domains, write_log, SendAlert, SendInfo, SendAction)

def on_message(client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
    try: 
        message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
        write_log(f"\nReceived: {message}")   # write on the log file the message received
        for topic in mqtt_topics:
            if message["bn"] == topic:
                try:
                    message = message["e"]
                    sensor_type = message["n"]
                    val = message["v"]
                    unit = message["u"]
                    timestamp = message["t"]
                    handle_message(topic, sensor_type, val, unit, timestamp)

                except KeyError as e:
                    write_log(f"Missing key in the message: {e}")
                except Exception as e:
                    write_log(f"Error processing the message: {e}")
                finally:
                    break   # if the message is processed, exit the loop

    except json.JSONDecodeError:
        write_log(f"Error decoding the MQTT message payload")
    except Exception as e:
        write_log(f"Unexpected error in on handling the message: {e}")

if __name__ == "__main__":
    while True:
        response = requests.get(f"{catalog_url}/get_sensors", params={"device_id": device_id, 'device_name': 'LightManagement'})
        if response.status_code == 200:
            sensors = response.json()["sensors"]  # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
            write_log(f"Received {len(sensors)} sensors: {sensors}")
            break

        else:
            write_log(f"Failed to get sensors from the Catalog\t(Response: {response.json()["error"]}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
            time.sleep(60)  # wait 60 seconds before trying again

    mqtt_topics = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor, build the topic and append it to the mqtt_topic array
        mqtt_topics.append(f"greenhouse_{sensor["greenhouse_id"]}/sensor_{sensor['sensor_id']}")
        tresholds[sensor['sensor_id']] = sensor['threshold']    # associate the threshold to the sensor id into the dictionary
        domains[sensor['sensor_id']] = sensor['domain']    # associate the domain to the sensor id into the dictionary
        expected_value[sensor['sensor_id']] = None
        timers[sensor['sensor_id']] = None

    # Subscribe to events requiring lighting management for the greenhouse handled by the current device
    mqtt_topics.append(f"greenhouse_{sensors[0]['greenhouse_id']}/Lighting")

    while True:
        try:        
            # create the client and connect it to the broker
            client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"LightManagement_{device_id}", on_message, write_log)
            client.start()  # start the client
            break

        except Exception as e:
            write_log(f"Error starting MQTT client: {e}\nTrying again in 60 seconds...")
            time.sleep(60)

    for topic in mqtt_topics:
        while True:
            try:
                client.subscribe(topic)
                break

            except Exception as e:
                write_log(f"Error subscribing the client to the topic ({topic}): {e}\nTrying again in 60 seconds...")
                time.sleep(60)  # wait for 60 seconds before trying again

    while True:
        time.sleep(1)
    client.stop()   # stop the client