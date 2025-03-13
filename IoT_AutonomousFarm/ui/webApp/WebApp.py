import time
import json
import requests

from MqttClient import MqttClient

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/WebApp.log", "a") as log_file:
        log_file.write(f"{message}\n")

received_messages = {}

# function for the device connector to receive the needed action and perform it
def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode())  # decode the message received and get the payload
    topic = message.topic    # get the topic of the message received
    write_log(f"Received message: {payload} on topic: {topic}")    # write the message received in the log file
    greenhouse_id = topic.split("/")[0].split("_")[1]    # get the greenhouse id from the topic
    message_type = topic.split("/")[1]  # get the type of the message from the topic
    device_id = topic.split("/")[2].split("_")[1]  # get the device id from the topic
    timestamp = payload["timestamp"]    # get the timestamp of the message received
    
    if device_id not in received_messages[greenhouse_id]:    # if the device id is not in the dictionary, add it
        received_messages[greenhouse_id].update({device_id: []})
    
    if len(received_messages[greenhouse_id][device_id]) > 0:    # if the list of messages received is empty, add the message received
        # if the message received has a timestamp different from the timestamp of the last message received, we are receiving a new transmission, so we can reset the list and save the new
        if received_messages[greenhouse_id][device_id][-1]['timestamp'] != timestamp:
            received_messages[greenhouse_id][device_id].clear()    # clear the list of messages received

    received_messages[greenhouse_id][device_id].append({'message': payload["message"], 'type': message_type, 'timestamp': timestamp})    # add the message received to the dictionary
    
# each time that the device starts, we clear the log file
with open("./logs/WebApp.log", "w") as log_file:
    pass

# read the device_id and mqtt information of the broker from the json file
with open("./WebApp_config.json", "r") as config_fd:
    config = json.load(config_fd)   # read the configuration from the json file
    catalog_url = config["catalog_url"] # read the url of the Catalog
    dataAnalysis_url = config["dataAnalysis_url"] # read the url of the Data Analysis
    device_id = config["device_id"] # read the device_id of the device connector
    mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # read the mqtt broker address
    mqtt_port = config["mqtt_connection"]["mqtt_port"]  # read the mqtt broker port
    keep_alive = config["mqtt_connection"]["keep_alive"]    # read the keep alive time of the mqtt connection

