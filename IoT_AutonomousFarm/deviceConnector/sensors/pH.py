import random

class pH:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False
        self.decrease = False
        
    # analog pH sensor is the sensor that measures pH values of the soil
    def getValue(self, elapsed_time):
        start_pH = 7.0  # default pH value for the simulation

        # add some random noise
        noise = random.uniform(-0.1, 0.1)
        # introduce gradual change
        trend = -0.1 * elapsed_time  # small decrease over time
        
        if self.increase:
            trend += 0.2
        elif self.decrease:
            trend -= 0.2

        # update the current pH value
        pH = start_pH + noise + trend
        
        # ensure pH stays within realistic bounds (3.0 to 9.0)
        pH = max(3.0, min(9.0, pH))

        # check if we have a goal for pH, to know when to stop the action
        if self.goal is not None:
            
            # if the command is to increase pH, we check if the current pH has reached the goal
            if self.increase:
            
                if pH >= self.goal:
                    # stop the action
                    self.increase = False
                    self.goal = None
            
            # if the command is to decrease pH, we check if the current pH has reached the goal
            elif self.decrease:
            
                if pH <= self.goal:
                    # stop the action
                    self.decrease = False
                    self.goal = None
        
        return pH