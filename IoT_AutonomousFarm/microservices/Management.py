import requests

# normalized evaluation of how far the value is from the interval
def Severity(distance, domain):
    max = domain["max"]
    min = domain["min"]
    severity = distance / max - min
    return severity
    
# function that checks if the value is in the accepted range
def Is_inside(min_treshold, val, max_treshold):
    return min_treshold <= val <= max_treshold
    
# function that checks if an action is needed, and updates the user
def Check_value(dataAnalysis_url, sensor_id, sensor_type, val, unit, timestamp, min_treshold, max_treshold, expected_value, domains, write_log, SendAlert, SendInfo, SendAction): 
    # get the value that we expect from that sensor in the next reading
    response = requests.get(f"{dataAnalysis_url}/get_next_value", params={'sensor_id': sensor_id, 'sensor_type': sensor_type, 'timestamp': timestamp})    # get the expected value from the data analysis
    if response.status_code == 200:
        expected_val = response.json()["next_value"]
        if expected_val is not None:    # the data analysis has returned a prediction
            write_log(f"Next expected value of sensor_{sensor_id} ({sensor_type}): {expected_val}")   # THIS INFO CAN BE SENT TO THE UI
            SendInfo(f"Next expected value of sensor_{sensor_id} ({sensor_type}): {expected_val}")
        else:   # if the response is None, we consider the prediction lost
            # send notification to the user through the telegram bot
            write_log(f"WARNING: Next expected value of sensor_{sensor_id} ({sensor_type}) not found")    # ALERT TO BE SENT TO THE UI
            SendAlert(f"WARNING: Next expected value of sensor_{sensor_id} ({sensor_type}) not found")
            return  # terminate the function
    else:   # if the request fails, we consider the prediction lost
        write_log(f"WARNING: Impossible to get the next expected value of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis\t(Response: {response.reason})")    # ALERT TO BE SENT TO THE UI
        SendAlert(f"WARNING: Impossible to get the next expected value of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis\t(Response: {response.reason})")
        return

    # starts to perform decision making after two values are received from the sensor
    if expected_value[sensor_id] is None:  # if it is the first value received from this sensor, just update the expected value and terminate the function
        expected_value[sensor_id] = expected_val   # update the next expected value
        write_log(f"Wait to see another value to start the decision making for sensor_{sensor_id} ({sensor_type})")
        return
    
    if sensor_type == "NPK":    # if the sensor is NPK, we must handle a dictionary of values
        for nutrient in ["N", "P", "K"]:
            nutrient_val = val[nutrient]
            expected_nutrient_val = expected_val[nutrient]
            # we use the previous expected value to check if the measured value is unexpected
            if abs(nutrient_val - expected_nutrient_val) > 5:    # if the value was unexpected, alert the user and wait for the next value
                write_log(f"WARNING: The measured value {nutrient_val} of sensor_{sensor_id} ({sensor_type} - {nutrient}) is unexpected. (Expected value: {expected_nutrient_val})\tWaiting for the next value")   # ALERT TO BE SENT TO THE UI
                SendAlert(f"WARNING: The measured value {nutrient_val} of sensor_{sensor_id} ({sensor_type} - {nutrient}) is unexpected. (Expected value: {expected_nutrient_val})\tWaiting for the next value")
            else:   # if the value was expected
                if not Is_inside(min_treshold[nutrient], nutrient_val, max_treshold[nutrient]):  # if the value is outside the range of accepted values, alert the user
                    write_log(f"WARNING: The measured value {nutrient_val} {unit} of sensor_{sensor_id} ({sensor_type} - {nutrient}) went outside the range [{min_treshold}, {max_treshold}]")    # ALERT TO BE SENT TO THE UI
                    SendAlert(f"WARNING: The measured value {nutrient_val} {unit} of sensor_{sensor_id} ({sensor_type} - {nutrient}) went outside the range [{min_treshold}, {max_treshold}]")

                    # evaluate how far the value is from the interval
                    if nutrient_val > max_treshold[nutrient]:  # if the value is higher than the max treshold
                        distance = (nutrient_val - max_treshold[nutrient])
                    else:   # nutrient_val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_t
                        distance = (min_treshold[nutrient] - nutrient_val)
                    severity = Severity(distance, domains[sensor_id])   # evaluate the severity of the problem

                    if severity is None:
                        write_log(f"WARNING: Failed to evaluate the severity of the problem for sensor_{sensor_id} ({sensor_type} - {nutrient})") # ALERT TO BE SENT TO THE UI
                        SendAlert(f"WARNING: Failed to evaluate the severity of the problem for sensor_{sensor_id} ({sensor_type} - {nutrient})")
                        return

                    if severity > 0.5:  # if the severity is high enough, action is needed
                        write_log(f"WARNING: The measured value {nutrient_val} is highly outside the range (Severity: {severity}). Action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")  # ALERT TO BE SENT TO THE UI
                        SendAction(f"WARNING: The measured value {nutrient_val} is highly outside the range (Severity: {severity}). Action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")
                    else:   # if the severity isn't high enough
                        # get the updated mean
                        response = requests.get(f"{dataAnalysis_url}/get_mean_value", params={'sensor_id': sensor_id, 'sensor_type':sensor_type, 'timestamp': timestamp})    # get the mean value from the data analysis
                        if response.status_code == 200:
                            mean_value = response.json()["mean_value"].get(nutrient)
                            if mean_value is not None:
                                write_log(f"Mean value of sensor_{sensor_id} ({sensor_type} - {nutrient}): {mean_value}")   # THIS INFO CAN BE SENT TO THE UI
                                SendInfo(f"Mean value of sensor_{sensor_id} ({sensor_type} - {nutrient}): {mean_value}")
                            else:   # if the response is None, we consider the evaluation lost
                                write_log(f"WARNING: Failed to get mean value of sensor_{sensor_id} ({sensor_type} - {nutrient}) from the DataAnalysis")   # ALERT TO BE SENT TO THE UI
                                SendAlert(f"WARNING: Failed to get mean value of sensor_{sensor_id} ({sensor_type} - {nutrient}) from the DataAnalysis")
                                return
                            if not Is_inside(min_treshold[nutrient], mean_value, max_treshold[nutrient]):    # if the mean value is outside the range, action is needed
                                # take preventive action by following the expected severity
                                write_log(f"WARNING: The measured value {nutrient_val} and the mean value {mean_value} are outside the range. Action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")   # ALERT TO BE SENT TO THE UI
                                SendAction(f"WARNING: The measured value {nutrient_val} and the mean value {mean_value} are outside the range. Action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")
                            else:   # if the mean value is inside the range
                                if abs(nutrient_val - mean_value) > 5:    # if the value is far from the mean, action is needed
                                    # take preventive action by following the expected severity
                                    write_log(f"WARNING: The measured value {nutrient_val} is far from the mean value {mean_value}. Action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")   # ALERT TO BE SENT TO THE UI
                                    SendAction(f"WARNING: The measured value {nutrient_val} is far from the mean value {mean_value}. Action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")
                                else:   # if the value is near the mean, check if the next expected value is in the range
                                    if not Is_inside(min_treshold[nutrient], expected_nutrient_val, max_treshold[nutrient]):    # if the expected value is outside the range, action is needed
                                        # take preventive action by following the expected severity
                                        write_log(f"WARNING: The measured value {nutrient_val} and the next expected one {expected_nutrient_val} are outside the range. Action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")   # ALERT TO BE SENT TO THE UI
                                        SendAction(f"WARNING: The measured value {nutrient_val} and the next expected one {expected_nutrient_val} are outside the range. Action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")
                        else:
                            write_log(f"Failed to get mean value of sensor_{sensor_id} ({sensor_type} - {nutrient}) from the DataAnalysis\t(Response: {response.reason})")    # ALERT TO BE SENT TO THE UI
                            SendAlert(f"Failed to get mean value of sensor_{sensor_id} ({sensor_type} - {nutrient}) from the DataAnalysis\t(Response: {response.reason})")
                            return

                else:   # if the value is inside the range
                    if not Is_inside(min_treshold[nutrient], expected_nutrient_val, max_treshold[nutrient]):    # if the next expected value is outside the range, action is needed
                        write_log(f"WARNING: The next expected value of sensor_{sensor_id} ({sensor_type} - {nutrient}) is outside the range [{min_treshold}, {max_treshold}]")    # ALERT TO BE SENT TO THE UI
                        SendAlert(f"WARNING: The next expected value of sensor_{sensor_id} ({sensor_type} - {nutrient}) is outside the range [{min_treshold}, {max_treshold}]")

                        if expected_nutrient_val > max_treshold: # if the expected value is higher than the max treshold
                            distance = (expected_nutrient_val - max_treshold)
                        else:   # expected_value < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_treshold
                            distance = (min_treshold - expected_nutrient_val)
                        severity = Severity(distance, domains[sensor_id])   # evaluate the severity of the problem
                        # take preventive action by following the expected severity
                        write_log(f"WARNING: The measured value {nutrient_val} is inside the range, but the next expected value {expected_nutrient_val} is predicted to be far from the range. Preventine action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")    # ALERT TO BE SENT TO THE UI
                        SendAction(f"WARNING: The measured value {nutrient_val} is inside the range, but the next expected value {expected_nutrient_val} is predicted to be far from the range. Preventine action needed for sensor_{sensor_id} ({sensor_type} - {nutrient})")
                    else:   # if the next expected value is inside the range
                        write_log(f"The measured value ({nutrient_val} {unit}) and the next prediction ({expected_nutrient_val} {unit}) of {sensor_type} ({sensor_type} - {nutrient}) are inside the range [{min_treshold}, {max_treshold}]")    # THIS INFO CAN BE SENT TO THE UI
                        SendInfo(f"The measured value ({nutrient_val} {unit}) and the next prediction ({expected_nutrient_val} {unit}) of {sensor_type} ({sensor_type} - {nutrient}) are inside the range [{min_treshold}, {max_treshold}]")
            
            expected_value[sensor_id][nutrient] = expected_nutrient_val   # update the next expected value

    else:
        # we use the previous expected value to check if the measured value is unexpected
        if abs(val - expected_value[sensor_id]) > 5:    # if the value was unexpected, alert the user and wait for the next value
            write_log(f"WARNING: The measured value {val} of sensor_{sensor_id} ({sensor_type}) is unexpected. (Expected value: {expected_val})\tWaiting for the next value")   # ALERT TO BE SENT TO THE UI
            SendAlert(f"WARNING: The measured value {val} of sensor_{sensor_id} ({sensor_type}) is unexpected. (Expected value: {expected_val})\tWaiting for the next value")
        else:   # if the value was expected
            if not Is_inside(min_treshold, val, max_treshold):  # if the value is outside the range of accepted values, alert the user
                write_log(f"WARNING: The measured value {val} {unit} of sensor_{sensor_id} ({sensor_type}) went outside the range [{min_treshold}, {max_treshold}]")    # ALERT TO BE SENT TO THE UI
                SendAlert(f"WARNING: The measured value {val} {unit} of sensor_{sensor_id} ({sensor_type}) went outside the range [{min_treshold}, {max_treshold}]")

                # evaluate how far the value is from the interval
                if val > max_treshold:  # if the value is higher than the max treshold
                    distance = (val - max_treshold)
                else:   # val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_t
                    distance = (min_treshold - val)
                severity = Severity(distance, domains[sensor_id])   # evaluate the severity of the problem

                if severity is None:
                    write_log(f"WARNING: Failed to evaluate the severity of the problem for sensor_{sensor_id} ({sensor_type})") # ALERT TO BE SENT TO THE UI
                    SendAlert(f"WARNING: Failed to evaluate the severity of the problem for sensor_{sensor_id} ({sensor_type})")
                    return

                if severity > 0.5:  # if the severity is high enough, action is needed
                    write_log(f"WARNING: The measured value {val} is highly outside the range (Severity: {severity}). Action needed for sensor_{sensor_id} ({sensor_type})")  # ALERT TO BE SENT TO THE UI
                    SendAction(f"WARNING: The measured value {val} is highly outside the range (Severity: {severity}). Action needed for sensor_{sensor_id} ({sensor_type})")
                else:   # if the severity isn't high enough
                    # get the updated mean
                    response = requests.get(f"{dataAnalysis_url}/get_mean_value", params={'sensor_id': sensor_id, 'sensor_type':sensor_type, 'timestamp': timestamp})    # get the mean value from the data analysis
                    if response.status_code == 200:
                        mean_value = response.json()["mean_value"]
                        if mean_value is not None:
                            write_log(f"Mean value of sensor_{sensor_id} ({sensor_type}): {mean_value}")   # THIS INFO CAN BE SENT TO THE UI
                            SendInfo(f"Mean value of sensor_{sensor_id} ({sensor_type}): {mean_value}")
                        else:   # if the response is None, we consider the evaluation lost
                            write_log(f"WARNING: Failed to get mean value of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis")   # ALERT TO BE SENT TO THE UI
                            SendAlert(f"WARNING: Failed to get mean value of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis")
                            return
                        if not Is_inside(min_treshold, mean_value, max_treshold):    # if the mean value is outside the range, action is needed
                            # take preventive action by following the expected severity
                            write_log(f"WARNING: The measured value {val} and the mean value {mean_value} are outside the range. Action needed for sensor_{sensor_id} ({sensor_type})")   # ALERT TO BE SENT TO THE UI
                            SendAction(f"WARNING: The measured value {val} and the mean value {mean_value} are outside the range. Action needed for sensor_{sensor_id} ({sensor_type})")
                        else:   # if the mean value is inside the range
                            if abs(val - mean_value) > 5:    # if the value is far from the mean, action is needed
                                # take preventive action by following the expected severity
                                write_log(f"WARNING: The measured value {val} is far from the mean value {mean_value}. Action needed for sensor_{sensor_id} ({sensor_type})")   # ALERT TO BE SENT TO THE UI
                                SendAction(f"WARNING: The measured value {val} is far from the mean value {mean_value}. Action needed for sensor_{sensor_id} ({sensor_type})")
                            else:   # if the value is near the mean, check if the next expected value is in the range
                                if not Is_inside(min_treshold, expected_val, max_treshold):    # if the expected value is outside the range, action is needed
                                    # take preventive action by following the expected severity
                                    write_log(f"WARNING: The measured value {val} and the next expected one {expected_val} are outside the range. Action needed for sensor_{sensor_id} ({sensor_type})")   # ALERT TO BE SENT TO THE UI
                                    SendAction(f"WARNING: The measured value {val} and the next expected one {expected_val} are outside the range. Action needed for sensor_{sensor_id} ({sensor_type})")
                    else:
                        write_log(f"Failed to get mean value of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis\t(Response: {response.reason})")    # ALERT TO BE SENT TO THE UI
                        SendAlert(f"Failed to get mean value of sensor_{sensor_id} ({sensor_type}) from the DataAnalysis\t(Response: {response.reason})")
                        return

            else:   # if the value is inside the range
                if not Is_inside(min_treshold, expected_val, max_treshold):    # if the next expected value is outside the range, action is needed
                    write_log(f"WARNING: The next expected value of sensor_{sensor_id} ({sensor_type}) is outside the range [{min_treshold}, {max_treshold}]")    # ALERT TO BE SENT TO THE UI
                    SendAlert(f"WARNING: The next expected value of sensor_{sensor_id} ({sensor_type}) is outside the range [{min_treshold}, {max_treshold}]")

                    if expected_val > max_treshold: # if the expected value is higher than the max treshold
                        distance = (expected_val - max_treshold)
                    else:   # expected_value < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_treshold
                        distance = (min_treshold - expected_val)
                    severity = Severity(distance, domains[sensor_id])   # evaluate the severity of the problem
                    # take preventive action by following the expected severity
                    write_log(f"WARNING: The measured value {val} is inside the range, but the next expected value {expected_val} is predicted to be far from the range. Preventine action needed for sensor_{sensor_id} ({sensor_type})")    # ALERT TO BE SENT TO THE UI
                    SendAction(f"WARNING: The measured value {val} is inside the range, but the next expected value {expected_val} is predicted to be far from the range. Preventine action needed for sensor_{sensor_id} ({sensor_type})")
                else:   # if the next expected value is inside the range
                    write_log(f"The measured value ({val} {unit}) and the next prediction ({expected_val} {unit}) of {sensor_type} ({sensor_type}) are inside the range [{min_treshold}, {max_treshold}]")    # THIS INFO CAN BE SENT TO THE UI
                    SendInfo(f"The measured value ({val} {unit}) and the next prediction ({expected_val} {unit}) of {sensor_type} ({sensor_type}) are inside the range [{min_treshold}, {max_treshold}]")
        
        expected_value[sensor_id] = expected_val   # update the next expected value