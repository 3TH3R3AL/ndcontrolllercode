from controllers import Caen, MHV4
import json
import time
import sys
import socket
import select
import threading
from log import log, startLogging, savePermLog
with open("config.json", "r") as f:
    config = json.loads(f.read())
enabled = [True,True,True,True]

mhv4, caen1, caen2, caen3 = {},{},{},{}
if(enabled[0]): caen1 = Caen(9600,name="CAEN 1", port=config["devices"]["CAEN 1"]["port"],enabled_channels=[False,False,False,True,False],voltage_presets=config["devices"]["CAEN 1"]["voltages"])
if(enabled[1]): caen2 = Caen(9600,name="CAEN 2", port=config["devices"]["CAEN 2"]["port"],voltage_presets=config["devices"]["CAEN 2"]["voltages"])
if(enabled[2]): caen3 = Caen(9600,name="CAEN 3", port=config["devices"]["CAEN 3"]["port"],voltage_presets=config["devices"]["CAEN 3"]["voltages"])
if(enabled[3]): mhv4 = MHV4(
    config["devices"]["MHV4"]["port"], 9600, config["devices"]["MHV4"]["voltages"], config["devices"]["MHV4"]["ramp_rate"],enabled_channels=[0,False,False,False,True],current_limits=config["devices"]["MHV4"]["current_limits"]
)

devices = {"CAEN 1": caen1, "CAEN 2": caen2, "CAEN 3": caen3, "MHV4": mhv4}
MHV4_CHANNEL = 4
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

log("main.log",["server started"])
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
            logging_thread = threading.Thread(target=startLogging, args=(devices,))
            logging_thread.daemon = True  # Set the thread as a daemon thread so it terminates automatically
            logging_thread.start()

            log("main.log",["Connection from address:", addr])
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
                #log("main.log",[split])
                for data in split:
                    if(data == ""):
                        continue
                    try: 
                        command = json.loads(data)
                    except:
                        log("main.log",["Bad command: \"",data,"\""])

                    device = devices[command["device"]]
                    if(device == {}):
                        sock.send(formatResponse("disabled",command["device"],0,0))
                        continue
                    if command["action"] == "close":
                        nbreak = 0
                        sock.close()
                        for _, device in devices.items():
                            if(device != {}): device.close()
                        with open('config.json','w') as f:
                            f.write(json.dumps(config))
                        savePermLog()
                        break
                    elif command["action"] == "reset_to_defaults":
                         with open("defaults.json", "r") as f:
                            config = json.loads(f.read())
                            for name, device in devices.items():
                                for i in range(len(device.enabled_channels)):
                                    if(device.enabled_channels[i]):
                                        device.queue.appendleft({"action":"set_property","property":"Voltage","channel":i,"amount":float(config["devices"][name]["voltages"][i])})
                                        if(name == "MHV4" and device.current_limits[i] != config["devices"][name]["current_limits"][i]):
                                            device.queue.appendleft({"action":"set_property","property":"Max Current","channel":i,"amount":float(config["devices"][name]["current_limits"][i])})


                    elif(command["action"] == "set_on" or command["action"] == "set_off" or command["action"] == "set_property"):
                        #log("main.log",[command["action"],"added to queue"])
                        if(command["action"] == "set_property" and command['property'] == 'Voltage'):
                            config["devices"][command["device"]]["voltages"][command["channel"]] = command['amount']
                        elif(command["action"] == "set_property" and command['property'] == 'Max Current'):
                            config["devices"][command["device"]]["current_limits"][command["channel"]] = command['amount']
                        
                        device.queue.appendleft(command)
                    else:
                        if((command["action"] != "get_voltage" and command["action"] != "get_current") or device.enabled_channels[command["channel"]]):
                            #log("main.log",[command])
                            if(len(device.queue) < 10):
                                device.queue.append(command)
                    if(len(device.queue) > 10):
                        log("main.log",[command["device"],"is over queued"])
                #log("main.log",[[(len(device.queue) if device != {} else 0) for _,device in devices.items()]])
            except Exception() as e:
                log("main.log",["Connection closed by remote end: ",e])
                rxset.remove(sock)
                sock.close()
server.close()
exit(0)