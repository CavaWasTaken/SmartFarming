import math
import random
from datetime import datetime

class Temperature:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False
        self.decrease = False

    def getValue(self, elapsed_time):
        time_of_day = datetime.now()
        time_of_day = (time_of_day.hour * 3600 + time_of_day.minute * 60 + time_of_day.second)/3600

        # simulate daily temperature variation using a sinusoidal pattern
        trend = 15 + 10 * math.cos(2 * math.pi * (time_of_day - 14) / 24)

        # add some random noise
        noise = random.uniform(-1.0, 1.0)

        if self.increase:
            trend += 2
        elif self.decrease:
            trend -= 2

        # update the current temperature
        current_temperature = trend + noise

        current_temperature = max(-10, min(40, current_temperature))

        # check if we have a goal for temperature, to know when to stop the action
        if self.goal is not None:   

            # if the command is to increase temperature, we check if the current temperature has reached the goal
            if self.increase:
            
                if current_temperature >= self.goal:
                    # stop the action
                    self.increase = False
                    self.goal = None
            
            # if the command is to decrease temperature, we check if the current temperature has reached the goal
            elif self.decrease:
            
                if current_temperature <= self.goal:
                    # stop the action
                    self.decrease = False
                    self.goal = None

        return current_temperature