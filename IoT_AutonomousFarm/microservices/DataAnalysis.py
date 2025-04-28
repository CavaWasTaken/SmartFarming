import json
import requests
import cherrypy
from scipy.stats import linregress
import time

from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/DataAnalysis.log", "a") as log_file:
        log_file.write(f"{message}\n")

# each time that the device starts, we clear the log file
with open("./logs/DataAnalysis.log", "w") as log_file:
    pass

try:
    # read the device_id and mqtt information of the broker from the json file
    with open("./DataAnalysis_config.json", "r") as config_fd:
        config = json.load(config_fd)
        catalog_url = config["catalog_url"]
        thingSpeak_url = config["thingSpeak_url"]
        device_id = config["device_id"]
        mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
        mqtt_port = config["mqtt_connection"]["mqtt_port"]
        keep_alive = config["mqtt_connection"]["keep_alive"]

except FileNotFoundError:
    write_log("DataAnalysis_config.json file not found")
    exit(1) # exit the program if the file is not found
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)

global N   # N is the number of values to keep track of

# function to evaluate means, expected values and timestamps of the last N values received for each sensor
def handle_message(topic, sensor_type, val, timestamp):
    # evaluation of the weighted mean on array of (at max N if the array is full) N values
    def weighted_mean(values, weights):    # calculate the weighted mean of a list of values
        if sensor_type == "NPK":
            return {
                "N": sum([v["N"]*w for v,w in zip(values, weights)]) / sum(weights),
                "P": sum([v["P"]*w for v,w in zip(values, weights)]) / sum(weights),
                "K": sum([v["K"]*w for v,w in zip(values, weights)]) / sum(weights)
            }
        else:
            return sum([v*w for v,w in zip(values, weights)]) / sum(weights)
    
    # perform linear regression on the array of (at max N if the array is full) N values to predict the next value
    def linear_regression(times, values):
        if len(times) > 1 and len(values) > 1:  # impossible to make prediction with just a value
            # predict the timestamp of the next value by evaluating the mean difference between two consecutive timestamps
            next_timestamp = sum([times[i] - times[i-1] for i in range(1, len(times))]) / (len(times) - 1) + times[-1]

            # NPK sensor collect three data in one, so has a different treatment
            if sensor_type == "NPK":
                N = [v["N"] for v in values]    # extract and separate from the dictionary the values of N, P and K
                P = [v["P"] for v in values]
                K = [v["K"] for v in values]
                slope_N, intercept_N, r_value_N, p_value_N, std_err_N = linregress(times, N)    # calculate the linear regression of the values
                slope_P, intercept_P, r_value_P, p_value_P, std_err_P = linregress(times, P)    # calculate the linear regression of the values
                slope_K, intercept_K, r_value_K, p_value_K, std_err_K = linregress(times, K)    # calculate the linear regression of the values

                # save in a dictionary the three expectations of the next value
                next_value = {
                    "N": float(slope_N * next_timestamp + intercept_N),
                    "P": float(slope_P * next_timestamp + intercept_P),
                    "K": float(slope_K * next_timestamp + intercept_K)
                }
            else:   # with all the other sensor just a linear regression is needed
                slope, intercept, r_value, p_value, std_err = linregress(times, values)    # calculate the linear regression of the values

                # predict the value of the next value by evaluating the linear regression of the values (y = mx + q)
                next_value = slope * next_timestamp + intercept

        else:
            # not enough data to calculate the linear regression
            write_log(f"Not enough data to calculate the linear regression")
            # no evaluation, None results
            next_timestamp = None
            next_value = None

        return next_timestamp, next_value
    
    # add the timestamp to the array of the timestamps of the last N values received
    def update_timestamps(times, timestamp):
        if len(times) >= N:    # if the length of the list of timestamps is N, remove the first element (the oldest)
            times.pop(0)
        times.append(timestamp)    # append the timestamp of the new value to the list of timestamps 
    
    # add the value to the array of the values of the last N values received
    def update_statistics(times, vals, val, sensor_id):
        if len(vals) >= N:    # if the length of the list of values is N, remove the first element (the oldest)
            vals.pop(0)
        vals.append(val)    # append the new value to the list
        weights = list(range(1, len(vals)+1))    # create a list of weights from 1 to N to calculate the weighted mean
        mean = weighted_mean(vals, weights)    # calculate the weighted mean of the values

        # evaluate predictions
        next_times, next_val = linear_regression(times, vals)    # calculate the linear regression of the values
        next_timestamp[sensor_id] = next_times
        next_value[sensor_id] = next_val

        return mean
    
    # function to handle the value read from a sensor and perform the necessary operations
    def handle_sensor(sensor_id, val):
        update_timestamps(timestamps[sensor_id], timestamp)    # update the list of timestamps of the last N values received
        mean_value[sensor_id] = update_statistics(timestamps[sensor_id], values[sensor_id], val, sensor_id)
        write_log(f"Sensor {sensor_id}: Weighted mean {sensor_type}: {mean_value[sensor_id]}")
        write_log(f"Sensor {sensor_id}: Expected next timestamp of {sensor_type}: {next_timestamp[sensor_id]}")
        write_log(f"Sensor {sensor_id}: Expected next value of {sensor_type}: {next_value[sensor_id]}")

    greenhouse, sensor = topic.split("/")  # split the topic and get all the information contained
    # sensor = "sensor_1" -> sensor_id = 1
    sensor = sensor.split("_")[1]   # get the sensor_id from the topic
    handle_sensor(int(sensor), val)

