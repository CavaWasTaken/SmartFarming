from flask import Flask, jsonify
import random
import time

app = Flask(__name__)

# our temperature and humidity sensor doesn't work, so we will simulate the data
def get_temperature():  
    return round(random.uniform(20.0, 30.0), 2)

def get_humidity():
    return round(random.uniform(30.0, 70.0), 2)

start_t = int(time.time())

# get method with URI http://raspberrypi.local:5000/temperature
@app.route('/temperature', methods=['GET'])
def temperature():
    t = int(time.time()) - start_t
    temperature = get_temperature()
    # the response is returned in SenML format:
    response = {
        "bn": "group/DHT11/temperature",    # base name
        "e": [  # array of data
            {
                "n": "temperature", # name of the data
                "u": "Cel", # unit of the data
                "t": t, # time of the data
                "v": temperature    # value of the data
            }
        ]
    }
    return jsonify(response)

# get method with URI http://raspberrypi.local:5000/humidity
@app.route('/humidity', methods=['GET'])
def humidity():
    t = int(time.time()) - start_t
    humidity = get_humidity()
    response = {
        "bn": "group/DHT11/humidity",
        "e": [
            {
                "n": "humidity",
                "u": "%RH",
                "t": t,
                "v": humidity
            }
        ]
    }
    return jsonify(response)

# get method with URI http://raspberrypi.local:5000/allSensor
@app.route('/allSensor', methods=['GET'])
def all_sensor():
    t = int(time.time()) - start_t
    temperature = get_temperature()
    humidity = get_humidity()
    response = {
        "bn": "group/DHT11/allSensor",
        "e": [
            {
                "n": "temperature",
                "u": "Cel",
                "t": t,
                "v": temperature
            },
            {
                "n": "humidity",
                "u": "%RH",
                "t": t,
                "v": humidity
            }
        ]
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # run the server on port 5000 on localhost of the Raspberry Pi