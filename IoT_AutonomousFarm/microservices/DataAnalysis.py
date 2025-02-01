import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests

# each time that the device starts, we clear the log file
with open("./logs/DataAnalysis.log", "w") as log_file:
    pass

# read the device_id and mqtt information of the broker from the json file
with open("./DataAnalysis_config.json", "r") as config_fd:
    config = json.load(config_fd)
    catalog_url = config["catalog_url"]
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
    mqtt_port = config["mqtt_connection"]["mqtt_port"]
    keep_alive = config["mqtt_connection"]["keep_alive"]

x_est = 20.0  # Initial estimate
P = 1.0  # Initial uncertainty
A = 1.0  # State transition model
H = 1.0  # Observation model
Q = 0.01  # Process noise covariance (small noise)
R = 0.5  # Measurement noise covariance (sensor noise)

def handle_message(topic, val):
    with open("./logs/DataAnalysis.log", "a") as log_file:
        global count_mean_t, mean_temperature, count_mean_h, mean_humidity, count_mean_l, mean_light, count_mean_sm, mean_soil_moisture, count_mean_pH, mean_pH, count_mean_N, mean_N, count_mean_P, mean_P, count_mean_K, mean_K
        greenhouse, plant, sensor_name, sensor_type = topic.split("/")  # split the topic and get all the information contained
        # log_file.write(f"Received message from {greenhouse} - {plant} - {sensor_name} - {sensor_type}\n")

        # function to update the mean value of the data collected by each sensor
        def update_mean(value, count, mean):
            count += 1
            mean += (value - mean) / count
            return count, mean
        
        def kalman_filter(z_meas):
            global x_est, P
            
            # Prediction Step
            x_pred = A * x_est
            P_pred = A * P * A + Q

            # Update Step
            K = P_pred * H / (H * P_pred * H + R)  # Kalman Gain
            x_est = x_pred + K * (z_meas - H * x_pred)  # Update estimate
            P = (1 - K * H) * P_pred  # Update uncertainty
            
            return x_est

        if sensor_type == "Temperature":    # keeps track of the mean temperature
            count_mean_t, mean_temperature = update_mean(val, count_mean_t, mean_temperature)
            log_file.write(f"Mean temperature: {mean_temperature}\n")
            pred = kalman_filter(val)
            log_file.write(f"Kalman Filter Prediction: {pred}\n")
        elif sensor_type == "Humidity":   # keeps track of the mean humidity
            count_mean_h, mean_humidity = update_mean(val, count_mean_h, mean_humidity)
            log_file.write(f"Mean humidity: {mean_humidity}\n")
        elif sensor_type == "LightIntensity":    # keeps track of the mean light
            count_mean_l, mean_light = update_mean(val, count_mean_l, mean_light)
            log_file.write(f"Mean light intensity: {mean_light}\n")
        elif sensor_type == "SoilMoisture":    # keeps track of the mean soil moisture
            count_mean_sm, mean_soil_moisture = update_mean(val, count_mean_sm, mean_soil_moisture)
            log_file.write(f"Mean soil moisture: {mean_soil_moisture}\n")
        elif sensor_type == "pH":   # keeps track of the mean pH
            count_mean_pH, mean_pH = update_mean(val, count_mean_pH, mean_pH)
            log_file.write(f"Mean pH: {mean_pH}\n")
        elif sensor_type == "NPK":    # keeps track of the mean NPK
            count_mean_N, mean_N = update_mean(val["N"], count_mean_N, mean_N)
            log_file.write(f"Mean N: {mean_N}\n")
            count_mean_P, mean_P = update_mean(val["P"], count_mean_P, mean_P)
            log_file.write(f"Mean P: {mean_P}\n")
            count_mean_K, mean_K = update_mean(val["K"], count_mean_K, mean_K)
            log_file.write(f"Mean K: {mean_K}\n")
            

class DataAnalysis(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("./logs/DataAnalysis.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    val = message["v"]
                    handle_message(topic, val)

# initialize the mean values of the sensors to 0 and the count of the messages received to 0
count_mean_t = 0
mean_temperature = 0
count_mean_h = 0
mean_humidity = 0
count_mean_l = 0
mean_light = 0
count_mean_sm = 0
mean_soil_moisture = 0
count_mean_pH = 0
mean_pH = 0
count_mean_N = 0
mean_N = 0
count_mean_P = 0
mean_P = 0
count_mean_K = 0
mean_K = 0

if __name__ == "__main__":
    # instead of reading the topics like this, i would like to change it and make that the microservices build the topics by itself by knowing the greenhouse where it is connected and the plant that it contains
    response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'DataAnalysis'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("./logs/DataAnalysis.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("./logs/DataAnalysis.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops

    mqtt_topic = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topic.append(f"greenhouse_{sensor['greenhouse_id']}/plant_{sensor['plant_id'] if sensor['plant_id'] is not None else 'ALL'}/{sensor['name']}/{sensor['type']}")

    # the mqtt subscriber subscribes to the topics
    subscriber = DataAnalysis(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()