import serial
import time
import pickle
import RPi.GPIO as GPIO
import os

def wait_for_Ublox_ready():
    while True:
        if os.path.exists('/dev/ttyACM0'):
            print("Ublox connected")
            break
        
        print("Waiting for Ublox...")
        time.sleep(5)

def get_gps():
	Ublox.reset_input_buffer()

	while True:
		line = Ublox.readline().decode()
		data = line.split(',')
		if data[0] == '$GPGGA':
			GPS_time = data[1]
			latitude = f"{data[2]} {data[3]}"
			longitude = f"{data[4]} {data[5]}"
			altitude = f"{data[9]} {data[10]}"
			break
	return f"{GPS_time} {latitude} {longitude} {altitude}"

wait_for_Ublox_ready()
Ublox = serial.Serial(port = '/dev/ttyACM0', baudrate=9600, timeout=1)

GPIO.cleanup()

GPIO.setmode(GPIO.BOARD)

input_pin_shutter = 13
output_pin_3v = 11
input_pin_shutoff = 15

GPIO.setup(input_pin_shutter, GPIO.IN, GPIO.PUD_DOWN)

GPIO.setup(output_pin_3v, GPIO.OUT)
GPIO.output(output_pin_3v, GPIO.HIGH)

GPIO.setup(input_pin_shutoff, GPIO.IN, GPIO.PUD_UP)

i = 1

time.sleep(.5)

print("Testing")

if os.path.exists("/home/grivera/Desktop/GPGGA_list.pkl"):
	with open("/home/grivera/Desktop/GPGGA_list.pkl", "rb") as file:
		GPGGA_list = pickle.load(file)
else:
	GPGGA_list = []

try:
    while True:
        shutter_state = GPIO.input(input_pin_shutter)
        if shutter_state == GPIO.HIGH:
            GPGGA_line = get_gps()
            GPGGA_list.append(GPGGA_line)
            print("Picture taken!")
            print(f"Shot #: {i}\n")
            time.sleep(0.2)
            GPIO.output(output_pin_3v, GPIO.LOW)
            time.sleep(0.2)
            GPIO.output(output_pin_3v, GPIO.HIGH)
            i = i + 1
        
        shutoff_button_state = GPIO.input(input_pin_shutoff)
        if shutoff_button_state == GPIO.LOW:
            break

finally:
    with open("/home/grivera/Desktop/GPGGA_list.pkl", "wb") as file:
        pickle.dump(GPGGA_list, file)
        file.flush()
        os.fsync(file.fileno())
    print("Program ended")
    Ublox.close()
    GPIO.cleanup()

