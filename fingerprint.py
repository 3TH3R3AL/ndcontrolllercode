from controllers import Caen
import serial
import json
import time

with open('config.json','r') as f:
    config = json.loads(f.read())


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
    for i in range(0,4):
        response.append(ser.readline().decode())
    
    if("?" not in response[0]):
        ret['type'] = "CAEN"
        ser.close()
        caen = Caen(9600,port=port)
        ret['serial_number'] = caen.get_serial_number()
        caen.close()
    elif("MSCF-16" in response[2]):
        ret['type'] = "MSCF-16"
        ser.close()
    elif("MHV-4" in response[2]):
        ret['type'] = "MHV-4"
        ser.close()
    else:
        print(response)
        ret['type'] = "Unknown"
    return ret
for i in range(0,5):
    port = '/dev/ttyUSB' + str(i)
    ports[port] = fingerprint(port)
config['ports'] = ports
with open('config.json','w') as f:
    f.write(json.dumps(config))

