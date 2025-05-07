import math
import random
from datetime import datetime

class DTH22:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.humidityGoal = None
        self.temperatureGoal = None
        self.humidityIncrease = False
        self.humidityDecrease = False
        self.temperatureIncrease = False
        self.temperatureDecrease = False

    # DTH22 is the sensor that measures temperature and humidity
    def get_DTH22_Humidity(self):
        time_of_day = datetime.now()
        time_of_day = (time_of_day.hour * 3600 + time_of_day.minute * 60 + time_of_day.second)/3600

        # simulate daily humidity variation using a sinusoidal pattern
        if time_of_day > 12:
            time_of_day = 24 - time_of_day

        trend = 60 + 20 * math.sin(2 * math.pi * (time_of_day - 16) / 24)

        # add some random noise
        noise = random.uniform(-3.0, 3.0)

        if self.humidityIncrease:
            trend += 5
        elif self.humidityDecrease:
            trend -= 5

        # update the current humidity
        current_humidity = trend + noise

        current_humidity = max(0, min(100, current_humidity))

        # check if we have a goal for humidity, to know when to stop the action
        if self.humidityGoal is not None:
            
            # if the command is to increase humidity, we check if the current humidity has reached the goal
            if self.humidityIncrease:
            
                if current_humidity >= self.humidityGoal:
                    # stop the action
                    self.humidityIncrease = False
                    self.humidityGoal = None
            
            # if the command is to decrease humidity, we check if the current humidity has reached the goal
            elif self.humidityDecrease:
            
                if current_humidity <= self.humidityGoal:
                    # stop the action
                    self.humidityDecrease = False
                    self.humidityGoal = None

        return current_humidity

    def get_DTH22_Temperature(self):
        time_of_day = datetime.now()
        time_of_day = (time_of_day.hour * 3600 + time_of_day.minute * 60 + time_of_day.second)/3600

        # simulate daily temperature variation using a sinusoidal pattern
        trend = 15 + 10 * math.cos(2 * math.pi * (time_of_day - 14) / 24)

        # add some random noise
        noise = random.uniform(-1.0, 1.0)

        if self.temperatureIncrease:
            trend += 2
        elif self.temperatureDecrease:
            trend -= 2

        # update the current temperature
        current_temperature = trend + noise

        current_temperature = max(-10, min(40, current_temperature))

        # check if we have a goal for temperature, to know when to stop the action
        if self.temperatureGoal is not None:   

            # if the command is to increase temperature, we check if the current temperature has reached the goal
            if self.temperatureIncrease:
            
                if current_temperature >= self.temperatureGoal:
                    # stop the action
                    self.temperatureIncrease = False
                    self.temperatureGoal = None
            
            # if the command is to decrease temperature, we check if the current temperature has reached the goal
            elif self.temperatureDecrease:
            
                if current_temperature <= self.temperatureGoal:
                    # stop the action
                    self.temperatureDecrease = False
                    self.temperatureGoal = None

        return current_temperature

    # from datetime import datetime
    # import matplotlib.pyplot as plt

    # start_time = datetime.now()
    # start_time = (start_time.hour*3600 + start_time.minute*60 + start_time.second)/3600

    # humidities = []
    # temperatures = []
    # for i in range(72):
    #     humidities.append(get_DTH22_Humidity((i+start_time)%24))
    #     temperatures.append(get_DTH22_Temperature((i+start_time)%24))
    #     print(f"Hour {int((i+start_time)%24)}: Humidity={humidities[-1]:.1f}%, Temperature={temperatures[-1]:.1f}C")

    # plt.figure()
    # plt.subplot(2, 1, 1)
    # plt.plot(humidities)
    # plt.title('DTH22 Humidity')
    # plt.ylabel('Humidity (%)')
    # plt.xlabel('Time (hours)')
    # plt.grid()
    # plt.subplot(2, 1, 2)
    # plt.plot(temperatures)
    # plt.title('DTH22 Temperature')
    # plt.ylabel('Temperature (C)')
    # plt.xlabel('Time (hours)')
    # plt.tight_layout()
    # plt.grid()
    # plt.show()