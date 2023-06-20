from controllers import Caen, MHV4
import json
import time
import sys
import socket
import select

with open('config.json','r') as f:
    config = json.loads(f.read())



caen1 = Caen(9600,port=config['devices']["CAEN 1"]["port"])
caen2 = Caen(9600,port=config['devices']["CAEN 2"]["port"])
caen3 = Caen(9600,port=config['devices']["CAEN 3"]["port"])
mhv4 = MHV4(config['devices']["MHV4"]["port"],9600,config['devices']["MHV4"]["voltages"],2.5)

devices = {
    "CAEN 1": caen1,
    "CAEN 2": caen2,
    "CAEN 3": caen3,
    "MHV4": mhv4
}


TCP_IP = '0.0.0.0'
TCP_PORT = 8880
BUFFER_SIZE = 1024
param = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((TCP_IP,TCP_PORT))
server.listen(1)

rxset = [server]
txset = []
nbreak = 1
while nbreak:
    rxfds, txfds, exfds = select.select(rxset, txset, rxset)

    for sock in rxfds:
        if sock is server:
            conn, addr = server.accept()
            conn.setblocking(0)
            rxset.append(conn)
            print('Connection from address:', addr)
        else:
            try:
                data = sock.recv(BUFFER_SIZE)
                if data == ";" :
                    print("Received all the data")
                    for x in param:
                        print(x)
                    param = []
                    rxset.remove(sock)
                    sock.close()
                else:
                    command = json.loads(data)
                    device = devices[command["device"]]
                    if(command["action"] == "set_on"):
                        device.set_on(command["channel"])
                    elif(command["action"] == "set_off"):
                        device.set_on(command["channel"])
                    elif(command["action"] == "heartbeat"):
                        sock.send(device.heartbeat().encode())
                    elif(command["action"] == "close"):
                        nbreak = 0
                        sock.close()
                        break;
                    param.append(data)
            except:
                print("Connection closed by remote end")
                param = []
                rxset.remove(sock)
                sock.close()


    
