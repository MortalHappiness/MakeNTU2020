#!/usr/bin/python
#+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#|R|a|s|p|b|e|r|r|y|P|i|-|S|p|y|.|c|o|.|u|k|
#+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
# ultrasonic_2.py
# Measure distance using an ultrasonic module
# in a loop.
#
# Author : Matt Hawkins
# Date   : 28/01/2013

# -----------------------
# Import required Python libraries
# -----------------------
import time
import RPi.GPIO as GPIO
import agent

# -----------------------
# Define some variables
# -----------------------

SERVER_HOST = os.getenv('SERVER_HOST', None)

if SERVER_HOST is None:
    print('Please specify SERVER_HOST ' +
          'as environment variables.')
    exit()

# -----------------------
# Define some functions
# -----------------------

def measure(GPIO_TRIGGER, GPIO_ECHO):
  # This function measures a distance
  GPIO.output(GPIO_TRIGGER, True)
  time.sleep(0.0008)
  GPIO.output(GPIO_TRIGGER, False)
  start = time.time()
  while GPIO.input(GPIO_ECHO)==0:
      #print(GPIO.input(GPIO_ECHO))
      if time.time()-start > 0.5:
          #print("too far!!!")
          return 10000
  while GPIO.input(GPIO_ECHO)==1:
    stop = time.time()
  #stop = time.time()
          
  
  #while GPIO.input(GPIO_ECHO)==0:
   # start = time.time()

  #while GPIO.input(GPIO_ECHO)==1:
   # stop = time.time()
  
  elapsed = stop-start
  distance = (elapsed * 34300)/2
  #print(elapsed)

  return distance

def measure_average(GPIO_TRIGGER, GPIO_ECHO):
  # This function takes 3 measurements and
  # returns the average.
  distance1=measure(GPIO_TRIGGER, GPIO_ECHO)
  time.sleep(0.01)
  distance2=measure(GPIO_TRIGGER, GPIO_ECHO)
  time.sleep(0.01)
  distance3=measure(GPIO_TRIGGER, GPIO_ECHO)
  distance = distance1 + distance2 + distance3
  distance = distance / 3
  return distance

# -----------------------
# Main Script
# -----------------------

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)

# Define GPIO to use on Pi
GPIO_TRIGGER1 = 27
GPIO_ECHO1    = 22
GPIO_TRIGGER2 = 10
GPIO_ECHO2    = 9

# print ("Ultrasonic Measurement")
# Set pins as output and input
GPIO.setup(GPIO_TRIGGER1,GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO1,GPIO.IN)      # Echo
GPIO.setup(GPIO_TRIGGER2,GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO2,GPIO.IN)      # Echo

# Set trigger to False (Low)
GPIO.output(GPIO_TRIGGER1, False)
GPIO.output(GPIO_TRIGGER2, False)
# Wrap main content in a try block so we can
# catch the user pressing CTRL-C and run the
# GPIO cleanup function. This will also prevent
# the user seeing lots of unnecessary error
# messages.
try:
    people = 0
    state = 0
    while True:
      distance2 = measure_average(GPIO_TRIGGER2, GPIO_ECHO2)
      #print("Distance2 : ", distance2)
      if distance2 >= 200 or (distance2 < 80 and distance2 > 20):
          #start = time.time()
          while True:
              for zz in range(3):
              #if time.time() - start < 0.5:
                  distance1 = measure_average(GPIO_TRIGGER1, GPIO_ECHO1)
                  #time.sleep(0.1)
                  #print("Distance1 : ", distance1)
                  if distance1 < 90 or distance1 > 250:
                      people = people + 1
                      update_current_people(SERVER_HOST, "邦食堂","123", people)
                      break
                  if zz==2:
                      state = 1
                      break
              if state==1:
                  state=0
                  people-=1
                  update_current_people(SERVER_HOST, "邦食堂","123", people)
                  time.sleep(0.3)
                  break
              else:
                  time.sleep(0.3)
                  break
          
      # print("people : ", people)
      time.sleep(0.3)

except KeyboardInterrupt:
  # User pressed CTRL-C
  # Reset GPIO settings
  GPIO.cleanup()