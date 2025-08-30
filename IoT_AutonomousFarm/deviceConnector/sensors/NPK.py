import math
import random
from datetime import datetime

class NPK:

    def __init__(self, Sensor):
        self.Sensor = Sensor
        self.goalN = None   # target value for Nitrogen in case of fertilization
        self.goalP = None   # target value for Phosphorus
        self.goalK = None   # target value for Potassium
        self.nitrogenIncrease = False   # flag for nitrogen fertilization
        self.nitrogenDecrease = False   # flag for nitrogen reduction
        self.phosphorusIncrease = False
        self.phosphorusDecrease = False
        self.potassiumIncrease = False
        self.potassiumDecrease = False
        
        self.current_npk = None  # store current NPK values
        self.last_update = None # last time the sensor was updated
        self.artificial_offset = {"N": 0.0, "P": 0.0, "K": 0.0}  # artificial offsets for each nutrient
        
        self.action_strength = {"N": 8.0, "P": 5.0, "K": 6.0}  # how much each action affects the nutrient levels (mg/kg per minute)
        self.decay_rate = {"N": 0.15, "P": 0.08, "K": 0.12}     # how fast nutrients decay over time (mg/kg per minute)
        
    # grove NPK sensor is the sensor that measures NPK values
    def getValue(self, elapsed_time):
        current_time = datetime.now()
        
        # in the first call initialize the NPK values
        if self.current_npk is None or self.last_update is None:
            self.last_update = current_time # update last update time
            # initialize current NPK with some realistic values
            self.current_npk = {
                "N": round(150.0 + random.uniform(-10, 10), 2),  # Nitrogen: varies more
                "P": round(200.0 + random.uniform(-15, 15), 2),  # Phosphorus: more stable
                "K": round(200.0 + random.uniform(-12, 12), 2)   # Potassium: moderate variation
            }
            return self.current_npk
        
        # evaluate time delta in minutes since last update
        time_delta = (current_time - self.last_update).total_seconds() / 60.0
        self.last_update = current_time
        
        # apply artificial actions (fertilizers or nutrient reduction)
        if self.nitrogenIncrease:
            self.artificial_offset["N"] = self.action_strength["N"] * time_delta
        elif self.nitrogenDecrease:
            self.artificial_offset["N"] = -1 * self.action_strength["N"] * time_delta
            
        if self.phosphorusIncrease:
            self.artificial_offset["P"] = self.action_strength["P"] * time_delta
        elif self.phosphorusDecrease:
            self.artificial_offset["P"] = -1 * self.action_strength["P"] * time_delta
            
        if self.potassiumIncrease:
            self.artificial_offset["K"] = self.action_strength["K"] * time_delta
        elif self.potassiumDecrease:
            self.artificial_offset["K"] = -1 * self.action_strength["K"] * time_delta
        
        # apply natural decay of nutrients
        for nutrient in ["N", "P", "K"]:
            # check if any action is active for this nutrient
            is_active = False
            if nutrient == "N":
                is_active = self.nitrogenIncrease or self.nitrogenDecrease
            elif nutrient == "P":
                is_active = self.phosphorusIncrease or self.phosphorusDecrease
            elif nutrient == "K":
                is_active = self.potassiumIncrease or self.potassiumDecrease
            
            if not is_active:
                # apply decay only if no action is active
                decay_amount = self.decay_rate[nutrient] * time_delta
                self.current_npk[nutrient] -= decay_amount
            else:
                # if an action is active, perform the action first
                self.current_npk[nutrient] += self.artificial_offset[nutrient]

        # add random noise to simulate sensor fluctuations
        noise = {
            'N': random.uniform(-0.1, 0.1),
            'P': random.uniform(-0.07, 0.07),
            'K': random.uniform(-0.09, 0.09)
        }
        for nutrient in ["N", "P", "K"]:
            self.current_npk[nutrient] += noise[nutrient]
        
        # ensure NPK values are within realistic limits
        self.current_npk['N'] = max(0.0, min(1000.0, self.current_npk['N']))
        self.current_npk['P'] = max(0.0, min(1000.0, self.current_npk['P']))
        self.current_npk['K'] = max(0.0, min(1000.0, self.current_npk['K']))
        
        # check if any goal has been reached and reset flags
        if self.goalN is not None:
            if self.nitrogenIncrease and self.current_npk['N'] >= self.goalN:
                self.nitrogenIncrease = False
                self.goalN = None
            elif self.nitrogenDecrease and self.current_npk['N'] <= self.goalN:
                self.nitrogenDecrease = False
                self.goalN = None
        
        if self.goalP is not None:
            if self.phosphorusIncrease and self.current_npk['P'] >= self.goalP:
                self.phosphorusIncrease = False
                self.goalP = None
            elif self.phosphorusDecrease and self.current_npk['P'] <= self.goalP:
                self.phosphorusDecrease = False
                self.goalP = None
        
        if self.goalK is not None:
            if self.potassiumIncrease and self.current_npk['K'] >= self.goalK:
                self.potassiumIncrease = False
                self.goalK = None
            elif self.potassiumDecrease and self.current_npk['K'] <= self.goalK:
                self.potassiumDecrease = False
                self.goalK = None
        
        # round the results to two decimal place
        result = {
            'N': round(self.current_npk['N'], 2),
            'P': round(self.current_npk['P'], 2),
            'K': round(self.current_npk['K'], 2)
        }
        
        return result