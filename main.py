from controllers import Caen, MHV4
import json
import time
import sys
import socket
import select
import threading

with open("config.json", "r") as f:
    config = json.loads(f.read())
enabled = [True,True,True,True]

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

print("server started")
while nbreak:
    rxfds, txfds, exfds = select.select(rxset, txset, rxset)

    for sock in rxfds:
        if sock is server:
            conn, addr = server.accept()
            conn.setblocking(0)
            rxset.append(conn)
            for name, device in devices.items():
                if(device != {}):
                    device.thread = threading.Thread(target=device.start_queue_processing,args=(conn,))
                    device.thread.start()

            print("Connection from address:", addr)
            '''
            welcome_message = "Connected to stgcontrol server\r\n"
            conn.sendall(welcome_message.encode())'''
        else:
            try:
                #for _,device in devices.
                rec = sock.recv(BUFFER_SIZE).decode('utf-8')
                split = rec.split("\n")
                if(split == ['']):
                    raise RuntimeError("Connection Closed")
                #print(split)
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
                        continue
                    if command["action"] == "close":
                        nbreak = 0
                        sock.close()
                        for _, device in devices.items():
                            if(device != {}): device.close()
                        break
                    elif(command["action"] == "set_on" or command["action"] == "set_off"):
                        #print(command["action"],"added to queue")
                        device.queue.appendleft(command)
                    else:
                        if((command["action"] != "get_voltage" and command["action"] != "get_current") or command["device"] != "MHV4" or command["channel"] == 1):
                            
                            #print(command)
                            device.queue.append(command)

                        

                    if(len(device.queue) > 10):
                        print(command["device"],"is over queued")
                #print([(len(device.queue) if device != {} else 0) for _,device in devices.items()])
            except Exception() as e:
                print("Connection closed by remote end: ",e)
                rxset.remove(sock)
                sock.close()
server.close()
