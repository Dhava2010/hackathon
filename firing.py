
from gpiozero import Servo
import time

def init_servo(pin=18):
    servo = Servo(pin)
    servo.mid()  
    return servo

def fire_gun(servo):
    servo.max()
    time.sleep(0.5) 
    servo.mid() 
