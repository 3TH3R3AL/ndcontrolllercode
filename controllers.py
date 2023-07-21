#! /bin/python
import re
import time
from collections import deque
import serial

VOLTAGE_LIMIT = 100
LOCK_TIMEOUT = 5
RAMP_INTERVAL = 1
LOCK_PATH = "/tmp/"
def formatResponse(action,device,channel,data):
    return "|{action},{device},{channel},{data}|\r\n".format(action=str(action),price=str(action),device=str(device),channel=int(channel),data=float(data)).encode()

def processCommand(command,device):
    sock = device.sock
    if sock.fileno() == -1:
        print("Socket is closed or disconnected.")
        return
    if command["action"] == "set_on":
        device.set_on(command["channel"])
        print("set on",command["device"],command["channel"])
    elif command["action"] == "set_off":
        device.set_off(command["channel"])
        print("set off",command["device"],command["channel"])

    elif command["action"] == "heartbeat":
        sock.send(formatResponse("heartbeat",command["device"],0,device.heartbeat()))

    elif command["action"] == "get_voltage":
        voltage = device.get_voltage(command["channel"])
        #print(command["device"],command["channel"],voltage)
        sock.send(formatResponse("get_voltage",command["device"],command["channel"],voltage))

    elif command["action"] == "get_current":
        sock.send(formatResponse("get_current",command["device"],command["channel"],device.get_current(command["channel"])))


class Caen:
    def __init__(self, baud, **kwargs):
        # Kwargs include serial_number, port
        self.port = kwargs['port'] if 'port' in kwargs else "/dev/ttyUSB0"
        self.ser = serial.Serial(port=self.port, baudrate=baud, timeout=1)
        time.sleep(0.1)  # Wait 100 ms after opening the port before sending commands
        self.ser.flushInput()  # Flush the input buffer of the serial port before sending any new commands
        time.sleep(0.1)
        self.queue = deque()
        self.thread = {}
        self.sock = {}
        self.enabled_channels = kwargs['enabled_channels'] if 'enabled_channels' in kwargs else [True,True,True,True]
        self.processing = True
        self.serial_number = self.get_serial_number()
        i = 1
        if('serial_number' in kwargs):
            while self.serial_number != kwargs["serial_number"]:
                self.port = "/dev/ttyUSB" + str(i)
                self.ser.close()
                self.ser = serial.Serial(port=self.port, baudrate=baud, timeout=1)
                time.sleep(0.1)  # Wait 100 ms after opening the port before sending commands
                self.ser.flushInput()
                time.sleep(0.1)
                self.serial_number = self.get_serial_number()
                i += 1

    def close(self):
        self.processing = False
        self.ser.close()

    def send_command(self, command="", channel="", parameter="", format="", value=0):
        time.sleep(0.1)
        if command == "" or channel == "":
            return ""
        COMMAND_STRING = "$BD:0,CMD:{CMD},CH:{CH},PAR:{PAR}{VAL}\r\n"

        if format != "":
            value = ",VAL:{value}".format(value=format.format(value=value))
        else:
            value = ""
        if channel == -1:
            COMMAND_STRING = "$BD:0,CMD:{CMD},PAR:{PAR}\r\n"
            self.ser.write(
                bytes(COMMAND_STRING.format(CMD=command, PAR=parameter), "utf8")
            )  # works better with older Python3 versions (<3.5)

        else:
            self.ser.write(
                bytes(
                    COMMAND_STRING.format(
                        CMD=command, CH=channel, PAR=parameter, VAL=value
                    ),
                    "utf8",
                )
            )  # works better with older Python3 versions (<3.5)
        time.sleep(0.1)
        returnVal = self.ser.readline().decode()
        if "ERR" in returnVal:
            print("Error: ", returnVal)
            raise Exception(returnVal)
        return returnVal  # return response from the unit

    def start_queue_processing(self,sock):
        self.sock = sock
        while self.processing:
            if self.queue:
                try:
                    processCommand(self.queue.popleft(),self)
                except Exception as e:
                    print(e)
            else:
                time.sleep(0.1)

    def flush_input_buffer(self):
        self.ser.flushInput()
    def flush_output_buffer(self):
        self.ser.flushOutput()

    def set_on(self, channel):
        if channel not in [0, 1, 2, 3, 4]:
            return
        response = self.send_command(channel=channel, command="SET", parameter="ON")

    def set_off(self, channel):
        if channel not in [0, 1, 2, 3, 4]:
            return
        response = self.send_command(channel=channel, command="SET", parameter="OFF")

    def get_voltage(self, channel):
        response = self.send_command(channel=channel, command="MON", parameter="VMON")
        linestr = response
        pattern = re.match(r".*VAL:(\d*.\d*)", linestr, re.IGNORECASE)

        if pattern is not None:
            voltage = float(pattern.group(1))
            return voltage
        else:
            return 0.0

    def get_serial_number(self):
        response = self.send_command(channel=-1, command="MON", parameter="BDSNUM")
        linestr = response
        pattern = re.match(r".*VAL:(\d*)", linestr, re.IGNORECASE)

        if pattern is not None:
            voltage = int(pattern.group(1))
            return voltage
        else:
            return 0.0

    def get_voltage_limit(self, channel):
        response = self.send_command(channel=channel, command="MON", parameter="MAXV")
        linestr = response
        pattern = re.match(r".*([+-])(\d*.\d*)", linestr, re.IGNORECASE)

        if pattern is not None:
            voltage = float(pattern.group(2))
            if pattern.group(1) == "-":
                voltage = -voltage
            return voltage
        else:
            return 0.0

    def get_current(self, channel):
        response = self.send_command(channel=channel, command="MON", parameter="IMON")
        linestr = response
        pattern = re.match(r".*([+-])(\d*.\d*)", linestr, re.IGNORECASE)

        if pattern is not None:
            current = float(pattern.group(2))
            if pattern.group(1) == "-":
                current = -current
            return current
        else:
            return 0.0

    def get_current_limit(self, channel):
        return self.current_limits[channel]

    def get_ramp(self, channel):
        response = self.send_command(channel=channel, command="MON", parameter="RUP")
        linestr = response
        pattern = re.match(r".*([+-])(\d*.\d*)", linestr, re.IGNORECASE)

        if pattern is not None:
            current = float(pattern.group(2))
            if pattern.group(1) == "-":
                current = -current
            return current
        else:
            return 0.0

    def set_voltage(self, channel, voltage):
        if voltage > VOLTAGE_LIMIT:  # safety check limit in the library
            return

        response = self.send_command(
            channel=channel,
            command="SET",
            parameter="VSET",
            value=voltage,
            format="{value:06.1f}",
        )
        return response

    def set_voltage_limit(self, channel, limit):
        response = self.send_command(
            channel=channel,
            command="SET",
            parameter="MAXV",
            value=limit,
            format="{value:07.2f}",
        )

    def set_voltage_polarity(self, channel, pol):
        response = self.send_command(channel=channel, command="SET", parameter="MAXV")
        return response

    def set_ramp_up(self, channel, rate):
        self.ramp_rate = rate
        response = self.send_command(
            channel=channel,
            command="SET",
            parameter="RUP",
            value=rate,
            format="{value:0>3d}",
        )

    def set_ramp_down(self, channel, rate):
        self.ramp_rate = rate
        response = self.send_command(
            channel=channel,
            command="SET",
            parameter="RDW",
            value=rate,
            format="{value:0>3d}",
        )
    def heartbeat(self):
        return self.get_serial_number() == self.serial_number


