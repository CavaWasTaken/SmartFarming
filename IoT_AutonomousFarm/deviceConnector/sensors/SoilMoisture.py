import math
import random
from datetime import datetime

class SoilMoisture:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False
        self.decrease = False
        self.current_moisture = None  # Store the actual current moisture
        self.last_update = None
        self.artificial_offset = 0.0  # Persistent offset from artificial actions (irrigation/drainage)
        self.action_strength = 2.0  # How fast irrigation/drainage changes moisture (% per minute)
        self.decay_rate = 0.05  # How fast artificial effects decay (evaporation/absorption rate per minute)

    # capacitive soil moisture sensor is the sensor that measures soil moisture
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # Initialize if first call
        if self.current_moisture is None or self.last_update is None:
            self.last_update = current_time
            # Start with moderate soil moisture (varies by time of day due to evaporation)
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            # Natural variation: higher at night (less evaporation), lower during hot afternoon
            self.current_moisture = 45 + 15 * math.cos(2 * math.pi * (time_of_day - 14) / 24)
            return max(0.0, min(100.0, self.current_moisture))
        
        # Calculate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # Calculate natural moisture trend (evaporation during day, stable at night)
        time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
        natural_moisture = 45 + 15 * math.cos(2 * math.pi * (time_of_day - 14) / 24)
        
        # Natural evaporation rate (higher during day, especially afternoon)
        evaporation_rate = 0.1 + 0.05 * math.sin(2 * math.pi * (time_of_day - 12) / 24)
        natural_moisture -= evaporation_rate * time_delta
        
        # Apply artificial actions (irrigation/drainage)
        if self.increase:  # Irrigation
            self.artificial_offset += self.action_strength * time_delta
        elif self.decrease:  # Drainage
            self.artificial_offset -= self.action_strength * time_delta
        else:
            # Gradually decay artificial effects when no action
            if self.artificial_offset > 0:
                # Excess water evaporates/drains naturally
                self.artificial_offset = max(0, self.artificial_offset - self.decay_rate * time_delta)
            elif self.artificial_offset < 0:
                # Soil slowly rehydrates from deeper layers
                self.artificial_offset = min(0, self.artificial_offset + (self.decay_rate * 0.5) * time_delta)
        
        # Combine natural moisture with artificial offset
        target_moisture = natural_moisture + self.artificial_offset
        
        # Soil absorption/drainage rate (how fast moisture changes towards target)
        absorption_rate = 0.15  # Soil changes moisture at 15% per minute towards target
        moisture_diff = target_moisture - self.current_moisture
        self.current_moisture += moisture_diff * absorption_rate * time_delta
        
        # Add some random noise (sensor fluctuations)
        noise = random.uniform(-1.0, 1.0)
        self.current_moisture += noise
        
        # Ensure soil moisture stays within realistic bounds (0 to 100%)
        self.current_moisture = max(0.0, min(100.0, self.current_moisture))
        
        # Check if we have reached the goal
        if self.goal is not None:
            tolerance = 2.0  # Accept ±2% as "reached goal"
            
            if self.increase and self.current_moisture >= (self.goal - tolerance):
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_moisture <= (self.goal + tolerance):
                self.decrease = False
                self.goal = None
        
        return round(self.current_moisture, 2)