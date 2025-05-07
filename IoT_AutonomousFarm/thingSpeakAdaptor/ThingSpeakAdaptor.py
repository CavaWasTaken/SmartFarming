import json
import requests
import cherrypy
import time

from MqttClient import MqttClient   # import the MqttClient class

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
        log_file.write(f"{message}\n")

# each time that the device starts, we clear the log file
with open("./logs/ThingSpeakAdaptor.log", "w") as log_file:
    pass

# read the info from the json file
with open("./ThingSpeakAdaptor_config.json", "r") as config_fd:
    config = json.load(config_fd)   # load the configuration from the file as a dictionary
    catalog_url = config["catalog_url"] # get the url of the catalog
    device_id = config["device_id"] # get the id of the device
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # mqtt broker
    mqtt_port = config["mqtt_connection"]["mqtt_port"]  # mqtt port
    keep_alive = config["mqtt_connection"]["keep_alive"]    # keep alive time
    write_url = config["write_url"] # url to write data to the ThingSpeak channel
    read_url = config["read_url"]   # url to read data from the ThingSpeak channel

thingSpeak_config = {}  # dictionary containing the configuration of the ThingSpeak channel

def handle_message(topic, sensor_type, val):
    greenhouse, sensor = topic.split("/")  # split the topic and get all the information contained
    greenhouse_id = greenhouse.split("_")[1]    # extract the id of the greenhouse from the topic
    sensor_id = sensor.split("_")[1]    # extract the id of the sensor from the topic

    fields = thingSpeak_config["fields"]    # get the fields of the ThingSpeak channel
    if sensor_type == "NPK":
        fields["Nitrogen"] = val["N"]
        fields["Phosphorus"] = val["P"]
        fields["Potassium"] = val["K"]
    else:
        fields[sensor_type] = val   # update the value of the field with the value received from the sensor

    missing_fields = [k for k, v in fields.items() if v == ""]  # find the keys of the missing values
    if missing_fields:  # if there are missing values in the fields, log them and return. We have to wait to have read all the data before sending to ThingSpeak
        write_log(f"Missing values for fields: {missing_fields}")
        return
    
    payload = { # payload to send to the ThingSpeak API
        "api_key": thingSpeak_config["write_api_key"],   # write api key of the channel
        **{f"field{i+1}": value for i, value in enumerate(fields.values())}    # add the values of the fields to the payload
    }

    response = requests.post(write_url, data=payload)    # send the request to the ThingSpeak API
    if response.status_code == 200:
        write_log(f"Successfully updated ThingSpeak channel {thingSpeak_config['channel_id']} with payload: {payload}")
    else:
        write_log(f"Failed to update ThingSpeak. Response: {response.reason}")
    
    write_log("")

    # reset the json to empty strings
    for key in fields.keys():
        fields[key] = ""

