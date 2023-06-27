import socket

def handle_client(client_socket):
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        print(data, end='')

    client_socket.close()

def run_server():
    host = '127.0.0.1'  # localhost
    port = 8000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection established from {client_address[0]}:{client_address[1]}")
        handle_client(client_socket)

if __name__ == '__main__':
    run_server()