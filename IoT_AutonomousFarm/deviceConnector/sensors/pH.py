import math
import random
from datetime import datetime

class pH:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goal = None
        self.increase = False
        self.decrease = False
        self.current_pH = None  # Store the actual current pH
        self.last_update = None
        self.artificial_offset = 0.0  # Persistent offset from artificial actions (pH buffers/acids)
        self.action_strength = 0.08  # How fast pH adjustment changes pH (units per minute)
        self.decay_rate = 0.01  # How fast artificial effects decay (buffering back to neutral per minute)

    # analog pH sensor is the sensor that measures pH values of the soil
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # Initialize if first call
        if self.current_pH is None or self.last_update is None:
            self.last_update = current_time
            # Start with slightly acidic soil pH (typical for agricultural soil)
            self.current_pH = 6.5 + random.uniform(-0.2, 0.2)
            return max(3.0, min(9.0, self.current_pH))
        
        # Calculate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # Natural pH tends to be slightly acidic (6.5) due to organic matter decomposition
        natural_pH = 6.5
        
        # Natural buffering - soil slowly returns to its natural pH
        buffering_rate = 0.005  # Very slow natural buffering per minute
        ph_diff_from_natural = self.current_pH - natural_pH
        natural_buffering = -ph_diff_from_natural * buffering_rate * time_delta
        
        # Apply artificial actions (pH adjusters)
        if self.increase:  # Adding lime/alkaline buffers
            self.artificial_offset += self.action_strength * time_delta
        elif self.decrease:  # Adding sulfur/acidic buffers
            self.artificial_offset -= self.action_strength * time_delta
        else:
            # Gradually decay artificial effects when no action (soil buffering)
            if self.artificial_offset > 0:
                # Alkaline additives gradually neutralize
                self.artificial_offset = max(0, self.artificial_offset - self.decay_rate * time_delta)
            elif self.artificial_offset < 0:
                # Acidic additives gradually neutralize
                self.artificial_offset = min(0, self.artificial_offset + self.decay_rate * time_delta)
        
        # Calculate target pH
        target_pH = natural_pH + self.artificial_offset + natural_buffering
        
        # Soil pH change rate (how fast pH changes towards target)
        # pH changes very slowly in soil due to buffering capacity
        ph_change_rate = 0.05  # Soil pH changes at 5% per minute towards target
        ph_diff = target_pH - self.current_pH
        self.current_pH += ph_diff * ph_change_rate * time_delta
        
        # Add some random noise (sensor fluctuations and micro-variations)
        noise = random.uniform(-0.05, 0.05)
        self.current_pH += noise
        
        # Ensure pH stays within realistic bounds (3.0 to 9.0)
        self.current_pH = max(3.0, min(9.0, self.current_pH))
        
        # Check if we have reached the goal
        if self.goal is not None:
            tolerance = 0.1  # Accept ±0.1 pH units as "reached goal"
            
            if self.increase and self.current_pH >= (self.goal - tolerance):
                self.increase = False
                self.goal = None
            elif self.decrease and self.current_pH <= (self.goal + tolerance):
                self.decrease = False
                self.goal = None
        
        return round(self.current_pH, 2)