from controllers import Caen, MHV4
import serial
import json
import time

with open('config.json','r') as f:
    config = json.loads(f.read())


ports = {

}


def fingerprint(port):
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
        for device in config['devices']:
            if(config['devices'][device]['controller'] == "Caen" and config['devices'][device]['serial_number'] == ret['serial_number']):
                config['devices'][device]['port'] = port

        caen.close()
    elif("MSCF-16" in response[2]):
        ret['type'] = "MSCF-16"
        ser.close()
    elif("MHV-4" in response[2]):
        ret['type'] = "MHV4"
        ser.flushOutput()
        ser.close()
        mhv4 = MHV4(port,9600,[50,50,50,50],2.5)
        for device in config['devices']:
            if(config['devices'][device]['controller'] == "MHV4"):
                config['devices'][device]['port'] = port
                config['devices'][device]['voltages'] = [mhv4.get_voltage_preset(i) for i in range(1,5)]
        mhv4.close()
    else:
        print(response)
        ret['type'] = "Unknown"
    return ret
for i in range(4,5):
    port = '/dev/ttyUSB' + str(i)
    config['ports'][port] = fingerprint(port)

with open('config.json','w') as f:
    f.write(json.dumps(config))

