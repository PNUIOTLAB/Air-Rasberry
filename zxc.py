import RPi.GPIO as GPIO

a = 26
b = 19

c = 6
d = 5

e = 27
f = 17

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(a, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(b, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(c, GPIO.OUT, initial = GPIO.LOW)	
GPIO.setup(d, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(e, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(f, GPIO.OUT, initial = GPIO.LOW)

while True:
    i = input("signal:")
    if i=="on1":
        GPIO.output(a, GPIO.HIGH)
    elif i=="off1":
        GPIO.output(a, GPIO.LOW)
    elif i =="on2":
        GPIO.output(b, GPIO.HIGH)
    elif i =="off2":
        GPIO.output(b, GPIO.LOW)
    elif i =="on3":
        GPIO.output(c, GPIO.HIGH)
    elif i =="off3":
        GPIO.output(c, GPIO.LOW)
    elif i=="on4":
        GPIO.output(d, GPIO.HIGH)
    elif i=="off4":
        GPIO.output(d, GPIO.LOW)
    elif i=="on5":
        GPIO.output(e, GPIO.HIGH)
    elif i=="off5":
        GPIO.output(e, GPIO.LOW)
    elif i=="on6":
        GPIO.output(f, GPIO.HIGH)
    elif i=="off6":
        GPIO.output(f, GPIO.LOW)