# function to be performed when a message on a topic of interest is received from the MQTT broker
def on_message(client, userdata, msg):
    try:
        message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
        write_log(f"\nReceived: {message}")
        for topic in mqtt_topics:
            if message["bn"] == topic:
                try:
                    message = message["e"]  # get the message from the dictionary
                    sensor_type = message["n"]  # get the type of the sensor
                    val = message["v"]  # get the value of the message
                    timestamp = message["t"]  # get the timestamp of the message
                    handle_message(topic, sensor_type, val, timestamp)
                    
                except KeyError as e:
                    write_log(f"Missing key in the message: {e}")
                except Exception as e:
                    write_log(f"Error processing the message: {e}")
                finally:
                    break  # if the message is processed, exit the loop

    except json.JSONDecodeError:
        write_log("Error decoding the MQTT message payload")
    except Exception as e:
        write_log(f"Unexpected error in on_message: {e}")

# dictionaries to store the values of each sensor
timestamps = {} # arrays of timestamps of the received value
values = {} # arrays of values received 
mean_value = {} # mean values
next_timestamp = {} # timestamp of when the next value is expected to be received
next_value = {} # expected value of the next value

# REST

# methods called from management components to get the mean statistics on the last N values received
def get_mean_value(sensor_id, sensor_type, timestamp):
    write_log(f"\nReceived request for the mean value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp}")
    count = 0   # count how many seconds we are waiting
    # to check if at the time of the request the DataAnalysis has already evaluated the updated mean value or not
    if float(timestamps[sensor_id][-1]) == float(timestamp):  # if the timestamp is the same as the last received, return the mean value
        write_log(f"The requested mean value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is ready ({mean_value[sensor_id]})")
        return {'mean_value': mean_value[sensor_id]}   # the value has been updated, so we can return it
    
    else:   # the value has not been updated yet, so we wait for it until it is updated
        write_log(f"The requested mean value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is not yet ready")
        # loop to wait for the value to be updated with a maximum of 60 seconds
        while float(timestamps[sensor_id][-1]) != float(timestamp):   # wait for the value to be updated
            write_log(f"{float(timestamps[sensor_id][-1])} != {float(timestamp)} : {float(timestamps[sensor_id][-1]) != float(timestamp)}")
            if count < 60:  # wait for a maximum of 60 seconds
                time.sleep(1)   # wait for 1 second
            else:   # if we waited for 60 seconds, return None
                write_log(f"The requested mean value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is considered lost")
                return {'mean_value': None}
            
            count += 1  # increment the counter
        write_log(f"The requested mean value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is ready ({mean_value[sensor_id]})")
        return {'mean_value': mean_value[sensor_id]}   # the value has been updated, so we can return it

