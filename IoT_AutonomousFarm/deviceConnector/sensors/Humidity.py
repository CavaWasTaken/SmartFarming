import math
import random
from datetime import datetime

class Humidity:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None    # target humidity for grow lights or dehumidifiers
        self.increase = False   # flag for artificial humidification (humidifiers/misters)
        self.decrease = False   # flag for artificial dehumidification (dehumidifiers/ventilation)

        self.current_humidity = None  # store current humidity level
        self.last_update = None
        self.artificial_offset = 0.0  # artificial offset for humidifiers/dehumidifiers

        self.action_strength = 1.5  # how fast humidification/dehumidification changes humidity (% per minute)
        self.diff = None  # difference between current humidity and natural humidity

    # DTH22 is the sensor that measures temperature and humidity
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # in the first call initialize the humidity level
        if self.current_humidity is None or self.last_update is None:
            self.last_update = current_time
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            # natural humidity pattern based on time of day
            self.current_humidity = 60 + 20 * math.sin(2 * math.pi * (time_of_day - 6) / 24)
            return round(max(0.0, min(100.0, self.current_humidity)), 2)
        
        # evaluate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # apply artificial actions (humidifiers/dehumidifiers)
        if self.increase:
            self.artificial_offset = self.action_strength * time_delta
            self.current_humidity += self.artificial_offset
            self.diff = None
        elif self.decrease:
            self.artificial_offset = -1 * self.action_strength * time_delta
            self.current_humidity += self.artificial_offset
            self.diff = None
        else:
            # if no action is active, apply natural humidity changes
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            natural_humidity = 60 + 20 * math.sin(2 * math.pi * (time_of_day - 6) / 24)
            if self.diff is None:
                # evaluate difference between current humidity and natural humidity
                self.diff = self.current_humidity - natural_humidity

            self.current_humidity = natural_humidity + self.diff

        # add some random noise (sensor fluctuations and micro air currents)
        noise = random.uniform(-0.8, 0.8)
        self.current_humidity += noise
        
        # ensure humidity stays within realistic bounds (0 to 100%)
        self.current_humidity = max(0.0, min(100.0, self.current_humidity))
        
        # check if we have reached the goal
        if self.goal is not None:          
            if self.increase and self.current_humidity >= self.goal:
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_humidity <= self.goal:
                self.decrease = False
                self.goal = None
        
        return round(self.current_humidity, 2)