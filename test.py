import socket

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
print("Server IP address:", ip_address)