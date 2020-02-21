import RPi.GPIO as GPIO
import threading, time, socket, pickle, os
from collections import deque
from gpiozero import MCP3008
from pathlib import Path
#import raspiwifi/reset_device/reset_lib

# Button Inputs
BUT_RESET = 4
BUT_UP = 22
BUT_DOWN = 27
BUT_CALL = 17

# Drive Outputs
POL_UP = 26
POL_DOWN = 19
DRIVE_UP = 21
DRIVE_DOWN = 20
CALL_LED = 23

# Drive Monitor
RUNNING = 16

# Global Flags
ACTIVE = False
UP = False
DOWN = False
CALL = False
UP_STATE = False
DOWN_STATE = False
MOTOR_STATE = True
CALL_STATE = False
WIND_STATE = True
POWER_LOW = False
POWER_OFF = False
COMMAND_RECV = False
COMMAND_SEND = False
TIMEOUT = False
LIMIT = False

# Global Variables
SERVER = "null"
SEND_PORT = 0
LISTEN_PORT = 12345
LOCALHOST_PATH = Path("/etc/hostname")
LOCALHOST = "null"
OUTPUT_QUEUE = deque()
INPUT_QUEUE = deque()
CONFIG = Path("/opt/sun/config.txt")
WIND_LIMIT = 30
HEART_TIME = 30

# ADC Sensor Definitions
wind_sensor = MCP3008(1)
current_sensor = MCP3008(2)
voltage_sensor = MCP3008(3)

# ADC Calibration
adc_correction = 5.15
wind_adc_offset = 9 
current_adc_offset = 0
voltage_adc_offset = 0.2789188909
five_three_offset = 0.6467878
twenty_two_offset = 0.0897043833
hall_offset = 2.445761379890371

# Functions
def incoming(connection, ip, port, MAX_BUFFER_SIZE = 4096):
	global INPUT_QUEUE
	raw_input_bytes = connection.recv(MAX_BUFFER_SIZE)
	INPUT_QUEUE.append(raw_input_bytes)
	connection.close()
	print("Connection " + ip + ":" + port + " closed")