# methods called from management components to get the predictions on when the next value will be received by the sensor
def get_next_timestamp(sensor_id, sensor_type, timestamp):
    write_log(f"\nReceived request for the next timestamp of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp}")
    count = 0   # count how many seconds we are waiting
    # to check if at the time of the request the DataAnalysis has already evaluated the updated mean value or not
    if float(timestamps[sensor_id][-1]) == float(timestamp):  # if the timestamp is the same as the last received, return the next timestamp
        write_log(f"The requested next timestamp of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is ready ({next_timestamp[sensor_id]})")
        return {'next_timestamp': next_timestamp[sensor_id]}   # the value has been updated, so we can return it
    
    else:   # the value has not been updated yet, so we wait for it
        write_log(f"The requested next timestamp of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is not yet ready\n")
        while float(timestamps[sensor_id][-1]) != float(timestamp):   # wait for the value to be updated
            if count < 60:  # wait for a maximum of 60 seconds
                time.sleep(1)   # wait for 1 second
            else:   # if we waited for 60 seconds, return None
                write_log(f"The requested next timestamp of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is considered lost")
                return {'next_timestamp': None}
            
            count += 1  # increment the counter
        write_log(f"The requested next timestamp of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is arrived ({next_timestamp[sensor_id]})")
        return {'next_timestamp': next_timestamp[sensor_id]}   # the value has been updated, so we can return it

# methods called from management components to get the predictions on the next value that will be received by the sensor
def get_next_value(sensor_id, sensor_type, timestamp):
    write_log(f"\nReceived request for the next value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp}\n")
    count = 0   # count how many seconds we are waiting
    # to check if at the time of the request the DataAnalysis has already evaluated the updated mean value or not
    if float(timestamps[sensor_id][-1]) == float(timestamp):  # if the timestamp is the same as the last received, return the next value
        write_log(f"The requested next value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is ready ({next_value[sensor_id]})\n")
        return {'next_value': next_value[sensor_id]}   # the value has been updated, so we can return it
    
    else:   # the value has not been updated yet, so we wait for it
        write_log(f"The requested next value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is not yet ready\n")
        while float(timestamps[sensor_id][-1]) != float(timestamp):   # wait for the value to be updated
            if count < 60:  # wait for a maximum of 60 seconds
                time.sleep(1)   # wait for 1 second
            else:   # if we waited for 60 seconds, return None
                write_log(f"The requested next value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is considered lost\n")
                return {'next_value': None}
            
            count += 1  # increment the counter
        write_log(f"The requested next value of sensor_{sensor_id} ({sensor_type}) at timestamp {timestamp} is ready ({next_value[sensor_id]})\n")
        return {'next_value': next_value[sensor_id]}   # the value has been updated, so we can return it

