import random

class SoilMoisture:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        
    # capacitive soil moisture sensor is the sensor that measures soil moisture
    def get_SoilMoisture_Values(self, elapsed_time):
        start_soil_moisture = 50.0  # default soil moisture value for the simulation

        # add some random noise
        noise = random.uniform(-2.0, 2.0)
        # introduce gradual decrease
        trend = -elapsed_time  # small decrease over time
        
        # update the current soil moisture value
        soil_moisture = start_soil_moisture + trend + noise
        
        # ensure soil moisture stays within realistic bounds (0 to 100)
        soil_moisture = max(0.0, min(100.0, soil_moisture))
        
        return soil_moisture

    # Example usage
    # start_soil_moisture = 50.0
    # elapsed_time = 0.0
    # for i in range(24):
    #     print(f"Elapsed time: {elapsed_time} hours, Soil moisture: {get_SoilMoisture_Values(start_soil_moisture, elapsed_time)}")
    #     elapsed_time += 1.0