# Threads
class Heartbeat(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global OUTPUT_QUEUE
		global UP_STATE
		global DOWN_STATE
		global MOTOR_STATE
		global CALL_STATE
		global WIND_STATE
		global ACTIVE
		global HEART_TIME
		print("Heartbeat Thread is Running")
		while True:
			time.sleep(HEART_TIME)
			data = {"UP_STATE": UP_STATE, "DOWN_STATE": DOWN_STATE, "MOTOR_STATE": MOTOR_STATE, "CALL_STATE": CALL_STATE, "WIND_STATE": WIND_STATE, "ACTIVE": ACTIVE}
			OUTPUT_QUEUE.append(pickle.dumps(data))


class ADC(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global wind_sensor
		global current_sensor
		global voltage_sensor
		global adc_correction
		global wind_adc_offset
		global current_adc_offset
		global voltage_adc_offset
		global five_three_offset
		global twenty_two_offset
		global hall_offset
		global OUTPUT_QUEUE
		global WIND_STATE
		global WIND_LIMIT
		wind_average = 0
		seconds = 0
		print("ADC Thread is Running")
		while True:
			data = {}
			#print("RAW values: ", (wind_sensor.value - adc_correction), (current_sensor.value - adc_correction), (voltage_sensor.value - adc_correction))
			#5V offset and Divider correction
			# Wind Speed Sensor results
			wind = ((wind_sensor.value * adc_correction) * wind_adc_offset) # Offset
			wind = wind * 2.237 # Conversion of meters/second to MPH
			wind_average = wind_average + wind
			if seconds == 10:
				if (wind_average / seconds) >= WIND_LIMIT:
					WIND_STATE = False
				wind_average = 0
				seconds = 0
			# Current Sensor results
			corrected = ((current_sensor.value - adc_correction) / wind_adc_offset) #/ five_three_offset # ADC offset
			amps = corrected / five_three_offset
			amps = amps - 2.53
			amps = amps / 0.1
			# Battery Voltage results
			#20v offset and Divider correction
			corrected = (voltage_sensor.value * adc_correction) #/ twenty_two_offset # ADC offset
			#print("System Voltage: ","%.3f" % corrected,"V")
			data = {"WIND": wind, "CURRENT": amps, "VOLTAGE": corrected}
			OUTPUT_QUEUE.append(pickle.dumps(data))
			time.sleep(1)
			seconds = seconds + 1


class Output(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global OUTPUT_QUEUE
		global SERVER
		global SEND_PORT
		global LOCALHOST
		print("Output Thread is Running")
		while True:
			if OUTPUT_QUEUE:
				try:
					out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
					out.connect((SERVER, SEND_PORT))
					output = pickle.loads(OUTPUT_QUEUE.popleft())
					output.update({"NODE": LOCALHOST})
					output = pickle.dumps(output)
					out.send(output)
					out.close()
				except ConnectionRefusedError:
					print("Server Connection Refused")
					OUTPUT_QUEUE.clear()
				except ConnectionResetError:
					print("Server Connection Reset")
					OUTPUT_QUEUE.clear()

class Remote_Parser(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global UP
		global DOWN
		global CALL
		global ACTIVE
		global LOCALHOST
		global INPUT_QUEUE
		global MOTOR_STATE
		global WIND_STATE
		global OUTPUT_QUEUE
		print("Remote_Parser Thread is Running")
		while True:
			if INPUT_QUEUE:
				out = {}
				data = pickle.loads(INPUT_QUEUE.popleft())
				print(data)
				if MOTOR_STATE and WIND_STATE:
					if "UP" in data:
						UP = data.get("UP")
					if "DOWN" in data:
						DOWN = data.get("DOWN")
					if "CALL" in data:
						CALL = data.get("CALL")
				if "MOTOR_STATE" in data:
					MOTOR_STATE = data.get("MOTOR_STATE")
					out.update({"MOTOR_STATE": MOTOR_STATE, "LOG": "Motor Enabled: Drive is ready for commands.",})
				if "WIND_STATE" in data:
					WIND_STATE = data.get("WIND_STATE")
					out.update({"WIND_STATE": WIND_STATE, "LOG": "Motor Enabled: Drive is ready for commands.",})
				if out:
					OUTPUT_QUEUE.append(pickle.dumps(out))

class Remote_In(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global LISTEN_PORT
		global incoming
		print("Remote_In Thread is Running")
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print('Listening on port', LISTEN_PORT)
		sock.bind(("", LISTEN_PORT))
		sock.listen(10)
		while True:
			connection, address = sock.accept()
			ip, port = str(address[0]), str(address[1])
			print("Accepting connection from " + ip + ":" + port)
			threading.Thread(target=incoming, args=(connection, ip, port)).start()
		sock.close()


class Limit_Timeout(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global RUNNING
		global ACTIVE
		global TIMEOUT
		global LIMIT
		global UP
		global DOWN
		GPIO.setup(RUNNING, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		start_time = 0
		new_time = 0
		reset = True
		print("Limit_Timeout Thread is Running")
		while True:
			while ACTIVE:
				if GPIO.input(RUNNING):
					if UP or DOWN:
						reset = True
					if reset:
						start_time = new_time = time.time()
						reset = False
					#print(new_time - start_time)
					if new_time - start_time >= 60:
						TIMEOUT = True
						reset = True
						ACTIVE = False
					new_time = time.time()
				else:
					LIMIT = True
					reset = True
					ACTIVE = False

class Buttons(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global BUT_RESET
		global BUT_UP
		global BUT_DOWN
		global BUT_CALL
		global CALL_LED
		global UP
		global DOWN
		global CALL
		global WIND_STATE
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(BUT_RESET, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(BUT_UP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(BUT_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(BUT_CALL, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(CALL_LED, GPIO.OUT)
		print("Button Thread is Running")
		while True:
			while MOTOR_STATE and WIND_STATE:	
				if GPIO.input(BUT_UP):
					UP = True
				if GPIO.input(BUT_DOWN):
					DOWN = True
				if GPIO.input(BUT_CALL):
					if CALL == True:
						CALL = False
					else:
						CALL = True
				"""while GPIO.input(BUT_RESET) == 1:
        			time.sleep(1)
        			counter = counter + 1

        			print(counter)

        			if counter == 9:
            		reset_lib.reset_to_host_mode()

        			if GPIO.input(BUT_RESET) == 0:
            		counter = 0
            		break"""

class Driver(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global POL_UP
		global POL_DOWN
		global DRIVE_UP
		global DRIVE_DOWN
		global UP_STATE
		global DOWN_STATE
		global MOTOR_STATE
		global CALL_STATE
		global WIND_STATE
		global LIMIT
		global ACTIVE
		global UP
		global DOWN
		global TIMEOUT
		global OUTPUT_QUEUE
		wind_down = False
		call_set = False
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(POL_UP, GPIO.OUT)
		GPIO.setup(POL_DOWN, GPIO.OUT)
		GPIO.setup(DRIVE_UP, GPIO.OUT)
		GPIO.setup(DRIVE_DOWN, GPIO.OUT)
		GPIO.output(DRIVE_UP, GPIO.HIGH)
		GPIO.output(DRIVE_DOWN, GPIO.HIGH)
		GPIO.output(POL_UP, GPIO.LOW)
		GPIO.output(POL_DOWN, GPIO.LOW)
		print("Driver Thread is Running")
		while True:
			while WIND_STATE:
				#print("WIND STATE")
				data = {}
				wind_down = False
				if TIMEOUT or LIMIT:
					ACTIVE = False
					if TIMEOUT:
						MOTOR_STATE = False
						data.update({"MOTOR_STATE": MOTOR_STATE, "LOG": "Drive Failure: Stopping Drive until Remote or Manual Reset", "TIMEOUT": TIMEOUT})
					if LIMIT:
						data.update({"LOG": "Drive Completed"})
					GPIO.output(POL_UP, GPIO.LOW)
					GPIO.output(POL_DOWN, GPIO.LOW)
					GPIO.output(DRIVE_UP, GPIO.HIGH)
					GPIO.output(DRIVE_DOWN, GPIO.HIGH)
					UP = DOWN = TIMEOUT = LIMIT = False
					data.update({"ACTIVE": ACTIVE})
				if ACTIVE:
					if UP:
						GPIO.output(POL_DOWN, GPIO.LOW)
						GPIO.output(DRIVE_DOWN, GPIO.HIGH)
						GPIO.output(DRIVE_UP, GPIO.LOW)
						GPIO.output(POL_UP, GPIO.HIGH)
						UP = False
						UP_STATE = True
						DOWN_STATE = False
						data.update({"LOG": "Drive UP Engaged", "DOWN_STATE": DOWN_STATE, "UP_STATE": UP_STATE})
					if DOWN:
						GPIO.output(POL_UP, GPIO.LOW)
						GPIO.output(DRIVE_UP, GPIO.HIGH)
						GPIO.output(DRIVE_DOWN, GPIO.LOW)
						GPIO.output(POL_DOWN, GPIO.HIGH)
						DOWN = False
						DOWN_STATE = True
						UP_STATE = False
						data.update({"LOG": "Drive DOWN Engaged", "DOWN_STATE": DOWN_STATE, "UP_STATE": UP_STATE})
				if UP and not ACTIVE:
					GPIO.output(DRIVE_UP, GPIO.LOW)
					GPIO.output(POL_UP, GPIO.HIGH)
					ACTIVE = True
					UP = False
					UP_STATE = True
					DOWN_STATE = False
					data.update({"LOG": "Drive UP Engaged", "ACTIVE": ACTIVE, "DOWN_STATE": DOWN_STATE, "UP_STATE": UP_STATE})
				if DOWN and not ACTIVE:
					GPIO.output(DRIVE_DOWN, GPIO.LOW)
					GPIO.output(POL_DOWN, GPIO.HIGH)
					ACTIVE = True
					DOWN = False
					DOWN_STATE = True
					UP_STATE = False
					data.update({"LOG": "Drive DOWN Engaged", "ACTIVE": ACTIVE, "DOWN_STATE": DOWN_STATE, "UP_STATE": UP_STATE})
				if CALL:
					GPIO.output(CALL_LED, GPIO.HIGH)
					if not CALL_STATE:
						CALL_STATE = True
						data.update({"CALL_STATE": True})
				if not CALL:
					GPIO.output(CALL_LED, GPIO.LOW)
					if CALL_STATE:
						CALL_STATE = False
						data.update({"CALL_STATE": False})
				if data:
					OUTPUT_QUEUE.append(pickle.dumps(data))

			#print("NOT WIND STATE")
			data = {}
			if not wind_down:
				GPIO.output(DRIVE_DOWN, GPIO.LOW)
				GPIO.output(POL_DOWN, GPIO.HIGH)
				ACTIVE = True
				DOWN = False
				DOWN_STATE = True
				UP_STATE = False
				wind_down =True
				data.update({"LOG": "High Wind Drive DOWN Engaged", "ACTIVE": ACTIVE, "DOWN_STATE": DOWN_STATE, "UP_STATE": UP_STATE})
			if LIMIT:
				data.update({"LOG": "High Wind Drive Completed"})
				GPIO.output(POL_UP, GPIO.LOW)
				GPIO.output(POL_DOWN, GPIO.LOW)
				GPIO.output(DRIVE_UP, GPIO.HIGH)
				GPIO.output(DRIVE_DOWN, GPIO.HIGH)
				UP = DOWN = TIMEOUT = LIMIT = False
				data.update({"ACTIVE": ACTIVE, "WIND_STATE": WIND_STATE})
			if data:
				OUTPUT_QUEUE.append(pickle.dumps(data))


# Main Program Start

# Initialize Threads into Class Objects
a = Buttons("Buttons")
b = Driver("Driver")
c = Limit_Timeout("Limit_Timeout")
d = Remote_In("Remote_In")
e = Remote_Parser("Remote_Parser")
f = Output("Output")
g = ADC("ADC")
h = Heartbeat("Heartbeat")

if CONFIG.is_file():
	hostname_file = open(str(LOCALHOST_PATH), 'r')
	LOCALHOST = hostname_file.read()
	LOCALHOST_split = LOCALHOST.split()
	LOCALHOST = LOCALHOST_split[0]
	config_file = open(str(CONFIG), 'r')
	file = config_file.read()
	file_split = file.split()
	SERVER = file_split[0]
	SEND_PORT = int(file_split[1])

	#Start Each Thread
	a.start()
	b.start()
	c.start()
	d.start()
	e.start()
	f.start()
	g.start()
	h.start()

	# Combine Threads together
	a.join()
	b.join()
	c.join()
	d.join()
	e.join()
	f.join()
	g.join()
	h.join()

else:
	d.start()
	f.start()
	while True:
		if INPUT_QUEUE:
			setup = pickle.loads(INPUT_QUEUE.popleft())
			if "SERVER" in setup:
				SERVER = setup.get("SERVER")
				SEND_PORT = setup.get("SEND_PORT")
				ack = ({"LOG": "OK"})
				OUTPUT_QUEUE.append(pickle.dumps(ack))
				CONFIG.touch()
				config_file = open(str(CONFIG), "w+")
				print(SERVER, SEND_PORT, file=config_file)
				config_file.close()
				#os.system("sudo reboot")


