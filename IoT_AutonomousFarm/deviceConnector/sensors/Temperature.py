import math
import random
from datetime import datetime

class Temperature:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False
        self.decrease = False
        self.current_temperature = None  # Store the actual current temperature
        self.last_update = None
        self.artificial_offset = 0.0  # Persistent offset from artificial actions
        self.action_strength = 0.5  # How fast the artificial change happens (°C per minute)
        self.decay_rate = 0.02  # How fast artificial effects decay back to natural (per minute)

    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # Initialize if first call
        if self.current_temperature is None or self.last_update is None:
            self.last_update = current_time
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            # Natural temperature variation (15°C at 2 PM, varying ±10°C throughout the day)
            self.current_temperature = 15 + 10 * math.cos(2 * math.pi * (time_of_day - 14) / 24)
            return self.current_temperature
        
        # Calculate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # Calculate natural temperature trend
        time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
        natural_temp = 15 + 10 * math.cos(2 * math.pi * (time_of_day - 14) / 24)
        
        # Apply artificial actions
        if self.increase:
            self.artificial_offset += self.action_strength * time_delta
        elif self.decrease:
            self.artificial_offset -= self.action_strength * time_delta
        else:
            # Gradually decay artificial effects back to natural when no action
            if self.artificial_offset > 0:
                self.artificial_offset = max(0, self.artificial_offset - self.decay_rate * time_delta)
            elif self.artificial_offset < 0:
                self.artificial_offset = min(0, self.artificial_offset + self.decay_rate * time_delta)
        
        # Combine natural temperature with artificial offset
        target_temp = natural_temp + self.artificial_offset
        
        # Gradually move current temperature towards target (thermal inertia)
        temp_change_rate = 0.1  # How fast temperature changes towards target (per minute)
        temp_diff = target_temp - self.current_temperature
        self.current_temperature += temp_diff * temp_change_rate * time_delta
        
        # Add some random noise
        noise = random.uniform(-0.5, 0.5)
        self.current_temperature += noise
        
        # Clamp to realistic bounds
        self.current_temperature = max(-10, min(40, self.current_temperature))
        
        # Check if we have reached the goal
        if self.goal is not None:
            tolerance = 0.5  # Accept ±0.5°C as "reached goal"
            
            if self.increase and self.current_temperature >= (self.goal - tolerance):
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_temperature <= (self.goal + tolerance):
                self.decrease = False
                self.goal = None
        
        return round(self.current_temperature, 2)