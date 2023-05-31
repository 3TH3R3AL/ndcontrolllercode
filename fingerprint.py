from controllers import Caen, MHV4
import serial
import json
import time

ports = {

}


def fingerprint(port):
    print(port)
    ret = {}
    ser = serial.Serial(port=port, baudrate=9600, timeout=1)
    time.sleep(0.1)
    ser.flushInput()
    ser.flushOutput()
    time.sleep(0.1)
    ser.write(
                bytes('?\r\n', "utf8")
            )
    
    
    response = []
    for i in range(0,2):
        response.append(ser.readline().decode())
    
    if("?" not in response[0]):
        ret['type'] = "CAEN"
        ser.close()
        caen = Caen(9600,port=port)
        ret['serial_number'] = caen.get_serial_number()
        caen.close()
    elif("MSCF-16" in response[1]):
        ret['type'] = "MSCF-16"
        ser.close()
    elif("MHV-4" in response[1]):
        ret['type'] = "MHV-4"
        ser.close()
    else:
        ret['type'] = "Unknown"
    ser.flushInput()
    time.sleep(0.1)
    return ret
for i in range(0,5):
    port = '/dev/ttyUSB' + str(i)
    ports[port] = fingerprint(port)

with open('config.json','w') as f:
    f.write(json.dumps(ports))

