from datetime import datetime
import random
import math


class Light:
    
    def __init__(self, Sensor):
        self.Sensor = Sensor

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
            
            # update the current light intensity value
            current_light_intensity = noise + trend
            
            # ensure light intensity stays within realistic bounds (0 to 1000)
            current_light_intensity = max(0.0, min(1000.0, current_light_intensity))
        
        return current_light_intensity

    # start_time = datetime.now()
    # start_time = (start_time.hour * 3600 + start_time.minute * 60 + start_time.second)/3600
    # current_light_intensity = 5 * math.sin(math.pi * start_time / 24)

    # for i in range(72):
    #     time = start_time + i
    #     time = time % 24
    #     print(f"Hour: {time}, {get_LightIntensity_Values(current_light_intensity, time)}")