import random

class pH:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        
    # analog pH sensor is the sensor that measures pH values of the soil
    def get_pH_Values(self, elapsed_time):
        start_pH = 7.0  # default pH value for the simulation

        # add some random noise
        noise = random.uniform(-0.1, 0.1)
        # introduce gradual change
        trend = -0.1 * elapsed_time  # small decrease over time
        
        # update the current pH value
        pH = start_pH + noise + trend
        
        # ensure pH stays within realistic bounds (3.0 to 9.0)
        pH = max(3.0, min(9.0, pH))
        
        return pH