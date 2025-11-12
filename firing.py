# firing.py
# This file handles initializing and controlling the servo to fire the Nerf gun.

from gpiozero import Servo
import time

def init_servo(pin=18):
    # Initialize the Miuzei digital servo on the specified GPIO pin
    servo = Servo(pin)
    servo.mid()  # Start at neutral position
    return servo

def fire_gun(servo):
    # Rotate servo to press the trigger (adjust values based on calibration)
    # Assuming max() presses the trigger
    servo.max()
    time.sleep(0.5)  # Hold to ensure press
    servo.mid()  # Return to neutral
