import math
import random
from datetime import datetime

class Humidity:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False
        self.decrease = False

    # DTH22 is the sensor that measures temperature and humidity
    def getValue(self, elapsed_time):
        time_of_day = datetime.now()
        time_of_day = (time_of_day.hour * 3600 + time_of_day.minute * 60 + time_of_day.second)/3600

        # simulate daily humidity variation using a sinusoidal pattern
        if time_of_day > 12:
            time_of_day = 24 - time_of_day

        trend = 60 + 20 * math.sin(2 * math.pi * (time_of_day - 16) / 24)

        # add some random noise
        noise = random.uniform(-3.0, 3.0)

        if self.increase:
            trend += 5
        elif self.decrease:
            trend -= 5

        # update the current humidity
        current_humidity = trend + noise

        current_humidity = max(0, min(100, current_humidity))

        # check if we have a goal for humidity, to know when to stop the action
        if self.goal is not None:
            
            # if the command is to increase humidity, we check if the current humidity has reached the goal
            if self.increase:
            
                if current_humidity >= self.goal:
                    # stop the action
                    self.increase = False
                    self.goal = None
            
            # if the command is to decrease humidity, we check if the current humidity has reached the goal
            elif self.decrease:
            
                if current_humidity <= self.goal:
                    # stop the action
                    self.decrease = False
                    self.goal = None

        return current_humidity