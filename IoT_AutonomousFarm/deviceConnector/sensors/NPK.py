import math
import random
from datetime import datetime

class NPK:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goalN = None
        self.goalP = None
        self.goalK = None
        self.nitrogenIncrease = False
        self.nitrogenDecrease = False
        self.phosphorusIncrease = False
        self.phosphorusDecrease = False
        self.potassiumIncrease = False
        self.potassiumDecrease = False
        
        # Current state tracking
        self.current_npk = None  # Store actual current NPK values
        self.last_update = None
        self.artificial_offset = {"N": 0.0, "P": 0.0, "K": 0.0}  # Persistent offset from fertilizers
        
        # Action parameters for each nutrient
        self.action_strength = {"N": 8.0, "P": 5.0, "K": 6.0}  # How fast fertilizers add nutrients (mg/kg per minute)
        self.decay_rate = {"N": 0.15, "P": 0.08, "K": 0.12}     # How fast nutrients are consumed by plants (per minute)
        
    # grove NPK sensor is the sensor that measures NPK values
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # Initialize if first call
        if self.current_npk is None or self.last_update is None:
            self.last_update = current_time
            # Start with moderate NPK levels (typical agricultural soil)
            self.current_npk = {
                "N": 150.0 + random.uniform(-10, 10),  # Nitrogen: varies more
                "P": 200.0 + random.uniform(-15, 15),  # Phosphorus: more stable
                "K": 200.0 + random.uniform(-12, 12)   # Potassium: moderate variation
            }
            return self.current_npk.copy()
        
        # Calculate time elapsed since last update (in minutes)
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # Calculate natural nutrient depletion (plant consumption)
        natural_npk = {
            "N": 150.0,  # Base nitrogen level
            "P": 200.0,  # Base phosphorus level  
            "K": 200.0   # Base potassium level
        }
        
        # Different consumption rates for each nutrient
        consumption_rates = {
            "N": 0.3,   # Nitrogen consumed fastest (mobile nutrient)
            "P": 0.1,   # Phosphorus consumed slowly (less mobile)
            "K": 0.2    # Potassium moderate consumption
        }
        
        # Apply plant consumption over time
        for nutrient in ["N", "P", "K"]:
            natural_depletion = consumption_rates[nutrient] * time_delta
            natural_npk[nutrient] -= natural_depletion
        
        # Apply artificial actions (fertilizers)
        if self.nitrogenIncrease:
            self.artificial_offset["N"] += self.action_strength["N"] * time_delta
        elif self.nitrogenDecrease:
            self.artificial_offset["N"] -= self.action_strength["N"] * time_delta
            
        if self.phosphorusIncrease:
            self.artificial_offset["P"] += self.action_strength["P"] * time_delta
        elif self.phosphorusDecrease:
            self.artificial_offset["P"] -= self.action_strength["P"] * time_delta
            
        if self.potassiumIncrease:
            self.artificial_offset["K"] += self.action_strength["K"] * time_delta
        elif self.potassiumDecrease:
            self.artificial_offset["K"] -= self.action_strength["K"] * time_delta
        
        # Natural decay of artificial effects (nutrient consumption/leaching)
        for nutrient in ["N", "P", "K"]:
            if not (getattr(self, f"{nutrient.lower()}{'nitrogen' if nutrient == 'N' else nutrient.lower()}Increase") or 
                   getattr(self, f"{nutrient.lower()}{'nitrogen' if nutrient == 'N' else nutrient.lower()}Decrease")):
                if self.artificial_offset[nutrient] > 0:
                    # Excess nutrients consumed by plants or leached
                    self.artificial_offset[nutrient] = max(0, self.artificial_offset[nutrient] - 
                                                          self.decay_rate[nutrient] * time_delta)
                elif self.artificial_offset[nutrient] < 0:
                    # Soil slowly recovers nutrients from organic matter decomposition
                    recovery_rate = self.decay_rate[nutrient] * 0.3
                    self.artificial_offset[nutrient] = min(0, self.artificial_offset[nutrient] + 
                                                          recovery_rate * time_delta)
        
        # Calculate target NPK levels
        target_npk = {}
        for nutrient in ["N", "P", "K"]:
            target_npk[nutrient] = natural_npk[nutrient] + self.artificial_offset[nutrient]
        
        # Soil nutrient availability rate (how fast nutrients become available)
        availability_rates = {
            "N": 0.08,  # Nitrogen becomes available quickly
            "P": 0.04,  # Phosphorus released slowly
            "K": 0.06   # Potassium moderate availability
        }
        
        # Update current NPK towards target
        for nutrient in ["N", "P", "K"]:
            npk_diff = target_npk[nutrient] - self.current_npk[nutrient]
            self.current_npk[nutrient] += npk_diff * availability_rates[nutrient] * time_delta
        
        # Add random noise (sensor fluctuations and soil heterogeneity)
        noise = {
            'N': random.uniform(-2.0, 2.0),
            'P': random.uniform(-1.5, 1.5),
            'K': random.uniform(-1.8, 1.8)
        }
        
        for nutrient in ["N", "P", "K"]:
            self.current_npk[nutrient] += noise[nutrient]
        
        # Ensure NPK values stay within realistic bounds (0 to 1000 mg/kg)
        self.current_npk['N'] = max(0.0, min(1000.0, self.current_npk['N']))
        self.current_npk['P'] = max(0.0, min(1000.0, self.current_npk['P']))
        self.current_npk['K'] = max(0.0, min(1000.0, self.current_npk['K']))
        
        # Check if we have reached goals
        tolerance = {"N": 5.0, "P": 3.0, "K": 4.0}  # Different tolerances for each nutrient
        
        if self.goalN is not None:
            if self.nitrogenIncrease and self.current_npk['N'] >= (self.goalN - tolerance["N"]):
                self.nitrogenIncrease = False
                self.goalN = None
            elif self.nitrogenDecrease and self.current_npk['N'] <= (self.goalN + tolerance["N"]):
                self.nitrogenDecrease = False
                self.goalN = None
        
        if self.goalP is not None:
            if self.phosphorusIncrease and self.current_npk['P'] >= (self.goalP - tolerance["P"]):
                self.phosphorusIncrease = False
                self.goalP = None
            elif self.phosphorusDecrease and self.current_npk['P'] <= (self.goalP + tolerance["P"]):
                self.phosphorusDecrease = False
                self.goalP = None
        
        if self.goalK is not None:
            if self.potassiumIncrease and self.current_npk['K'] >= (self.goalK - tolerance["K"]):
                self.potassiumIncrease = False
                self.goalK = None
            elif self.potassiumDecrease and self.current_npk['K'] <= (self.goalK + tolerance["K"]):
                self.potassiumDecrease = False
                self.goalK = None
        
        # Round values for realistic sensor precision
        result = {
            'N': round(self.current_npk['N'], 1),
            'P': round(self.current_npk['P'], 1),
            'K': round(self.current_npk['K'], 1)
        }
        
        return result