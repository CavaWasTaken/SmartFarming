import random

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
        
    # grove NPK sensor is the sensor that measures NPK values
    def get_NPK_Values(self, elapsed_time):    
        start_npk = {"N": 150.0, "P": 200.0, "K": 200.0}

        # add some random noise
        noise = {
            'N': random.uniform(-2.0, 2.0),
            'P': random.uniform(-2.0, 2.0),
            'K': random.uniform(-2.0, 2.0)
        }
        # introduce gradual decrease
        trend = {
            'N': -5 * elapsed_time,  # small decrease over time
            'P': -5 * elapsed_time,  # small decrease over time
            'K': -5 * elapsed_time   # small decrease over time
        }

        if self.nitrogenIncrease:
            trend['N'] += 5
        elif self.nitrogenDecrease:
            trend['N'] -= 5
        if self.phosphorusIncrease:
            trend['P'] += 5
        elif self.phosphorusDecrease:
            trend['P'] -= 5
        if self.potassiumIncrease:
            trend['K'] += 5
        elif self.potassiumDecrease:
            trend['K'] -= 5

        npk = {}
        
        # update the current NPK values
        npk['N'] = start_npk['N'] + noise['N'] + trend['N']
        npk['P'] = start_npk['P'] + noise['P'] + trend['P']
        npk['K'] = start_npk['K'] + noise['K'] + trend['K']

        # ensure NPK values stay within realistic bounds (0 to 1000)
        npk['N'] = max(0.0, min(1000.0, npk['N']))
        npk['P'] = max(0.0, min(1000.0, npk['P']))
        npk['K'] = max(0.0, min(1000.0, npk['K']))

        # check if we have a goal for NPK, to know when to stop the action
        if self.goalN is not None:
        
            # if the command is to increase nitrogen, we check if the current nitrogen has reached the goal
            if self.nitrogenIncrease:
        
                if npk['N'] >= self.goalN:
                    # stop the action
                    self.nitrogenIncrease = False
                    self.goalN = None
        
            # if the command is to decrease nitrogen, we check if the current nitrogen has reached the goal
            elif self.nitrogenDecrease:
        
                if npk['N'] <= self.goalN:
                    # stop the action
                    self.nitrogenDecrease = False
                    self.goalN = None
        
        if self.goalP is not None:
        
            # if the command is to increase phosphorus, we check if the current phosphorus has reached the goal
            if self.phosphorusIncrease:
        
                if npk['P'] >= self.goalP:
                    # stop the action
                    self.phosphorusIncrease = False
                    self.goalP = None
        
            # if the command is to decrease phosphorus, we check if the current phosphorus has reached the goal
            elif self.phosphorusDecrease:
        
                if npk['P'] <= self.goalP:
                    # stop the action
                    self.phosphorusDecrease = False
                    self.goalP = None
        
        if self.goalK is not None:
        
            # if the command is to increase potassium, we check if the current potassium has reached the goal
            if self.potassiumIncrease:
        
                if npk['K'] >= self.goalK:
                    # stop the action
                    self.potassiumIncrease = False
                    self.goalK = None
        
            # if the command is to decrease potassium, we check if the current potassium has reached the goal
            elif self.potassiumDecrease:
        
                if npk['K'] <= self.goalK:
                    # stop the action
                    self.potassiumDecrease = False
                    self.goalK = None
        
        return npk

    # start_time = time.time()
    # starting_hour = datetime.datetime.now().hour
    # current_npk = {"N": 500.0, "P": 500.0, "K": 500.0}  # default NPK values for the simulation

    # npk_values = []
    # for i in range(72):
    #     npk_values.append(get_NPK_Values(current_npk.copy(), i))
    #     print(f"Hour {(i+starting_hour)%24}: NPK={npk_values[-1]}")

    # plt.figure()
    # plt.subplot(3, 1, 1)
    # plt.plot([npk['N'] for npk in npk_values])
    # plt.title('NPK Nitrogen')
    # plt.ylabel('N (%)')
    # plt.xlabel('Time (hours)')
    # plt.grid()
    # plt.subplot(3, 1, 2)
    # plt.plot([npk['P'] for npk in npk_values])
    # plt.title('NPK Phosphorus')
    # plt.ylabel('P (%)')
    # plt.xlabel('Time (hours)')
    # plt.grid()
    # plt.subplot(3, 1, 3)
    # plt.plot([npk['K'] for npk in npk_values])
    # plt.title('NPK Potassium')
    # plt.ylabel('K (%)')
    # plt.xlabel('Time (hours)')
    # plt.tight_layout()
    # plt.grid()
    # plt.show()