import paho.mqtt.client as mqtt
import time
import random
import json

# device connector is a MQTT publisher that reads data from the sensors connected to RaspberryPi and publishes it to the MQTT broker

# MQTT configuration
mqtt_broker = "mqtt.eclipseprojects.io" # broker address
mqtt_port = 1883    # broker port
mqtt_topic = "greenhouse/sensors"   # topic to publish sensor values
keep_alive = 60

# MQTT Client setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, keep_alive)

# DTH22 is the sensor that measures temperature and humidity
def get_DTH22_Values():
    humidity = random.uniform(20.0, 90.0)  # Read data from the sensors
    temperature = random.uniform(10.0, 35.0)  # Read data from the sensors
    if humidity is not None and temperature is not None:
        return temperature, humidity
    else:
        return None, None
# grove NPK sensor is the sensor that measures NPK values
def get_NPK_Values():
    NPK = random.uniform(0.0, 1000.0)  # Read data from the sensors
    if NPK is not None:
        return NPK
    else:
        return None
    
# capacitive soil moisture sensor is the sensor that measures soil moisture
def get_SoilMoisture_Values():
    soil_moisture = random.uniform(0.0, 100.0)  # Read data from the sensors
    if soil_moisture is not None:
        return soil_moisture
    else:
        return None
    
# analog pH sensor is the sensor that measures pH values of the soil
def get_pH_Values():
    pH = random.uniform(3.0, 9.0)  # Read data from the sensors
    if pH is not None:
        return pH
    else:
        return None
    
# ldr sensor is the sensor that measures light intensity
def get_LightIntensity_Values():
    light_intensity = random.uniform(0.0, 1000.0)  # Read data from the sensors
    if light_intensity is not None:
        return light_intensity
    else:
        return None

start_time = int(time.time())

while True:
    timestamp = int(time.time()-start_time)
    temperature, humidity = get_DTH22_Values()
    NPK = get_NPK_Values()
    soil_moisture = get_SoilMoisture_Values()
    pH = get_pH_Values()
    light_intensity = get_LightIntensity_Values()
    
    # Create SenML records for each sensor value
    temperature_senml = json.dumps({"bn": f"{mqtt_topic}/DTH22/Temperature", "n": "temperature", "u": "Cel", "v": temperature, "t": timestamp})
    humidity_senml = json.dumps({"bn": f"{mqtt_topic}/DTH22/Humidity", "n": "humidity", "u": "%RH", "v": humidity, "t": timestamp})
    NPK_senml = json.dumps({"bn": f"{mqtt_topic}/NPK", "n": "NPK", "u": "mg/L", "v": NPK, "t": timestamp})
    soil_moisture_senml = json.dumps({"bn": f"{mqtt_topic}/SoilMoisture", "n": "soil_moisture", "u": "%", "v": soil_moisture, "t": timestamp})
    pH_senml = json.dumps({"bn": f"{mqtt_topic}/Ph", "n": "pH", "v": pH, "t": timestamp})
    light_intensity_senml = json.dumps({"bn": f"{mqtt_topic}/LightIntensity", "n": "light_intensity", "u": "lux", "v": light_intensity, "t": timestamp})
    
    # Publish the sensor values to the MQTT broker
    client.publish(f"{mqtt_topic}/DTH22/Temperature", temperature_senml)
    client.publish(f"{mqtt_topic}/DTH22/Humidity", humidity_senml)
    client.publish(f"{mqtt_topic}/NPK", NPK_senml)
    client.publish(f"{mqtt_topic}/SoilMoisture", soil_moisture_senml)
    client.publish(f"{mqtt_topic}/Ph", pH_senml)
    client.publish(f"{mqtt_topic}/LightIntensity", light_intensity_senml)
    
    with open("./logs/logs_DeviceConnector.txt", "a") as log_file:
        log_file.write(f"Published: {temperature_senml}\n")
        log_file.write(f"Published: {humidity_senml}\n")
        log_file.write(f"Published: {NPK_senml}\n")
        log_file.write(f"Published: {soil_moisture_senml}\n")
        log_file.write(f"Published: {pH_senml}\n")
        log_file.write(f"Published: {light_intensity_senml}\n")
    
    time.sleep(10)  # Publish sensor values every 10 seconds