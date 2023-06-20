import socket

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to all network interfaces and a specific port
server_address = ('0.0.0.0', 8880)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(5)
print("Server started. Listening for incoming connections...")

while True:
    # Wait for a connection
    client_socket, client_address = sock.accept()
    print(f"Connection established from: {client_address}")

    # Send a welcome message to the client
    welcome_message = "Welcome to the server!"
    client_socket.sendall(welcome_message.encode())

    # Close the client connection
    client_socket.close()