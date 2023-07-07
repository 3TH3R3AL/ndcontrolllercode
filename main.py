from controllers import Caen, MHV4
import json
import time
import sys
import socket
import select
import threading

with open("config.json", "r") as f:
    config = json.loads(f.read())
enabled = [True,True,True,False]

mhv4, caen1, caen2, caen3 = {},{},{},{}
if(enabled[0]): caen1 = Caen(9600, port=config["devices"]["CAEN 1"]["port"])
if(enabled[1]): caen2 = Caen(9600, port=config["devices"]["CAEN 2"]["port"])
if(enabled[2]): caen3 = Caen(9600, port=config["devices"]["CAEN 3"]["port"])
if(enabled[3]): mhv4 = MHV4(
    config["devices"]["MHV4"]["port"], 9600, config["devices"]["MHV4"]["voltages"], 2.5
)

devices = {"CAEN 1": caen1, "CAEN 2": caen2, "CAEN 3": caen3, "MHV4": mhv4}

caen1.set_voltage(1,100)
TCP_IP = "0.0.0.0"
TCP_PORT = 8880
BUFFER_SIZE = pow(2,15)
param = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((TCP_IP, TCP_PORT))
server.listen(1)

rxset = [server]
txset = []
nbreak = 1

def formatResponse(action,device,channel,data):
    return "|{action},{device},{channel},{data}|\r\n".format(action=str(action),price=str(action),device=str(device),channel=int(channel),data=float(data)).encode()


while nbreak:
    rxfds, txfds, exfds = select.select(rxset, txset, rxset)

    for sock in rxfds:
        if sock is server:
            conn, addr = server.accept()
            conn.setblocking(0)
            rxset.append(conn)
            for device in devices:
                if(device != {}):
                    device.thread = threading.Thread(target=device.start_queue_processing(sock))

            print("Connection from address:", addr)
            '''
            welcome_message = "Connected to stgcontrol server\r\n"
            conn.sendall(welcome_message.encode())'''
        else:
            try:
                rec = sock.recv(BUFFER_SIZE).decode('utf-8')
                split = rec.split("\n")
                if(split == ['']):
                    raise RuntimeError("Connection Closed")
                print(split)
                for data in split:
                    if(data == ""):
                        continue
                    try: 
                        command = json.loads(data)
                    except:
                        print("Bad command: \"",data,"\"")

                    device = devices[command["device"]]
                    if(device == {}):
                        sock.send(formatResponse("disabled",command["device"],0,0))
                    
                    if command["action"] == "close":
                        nbreak = 0
                        sock.close()
                        for _, device in devices.items():
                            if(device != {}): device.close()
                        break
                    device.queue.append(command)
            except Exception() as e:
                print("Connection closed by remote end: ",e)
                rxset.remove(sock)
                sock.close()
server.close()
