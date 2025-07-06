from datetime import datetime
import random
import math

class Light:
    
    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None    # target light intensity for grow lights or shading
        self.increase = False  # flag for artificial grow lights
        self.decrease = False   # flag for shading/dimming

        self.current_light = None  # store current light intensity
        self.last_update = None # last time the sensor was updated
        self.artificial_offset = 0.0  # artificial offset for grow lights or shading

        self.action_strength = 15.0  # how much each action affects light intensity (lux per minute)
        self.diff = None # difference between current light and natural light

    # ldr sensor is the sensor that measures light intensity
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # in the first call initialize the light intensity
        if self.current_light is None or self.last_update is None:
            self.last_update = current_time
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            self.current_light = self._calculate_natural_light(time_of_day)
            return round(max(0.0, min(1000.0, self.current_light)), 2)
        
        # evaluate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # apply artificial actions (grow lights/shading)
        if self.increase:
            self.artificial_offset = self.action_strength * time_delta
            self.current_light += self.artificial_offset
            self.diff = None # reset diff since we are actively changing light
        elif self.decrease:
            self.artificial_offset = -1 * self.action_strength * time_delta
            self.current_light += self.artificial_offset
            self.diff = None  # reset diff since we are actively changing light
        else:
            # if no action is active, apply natural light changes
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            natural_light = self._calculate_natural_light(time_of_day)
            if self.diff is None:
                # evaluate difference between current light and natural light
                self.diff = self.current_light - natural_light

            self.current_light = natural_light + self.diff

        # add random noise to simulate sensor fluctuations
        noise = random.uniform(-5.0, 5.0)
        self.current_light += noise
        
        # ensure light intensity stays within realistic bounds (0 to 1000 lux)
        self.current_light = max(0.0, min(1000.0, self.current_light))
        
        # check if any goal has been reached and reset flags
        if self.goal is not None:            
            if self.increase and self.current_light >= self.goal:
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_light <= self.goal:
                self.decrease = False
                self.goal = None
        
        return round(self.current_light, 2)
    
    def _calculate_natural_light(self, time_of_day):
        if time_of_day < 5 or time_of_day > 20:  # Night time (8 PM to 5 AM)
            return 0.0
        elif time_of_day < 6:  # Dawn (5-6 AM)
            # Gradual sunrise
            progress = (time_of_day - 5) / 1  # 0 to 1 over 1 hour
            return 50 * math.sin(math.pi * progress / 2)  # Gradual increase to ~50 lux
        elif time_of_day < 7:  # Early morning (6-7 AM)
            progress = (time_of_day - 6) / 1
            return 50 + 150 * math.sin(math.pi * progress / 2)  # 50 to 200 lux
        elif time_of_day < 9:  # Morning (7-9 AM)
            progress = (time_of_day - 7) / 2
            return 200 + 300 * math.sin(math.pi * progress / 2)  # 200 to 500 lux
        elif time_of_day < 16:  # Daytime (9 AM to 4 PM)
            # Peak sunlight with realistic variation
            mid_day = 12.5
            peak_intensity = 800 + 100 * math.cos(2 * math.pi * (time_of_day - mid_day) / 7)
            # Add cloud simulation
            cloud_factor = 0.8 + 0.2 * math.sin(2 * math.pi * time_of_day / 3)  # Varying clouds
            return peak_intensity * cloud_factor
        elif time_of_day < 18:  # Late afternoon (4-6 PM)
            progress = (18 - time_of_day) / 2
            return 200 + 300 * math.sin(math.pi * progress / 2)  # 500 to 200 lux
        elif time_of_day < 19:  # Evening (6-7 PM)
            progress = (19 - time_of_day) / 1
            return 50 + 150 * math.sin(math.pi * progress / 2)  # 200 to 50 lux
        else:  # Dusk (7-8 PM)
            progress = (20 - time_of_day) / 1
            return 50 * math.sin(math.pi * progress / 2)  # 50 to 0 lux