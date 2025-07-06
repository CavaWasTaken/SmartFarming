import math
import random
from datetime import datetime

class Temperature:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None    # target temperature for heating/cooling systems
        self.increase = False   # flag for artificial heating (heaters)
        self.decrease = False   # flag for artificial cooling (cooling systems)

        self.current_temperature = None  # Store the actual current temperature
        self.last_update = None
        self.artificial_offset = 0.0  # Persistent offset from artificial actions

        self.action_strength = 0.5  # How fast the artificial change happens (°C per minute)
        self.diff = None  # difference between current temperature and natural temperature

    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # Initialize if first call
        if self.current_temperature is None or self.last_update is None:
            self.last_update = current_time
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            # natural temperature pattern based on time of day
            self.current_temperature = 15 + 10 * math.cos(2 * math.pi * (time_of_day - 14) / 24)
            return round(self.current_temperature, 2)
        
        # evaluate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
                
        # apply artificial actions
        if self.increase:
            self.artificial_offset = self.action_strength * time_delta
            self.current_temperature += self.artificial_offset
            self.diff = None
        elif self.decrease:
            self.artificial_offset = -1 * self.action_strength * time_delta
            self.current_temperature += self.artificial_offset
            self.diff = None
        else:
            # if no action is active, apply natural temperature changes
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            natural_temperature = 15 + 10 * math.cos(2 * math.pi * (time_of_day - 14) / 24)
            if self.diff is None:
                # evaluate difference between current temperature and natural temperature
                self.diff = self.current_temperature - natural_temperature

            self.current_temperature = natural_temperature + self.diff
        
        # add some random noise
        noise = random.uniform(-0.5, 0.5)
        self.current_temperature += noise
        
        # ensure temperature stays within realistic bounds (-10 to 40°C)
        self.current_temperature = max(-10, min(40, self.current_temperature))
        
        # check if we have reached the goal
        if self.goal is not None:            
            if self.increase and self.current_temperature >= self.goal:
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_temperature <= self.goal:
                self.decrease = False
                self.goal = None
        
        return round(self.current_temperature, 2)