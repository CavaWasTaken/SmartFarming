import math
import random
from datetime import datetime

class SoilMoisture:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None    # target soil moisture level for irrigation/drainage    
        self.increase = False   # flag for artificial irrigation (increasing moisture)
        self.decrease = False   # flag for artificial drainage (decreasing moisture)

        self.current_moisture = None    # store the actual current soil moisture
        self.last_update = None # last time the sensor was updated
        self.artificial_offset = 0.0  # artificial offset from irrigation/drainage actions

        self.action_strength = 2.0  # how fast irrigation/drainage changes moisture (% per minute)
        self.decay_rate = 0.05  # how fast artificial effects decay (evaporation/absorption rate per minute)

    # capacitive soil moisture sensor is the sensor that measures soil moisture
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # in the first call initialize the soil moisture
        if self.current_moisture is None or self.last_update is None:
            self.last_update = current_time
            # initialize current moisture with a realistic value
            self.current_moisture = 50.0 + random.uniform(-5, 5)  # 45% to 55% moisture
            return (max(0.0, min(100.0, self.current_moisture)), 2)
        
        # evaluate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time

        # apply artificial actions (irrigation/drainage)
        if self.increase:
            self.artificial_offset = self.action_strength * time_delta
            self.current_moisture += self.artificial_offset
        elif self.decrease:
            self.artificial_offset = -1 * self.action_strength * time_delta
            self.current_moisture += self.artificial_offset
        else:
            # if no action is active, apply decay
            decay_amount = self.decay_rate * time_delta
            self.current_moisture -= decay_amount

        # add some random noise (sensor fluctuations)
        noise = random.uniform(-1.0, 1.0)
        self.current_moisture += noise
        
        # ensure soil moisture stays within realistic bounds (0 to 100%)
        self.current_moisture = max(0.0, min(100.0, self.current_moisture))
        
        # check if we have reached the goal
        if self.goal is not None:
            tolerance = 2.0  # Accept ±2% as "reached goal"
            
            if self.increase and self.current_moisture >= (self.goal - tolerance):
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_moisture <= (self.goal + tolerance):
                self.decrease = False
                self.goal = None
        
        return round(self.current_moisture, 2)