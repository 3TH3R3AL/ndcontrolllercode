from controllers import Caen, MHV4
import serial
import json

ports = {

}


def fingerprint(port):
    ret = {}
    ser = serial.Serial(port=port, baudrate=9600, timeout=1)
    ser.write(
                bytes('?\r\n', "utf8")
            )
    response = ser.readline().decode()
    print(port)
    print(response)
    response = ser.readline().decode()
    print(response)

for i in range(0,5):
    port = '/dev/ttyUSB' + str(i)
    ports[port] = fingerprint(port)

with open('config.json','w') as f:
    f.write(json.dumps(ports))

