from datetime import datetime
import random
import math

class Light:
    
    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False  # Fixed typo: was "increse"
        self.decrease = False
        self.current_light = None  # Store the actual current light intensity
        self.last_update = None
        self.artificial_offset = 0.0  # Persistent offset from artificial lighting
        self.action_strength = 15.0  # How fast artificial lights change intensity (lux per minute)
        self.decay_rate = 2.0  # How fast artificial effects decay when lights turn off (lux per minute)

    # ldr sensor is the sensor that measures light intensity
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # Initialize if first call
        if self.current_light is None or self.last_update is None:
            self.last_update = current_time
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            self.current_light = self._calculate_natural_light(time_of_day)
            return max(0.0, min(1000.0, self.current_light))
        
        # Calculate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # Calculate natural light trend
        time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
        natural_light = self._calculate_natural_light(time_of_day)
        
        # Apply artificial actions (grow lights/shading)
        if self.increase:  # Artificial grow lights
            self.artificial_offset += self.action_strength * time_delta
        elif self.decrease:  # Shading/dimming
            self.artificial_offset -= self.action_strength * time_delta
        else:
            # Gradually decay artificial effects when no action
            if self.artificial_offset > 0:
                # Artificial lights fade out gradually (not instant off)
                self.artificial_offset = max(0, self.artificial_offset - self.decay_rate * time_delta)
            elif self.artificial_offset < 0:
                # Shading effects gradually removed
                self.artificial_offset = min(0, self.artificial_offset + self.decay_rate * time_delta)
        
        # Combine natural light with artificial offset
        target_light = natural_light + self.artificial_offset
        
        # Light response rate (how fast light changes towards target)
        response_rate = 0.2  # Light changes at 20% per minute towards target
        light_diff = target_light - self.current_light
        self.current_light += light_diff * response_rate * time_delta
        
        # Add some random noise (sensor fluctuations and cloud shadows)
        noise = random.uniform(-5.0, 5.0)
        self.current_light += noise
        
        # Ensure light intensity stays within realistic bounds (0 to 1000 lux)
        self.current_light = max(0.0, min(1000.0, self.current_light))
        
        # Check if we have reached the goal
        if self.goal is not None:
            tolerance = 10.0  # Accept ±10 lux as "reached goal"
            
            if self.increase and self.current_light >= (self.goal - tolerance):
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_light <= (self.goal + tolerance):
                self.decrease = False
                self.goal = None
        
        return round(self.current_light, 2)
    
    def _calculate_natural_light(self, time_of_day):
        """Calculate natural sunlight based on time of day"""
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