def on_message(client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
    try:
        message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
        write_log(f"Received: {message}")
        for topic in mqtt_topics:
            if message["bn"] == topic:
                try:
                    message = message["e"]
                    sensor_type = message["n"]
                    val = message["v"]
                    handle_message(topic, sensor_type, val)
                    break   # if the message is processed, break the loop

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
        
def get_field_data(field, n):
    write_log(f"Request to get last {n} values of field '{field}'")
    try:
    # ask to the ThingSpeak API the last N data of the field
        response = requests.get(f"{read_url}/{thingSpeak_config["channel_id"]}/feeds.json", params={'api_key': thingSpeak_config["read_api_key"], 'results': 0})
        if response.status_code == 200:
            data = response.json()
            channel_info = data.get("channel", {})
            field_num = None

            for key, value in channel_info.items():
                if value == field and key.startswith("field"):
                    field_number = key.replace("field", "")  # Extract the number
                    break

            if field_number:
                response = requests.get(f"{read_url}/{thingSpeak_config['channel_id']}/fields/{field_number}.json", params={"api_key": thingSpeak_config["read_api_key"], "results": n})

                if response.status_code == 200:
                    field_data = response.json()
                    entries = field_data.get("feeds", [])
                    values = [entry.get(f"field{field_number}") for entry in entries if entry.get(f"field{field_number}") is not None]

                    write_log(f"Successfully fetched {len(values)} values of field '{field}': {values}")
                    return {"values": values}
                
                else:
                    write_log(f"Failed to fetch data from ThingSpeak. Response: {response.reason}")
                    cherrypy.response.status = 500
                    return {"error": "Failed to fetch data from ThingSpeak"}

            else:
                write_log(f"Failed to fetch data from ThingSpeak. Field '{field}' not found in the channel")
                cherrypy.response.status = 404
                return {"error": "Field not found in the channel"}

        else:
            write_log(f"Failed to fetch data from ThingSpeak. Response: {response.reason}")
            cherrypy.response.status = 500
            return {"error": "Failed to fetch data from ThingSpeak"}
        
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

# REST API exposed by the ThingSpeak Adaptor
class ThingSpeakAdaptorRestAPI(object):
    exposed = True

    def __init__(self, thingSpeak_connection):
        self.thingSpeak_connection = thingSpeak_connection

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri) == 0:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}
        
        elif uri[0] == "get_field_data":
            if 'field' not in params or 'n' not in params:
                cherrypy.response.status = 400
                return {"error": "MISSING PARAMETERS"}
            
            return get_field_data(params['field'], params['n'])
        
        else:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}
    
    @cherrypy.tools.json_out()  # automatically convert return value
    def POST(self, *uri, **params):
        cherrypy.response.status = 405
        return {"error": "METHOD NOT ALLOWED"}
    
    @cherrypy.tools.json_out()  # automatically convert return value        
    def PUT(self, *uri, **params):
        cherrypy.response.status = 405
        return {"error": "METHOD NOT ALLOWED"}
            
    @cherrypy.tools.json_out()  # automatically convert return value
    def DELETE(self, *uri, **params):
        cherrypy.response.status = 405
        return {"error": "METHOD NOT ALLOWED"}
    
if __name__ == "__main__":
    try:
        thingSpeakClient = ThingSpeakAdaptorRestAPI(None)
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True,
            }
        }
        cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8082})
        cherrypy.tree.mount(thingSpeakClient, '/', conf)
        cherrypy.engine.start()
    
    except Exception as e:
        write_log(f"Error starting ThingSpeakAdaptor: {e}")
        exit(1)

    for _ in range(5):
        try: 
            response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'ThingSpeakAdaptor'})    # get the device information from the catalog
            if response.status_code == 200:
                sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
                write_log(f"Received {len(sensors)} sensors: {sensors}")
                break

            else:
                write_log(f"Failed to get sensors from the Catalog\nResponse: {response.reason}")    # in case of error, write the reason of the error in the log file
                if _ == 4:
                    write_log("Failed to get sensors from the Catalog after 5 attempts")
                    exit(1)
                
                time.sleep(60)  # wait 60 seconds before retrying

        except Exception as e:
            write_log(f"Error getting sensors from the Catalog: {e}")
            if _ == 4:
                write_log("Failed to get sensors from the Catalog after 5 attempts")
                exit(1)
            
            time.sleep(60)
        
    for _ in range(5):
        try:
            response = requests.get(f"{catalog_url}/get_greenhouse_info", params={'greenhouse_id': sensors[0]["greenhouse_id"], 'device_id': device_id})    # get the greenhouse information from the catalog
            if response.status_code == 200:
                greenhouse_info = response.json()    # greenhouse_info is a dictionary with the information of the greenhouse
                write_log(f"Received greenhouse information: {greenhouse_info}")
                thingSpeak_config = greenhouse_info["thingSpeak_config"]
                break

            else:
                write_log(f"Failed to get greenhouse information from the Catalog\nResponse: {response.reason}")
                if _ == 4:
                    write_log("Failed to get greenhouse information from the Catalog after 5 attempts")
                    exit(1)
                
                time.sleep(60)  # wait 60 seconds before retrying

        except Exception as e:
            write_log(f"Error getting greenhouse information from the Catalog: {e}")
            if _ == 4:
                write_log("Failed to get greenhouse information from the Catalog after 5 attempts")
                exit(1)
            
            time.sleep(60)

    mqtt_topics = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topics.append(f"greenhouse_{sensor['greenhouse_id']}/sensor_{sensor['sensor_id']}")

    write_log("")

    for _ in range(5):
        try:
            # create the mqtt client
            client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"ThingSpeakAdaptor_{device_id}", on_message, write_log)
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
        time.sleep(1)
    client.stop()