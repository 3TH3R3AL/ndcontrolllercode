from controllers import Caen, MHV4
import json
import time

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

while True:
    command = json.loads(input("Command:"))
    device = devices[command["device"]]
    if(command["action"] == "set_on"):
        device.set_on(command["channel"])
    elif(command["action"] == "set_off"):
        device.set_on(command["channel"])
    elif(command["action"] == "heartbeat"):
        print(device.heartbeat())
    time.sleep(1)
