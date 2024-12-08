import time

import RPi.GPIO as GPIO

# Set up the GPIO pin for the LED
LED1_PIN = 18
LED2_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED1_PIN, GPIO.OUT)
GPIO.setup(LED2_PIN, GPIO.OUT)

try:
    while True:
        # Turn the LED on
        GPIO.output(LED1_PIN, GPIO.HIGH)
        time.sleep(0.5)  # Keep it on for 1 second

        # Turn the LED off
        GPIO.output(LED1_PIN, GPIO.LOW)
        time.sleep(0.5)  # Keep it off for 1 second

        # Turn the LED on
        GPIO.output(LED2_PIN, GPIO.HIGH)
        time.sleep(0.5)

        # Turn the LED off
        GPIO.output(LED2_PIN, GPIO.LOW)
        time.sleep(0.5)

except KeyboardInterrupt:
    # Clean up GPIO settings before exiting
    GPIO.cleanup()