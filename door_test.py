import RPi.GPIO as GPIO
import time

DOOR_PIN = 17
#DOOR_PIN2 = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(DOOR_PIN, GPIO.OUT)

def unlock_door():
   GPIO.output(DOOR_PIN, GPIO.HIGH)
   print("open")
   time.sleep(5)
   GPIO.output(DOOR_PIN, GPIO.LOW)

try:
   unlock_door()
finally:
   GPIO.cleanup()