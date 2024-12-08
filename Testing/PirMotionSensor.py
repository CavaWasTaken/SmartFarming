from gpiozero import MotionSensor, Device
from gpiozero.pins.rpigpio import RPiGPIOFactory
from signal import pause
import sys
import time

# Set the pin factory to RPiGPIO
Device.pin_factory = RPiGPIOFactory()

pir = MotionSensor(18)
count_motions = 0
start_time = time.time()
last_motion_time = start_time

def motion_function():
    global count_motions, last_motion_time
    count_motions += 1
    current_time = time.time()
    elapsed_time = current_time - start_time
    time_since_last_motion = current_time - last_motion_time
    last_motion_time = current_time
    print(f"Motion {count_motions} detected at {elapsed_time:.2f} seconds, {time_since_last_motion:.2f} seconds since last motion")

pir.when_motion = motion_function

# Keep the script running to monitor for motion events
pause()