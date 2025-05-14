import random

class SoilMoisture:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False
        self.decrease = False
        
    # capacitive soil moisture sensor is the sensor that measures soil moisture
    def getValue(self, elapsed_time):
        start_soil_moisture = 50.0  # default soil moisture value for the simulation

        # add some random noise
        noise = random.uniform(-2.0, 2.0)
        # introduce gradual decrease
        trend = -elapsed_time  # small decrease over time

        if self.increase:
            trend += 5
        elif self.decrease:
            trend -= 5
        
        # update the current soil moisture value
        soil_moisture = start_soil_moisture + trend + noise
        
        # ensure soil moisture stays within realistic bounds (0 to 100)
        soil_moisture = max(0.0, min(100.0, soil_moisture))

        # check if we have a goal for soil moisture, to know when to stop the action
        if self.goal is not None:
            
            # if the command is to increase soil moisture, we check if the current soil moisture has reached the goal
            if self.increase:
            
                if soil_moisture >= self.goal:
                    # stop the action
                    self.increase = False
                    self.goal = None
            
            # if the command is to decrease soil moisture, we check if the current soil moisture has reached the goal
            elif self.decrease:
            
                if soil_moisture <= self.goal:
                    # stop the action
                    self.decrease = False
                    self.goal = None
        
        return soil_moisture

    # Example usage
    # start_soil_moisture = 50.0
    # elapsed_time = 0.0
    # for i in range(24):
    #     print(f"Elapsed time: {elapsed_time} hours, Soil moisture: {get_SoilMoisture_Values(start_soil_moisture, elapsed_time)}")
    #     elapsed_time += 1.0