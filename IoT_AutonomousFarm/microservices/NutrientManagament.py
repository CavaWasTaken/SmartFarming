import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests

# each time that the device starts, we clear the log file
with open("./logs/NutrientManagement.log", "w") as log_file:
    pass

# read the device_id and mqtt information of the broker from the json file
with open("./NutrientManagement_config.json", "r") as config_fd:
    config = json.load(config_fd)
    catalog_url = config["catalog_url"]
    dataAnalysis_url = config["dataAnalysis_url"]
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
    mqtt_port = config["mqtt_connection"]["mqtt_port"]
    keep_alive = config["mqtt_connection"]["keep_alive"]

def handle_message(topic, val):
    with open("./logs/NutrientManagement.log", "a") as log_file:

        def check_val(sensor_id, param, unit, val, min_treshold, max_treshold):   # function that checks if the value is in the accepted range
            out = False # if the value is in the accepted range, out is False
            if val < min_treshold:  # if the value is lower than the accepted range, out is True
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} {unit} is low\taccepted range {min_treshold}-{max_treshold}\n")
            elif val > max_treshold:    # if the value is higher than the accepted range, out is True
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} is high\taccepted range {min_treshold}-{max_treshold}\n")
            else:   # if the value is in the accepted range, out is False
                out = True
                log_file.write(f"Sensor_{sensor_id} ({param}): {val} is in the accepted range {min_treshold}-{max_treshold}\n")
            return out
        
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        # i have all the information about the sensor but i don't know its id, so i need to ask the catalog. I need the id cause i use it to access to its tresholds
        response = requests.get(f"{catalog_url}/get_sensor_id", params={'device_id': device_id, 'device_name': 'NutrientManagement', 'greenhouse_id': greenhouse.split("_")[1], 'plant_id': plant.split("_")[1], 'sensor_name': sensor_name, 'sensor_type': sensor_type})    # get the sensor id from the catalog
        if response.status_code == 200:
            sensor_id = response.json()["sensor_id"]
            log_file.write(f"New value collected by sensor {sensor_id}\n")
        else:
            log_file.write(f"Failed to get sensor id from the Catalog\nResponse: {response.reason}\n")
            exit(1) # if the request fails, the device connector stops

        treshold = tresholds[f"sensor_{sensor_id}"]    # get the treshold for the sensor

        if sensor_type == "NPK":    # check the values of NPK
            response = requests.get(f"{dataAnalysis_url}/get_mean_N")    # get the treshold for NPK from the data analysis
            if response.status_code == 200:
                mean_N = response.json()["mean_N"]
                log_file.write(f"Mean N: {mean_N}\n")
                if not check_val(sensor_id, "N", "mg/L", val["N"], treshold["N"]["min"], treshold["N"]["max"]): # check if the value is not in the accepted range, then we need to check also the mean
                    if not check_val(sensor_id, "N", "mg/L", mean_N, treshold["N"]["min"], treshold["N"]["max"]): # check if the mean is not in the accepted range, then we need to take action
                        log_file.write(f"Action needed for sensor_{sensor_id}\n")
            else:
                log_file.write(f"Failed to get mean N from the Data Analysis\nResponse: {response.reason}\n")
                exit(1) # if the request fails, the device connector stops
            
            response = requests.get(f"{dataAnalysis_url}/get_mean_P")    # get the treshold for NPK from the data analysis
            if response.status_code == 200:
                mean_P = response.json()["mean_P"]
                log_file.write(f"Mean P: {mean_P}\n")
                if not check_val(sensor_id, "P", "mg/L", val["P"], treshold["P"]["min"], treshold["P"]["max"]): # check if the value is not in the accepted range, then we need to check also the mean
                    if not check_val(sensor_id, "P", "mg/L", mean_P, treshold["P"]["min"], treshold["P"]["max"]):   # check if the mean is not in the accepted range, then we need to take action
                        log_file.write(f"Action needed for sensor_{sensor_id}\n")
            else:
                log_file.write(f"Failed to get mean P from the Data Analysis\nResponse: {response.reason}\n")
                exit(1) # if the request fails, the device connector stops

            response = requests.get(f"{dataAnalysis_url}/get_mean_K")    # get the treshold for NPK from the data analysis
            if response.status_code == 200:
                mean_K = response.json()["mean_K"]
                log_file.write(f"Mean K: {mean_K}\n")
                if not check_val(sensor_id, "K", "mg/L", val["K"], treshold["K"]["min"], treshold["K"]["max"]): # check if the value is not in the accepted range, then we need to check also the mean
                    if not check_val(sensor_id, "K", "mg/L", mean_K, treshold["K"]["min"], treshold["K"]["max"]):   # check if the mean is not in the accepted range, then we need to take action
                        log_file.write(f"Action needed for sensor_{sensor_id}\n")
            else:
                log_file.write(f"Failed to get mean K from the Data Analysis\nResponse: {response.reason}\n")
                exit(1) # if the request fails, the device connector stops

        elif sensor_type == "pH":   # check the value of pH
            response = requests.get(f"{dataAnalysis_url}/get_mean_pH")    # get the treshold for pH from the data analysis
            if response.status_code == 200:
                mean_pH = response.json()["mean_pH"]
                log_file.write(f"Mean pH: {mean_pH}\n")
                if not check_val(sensor_id, "pH", "", val, treshold["min"], treshold["max"]):    # check if the value is not in the accepted range, then we need to check also the mean
                    if not check_val(sensor_id, "pH", "", mean_pH, treshold["min"], treshold["max"]):  # check if the mean is not in the accepted range, then we need to take action
                        log_file.write(f"Action needed for sensor_{sensor_id}\n")
            else:
                log_file.write(f"Failed to get mean pH from the Data Analysis\nResponse: {response.reason}\n")
                exit(1) # if the request fails, the device connector stops

        elif sensor_type == "SoilMoisture":   # check the value of soil moisture
            response = requests.get(f"{dataAnalysis_url}/get_mean_soil_moisture")    # get the treshold for soil moisture from the data analysis
            if response.status_code == 200:
                mean_soil_moisture = response.json()["mean_soil_moisture"]
                log_file.write(f"Mean soil moisture: {mean_soil_moisture}\n")
                if not check_val(sensor_id, "soil moisture", "%", val, treshold["min"], treshold["max"]):   # check if the value is not in the accepted range, then we need to check also the mean
                    if not check_val(sensor_id, "soil moisture", "%", mean_soil_moisture, treshold["min"], treshold["max"]):    # check if the mean is not in the accepted range, then we need to take action
                        log_file.write(f"Action needed for sensor_{sensor_id}\n")
            else:
                log_file.write(f"Failed to get mean soil moisture from the Data Analysis\nResponse: {response.reason}\n")
                exit(1) # if the request fails, the device connector stops
            
class NutrientManagement(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):
        with open("./logs/NutrientManagement.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode()) # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)

if __name__ == "__main__":
    response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'NutrientManagement'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]   # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("./logs/NutrientManagement.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("./logs/NutrientManagement.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # array of topics where the device is subscribed
    global tresholds    # global variable that contains the tresholds for each sensor
    tresholds = {}  # dictionary that contains the tresholds for each sensor
    for sensor in sensors:  # for each sensor build the topic where the device is subscribed and build the dictionary of tresholds
        mqtt_topic.append(f"greenhouse_{sensor["greenhouse_id"]}/plant_{sensor["plant_id"] if sensor["plant_id"] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")
        tresholds[f"sensor_{sensor['sensor_id']}"] = sensor['threshold']    # associate the threshold to the sensor id into the dictionary

    # the mqtt subscriber subscribes to the topics
    subscriber = NutrientManagement(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()