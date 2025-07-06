import math
import random
from datetime import datetime

class pH:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None    # target pH level for soil adjustment
        self.increase = False   # flag for artificial pH increase (lime/alkaline buffers)
        self.decrease = False   # flag for artificial pH decrease (sulfur/acidic buffers)

        self.current_pH = None  # store the actual current pH value
        self.last_update = None # last time the sensor was updated
        self.artificial_offset = 0.0  # artificial offset from pH adjustment actions

        self.action_strength = 0.08  # how fast pH adjustment changes pH (units per minute)
        self.decay_rate = 0.01  # how fast artificial effects decay (buffering back to neutral per minute)

    # analog pH sensor is the sensor that measures pH values of the soil
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # in the first call initialize the soil pH
        if self.current_pH is None or self.last_update is None:
            self.last_update = current_time
            # initialize current pH with a realistic value
            self.current_pH = 6.5 + random.uniform(-0.2, 0.2)
            return round(max(3.0, min(9.0, self.current_pH)), 2)
        
        # evaluate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time

        # apply artificial actions (pH adjusters)
        if self.increase:
            self.artificial_offset = self.action_strength * time_delta
            self.current_pH += self.artificial_offset
        elif self.decrease:
            self.artificial_offset = -1 * self.action_strength * time_delta
            self.current_pH += self.artificial_offset
        else:
            # if no action is active, apply natural decay towards neutral pH
            decay_amount = self.decay_rate * time_delta
            if self.current_pH < 7.0:
                # if pH is below neutral, it tends to increase towards neutral
                self.current_pH += decay_amount
            elif self.current_pH > 7.0:
                # if pH is above neutral, it tends to decrease towards neutral
                self.current_pH -= decay_amount

        # add some random noise (sensor fluctuations and micro-variations)
        noise = random.uniform(-0.05, 0.05)
        self.current_pH += noise
        
        # ensure pH stays within realistic bounds (3.0 to 9.0)
        self.current_pH = max(3.0, min(9.0, self.current_pH))
        
        # check if we have reached the goal
        if self.goal is not None:
            tolerance = 0.1  # Accept ±0.1 pH units as "reached goal"
            
            if self.increase and self.current_pH >= (self.goal - tolerance):
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_pH <= (self.goal + tolerance):
                self.decrease = False
                self.goal = None
        
        return round(self.current_pH, 2)