import random

# grove NPK sensor is the sensor that measures NPK values
def get_NPK_Values(elapsed_time):    
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

    npk = {}
    
    # update the current NPK values
    npk['N'] = start_npk['N'] + noise['N'] + trend['N']
    npk['P'] = start_npk['P'] + noise['P'] + trend['P']
    npk['K'] = start_npk['K'] + noise['K'] + trend['K']

    # ensure NPK values stay within realistic bounds (0 to 1000)
    npk['N'] = max(0.0, min(1000.0, npk['N']))
    npk['P'] = max(0.0, min(1000.0, npk['P']))
    npk['K'] = max(0.0, min(1000.0, npk['K']))
    
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