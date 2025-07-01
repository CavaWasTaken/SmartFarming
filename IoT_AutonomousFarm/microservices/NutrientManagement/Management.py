import requests

# normalized evaluation of how far the value is from the interval
def Severity(distance, domain):
    max = domain["max"]
    min = domain["min"]
    severity = distance / max - min
    return severity
    
# function that checks if the value is in the accepted range
def isInside(min_treshold, val, max_treshold):
    return float(min_treshold) <= float(val) <= float(max_treshold)
    
# function that checks if an action is needed, and updates the user
def checkValue(dataAnalysis_url, sensor_id, sensor_type, val, unit, timestamp, min_treshold, max_treshold, expected_value, domains, write_log, sendTelegramMessage, sendAction):

    # get the value that we expect from that sensor in the next reading
    response = requests.get(f"{dataAnalysis_url}/get_next_value", params={'sensor_id': sensor_id, 'sensor_type': sensor_type, 'timestamp': timestamp})    # get the expected value from the data analysis
    if response.status_code == 200:
        expected_val = response.json()["next_value"]
        if expected_val is not None:    # the data analysis has returned a prediction
            write_log(f"The next value of {sensor_type} (sensor_{sensor_id}) is expected to be: {expected_val} {unit}")

        else:   # if the response is None, we consider the prediction lost
            write_log(f"WARNING: Failed to get the next expected value of {sensor_type} (sensor_{sensor_id})")
            sendTelegramMessage(
                f"⚠️ *Failed to predict the next value!*\n\n"
                f"*Sensor Type:* {sensor_type}\n"
                f"*Sensor ID:* {sensor_id}\n"
                "The next expected value of the sensor is not available. This may be due to a lack of data or a problem with the Data Analysis component.\n"
            )
            return  # terminate the function

    else:   # if the request fails, we consider the prediction lost
        write_log(f"WARNING: A problem with DataAnalysis component occured while getting the next expected value of {sensor_type} (sensor_{sensor_id})\t(Response: {response.reason})")
        sendTelegramMessage(
            f"⚠️ *Data Analysis error!*\n\n"
            f"*Sensor Type:* {sensor_type}\n"
            f"*Sensor ID:* {sensor_id}\n"
            "Data Analysis component is not responding correctly. The next expected value of the sensor is not available.\n"
        )        
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

            if (abs(nutrient_val - expected_nutrient_val) / abs(expected_nutrient_val)) > 0.5:    # if the value was unexpected, alert the user and wait for the next value
                write_log(f"WARNING: The measured value {nutrient_val} {unit} of {sensor_type} - {nutrient} (sensor_{sensor_id}) is unexpected. (Expected value was {expected_nutrient_val} {unit})\tWaiting to receive another value")   # ALERT TO BE SENT TO THE UI
                sendTelegramMessage(f"⚠️ *Unexpected Value!*\n\n"
                                    f"*Sensor Type:* {sensor_type} - {nutrient}\n"
                                    f"*Sensor ID:* {sensor_id}\n"
                                    f"*Measured Value:* {nutrient_val} {unit}\n"
                                    f"*Expected Value:* {expected_nutrient_val} {unit}\n"
                                    f"Waiting to receive another value...")

            else:   # if the value was expected
                if not isInside(min_treshold[nutrient], nutrient_val, max_treshold[nutrient]):  # if the value is outside the range of accepted values, alert the user
                    write_log(f"WARNING: The measured value {nutrient_val} {unit} of sensor_{sensor_id} ({sensor_type} - {nutrient}) went outside the range [{min_treshold[nutrient]}, {max_treshold[nutrient]}]")    # ALERT TO BE SENT TO THE UI

                    # evaluate how far the value is from the interval
                    if nutrient_val > max_treshold[nutrient]:  # if the value is higher than the max treshold
                        distance = (nutrient_val - max_treshold[nutrient])
                    else:   # nutrient_val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_t
                        distance = (min_treshold[nutrient] - nutrient_val)
                    severity = Severity(distance, domains[sensor_id])   # evaluate the severity of the problem

                    if severity is None:
                        write_log(f"WARNING: Failed to evaluate the severity of the problem for sensor_{sensor_id} ({sensor_type} - {nutrient})") # ALERT TO BE SENT TO THE UI

                    if severity is not None and severity > 0.5:  # if the severity is high enough, action is needed                        
                        if nutrient_val > max_treshold[nutrient]:  # if the value is higher than the max treshold
                            action = "decrease"
                        else:   # nutrient_val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_t
                            action = "increase"

                        write_log(f"WARNING: The measured value {nutrient_val} {unit} of {sensor_type} - {nutrient} (sensor_{sensor_id}) is highly outside the range [{min_treshold[nutrient]}, {max_treshold[nutrient]}] (Severity: {severity}).\nAction needed to {action} the value")  # ALERT TO BE SENT TO THE UI
                        sendTelegramMessage(f"⚠️ *Action Needed for Value!*\n\n"
                                            f"*Sensor Type:* {sensor_type} - {nutrient}\n"
                                            f"*Sensor ID:* {sensor_id}\n"
                                            f"*Measured Value:* {nutrient_val} {unit}\n"
                                            f"*Range:* [{min_treshold[nutrient]}, {max_treshold[nutrient]}]\n"
                                            f"*Action:* {action}"
                                            f"The measured value is far from the desired range.")

                        sendAction({
                            "action": action,
                            "val": nutrient_val,
                            "min_treshold": min_treshold[nutrient],
                            "max_treshold": max_treshold[nutrient],
                            "nutrient": nutrient
                        })

                    else:   # if the severity isn't high enough, or if is it None, check if the next expected value is in the range
                        if not isInside(min_treshold[nutrient], expected_nutrient_val, max_treshold[nutrient]):    # if the expected value is outside the range, action is needed
                            if nutrient_val > max_treshold[nutrient]:
                                action = f"decrease"
                            else:
                                action = f"increase"

                            write_log(f"WARNING: The measured value {nutrient_val} {unit} and the next expected one {expected_nutrient_val} {unit} of {sensor_type} - {nutrient} (sensor_{sensor_id}) are outside the range.\nAction needed to {action} the value")   # ALERT TO BE SENT TO THE UI
                            sendTelegramMessage(f"⚠️ *Action Needed for Value!*\n\n"
                                                f"*Sensor Type:* {sensor_type} - {nutrient}\n"
                                                f"*Sensor ID:* {sensor_id}\n"
                                                f"*Measured Value:* {nutrient_val} {unit}\n"
                                                f"*Next Expected Value:* {expected_nutrient_val} {unit}\n"
                                                f"*Range:* [{min_treshold[nutrient]}, {max_treshold[nutrient]}]\n"
                                                f"*Action:* {action}"
                                                f"Both the measured value and the next expected value are outside the desired range. Corrective action is needed."
                                            )        

                            sendAction({
                                "action": action,
                                "val": nutrient_val,
                                "min_treshold": min_treshold[nutrient],
                                "max_treshold": max_treshold[nutrient],
                                "nutrient": nutrient
                            })
                        
                        else:
                            sendTelegramMessage(
                                f"ℹ️ *No Action Needed for Value!*\n\n"
                                f"*Sensor Type:* {sensor_type} - {nutrient}\n"
                                f"*Sensor ID:* {sensor_id}\n"
                                f"*Measured Value:* {nutrient_val} {unit}\n"
                                f"*Next Expected Value:* {expected_nutrient_val} {unit}\n"
                                f"*Range:* [{min_treshold[nutrient]}, {max_treshold[nutrient]}]\n"
                                "The measured value is currently outside the desired range, but the next expected value is predicted to return within the range. No action is needed at this time."
                            )

                else:   # if the value is inside the range, check if the value is expected to go far from the range
                    if not isInside(min_treshold[nutrient], expected_nutrient_val, max_treshold[nutrient]):    # check if the next expected value is outside the range, and measure the distance from the range
                        write_log(f"WARNING: The next expected value {expected_nutrient_val} {unit} of {sensor_type} - {nutrient} (sensor_{sensor_id}) is outside the range [{min_treshold[nutrient]}, {max_treshold[nutrient]}]")

                        if expected_nutrient_val > max_treshold[nutrient]: # if the expected value is higher than the max treshold
                            distance = (expected_nutrient_val - max_treshold[nutrient])
                        else:   # expected_value < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_treshold
                            distance = (min_treshold[nutrient] - expected_nutrient_val)
                        severity = Severity(distance, domains[sensor_id])   # evaluate the severity of the problem

                        if severity is None:
                            write_log(f"WARNING: Failed to evaluate the severity of the problem at the next expected value for sensor_{sensor_id} ({sensor_type} - {nutrient})")

                        if severity is not None and severity > 0.5:  # if the severity is high enough, action is needed                        
                            if nutrient_val > max_treshold[nutrient]:  # if the value is higher than the max treshold
                                action = "decrease"
                            else:   # nutrient_val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_t
                                action = "increase"

                            # take preventive action by following the expected severity
                            write_log(f"WARNING: The measured value {nutrient_val} {unit} is inside the range, but the next expected value {expected_nutrient_val} {unit} of {sensor_type} - {nutrient} (sensor_{sensor_id}) is predicted to be far from the range.\nPreventine action needed to {action} the value")    # ALERT TO BE SENT TO THE UI
                            sendTelegramMessage(f"⚠️ *Preventive Action Needed for Value!*\n\n"
                                                f"*Sensor Type:* {sensor_type} - {nutrient}\n"
                                                f"*Sensor ID:* {sensor_id}\n"
                                                f"*Measured Value:* {nutrient_val} {unit}\n"
                                                f"*Next Expected Value:* {expected_nutrient_val} {unit}\n"
                                                f"*Range:* [{min_treshold[nutrient]}, {max_treshold[nutrient]}]\n"
                                                f"*Action:* {action}"
                                                f"The next expected value is predicted to be far from the desired range.")

                            sendAction({
                                "action": action,
                                "val": nutrient_val,
                                "min_treshold": min_treshold[nutrient],
                                "max_treshold": max_treshold[nutrient],
                                "nutrient": nutrient
                            })

                        else:
                            sendTelegramMessage(f"ℹ️ *No Action Needed for Value!*\n\n"
                                                f"*Sensor Type:* {sensor_type} - {nutrient}\n"
                                                f"*Sensor ID:* {sensor_id}\n"
                                                f"*Measured Value:* {nutrient_val} {unit}\n"
                                                f"*Next Expected Value:* {expected_nutrient_val} {unit}\n"
                                                f"*Range:* [{min_treshold[nutrient]}, {max_treshold[nutrient]}]\n"
                                                "The measured value is inside the desired range, but the next expected value is predicted to go slightly outside the range. Wait to see the next value before taking any action.")

                    else:   # if the next expected value is inside the range
                        write_log(f"The measured value ({nutrient_val} {unit}) and the next prediction ({expected_nutrient_val} {unit}) of {sensor_type} - {nutrient} (sensor_{sensor_id}) are inside the range [{min_treshold[nutrient]}, {max_treshold[nutrient]}]")    # THIS INFO CAN BE SENT TO THE UI
                        sendTelegramMessage(f"ℹ️ *Value Within Range!*\n\n"
                                            f"*Sensor Type:* {sensor_type} - {nutrient}\n"
                                            f"*Sensor ID:* {sensor_id}\n"
                                            f"*Measured Value:* {nutrient_val} {unit}\n"
                                            f"*Next Expected Value:* {expected_nutrient_val} {unit}\n"
                                            f"*Range:* [{min_treshold[nutrient]}, {max_treshold[nutrient]}]\n"
                                            "Both the measured value and the next expected value are within the desired range. No action is needed at this time.")
                        
            expected_value[sensor_id][nutrient] = expected_nutrient_val   # update the next expected value

    else:
        # we use the previous expected value to check if the measured value is unexpected
        if (abs(val - expected_value[sensor_id]) / abs(expected_value[sensor_id])) > 0.5:    # if the value was unexpected, alert the user and wait for the next value
            write_log(f"WARNING: The measured value {val} {unit} of {sensor_type} (sensor_{sensor_id}) is unexpected. (Expected value was {expected_val} {unit})\tWaiting to receive another value")   # ALERT TO BE SENT TO THE UI
            sendTelegramMessage(f"⚠️ *Unexpected Value!*\n\n"
                                f"*Sensor Type:* {sensor_type}\n"
                                f"*Sensor ID:* {sensor_id}\n"
                                f"*Measured Value:* {val} {unit}\n"
                                f"*Expected Value:* {expected_val} {unit}\n"
                                "Waiting to receive another value...")

        else:   # if the value was expected
            if not isInside(min_treshold, val, max_treshold):  # if the value is outside the range of accepted values, alert the user
                write_log(f"WARNING: The measured value {val} {unit} of {sensor_type} (sensor_{sensor_id}) went outside the range [{min_treshold}, {max_treshold}]")    # ALERT TO BE SENT TO THE UI

                # evaluate how far the value is from the interval
                if val > max_treshold:  # if the value is higher than the max treshold
                    distance = (val - max_treshold)
                else:   # val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_t
                    distance = (min_treshold - val)
                severity = Severity(distance, domains[sensor_id])   # evaluate the severity of the problem

                if severity is None:
                    write_log(f"WARNING: Failed to evaluate the severity of the problem for sensor_{sensor_id} ({sensor_type})")

                if severity is not None and severity > 0.5:  # if the severity is high enough, action is needed                    
                    if val > max_treshold:  # if the value is higher than the max treshold
                        action = "decrease"
                    else:   # val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_treshold
                        action = "increase"

                    write_log(f"WARNING: The measured value {val} {unit} of {sensor_type} (sensor_{sensor_id}) is highly outside the range [{min_treshold}, {max_treshold}] (Severity: {severity}).\nAction needed to {action} the value")  # ALERT TO BE SENT TO THE UI
                    sendTelegramMessage(f"⚠️ *Action Needed!*\n\n"
                                        f"*Sensor Type:* {sensor_type}\n"
                                        f"*Sensor ID:* {sensor_id}\n"
                                        f"*Measured Value:* {val} {unit}\n"
                                        f"*Range:* [{min_treshold}, {max_treshold}]\n"
                                        f"*Action:* {action}"
                                        f"The measured value is far from the desired range.")

                    sendAction({
                        "action": action,
                        "val": val,
                        "min_treshold": min_treshold,
                        "max_treshold": max_treshold
                    })

                else:   # if the severity isn't high enough, or if is it None, check if the next expected value is in the range
                    if not isInside(min_treshold, expected_val, max_treshold):    # if the expected value is outside the range, action is needed                                    
                        if val > max_treshold:  # if the value is higher than the max treshold
                            action = "decrease"
                        else:   # val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_treshold
                            action = "increase"

                        write_log(f"WARNING: The measured value {val} {unit} and the next expected one {expected_val} {unit} of sensor_{sensor_id} ({sensor_type}) are outside the range [{min_treshold}, {max_treshold}].\nAction needed to {action} the value")   # ALERT TO BE SENT TO THE UI
                        sendTelegramMessage(f"⚠️ *Action Needed for Value!*\n\n"
                                            f"*Sensor Type:* {sensor_type}\n"
                                            f"*Sensor ID:* {sensor_id}\n"
                                            f"*Measured Value:* {val} {unit}\n"
                                            f"*Next Expected Value:* {expected_val} {unit}\n"
                                            f"*Range:* [{min_treshold}, {max_treshold}]\n"
                                            f"*Action:* {action}"
                                            f"Both the measured value and the next expected value are outside the desired range. Corrective action is needed."
                                        )

                        sendAction({
                            "action": action,
                            "val": val,
                            "min_treshold": min_treshold,
                            "max_treshold": max_treshold
                        })

                    else:
                        sendTelegramMessage(f"ℹ️ *No Action Needed for Value!*\n\n"
                                            f"*Sensor Type:* {sensor_type}\n"
                                            f"*Sensor ID:* {sensor_id}\n"
                                            f"*Measured Value:* {val} {unit}\n"
                                            f"*Next Expected Value:* {expected_val} {unit}\n"
                                            f"*Range:* [{min_treshold}, {max_treshold}]\n"
                                            "The measured value is currently outside the desired range, but the next expected value is predicted to return within the range. No action is needed at this time.")


            else:   # if the value is inside the range
                if not isInside(min_treshold, expected_val, max_treshold):    # check if the next expected value is outside the range, and measure the distance from the range
                    write_log(f"WARNING: The next expected value {expected_val} {unit} of sensor_{sensor_id} ({sensor_type}) is outside the range [{min_treshold}, {max_treshold}]")    # ALERT TO BE SENT TO THE UI

                    if expected_val > max_treshold: # if the expected value is higher than the max treshold
                        distance = (expected_val - max_treshold)
                    else:   # expected_value < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_treshold
                        distance = (min_treshold - expected_val)
                    severity = Severity(distance, domains[sensor_id])   # evaluate the severity of the problem

                    if severity is None:
                        write_log(f"WARNING: Failed to evaluate the severity of the problem at the next expected value for sensor_{sensor_id} ({sensor_type})")

                    if severity is not None and severity > 0.5:  # if the severity is high enough, action is needed
                        # take preventive action by following the expected severity                    
                        if expected_val > max_treshold:  # if the value is higher than the max treshold
                            action = "decrease"
                        else:   # val < min_treshold - we know that we are outside the interval, so clearly if it is not higher than max, then it is lower than min_treshold
                            action = "increase"

                        write_log(f"WARNING: The measured value {val} {unit} is inside the range, but the next expected value {expected_val} {unit} of sensor_{sensor_id} ({sensor_type}) is predicted to be far from the range.\nPreventine action needed to {action} the value")    # ALERT TO BE SENT TO THE UI
                        sendTelegramMessage(f"⚠️ *Preventive Action Needed for Value!*\n\n"
                                            f"*Sensor Type:* {sensor_type}\n"
                                            f"*Sensor ID:* {sensor_id}\n"
                                            f"*Measured Value:* {val} {unit}\n"
                                            f"*Next Expected Value:* {expected_val} {unit}\n"
                                            f"*Range:* [{min_treshold}, {max_treshold}]\n"
                                            f"*Action:* {action}"
                                            f"The next expected value is predicted to be far from the desired range.")

                        sendAction({
                            "action": action,
                            "val": val,
                            "min_treshold": min_treshold,
                            "max_treshold": max_treshold
                        })

                    else:
                        sendTelegramMessage(f"ℹ️ *No Action Needed for Value!*\n\n"
                                            f"*Sensor Type:* {sensor_type}\n"
                                            f"*Sensor ID:* {sensor_id}\n"
                                            f"*Measured Value:* {val} {unit}\n"
                                            f"*Next Expected Value:* {expected_val} {unit}\n"
                                            f"*Range:* [{min_treshold}, {max_treshold}]\n"
                                            "The measured value is inside the desired range, but the next expected value is predicted to go slightly outside the range. Wait to see the next value before taking any action.")

                else:   # if the next expected value is inside the range
                    write_log(f"The measured value ({val} {unit}) and the next prediction ({expected_val} {unit}) of sensor_{sensor_id} ({sensor_type}) are inside the range [{min_treshold}, {max_treshold}]")
                    sendTelegramMessage(f"ℹ️ *Value Within Range!*\n\n"
                                        f"*Sensor Type:* {sensor_type}\n"
                                        f"*Sensor ID:* {sensor_id}\n"
                                        f"*Measured Value:* {val} {unit}\n"
                                        f"*Next Expected Value:* {expected_val} {unit}\n"
                                        f"*Range:* [{min_treshold}, {max_treshold}]\n"
                                        "Both the measured value and the next expected value are within the desired range. No action is needed at this time.")

        expected_value[sensor_id] = expected_val   # update the next expected value