from datetime import datetime
import random
import math


class Light:
    
    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increse = False
        self.decrease = False

    # ldr sensor is the sensor that measures light intensity
    def getValue(self, elapsed_time):
        time_of_day = datetime.now()
        time_of_day = (time_of_day.hour * 3600 + time_of_day.minute * 60 + time_of_day.second)/3600

        # add some random noise
        noise = random.uniform(-5.0, 5.0)
        
        if time_of_day > 20 or time_of_day < 5:  # simulate night time
            current_light_intensity = 0.0
        else:
            # introduce gradual change
            trend = 100 + 600 * math.sin(math.pi * time_of_day / 24)  # simulate daily light intensity variation
            
            if self.increse:
                trend += 5
            elif self.decrease:
                trend -= 5

            # update the current light intensity value
            current_light_intensity = noise + trend
            
            # ensure light intensity stays within realistic bounds (0 to 1000)
            current_light_intensity = max(0.0, min(1000.0, current_light_intensity))
        
            # check if we have a goal for light intensity, to know when to stop the action
            if self.goal is not None:
            
                # if the command is to increase light intensity, we check if the current light intensity has reached the goal
                if self.increse:
            
                    if current_light_intensity >= self.goal:
                        # stop the action
                        self.increse = False
                        self.goal = None
            
                # if the command is to decrease light intensity, we check if the current light intensity has reached the goal
                elif self.decrease:
            
                    if current_light_intensity <= self.goal:
                        # stop the action
                        self.decrease = False
                        self.goal = None

        return current_light_intensity