# REST API exposed by the DataAnalysis microservice
class DataAnalysisREST(object):
    exposed = True

    def __init__(self, data_analysis_connection):
        self.data_analysis_connection = data_analysis_connection

    # handles all the different HTTP methods
    @cherrypy.tools.json_out()  # automatically convert return value
    def GET(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        elif uri[0] == 'get_mean_value':
            return get_mean_value(int(params['sensor_id']), params['sensor_type'], params['timestamp'])
        elif uri[0] == 'get_next_timestamp':
            return get_next_timestamp(int(params['sensor_id']), params['sensor_type'], params['timestamp'])
        elif uri[0] == 'get_next_value':
            return get_next_value(int(params['sensor_id']), params['sensor_type'], params['timestamp'])
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        
    @cherrypy.tools.json_out()  # automatically convert return value
    def POST(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')

    @cherrypy.tools.json_out()  # automatically convert return value        
    def PUT(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')
        
    @cherrypy.tools.json_out()  # automatically convert return value
    def DELETE(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')

if __name__ == "__main__":
    # RESR API exposed by the DataAnalysis microservice and used by management components to get statistics
    dataAnalysisClient = DataAnalysisREST(None)
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8081})
    cherrypy.tree.mount(dataAnalysisClient, '/', conf)
    cherrypy.engine.start()

    while True:
        # it has to read the parameter N from the catalog
        response = requests.get(f"{catalog_url}/get_device_info", params={'device_id': device_id, 'device_name': 'DataAnalysis'})    # get the device information from the catalog
        if response.status_code == 200:
            device_info = response.json()    # device_info is a dictionary with the information of the device
            write_log(f"Received device information: {device_info}")
            
            try:
                N = device_info["params"]['N']    # get the number of values to keep track of from the device information
                break   # exit the loop if the progeram has red the N param inside the device info

            except KeyError as e:
                write_log(f"Missing key in JSON device configuration: {e}\nTrying again in 60 seconds...")
                time.sleep(60)  # wait for 60 seconds before trying again
                
        else:
            write_log(f"Failed to get device information from the Catalog\nResponse: {response.json()["error"]}\nTrying again in 60 seconds...")
            time.sleep(60)  # wait for 60 seconds before trying again

    while True:
        # it has to read the sensors from the catalog
        response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'DataAnalysis'})
        if response.status_code == 200:
            sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
            write_log(f"Received {len(sensors)} sensors: {sensors}")
            break   # exit the loop if the request is successful
        
        else:
            write_log(f"Failed to get sensors from the Catalog\nResponse: {response.json()["error"]}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
            time.sleep(60)   # wait for 60 seconds before trying again

    mqtt_topics = [] # initialize the array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topics.append(f"greenhouse_{sensor['greenhouse_id']}/sensor_{sensor['sensor_id']}")
        timestamps[sensor["sensor_id"]] = []
        values[sensor["sensor_id"]] = []
        mean_value[sensor["sensor_id"]] = 0
        next_timestamp[sensor["sensor_id"]] = 0
        next_value[sensor["sensor_id"]] = 0

    write_log("")

    # import matplotlib.pyplot as plt

    # def askDataForPlot(field, n):
    #     with open("./logs/DataAnalysis.log", "a") as log_file:
    #         log_file.write(f"\nRequesting {n} values of {field} from ThingSpeak\n")
    #         response = requests.get(f"{thingSpeak_url}/get_field_data", params={'field': field, 'n': n})
    #         if response.status_code == 200:
    #             values = response.json()["values"]
    #             # reduce the amount of decimal digits
    #             values = [round(float(v), 2) for v in values]
    #             log_file.write(f"Received {len(values)} values of {field} from ThingSpeak:\n{values}\n")
    #             if len(values) < n:
    #                 log_file.write(f"Requested {n} values, but only {len(values)} are avaible\n")
    #             # generate a plot with the data received
    #             plt.figure(1)
    #             plt.plot(values)
    #             plt.xlabel("Timestamp")
    #             plt.ylabel("Value")
    #             plt.title(f"{field} values")
    #             plt.savefig(f"./plots/{field}_plot.png")
    #         else:
    #             log_file.write(f"Failed to get data from ThingSpeak\nResponse: {response.reason}\n")

    # askDataForPlot("Temperature", 10)

    while True:
        try:
            client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"DataAnalysis_{device_id}", on_message, write_log)
            client.start()
            break   # exit the loop if the client is started successfully

        except Exception as e:
            write_log(f"Error starting MQTT client: {e}\nTrying again in 60 seconds...")    # in case of error, write the reason of the error in the log file
            time.sleep(60)   # wait for 60 seconds before trying again

    for topic in mqtt_topics:
        while True:
            try:
                client.subscribe(topic)
                break

            except Exception as e:
                write_log(f"Error subscribing the client to the topic ({topic}): {e}\nTrying again in 60 seconds...")
                time.sleep(60)  # wait for 60 seconds before trying again