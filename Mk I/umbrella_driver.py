import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)

loop = True
time_to_open = 40

def main():
	choice ='9'
	print("Main Menu")
	print("1. Open Umbrella")
	print("2. Close Umbrella")
	print("0. Exit")
	choice = input("Please make a Selection: ")

	if choice == "1":
        	open()
	elif choice == "2":
		close()
	elif choice == "0":
		exit()
	else:
		print("Invalid Choice")

def open():
	print("\nOpening Umbrella Cycle for ", time_to_open, " seconds.")
	GPIO.output(23, GPIO.HIGH)
	time.sleep(time_to_open)
	GPIO.output(23, GPIO.LOW)
	print("Open Cycle Completed\n")
	return;

def close():
	print("\nClosing Umbrella Cycle for ", time_to_open, " seconds.")
	GPIO.output(24, GPIO.HIGH)
	time.sleep(time_to_open)
	GPIO.output(24, GPIO.LOW)
	print("Open Cycle Completed\n")
	return;

while loop:
	main()
