import socket, threading, pickle, operator, time
from collections import deque
from tkinter import *
from tkinter.ttk import *

# Global Variables
EXIT = False
CALL = False
OPEN_CLOSE = False
INCOMING_QUEUE = deque()
OUTPUT_QUEUE = deque()
DATA = {}
HOSTNAME = "10.10.0.130"
LISTEN_PORT = 12346
SEND_PORT = 12345
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
		while not EXIT:
			if INCOMING_QUEUE:
				DATA = pickle.loads(INCOMING_QUEUE.popleft())
				node = DATA.get("NODE")
				print(DATA)
				slot = locate(node)
				if slot is not -1:
					NODE_ARRAY[slot].update(DATA)
					if "LOG" in DATA:
						print(time.strftime('%Y_%m_%d_%H:%M:%S:'), node, "--", DATA.get("LOG"))

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
		while not EXIT:
			connection, address = sock.accept()
			ip, port = str(address[0]), str(address[1])
			#print("Accepting connection from " + ip + ":" + port)
			threading.Thread(target=incoming, args=(connection, ip, port)).start()
		sock.close()

class Output(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global OUTPUT_QUEUE
		print("Output Thread is Running")
		while not EXIT:
			if OUTPUT_QUEUE:
				output = pickle.loads(OUTPUT_QUEUE.popleft())
				target = output.get("TARGET")
				output = pickle.dumps(output)
				try:
					out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
					out.connect((target, SEND_PORT))
					out.send(output)
					out.close()
				except ConnectionRefusedError:
					print("Node Connection Refused")
				except ConnectionResetError:
					print("Node Connection Reset")
				except TypeError:
					print("Not a string")
				except socket.gaierror:
					print("Node is down")

class GUI(Frame):
	def __init__(self, parent):
		Frame.__init__(self, parent)
		self.CreateUI()
		self.LoadTable()
		self.grid(sticky = (N,S,W,E))
		parent.grid_rowconfigure(0, weight = 1)
		parent.grid_columnconfigure(0, weight = 1)

	def CreateUI(self):
		tv = Treeview(self)
		tv['columns'] = ('status', 'call', 'wind', 'voltage')
		tv.heading("#0", text='Nodes', anchor='w')
		tv.column("#0", anchor="w")
		tv.heading('status', text='Status')
		tv.column('status', anchor='center', width=100)
		tv.heading('call', text='Call')
		tv.column('call', anchor='center', width=100)
		tv.heading('wind', text='Wind Speed (MPH)')
		tv.column('wind', anchor='center', width=100)
		tv.heading('voltage', text='Batt. Voltage')
		tv.column('voltage', anchor='center', width=100)
		tv.grid(sticky = (N,S,W,E))
		self.treeview = tv
		self.grid_rowconfigure(0, weight = 1)
		self.grid_columnconfigure(0, weight = 1)
		open_all_button = Button(root, text = 'Open All', command=self.OpenAll)
		open_all_button.place(relx = 0.5, rely = 0.4, anchor = 'center')
		close_all_button = Button(root, text = 'Close All', command=self.CloseAll)
		close_all_button.place(relx = 0.5, rely = 0.6, anchor = 'center')
		node1_oc_button = Button(root, text = NODE_ARRAY[0].NAME + ' - ' + 'Open/Close', command=self.Node1OpenClose)
		node1_oc_button.place(relx = 0.05, rely = 0.4, anchor = 'w')
		node1_call_button = Button(root, text = NODE_ARRAY[0].NAME + ' - ' + 'Call Toggle', command=self.Node1CallToggle)
		node1_call_button.place(relx = 0.05, rely = 0.6, anchor = 'w')
		node2_oc_button = Button(root, text = NODE_ARRAY[1].NAME + ' - ' + 'Open/Close', command=self.Node2OpenClose)
		node2_oc_button.place(relx = 0.95, rely = 0.4, anchor = 'e')
		node2_call_button = Button(root, text = NODE_ARRAY[1].NAME + ' - ' + 'Call Toggle', command=self.Node2CallToggle)
		node2_call_button.place(relx = 0.95, rely = 0.6, anchor = 'e')

	def LoadTable(self):
		global NODE_ARRAY
		self.treeview.insert('', 'end', text=NODE_ARRAY[0].NAME, values=('', '', NODE_ARRAY[0].WIND, NODE_ARRAY[0].VOLTAGE))
		self.treeview.insert('', 'end', text=NODE_ARRAY[1].NAME, values=('', '', NODE_ARRAY[1].WIND, NODE_ARRAY[0].VOLTAGE))

	def Refresh(self):
		global NODE_ARRAY
		for i in range(len(NODE_ARRAY)):
			child = 'I00' + str(i + 1)
			status = ''
			if not NODE_ARRAY[i].MOTOR_STATE:
				status = "Drive Failure"
			elif not NODE_ARRAY[i].WIND_STATE:
				status = "High Winds"
			elif NODE_ARRAY[i].ACTIVE:
				status = "In Motion"
			elif NODE_ARRAY[i].UP_STATE:
				status = "Open"
			elif NODE_ARRAY[i].DOWN_STATE:
				status = "Closed"
			if NODE_ARRAY[i].CALL_STATE:
				call = "XXX"
			else:
				call = ""
			self.treeview.item(child, values=(status, call, round(NODE_ARRAY[i].WIND, 2), round(NODE_ARRAY[i].VOLTAGE, 2)))
		self.after(1000, self.Refresh)

	def OpenAll(self):
		global NODE_ARRAY
		for i in range(len(NODE_ARRAY)):
			data = {}
			data.update({"UP": True, "TARGET": NODE_ARRAY[i].NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))

	def CloseAll(self):
		global NODE_ARRAY
		for i in range(len(NODE_ARRAY)):
			data = {}
			data.update({"DOWN": True, "TARGET": NODE_ARRAY[i].NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))

	def Node1OpenClose(self):
		node = NODE_ARRAY[0]
		state = ""
		data = {}
		if node.UP_STATE:
			data.update({"DOWN": True, "TARGET": node.NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))
		else:
			data.update({"UP": True, "TARGET": node.NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))

	def Node1CallToggle(self):
		node = NODE_ARRAY[0]
		state = ""
		data = {}
		if node.CALL_STATE:
			data.update({"CALL": False, "TARGET": node.NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))
		else:
			data.update({"CALL": True, "TARGET": node.NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))

	def Node2OpenClose(self):
		node = NODE_ARRAY[1]
		state = ""
		data = {}
		if node.UP_STATE:
			data.update({"DOWN": True, "TARGET": node.NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))
		else:
			data.update({"UP": True, "TARGET": node.NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))

	def Node2CallToggle(self):
		node = NODE_ARRAY[1]
		state = ""
		data = {}
		if node.CALL_STATE:
			data.update({"CALL": False, "TARGET": node.NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))
		else:
			data.update({"CALL": True, "TARGET": node.NODE})
			OUTPUT_QUEUE.append(pickle.dumps(data))


# Main Program Start
a = Remote_In("Remote_In")
b = Parser("Parser")
c = Output("Output")
a.start()
b.start()
c.start()

NODE_ARRAY.append(Node("Umbrella", "SUN_NODE_1305"))
NODE_ARRAY.append(Node("LED Breadboard", "SUN_NODE_221d"))

root = Tk()
root.title("S.U.N. Shade Sysytem")
window = GUI(root)
root.after(1000, window.Refresh)
root.mainloop()

EXIT = True

