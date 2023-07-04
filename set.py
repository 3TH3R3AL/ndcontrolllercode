from controllers import Caen, MHV4
import json
import time
import sys
import socket
import select

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