def runApp(user_id, username):
    print(f"\nWelcome {username}")
    response = requests.get(f'{catalog_url}/get_user_greenhouses', params={'user_id': user_id})
    if response.status_code == 200:
        greenhouses = response.json()['greenhouses']
        if len(greenhouses) == 0:
            print("No greenhouses found")
            return
        
    else:
        print(f"Error: {response.reason}")
        return
    
    for greenhouse in greenhouses:
        greenhouse_id = greenhouse['greenhouse_id']
        client.subscribe(f"greenhouse_{greenhouse_id}/action/#")    # subscribe to the topic to get all the actions emitted in that greenhouse by the management components
        client.subscribe(f"greenhouse_{greenhouse_id}/info/#")    # subscribe to the topic to get all the info emitted in that greenhouse by the management components
        client.subscribe(f"greenhouse_{greenhouse_id}/alert/#")    # subscribe to the topic to get all the alerts emitted in that greenhouse by the management components
        received_messages.update({str(greenhouse_id): {}})    # create a dictionary with the greenhouse id as key and an empty dictionary as value

    while True:
        print(f"\nAvaible greenhouses:")
        for greenhouse in greenhouses:
            print(f"{greenhouse['greenhouse_id']} - {greenhouse['name']} - {greenhouse['location']}")
        
        print("\nSelect which greenhouse you want to view:")
        greenhouse_id = input("Enter greenhouse id: ")
        for greenhouse in greenhouses:
            if int(greenhouse['greenhouse_id']) == int(greenhouse_id):
                print(f"\nView {greenhouse['name']} - {greenhouse['location']}:")
            
                response = requests.get(f'{catalog_url}/get_greenhouse_configurations', params={'greenhouse_id': greenhouse['greenhouse_id']})
                if response.status_code == 200:
                    configurations = response.json()
                    if len(configurations) == 0:
                        print("No configurations of the greenhouse found")
                        return
                    
                    print("\nSensors of the greenhouse:")
                    for sensor in configurations['sensors']:
                        print(f"{sensor['sensor_id']} - {sensor['name']} - {sensor['type']} - {sensor['threshold']}")

                    print("\nIoT devices of the greenhouse:")
                    for device in configurations['devices']:
                        print(f"{device['device_id']} - {device['name']} - {device['type']}")

                    print("\nPlants inside the greenhouse:")
                    for plant in configurations['plants']:
                        print(f"{plant['plant_id']} - {plant['name']} - {plant['species']}")
                        print("Desired thresholds:")
                        for dt in plant['desired_thresholds'].items():
                            print(f"{dt[0]}: {dt[1]}")
                        print("\n")

                    print("What do you want to do?")
                    print("1. Change threshold for a sensor")
                    print("2. Add a plant to the greenhouse")
                    print("3. Remove a plant from the greenhouse")
                    print("4. Check IoT devices information")
                    print("5. Ask for a plot")
                    print("6. Manage scheduled events")
                    print("7. Exit")

                    choice = input("Enter your choice: ")
                    if choice == "7":
                        return
                    
                    if choice == "1":
                        print("\nSet threshold for a sensor:")
                        sensor_id = input("Enter sensor id: ")
                        new_threshold = {}
                        for sensor in configurations['sensors']:    # understand the type of the sensor selected and ask the user to insert the new threshold
                            if int(sensor['sensor_id']) == int(sensor_id):
                                print(f"Current threshold: {sensor['threshold']}")
                                if sensor['type'] == "NPK": # if the sensor is a NPK sensor, ask the user to insert the new threshold for each nutrient
                                    for nutrient in ["N", "P", "K"]:
                                        try:
                                            max_threshold = float(input(f"Enter max threshold for {nutrient}: "))
                                            min_threshold = float(input(f"Enter min threshold for {nutrient}: "))
                                            new_threshold.update({nutrient: ({'max': max_threshold, 'min': min_threshold})})   # create a compleate json with the new thresholds
                                        except ValueError:
                                            print("Invalid input")
                                else:
                                    try:
                                        max_threshold = float(input("Enter max threshold: "))
                                        min_threshold = float(input("Enter min threshold: "))
                                        new_threshold = {'max': max_threshold, 'min': min_threshold}
                                    except ValueError:
                                        print("Invalid input")
                                break

                        response = requests.post(f'{catalog_url}/set_sensor_threshold', json={'sensor_id': sensor_id, 'threshold': new_threshold})
                        if response.status_code == 200:
                            print("Threshold set")
                        else:
                            print(f"Error: {response.reason}")
                            return
                        
                    if choice == "2":
                        print("\nAdd a plant to the greenhouse:")
                        response = requests.get(f'{catalog_url}/get_all_plants')
                        if response.status_code == 200:
                            plants = response.json()["plants"]
                            print("Available plants:")
                            for plant in plants:
                                print(f"{plant['plant_id']} - {plant['name']} - {plant['species']} - {plant['desired_thresholds']}")
                            
                            plant_id = input("\nEnter the id of the plant you want to add: ")
                            response = requests.post(f'{catalog_url}/add_plant_to_greenhouse', json={'greenhouse_id': greenhouse['greenhouse_id'], 'plant_id': plant_id})
                            if response.status_code == 200:
                                print("Plant added")
                                configurations["plants"] = response.json()
                            else:
                                print(f"Error: {response.reason}")
                                return
                            
                    if choice == "3":
                        print("\nRemove a plant from the greenhouse: ")
                        plant_id = input("Enter the id of the plant you want to remove:")
                        response = requests.post(f'{catalog_url}/remove_plant_from_greenhouse', json={'greenhouse_id': greenhouse['greenhouse_id'], 'plant_id': plant_id})
                        if response.status_code == 200:
                            print("Plant removed")
                        else:
                            print(f"Error: {response.reason}")
                            return
                    
                    if choice == "4":
                        print("\nCheck IoT devices information:")
                        try:
                            selected_device = int(input("Enter the id of the device you want to check: "))
                            found = False
                            for device in configurations["devices"]:
                                if selected_device == int(device["device_id"]):
                                    found = True
                                    print(f"Selected device: {device['name']} - {device['type']}")
                                    if received_messages.get(greenhouse_id) == None:
                                        print("No messages received yet")
                                        continue
                                    if received_messages.get(greenhouse_id).get(str(selected_device)) == None:
                                        print("No messages received yet")
                                        continue
                                    print(f"Status of the device:")
                                    for message in received_messages.get(greenhouse_id).get(str(selected_device)):
                                        print(f"Message: {message['message']} - Type: {message['type']} - Timestamp: {message['timestamp']}")
                                    break
                            if found == False:
                                print("Device not found")
                                continue
                        except ValueError:
                            print("Invalid input")
                            continue
                        # here i should see an history of the mqtt communications emitted by the selected device

                    if choice == "5":
                        print("\nAsk for a plot:")
                        # select which sensor values from the id of the sensor
                        # decide how many values to show / or a date range
                        # ask the plot to the data analysis rest api

                    if choice == "6":
                        print("\nManage scheduled events:")

                else:
                    print(f"Error: {response.reason}")
                    return
            else:
                print("Invalid greenhouse id")
                continue

# create a client for mqtt
client = MqttClient(mqtt_broker, mqtt_port, keep_alive, f"WebApp_{device_id}", on_message, write_log)    # create a client for mqtt
client.start()

print("WebApp started")
while True:
    print("1. Login")
    print("2. Register")
    print("3. Exit")
    choice = input("Enter your choice: ")
    if choice == "1":
        # username = input("Enter username: ")
        # password = input("Enter password: ")
        username = "Lorenzo"
        password = "WeWillDieForIoT"
        response = requests.post(f'{catalog_url}/login', json={'username': username, 'password': password})
        if response.status_code == 200:
            response = response.json()
            runApp(response['user_id'], response['username'])
            break
        else:
            print(f"Login failed: {response.reason} - {response.text}")
    elif choice == "2":
        username = input("Enter username: ")
        email = input("Enter email: ")
        password = input("Enter password: ")
        response = requests.post(f'{catalog_url}/register', json={'username': username, 'email': email, 'password': password})
        if response.status_code == 200:
            runApp(response['user_id'], response['username'])
            break
        else:
            print(f"Registration failed: {response.reason}")
    elif choice == "3":
        exit(0)
    else:
        print("Invalid choice")

client.stop()   # stop the client for mqtt