import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

fire_alarm = 17
fan = 18
aircon = 27
airclean = 22

GPIO.setup(fire_alarm, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(fan , GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(aircon, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(airclean, GPIO.OUT, initial=GPIO.LOW)

alarm_check = 0b1000
fan_check = 0b0100
aircon_check = 0b0010
airclean_check = 0b0001

try:
        while 1:
                signal = int(input('signal: '), 16)
                #signal_hex = hex(signal)
                #check alarm
                if bin(signal & alarm_check)=='0b0':
                        GPIO.output(fire_alarm, GPIO.LOW)
                        print("fire off")
                if bin(signal & alarm_check)=='0b1000':
                        GPIO.output(fire_alarm, GPIO.HIGH)
                        print("fire on")
                if bin(signal & fan_check)=='0b0':
                        GPIO.output(fan, GPIO.LOW)
                        print("fan off")
                if bin(signal & fan_check)=='0b100':
                        GPIO.output(fan, GPIO.HIGH)
                        print("fan on")
                if bin(signal & aircon_check)=='0b0':
                        GPIO.output(aircon, GPIO.LOW)
                        print("aircon off")
                if bin(signal & aircon_check)=='0b10':
                        GPIO.output(aircon, GPIO.HIGH)
                        print("aircon on")
                if bin(signal & airclean_check)=='0b0':
                        GPIO.output(airclean, GPIO.LOW)
                        print("airclean off")
                if bin(signal & airclean_check)=='0b1':
                        GPIO.output(airclean, GPIO.HIGH)
                        print("airclean on")

except KeyboardInterrupt:
        pass

GPIO.cleanup()

