#! /bin/python
import re
import time

import serial

VOLTAGE_LIMIT = 100
LOCK_TIMEOUT = 5
RAMP_INTERVAL = 1
# From Manual: $BD:**,CMD:***,CH*,PAR:***,VAL:***.**<CR, LF >
COMMAND_STRING = "$BD:0,CMD:{CMD},CH:{CH},PAR:{PAR}{VAL}\r\n"
LOCK_PATH = '/tmp/'

class Caen():
    def __init__(self,port,baud,voltage_limits,ramp_rate):
        self.port = port
        self.voltage_limits = voltage_limits
        self.ramp_rate = ramp_rate
        self.ser = serial.Serial( port=self.port, baudrate=baud, timeout=1 )
        time.sleep(0.1) # Wait 100 ms after opening the port before sending commands
        self.ser.flushInput() # Flush the input buffer of the serial port before sending any new commands
        time.sleep(0.1)
    def close(self):
        """The function closes and releases the serial port connection attached to the unit.

        """
        self.ser.close()
        #:with expression as target:
            #pass.lock.release()

    def send_command(self, command='', channel='', parameter='',format='',value=0):
        """The function sends a command to the unit and returns the response string.

        """
        if command == '' or channel == '': return ''

        if(format != ''):
            value = ',VAL:{value}'.format(value = format.format(value=value))
        else:
            value = ''
        print("sent command '",bytes(COMMAND_STRING.format(CMD = command, CH = channel, PAR = parameter, VAL = value), 'utf8'),"'",sep="")
        self.ser.write( bytes(COMMAND_STRING.format(CMD = command, CH = channel, PAR = parameter, VAL = value), 'utf8') ) # works better with older Python3 versions (<3.5)
        time.sleep(0.1)
        returnVal = self.ser.readline().decode()
        print("returned: ",returnVal)
        if("ERR" in returnVal):
            print("Error: ",returnVal)
            raise Exception(returnVal)
        return returnVal # return response from the unit

    def flush_input_buffer(self):
        """ Flush the input buffer of the serial port.
        """
        self.ser.flushInput()

    def set_on(self,channel):
        """The function turns the voltage ON for the given ``channel`` number.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that is to be turned ON.
        """

        if channel not in [0,1,2,3,4]: return
        response = self.send_command(channel=channel,command='SET',parameter='ON')
        

    def set_off(self,channel):
        """The function turns the voltage OFF for the given ``channel`` number.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that is to be turned OFF.
        """

        if channel not in [0,1,2,3,4]: return
        response = self.send_command(channel=channel,command='SET',parameter='OFF')

    def get_voltage(self,channel):
        """The function returns the measured voltage reading of the given ``channel`` number.
        The possible channel numbers are 0,1,2,3.
        Number 4 applies to ALL channels (not tested?).

        Note: Returns always 0, if the channel is turned OFF !

        :param channel: The channel number of which the voltage reading is requested.
                        The return value is positive or negative depending on the set polarity.
        """
        response = self.send_command(channel=channel,command='MON',parameter='VMON')
        print(response)
        linestr = response
        pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)

        if pattern is not None:
            voltage = float(pattern.group(2))
            if pattern.group(1) == '-':
                voltage = -voltage
            return voltage
        else :
            return 0.

    def get_voltage_limit(self,channel):
        """
        The possible channel numbers are 0,1,2,3.
        Number 4 applies to ALL channels (not tested?).

        :param channel: The channel number of which the preset voltage reading is requested.
                        The return value is positive regardless of what the polarity is set to.
        """
        response = self.send_command(channel=channel,command='MON',parameter='MAXV')
        linestr = response
        pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)

        if pattern is not None:
            voltage = float(pattern.group(2))
            if pattern.group(1) == '-':
                voltage = -voltage
            return voltage
        else :
            return 0.

    def get_current(self,channel):
        response = self.send_command(channel=channel,command='MON',parameter='IMON')
        linestr = response
        pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)

        if pattern is not None:
            current = float(pattern.group(2))
            if pattern.group(1) == '-':
                current = -current
            return current
        else :
            return 0.

    def get_current_limit(self,channel):
        return self.current_limits[channel]

    ''' 
Not Yet Implemented
    def get_polarity(self,channel):
        """ not tested !"""
        response = self.send_command(channel=channel,command='MON',parameter='IMON')
        return response.decode('utf8')

    def get_temp(self,inputc):
        """ not tested ! Get temperature at given input"""
        response = self.send_command(channel=channel,command='MON',parameter='IMON')
        return response.decode('utf8')
    def get_temp_comp(self,channel):
        """ not tested ! Get complete settings for temperature compensation of
        given channel"""
        response = self.send_command( 'RTC %d\r' % channel )
        return response.decode('utf8')
    '''

    def get_ramp(self,channel):
        response = self.send_command(channel=channel,command='MON',parameter='RUP')
        print(response)
        linestr = response
        pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)

        if pattern is not None:
            current = float(pattern.group(2))
            if pattern.group(1) == '-':
                current = -current
            return current
        else :
            return 0.
    def set_voltage(self,channel, voltage):
        """The function sets the voltage of the given ``channel`` number to ``voltage``.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that the voltage setting is applied to.
        :param voltage: The voltage that is to be set for the channel in Volts.
        """
        if voltage > VOLTAGE_LIMIT: # safety check limit in the library
            return

        # MHV-4 protocol expects voltage in 0.1 V units
        response = self.send_command(channel=channel,command='SET',parameter='VSET',value=voltage,format="{value:06.1f}")
        return response
    '''
    def set_current_limit(self,channel, limit):
        """The function sets the current limit of the given ``channel`` number
        to ``limit``.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that the current limit setting is applied to.
        :param limit: The current limit value that is to be set for the channel in units of nA.
        """

        response = self.send_command(channel=channel,command='SET',parameter='IMRANGE',value)
        return response.decode('utf8')
'''
    def set_voltage_limit(self,channel, limit):
        """The function sets the voltage limit of the given ``channel`` number
        to ``limit``.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that the voltage limit setting is applied to.
        :param limit: The voltage limit value that is to be set for the channel in units of Volts.
        """
        # MHV-4 protocol expects voltage in 0.1 V units
        response = self.send_command(channel=channel,command='SET',parameter='MAXV',value=limit,format="{value:07.2f}")

    def set_voltage_polarity(self,channel, pol):
        """The function sets the voltage polarity (negative/positive) for the given ``channel`` number.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        Note:   SP c p ,
                where c = channel, p = polarity: p/+/1 or n/-/0
                e.g.: SP 0 n sets the polarity of channel 0 to negative.

                For security reasons: if HV is on, it will be switched off automatically,
                HV preset will be set to 0 V, polarity is switched when	HV is down.
/dev/ttyUSB4
                After switching: set presets again to desired values.

        :param channel: The channel number that the polarity change is applied to.
        :param pol: The desired polarity of the voltage for the channel 0 or 1.
        """
        response = self.send_command(channel=channel,command='SET',parameter='MAXV')
        return response

    def set_ramp_up(self, channel, rate):
        """The function sets the ramp speed of the whole unit.

        :param n: The desired ramp speed option 
        """
        self.ramp_rate = rate 
        response = self.send_command(channel=channel,command='SET',parameter='RUP',value=rate,format="{value:0>3d}")
        print("Response RUP: ",response)
    def set_ramp_down(self, channel, rate):
        """The function sets the ramp speed of the whole unit.

        :param n: The desired ramp speed option 
        """
        self.ramp_rate = rate 
        response = self.send_command(channel=channel,command='SET',parameter='RDW',value=rate,format="{value:0>3d}")
        print("Response RDW: ",response)

caen = Caen("/dev/ttyUSB0",9600,[50,50,50,50],2.5)
#mhv1.send_command('?')
##
caen.get_voltage(3)
#mhv1.ramp_up(1)

