# client.py

import socket, pickle

server = "SUN_NODE_221d"
port = 12345
run = ""

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
soc.connect((server, port))

clients_input = {"WIND_STATE": True} 
soc.send(pickle.dumps(clients_input)) # we must encode the string to bytes
#run = input("/n/nDone? (y/n):  ")  
#result_bytes = soc.recv(4096) # the number means how the response can be in bytes  
#result_string = result_bytes.decode("utf8") # the return will be in bytes, so decode

#print("Result from server is {}".format(result_string))  

"""
Motor Down
Start spike 0.7A, 0.25A - 0.35A running
Motor up
Start Spike 0.6A, 0.35 - 0.50A running
batt up
0.49A - 0.65A  No canopy
batt Down
0.40A - 0.55A No canopy
batt idle
Idle draw 0.06A without voltage divider or wind sensor


47k
5.6k
 
27k

hall 2.59/2.6
sensor 1.67/1.68
"""