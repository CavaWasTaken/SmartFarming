import json
import paho.mqtt.client as PahoMQTT
from MqttSub import MqttSubscriber
import requests
import cherrypy

# each time that the device starts, we clear the log file
with open("./logs/ThingSpeakAdaptor.log", "w") as log_file:
    pass


# read the device_id and mqtt information of the broker from the json file
with open("./ThingSpeakAdaptor_config.json", "r") as config_fd:
    config = json.load(config_fd)
    catalog_url = config["catalog_url"]
    device_id = config["device_id"]
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]
    mqtt_port = config["mqtt_connection"]["mqtt_port"]
    keep_alive = config["mqtt_connection"]["keep_alive"]
    write_url = config["write_url"]
    read_url = config["read_url"]

thingSpeak_config = {}  # dictionary containing the configuration of the ThingSpeak channel

def handle_message(topic, sensor_type, val):
    with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
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
            log_file.write(f"Missing values for fields: {missing_fields}\n")
            return
        
        payload = { # payload to send to the ThingSpeak API
            "api_key": thingSpeak_config["write_api_key"],   # write api key of the channel
            **{f"field{i+1}": value for i, value in enumerate(fields.values())}    # add the values of the fields to the payload
        }

        response = requests.post(write_url, data=payload)    # send the request to the ThingSpeak API
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:    
            if response.status_code == 200:
                log_file.write(f"Successfully updated ThingSpeak channel {thingSpeak_config['channel_id']} with payload: {payload}\n")
            else:
                log_file.write(f"Failed to update ThingSpeak. Response: {response.reason}\n")

        # reset the json to empty strings
        for key in fields.keys():
            fields[key] = ""

class ThingSpeakAdaptor(MqttSubscriber):
    def __init__(self, broker, port, topics):
        super().__init__(broker, port, topics)

    def on_message(self, client, userdata, msg):    # when a new message of one of the topic where it is subscribed arrives to the broker
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:  # print all the messages received on a log file
            message = json.loads(msg.payload.decode())  # decode the message from JSON format, so we can access the values of the message as a dictionary
            log_file.write(f"Received: {message}\n")
            log_file.flush()
            for topic in mqtt_topic:
                if message["bn"] == topic:
                    message = message["e"]
                    sensor_type = message["n"]
                    val = message["v"]
                    handle_message(topic, sensor_type, val)
                    break   # if the message is processed, break the loop

def get_field_data(field, n):
    with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
        log_file.write(f"Request to get last {n} values of field '{field}'\n")
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

                    log_file.write(f"Successfully fetched {len(values)} values of field '{field}': {values}\n")
                    return {"values": values}
                else:
                    log_file.write(f"Failed to fetch data from ThingSpeak. Response: {response.reason}\n")
                    raise cherrypy.HTTPError(status=500, message='Failed to fetch data from ThingSpeak')
            else:
                log_file.write(f"Failed to fetch data from ThingSpeak. Field '{field}' not found in the channel\n")
                raise cherrypy.HTTPError(status=404, message='Field not found in the channel')
        else:
            log_file.write(f"Failed to fetch data from ThingSpeak. Response: {response.reason}\n")
            raise cherrypy.HTTPError(status=500, message='Failed to fetch data from ThingSpeak')

# REST API exposed by the ThingSpeak Adaptor
class ThingSpeakAdaptorRestAPI(object):
    exposed = True

    def __init__(self, thingSpeak_connection):
        self.thingSpeak_connection = thingSpeak_connection

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        elif uri[0] == "get_field_data":
            return get_field_data(params['field'], params['n'])
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

    # instead of reading the topics like this, i would like to change it and make that the microservices build the topics by itself by knowing the greenhouse where it is connected and the plant that it contains
    response = requests.get(f"{catalog_url}/get_sensors", params={'device_id': device_id, 'device_name': 'ThingSpeakAdaptor'})    # get the device information from the catalog
    if response.status_code == 200:
        sensors = response.json()["sensors"]    # sensors is a list of dictionaries, each correspond to a sensor of the greenhouse
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Received {len(sensors)} sensors: {sensors}\n")
    else:
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Failed to get sensors from the Catalog\nResponse: {response.reason}\n")    # in case of error, write the reason of the error in the log file
            exit(1) # if the request fails, the device connector stops
        
    response = requests.get(f"{catalog_url}/get_greenhouse_info", params={'greenhouse_id': sensors[0]["greenhouse_id"], 'device_id': device_id})    # get the greenhouse information from the catalog
    if response.status_code == 200:
        greenhouse_info = response.json()    # greenhouse_info is a dictionary with the information of the greenhouse
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Received greenhouse information: {greenhouse_info}\n")
            thingSpeak_config = greenhouse_info["thingSpeak_config"]
    else:
        with open("./logs/ThingSpeakAdaptor.log", "a") as log_file:
            log_file.write(f"Failed to get greenhouse information from the Catalog\nResponse: {response.reason}\n")
            exit(1)


    mqtt_topic = [] # array of topics where the microservice is subscribed
    for sensor in sensors:  # for each sensor of interest for the microservice, add the topic to the list of topics
        mqtt_topic.append(f"greenhouse_{sensor['greenhouse_id']}/sensor_{sensor['sensor_id']}")

    # the mqtt subscriber subscribes to the topics
    subscriber = ThingSpeakAdaptor(mqtt_broker, mqtt_port, mqtt_topic)
    subscriber.connect()