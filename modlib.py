# -*- coding: utf-8 -*-
"""
The library for controlling the Mesytec MHV-4 high voltage unit via
the USB serial control interface.

Protocol data format is 9600 baud 8N1 (8 bit, no parity, 1 stop bit)
The input characters are echoed before the response from the unit.
"""
__author__ = "Joonas Konki"
__license__ = "MIT, see LICENSE for more details"
__copyright__ = "2018 Joonas Konki"

import serial
import time
import re
from lockfile import LockFile

VOLTAGE_LIMIT = 100
LOCK_TIMEOUT = 5
RAMP_INTERVAL = 0.05
LOCK_PATH = '/tmp/'

class MHV4():
    def __init__(self,port,baud,voltage_limits,current_limits,ramp_rate):
        lock_file = '.mhv4lib.'+port[4:]+'.lock'
        print(lock_file)
        self.lock = LockFile(LOCK_PATH + lock_file)
        try:
            if not self.lock.acquire(timeout=LOCK_TIMEOUT):
                raise Exception()
            if self.lock.is_locked():
                print('Lockfile acquired successfully: ' + LOCK_PATH + lock_file )
                self.port = port
                self.voltage_limits = voltage_limits
                self.current_limits = current_limits
                self.ramp_rate = ramp_rate
                self.ser = serial.Serial( port=self.port, baudrate=baud, timeout=1 )
                time.sleep(0.1) # Wait 100 ms after opening the port before sending commands
                self.ser.flushInput() # Flush the input buffer of the serial port before sending any new commands
                time.sleep(0.1)
        except Exception as e:
            print('Lockfile could not be acquired for port ' + port)
            print('Is there another program using mhv4lib ??')



    def close(self):
        """The function closes and releases the serial port connection attached to the unit.

        """
        self.ser.close()
        self.lock.release()

    def send_command(self, command=''):
        """The function sends a command to the unit and returns the response string.

        """
        if command == '': return ''
        self.ser.write( bytes(command, 'utf8') ) # works better with older Python3 versions (<3.5)
        time.sleep(0.1)
        self.ser.readline() # read out echoed command
        return self.ser.readline() # return response from the unit

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
        response = self.send_command( 'ON %d\r' % channel )

    def set_off(self,channel):
        """The function turns the voltage OFF for the given ``channel`` number.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that is to be turned OFF.
        """

        if channel not in [0,1,2,3,4]: return
        response = self.send_command( 'OFF %d\r' % channel )

    def get_voltage(self,channel):
        """The function returns the measured voltage reading of the given ``channel`` number.
        The possible channel numbers are 0,1,2,3.
        Number 4 applies to ALL channels (not tested?).

        Note: Returns always 0, if the channel is turned OFF !

        :param channel: The channel number of which the voltage reading is requested.
                        The return value is positive or negative depending on the set polarity.
        """
        response = self.send_command( 'RU %d\r' % channel )
        linestr = response.decode('utf8')
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
        return self.voltage_limit[channel]

    def get_current(self,channel):
        response = self.send_command( 'RI %d\r' % channel )
        linestr = response.decode('utf8')
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


    def get_polarity(self,channel):
        """ not tested !"""
        response = self.send_command( 'RP %d\r' % channel )
        return response.decode('utf8')

    def get_temp(self,inputc):
        """ not tested ! Get temperature at given input"""
        response = self.send_command( 'RT %d\r' % inputc )
        return response.decode('utf8')
# irdk what this means, so not implementing it yet
    '''def get_temp_comp(self,channel):
        """ not tested ! Get complete settings for temperature compensation of
        given channel"""
        response = self.send_command( 'RTC %d\r' % channel )
        return response.decode('utf8')
'''
    def get_ramp(self):
        return self.ramp_rate
    def set_voltage(self,channel, voltage):
        """The function sets the voltage of the given ``channel`` number to ``voltage``.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that the voltage setting is applied to.
        :param voltage: The voltage that is to be set for the channel in Volts.
        """
        if voltage > VOLTAGE_LIMIT: # safety check limit in the library
            return

        # MHV-4 protocol expects voltage in 0.1 V units
        response = self.send_command( 'SU %d %d\r' % (channel, voltage*10) )
        return response.decode('utf8')

    def set_current_limit(self,channel, limit):
        """The function sets the current limit of the given ``channel`` number
        to ``limit``.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that the current limit setting is applied to.
        :param limit: The current limit value that is to be set for the channel in units of nA.
        """

        self.current_limits[channel] = limit

    def set_voltage_limit(self,channel, limit):
        """The function sets the voltage limit of the given ``channel`` number
        to ``limit``.
        The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.

        :param channel: The channel number that the voltage limit setting is applied to.
        :param limit: The voltage limit value that is to be set for the channel in units of Volts.
        """
        # MHV-4 protocol expects voltage in 0.1 V units
        self.voltage_limits[channel] = limit

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
        response = self.send_command( 'SP %d %d\r' % (channel, pol) )
        return response.decode('utf8')

    def set_ramp(self, rate):
        """The function sets the ramp speed of the whole unit.

        :param n: The desired ramp speed option 
        """
        self.ramp_rate = rate 
    def ramp_up(self,channel):
        voltage = 0
        interval = self.ramp_rate*RAMP_INTERVAL
        maximum = self.voltage_limits[channel]
        while True:
            voltage += interval
            if(voltage > maximum):
                voltage = maximum
            
            response = self.send_command( 'SP %d %d\r' % (channel, voltage) )
            if(voltage == maximum):
                break
            
            time.sleep(RAMP_INTERVAL)
    def ramp_down(self,channel):
        voltage = self.voltage_limits[channel]
        interval = self.ramp_rate*RAMP_INTERVAL
        while True:
            voltage -= interval
            if(voltage < 0):
                voltage = 0
            response = self.send_command( 'SP %d %d\r' % (channel, voltage) )
            if(voltage == 0):
                break
            
            time.sleep(RAMP_INTERVAL)
    def ramp_to(self,channel,target_voltage):
        voltage = self.get_voltage()
        if(voltage == target_voltage):
            return
        direction = 1 if voltage < target_voltage else -1
        interval = self.ramp_rate*RAMP_INTERVAL * direction
        while True:
            voltage += interval
            if(voltage*direction > target_voltage*direction):
                voltage = target_voltage
            
            response = self.send_command( 'SP %d %d\r' % (channel, voltage) )
            if(voltage == target_voltage):
                break
            
            time.sleep(RAMP_INTERVAL)

mhv1 = MHV4("/dev/ttyUSB4",9600,[50,50,50,50],[40,40,40,40],2.5)
mhv1.set_on(1)
mhv1.ramp_up(1)