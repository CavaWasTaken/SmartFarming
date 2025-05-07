from datetime import datetime
import random
import math


class Light:
    
    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.lightIncrease = False
        self.lightDecrease = False

    # ldr sensor is the sensor that measures light intensity
    def get_LightIntensity_Values(self):
        time_of_day = datetime.now()
        time_of_day = (time_of_day.hour * 3600 + time_of_day.minute * 60 + time_of_day.second)/3600

        # add some random noise
        noise = random.uniform(-5.0, 5.0)
        
        if time_of_day > 20 or time_of_day < 5:  # simulate night time
            current_light_intensity = 0.0
        else:
            # introduce gradual change
            trend = 100 + 600 * math.sin(math.pi * time_of_day / 24)  # simulate daily light intensity variation
            
            if self.lightIncrease:
                trend += 5
            elif self.lightDecrease:
                trend -= 5

            # update the current light intensity value
            current_light_intensity = noise + trend
            
            # ensure light intensity stays within realistic bounds (0 to 1000)
            current_light_intensity = max(0.0, min(1000.0, current_light_intensity))
        
            # check if we have a goal for light intensity, to know when to stop the action
            if self.goal is not None:
            
                # if the command is to increase light intensity, we check if the current light intensity has reached the goal
                if self.lightIncrease:
            
                    if current_light_intensity >= self.goal:
                        # stop the action
                        self.lightIncrease = False
                        self.goal = None
            
                # if the command is to decrease light intensity, we check if the current light intensity has reached the goal
                elif self.lightDecrease:
            
                    if current_light_intensity <= self.goal:
                        # stop the action
                        self.lightDecrease = False
                        self.goal = None

        return current_light_intensity

    # start_time = datetime.now()
    # start_time = (start_time.hour * 3600 + start_time.minute * 60 + start_time.second)/3600
    # current_light_intensity = 5 * math.sin(math.pi * start_time / 24)

    # for i in range(72):
    #     time = start_time + i
    #     time = time % 24
    #     print(f"Hour: {time}, {get_LightIntensity_Values(current_light_intensity, time)}")