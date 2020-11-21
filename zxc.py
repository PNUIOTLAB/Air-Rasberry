import RPi.GPIO as GPIO

a = 17
c = 27
d = 22
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(a, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(c, GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(d, GPIO.OUT, initial = GPIO.LOW)



while True:
    b = input("signal:")
    if b=="0":
        GPIO.output(a, GPIO.HIGH)
    elif b=="1":
        GPIO.output(a, GPIO.LOW)
    elif b == "2":
        GPIO.output(c, GPIO.HIGH)
    elif b == "3":
        GPIO.output(c, GPIO.LOW)
    elif b == "4":
        GPIO.output(d, GPIO.HIGH)
    elif b == "5":
        GPIO.output(d, GPIO.LOW)
