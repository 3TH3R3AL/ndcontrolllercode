import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('stgcontrol1.phys.nd.edu', 8888)
sock.connect(server_address)





message = '{"device": "MHV4","action":"heartbeat"}'
sock.send(message.encode())
sock.close()