class MHV4:
    def __init__(self, port, baud, voltage_limits, ramp_rate,**kwargs):
        self.port = port
        self.voltage_limits = voltage_limits
        self.ramp_rate = ramp_rate
        self.queue = deque()
        self.processing = True
        self.thread = {}
        self.current_limits = kwargs['current_limits'] if 'current_limits' in kwargs else [0,0.7,0.7,0.7,0.45]
        self.sock = {}
        self.enabled_channels = kwargs['enabled_channels'] if 'enabled_channels' in kwargs else [0,True,True,True,True]
        print("MHV4: ",self.enabled_channels)
        self.ser = serial.Serial(port=self.port, baudrate=baud, timeout=1)
        time.sleep(0.1)  # Wait 100 ms after opening the port before sending commands
        self.ser.flushInput()  # Flush the input buffer of the serial port before sending any new commands
        time.sleep(0.1)
        

    
    def close(self):
        self.processing = False
        self.ser.close()

    def send_command(self, command=""):
        time.sleep(0.2)
        command += "\r"
        #print("sent command '", bytes(command, "utf8"), "'", sep="")
        if command == "":
            return ""
        print(command)
        self.ser.write(bytes(command, "utf8"))
        time.sleep(0.1)
        self.ser.readline()
        resp = self.ser.readline()
        self.flush_input_buffer()
        return resp

    def start_queue_processing(self,sock):
        self.sock = sock
        self.send_command("C1")
        time.sleep(0.1)
        for i in range(1,5):
            self.set_voltage(i,0)
            time.sleep(0.1)
            self.set_current_limit(i,0.7)
            time.sleep(0.1)

        while self.processing:
            if self.queue:
                try:
                    processCommand(self.queue.popleft(),self)
                except Exception as e:
                    print(e)
            else:
                time.sleep(0.1)
    def flush_input_buffer(self):
        self.ser.flushInput()
    def flush_output_buffer(self):
        self.ser.flushOutput()
    def set_on(self, channel):
        if channel not in [0, 1, 2, 3, 4]:
            return
        response = self.send_command("ON%d" % channel)
        self.ramp_up(channel)

    def set_off(self, channel):
        if channel not in [0, 1, 2, 3, 4]:
            return
        self.ramp_down(channel)
        response = self.send_command("OFF%d" % channel)

    def get_voltage(self, channel):
        response = self.send_command("U%d" % channel)
        linestr = response.decode("utf8")
        pattern = re.match(r".*([+-])(\d*.\d*)", linestr, re.IGNORECASE)

        if pattern is not None:
            voltage = float(pattern.group(2))
            if pattern.group(1) == "-":
                voltage = -voltage
            return voltage
        else:
            return 0.0
    def get_voltage_preset(self, channel):
        response = self.send_command("R%d" % channel)
        linestr = response.decode("utf8")
        pattern = re.match(r".*([\+\-\ ])(\d*.\d*) V", linestr, re.IGNORECASE)

        if pattern is not None:
            voltage = float(pattern.group(2))
            if pattern.group(1) == "-":
                voltage = -voltage
            return voltage
        else:
            return 0.0
    def get_voltage_limit(self, channel):
        return self.voltage_limit[channel]

    def get_current(self, channel):
        response = self.send_command("R%d" % channel)
        linestr = response.decode("utf8")
        pattern = re.match(r".*([+-])(\d*.\d*)", linestr, re.IGNORECASE)

        if pattern is not None:
            current = float(pattern.group(2))
            if pattern.group(1) == "-":
                current = -current
            return current
        else:
            return 0.0

    def get_current_limit(self, channel):
        return self.current_limits[channel]

    def get_polarity(self, channel):
        """not tested !"""
        response = self.send_command("RP %d" % channel)
        return response.decode("utf8")

    def get_temp(self, inputc):
        """not tested ! Get temperature at given input"""
        response = self.send_command("RT %d" % inputc)
        return response.decode("utf8")

    def get_ramp(self):
        return self.ramp_rate

    def set_voltage(self, channel, voltage):
        if voltage > VOLTAGE_LIMIT:  # safety check limit in the library
            return

        # MHV-4 protocol expects voltage in 0.1 V units
        response = self.send_command("S%d %04d" % (channel, voltage * 10))
        return response.decode("utf8")

    def set_current_limit(self, channel, limit):
        response = self.send_command("T%d %04d" % (channel, limit*100))
        return response.decode("utf8")

    def set_voltage_limit(self, channel, limit):
        self.voltage_limits[channel] = limit

    def set_voltage_polarity(self, channel, pol):
        response = self.send_command("SP %d %d" % (channel, pol))
        return response.decode("utf8")

    def set_ramp(self, rate):
        self.ramp_rate = rate

    def ramp_up(self, channel):
        voltage = 0
        interval = self.ramp_rate * RAMP_INTERVAL
        maximum = self.voltage_limits[channel]
        print(maximum)
        while True:
            voltage += interval
            if voltage > maximum:
                voltage = maximum

            self.send_command("S%d %04d" % (channel, voltage*10))
            if voltage == maximum:
                break

            time.sleep(RAMP_INTERVAL)
        self.flush_input_buffer()
    def ramp_down(self, channel):
        voltage = self.voltage_limits[channel]
        interval = self.ramp_rate * RAMP_INTERVAL
        while True:
            voltage -= interval
            if voltage < 0:
                voltage = 0
            response = self.send_command("S%d %04d" % (channel, voltage * 10))
            if voltage == 0:
                break

            time.sleep(RAMP_INTERVAL)
            self.flush_input_buffer()
    def ramp_to(self, channel, target_voltage):
        voltage = self.get_voltage()
        if voltage == target_voltage:
            return
        direction = 1 if voltage < target_voltage else -1
        interval = self.ramp_rate * RAMP_INTERVAL * direction 
        while True:
            voltage += interval
            if voltage * direction > target_voltage * direction:
                voltage = target_voltage

            self.send_command("S%d %d" % (channel, voltage* 10))
            if voltage == target_voltage:
                break

            time.sleep(RAMP_INTERVAL)
    def heartbeat(self):
        response  = self.send_command("PR")
        time.sleep(0.3)
        self.flush_output_buffer()
        self.flush_input_buffer()
        return response  == b'\rMHV-4 preset summary:\n'
    '''
mhv4 = MHV4("/dev/ttyUSB4",9600,[0,0,0,0],3)
print(mhv4.heartbeat())
print(mhv4.heartbeat())
print(mhv4.heartbeat())
print(mhv4.heartbeat())
print(mhv4.heartbeat())
print(mhv4.heartbeat())'''