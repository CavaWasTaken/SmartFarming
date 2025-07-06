import math
import random
from datetime import datetime

class Humidity:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False
        self.decrease = False
        self.current_humidity = None  # Store the actual current humidity
        self.last_update = None
        self.artificial_offset = 0.0  # Persistent offset from artificial actions (humidifiers/dehumidifiers)
        self.action_strength = 1.5  # How fast humidification/dehumidification changes humidity (% per minute)
        self.decay_rate = 0.08  # How fast artificial effects decay (air circulation rate per minute)

    # DTH22 is the sensor that measures temperature and humidity
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # Initialize if first call
        if self.current_humidity is None or self.last_update is None:
            self.last_update = current_time
            time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
            # Natural humidity variation: higher at dawn/dusk, lower during hot afternoon
            self.current_humidity = 60 + 20 * math.sin(2 * math.pi * (time_of_day - 6) / 24)
            return max(0.0, min(100.0, self.current_humidity))
        
        # Calculate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # Calculate natural humidity trend
        time_of_day = (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) / 3600
        # Natural pattern: higher humidity at dawn/dusk, lower during hot afternoon
        natural_humidity = 60 + 20 * math.sin(2 * math.pi * (time_of_day - 6) / 24)
        
        # Natural air circulation effect (humidity tends to equalize with environment)
        air_circulation_rate = 0.03  # Natural air exchange rate per minute
        natural_humidity -= (self.current_humidity - natural_humidity) * air_circulation_rate * time_delta
        
        # Apply artificial actions (humidifiers/dehumidifiers)
        if self.increase:  # Humidifiers/misters
            self.artificial_offset += self.action_strength * time_delta
        elif self.decrease:  # Dehumidifiers/ventilation
            self.artificial_offset -= self.action_strength * time_delta
        else:
            # Gradually decay artificial effects when no action (air circulation normalizes humidity)
            if self.artificial_offset > 0:
                # Excess humidity dissipates through air circulation
                self.artificial_offset = max(0, self.artificial_offset - self.decay_rate * time_delta)
            elif self.artificial_offset < 0:
                # Dry air gradually returns to ambient levels
                self.artificial_offset = min(0, self.artificial_offset + self.decay_rate * time_delta)
        
        # Combine natural humidity with artificial offset
        target_humidity = natural_humidity + self.artificial_offset
        
        # Air mixing rate (how fast humidity changes towards target)
        mixing_rate = 0.12  # Air humidity changes at 12% per minute towards target
        humidity_diff = target_humidity - self.current_humidity
        self.current_humidity += humidity_diff * mixing_rate * time_delta
        
        # Add some random noise (sensor fluctuations and micro air currents)
        noise = random.uniform(-0.8, 0.8)
        self.current_humidity += noise
        
        # Ensure humidity stays within realistic bounds (0 to 100%)
        self.current_humidity = max(0.0, min(100.0, self.current_humidity))
        
        # Check if we have reached the goal
        if self.goal is not None:
            tolerance = 1.5  # Accept ±1.5% as "reached goal"
            
            if self.increase and self.current_humidity >= (self.goal - tolerance):
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_humidity <= (self.goal + tolerance):
                self.decrease = False
                self.goal = None
        
        return round(self.current_humidity, 2)