import socket, threading, pickle, operator, time
from collections import deque

# Global Variables
EXIT = False
INCOMING_QUEUE = deque()
DATA = {}
HOSTNAME = "10.10.0.130"
LISTEN_PORT = 12346
NODE_ARRAY = []
test = {'CURRENT': 0.8923919159192195, 'WIND': 0.09949649555531538, 'VOLTAGE': 3.944045643925005, 'NODE': 'raspberrypi'}

class Node(object):
	def update(self, newdata):
		for key,value in newdata.items():
			setattr(self, key, value)

	def display(self):
		print("Custom Name: ", self.NAME)
		print("Node Hostname: ", self.NODE)
		print("Motor Status: ", self.MOTOR_STATE)
		print("Motor Active: ", self.ACTIVE)
		print("Umbrella OPEN: ", self.UP_STATE)
		print("Umbrella CLOSED: ", self.DOWN_STATE)
		print("CALL Status: ", self.CALL_STATE)
		print("WIND Control", self.WIND_STATE)
		print("WIND Sensor: ", self.WIND)
		print("CURRENT Sensor: ", self.CURRENT)
		print("VOLTAGE Sensor: ", self.VOLTAGE)

	def __init__(self, name=None, node=None, active=False, up=False, down=False, call=False, timeout=True, wind_state=True, wind=0, current=0, voltage=0):
		self.NAME = name
		self.NODE = node
		self.ACTIVE = active
		self.UP_STATE = up
		self.DOWN_STATE = down
		self.CALL_STATE = call
		self.MOTOR_STATE = timeout
		self.WIND_STATE = wind_state
		self.WIND = wind
		self.CURRENT = current
		self.VOLTAGE = voltage

def locate(node):
	slot = 0
	for i in NODE_ARRAY:
		if i.NODE == node:
			return slot
		slot = slot + 1
	return -1

def incoming(connection, ip, port, MAX_BUFFER_SIZE = 4096):
	global INCOMING_QUEUE
	raw_input_bytes = connection.recv(MAX_BUFFER_SIZE)
	INCOMING_QUEUE.append(raw_input_bytes)
	connection.close()

def menu():
	choice ='9'
	print("Main Menu")
	print("1. Add Node")
	print("2. Control Node")
	print("3. Remove Node")
	print("0. Exit")
	NODE_ARRAY.append(Node("raspberrypi", "raspberrypi"))
	choice = input("Please make a Selection: ")

	if choice == "1":
		option = ""
		temp_node = input("What is the name of the node? (Listed on the Wifi Setup Page)\n:: ")
		option = input("Would you like to use a custom name? (y/n)\n:: ")
		if option == "y":
			temp_name = input("Please input the desired name (NO SPACES\n:: ")
		else:
			temp_name = temp_node
		print("Attempting to add Node")
		add_node(temp_name, temp_node, LISTEN_PORT)
		print(locate(temp_node))

	#elif choice == "2":
		#NODE_ARRAY[0].update(test)
	elif choice == "3":
		NODE_ARRAY[0].display()
		#remove_node()
	elif choice == "0":
		EXIT = True
		exit()
	else:
		print("Invalid Choice")

def add_node(name, node, port):
	global Node
	global HOSTNAME
	try:	
		data = ({"SERVER": HOSTNAME, "SEND_PORT": port})
		data = pickle.dumps(data)
		soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
		soc.connect((node, 12345))
		soc.send(data) 
		soc.close()
		NODE_ARRAY.append(Node(name, node))
	except socket.gaierror:
		print("Not Found, Try Again")


class Parser(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global EXIT
		global DATA
		global NODE_ARRAY
		global locate
		while True:
			if EXIT:
				exit()
			if INCOMING_QUEUE:
				DATA = pickle.loads(INCOMING_QUEUE.popleft())
				node = DATA.get("NODE")
				print(DATA)
				slot = locate(node)
				if slot is not -1:
					NODE_ARRAY[slot].update(DATA)
					if "LOG" in DATA:
						print(node, ":  ", DATA.get("LOG"))

class Remote_In(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global EXIT
		global LISTEN_PORT
		global incoming
		print("Remote_In Thread is Running")
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print('Listening on port', LISTEN_PORT)
		sock.bind(("", LISTEN_PORT))
		sock.listen(10)
		while True:
			if EXIT:
				sock.close()
				exit()
			connection, address = sock.accept()
			ip, port = str(address[0]), str(address[1])
			#print("Accepting connection from " + ip + ":" + port)
			threading.Thread(target=incoming, args=(connection, ip, port)).start()
		sock.close()


# Main Program Start
a = Remote_In("Remote_In")
b = Parser("Parser")
a.start()
b.start()
NODE_ARRAY.append(Node("raspberrypi", "raspberrypi"))
while True:
	NODE_ARRAY[0].display()
	time.sleep(1)
	#menu()
	#if INCOMING_QUEUE:
	#	data = pickle.loads(INCOMING_QUEUE.popleft())
	#	print(data)
