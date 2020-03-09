#!/usr/bin/env python
# This script will run the ads1115 in singleshot mode using pigpio. I couldn't
# find a library that uses this ADC with pigpio so I created my own.
# No other modes have been implemented as I only needed the singleshot mod. You
# are free to use this as a jumping off point if you wish to implement the
# other modes.
# This script has only been tested with python 3.X. Support for python 2.X is unknown

import time
import struct

# Comment this line out if using python 2.X
buffer = memoryview

# Register Values
CONVERSION_REG          = 0x00
CONFIG_REG              = 0x01

MUX_OFFSET              = 12

# Settings
CONFIG_DISABLE_COMPARATOR       = 0x0003
CONFIG_MODE_SINGLESHOT          = 0x0100

# Disabled/Unneeded Settings (Value = 0x0000)
#CONFIG_LATCHING                 = 0x0000
#CONFIG_COMPARATOR_POLARITY      = 0x0000
#CONFIG_COMPARATOR_MODE          = 0x0000

START_SINGLESHOT_CONVERSION     = 0x8000

# Units: SPS
CONFIG_DATA_RATE = {
    8:   0x0000,
    16:  0x0020,
    32:  0x0040,
    64:  0x0060,
    128: 0x0080,    # (default)
    250: 0x00A0,
    475: 0x00C0,
    860: 0x00E0
}

# Maping of gain values to config register values.
# To get analog voltage do: Gain_Voltage * ADC_Val / (2 ^ 15)
# Max/Min voltage the ADC can read is ±(min(Gain_Voltage, VDD + ~0.3))
# 0v = GND
CONFIG_GAIN = {
    2/3: 0x0000,    # Gain = ±6.144v
    1:   0x0200,    # Gain = ±4.096v (class default)
    2:   0x0400,    # Gain = ±2.048v (device default)
    4:   0x0600,    # Gain = ±1.024v
    8:   0x0800,    # Gain = ±0.512v
    16:  0x0A00     # Gain = ±0.256v
}

# Mapping of addresses depending on pin
DEVICE_ADDRESS = {
    "GND": 0x48,
    "VDD": 0x49,
    "SDA": 0x4A,
    "SCL": 0x4B
}


class ADS1115:

    # Arguements:
    # pi: The pigpio instance running
    # address: A hex value corrosponding to the devices address or a string of the name the ADDR pin is connected to
    # sensors: An array of numbers between 0 and 3 corrosponding to the analog pins that are in use (for readAll command)
    # gain: The gain you wish to use (Must give a key from CONFIG_GAIN)
    # data_rate: The data rate you wish to use in SPS (See CONFIG_DATA_RATE)
    # i2c_bus: The i2c bus you wish to use (Probably 1 on any current rpi)
    def __init__(self, pi, address, sensors, gain=1, data_rate=128, i2c_bus=1):
        if isinstance(address, int):
            if address not in DEVICE_ADDRESS.values():
                raise ValueError('Gain must be one of: 0x48, 0x49, 0x4A, 0x4B')
        else:
            if address not in DEVICE_ADDRESS:
                raise ValueError('Gain must be one of: \"GND\", \"VDD,\", \"SDA\", \"SCL\"')
            else:
                address = DEVICE_ADDRESS[address]

        if gain not in CONFIG_GAIN:
            raise ValueError('Gain must be one of: 2/3, 1, 2, 4, 8, 16')
        
        if data_rate not in CONFIG_DATA_RATE:
            raise ValueError('Data rate must be one of: 8, 16, 32, 64, 128, 250, 475, 860')

        self.pi = pi
        self.handle = pi.i2c_open(i2c_bus, address)
        self.maxVoltage = 4.096 / gain
        
        if self.handle < 0:
            raise Exception("I2C failed to open device " + DEVICE_ADDRESS[address] + " on bus " + i2c_bus)

        # Approx. amount of time the ADS1115 needs to get the data ready
        self.waitTime = (1.0/CONFIG_DATA_RATE[data_rate]) + 0.0001
        self.config = (CONFIG_DISABLE_COMPARATOR |
                       CONFIG_DATA_RATE[data_rate] |
                       CONFIG_MODE_SINGLESHOT |
                       CONFIG_GAIN[gain] |
                       START_SINGLESHOT_CONVERSION)

        self.sensors = sensors


    # Checks data against threshold and notifies if necessary
    # Higher number = drier soil
    @staticmethod
    def checkData(data, notifier, threshold):
        for i in data:
            if data[i] > threshold:
                notifier.send("Greenhouse - Moisture Sensor " + str(i) + " is too dry")


    # Reads all sensors as defined by self.sensors and returns data as dict
    def readAll(self):
        data = {}

        for i in self.sensors:
            data[i] = self.read(i)

        return data


    # Stops the i2c connection. Not much use except for example
    def stop(self):
        self.pi.i2c_close(self.handle)


    # Get voltage read by the ADC
    def getVoltage(self, pin):
        return self.read(pin) * self.maxVoltage / 0x7FFF


    # Get the raw data from the ADC
    def read(self, pin):

        # Calculate final i2c command
        cmd = ((pin + 4) << MUX_OFFSET) | self.config

        # Convert i2c command into raw bits
        buff = bytearray(3)
        buff[0] = CONFIG_REG
        buff[1] = (cmd >> 8) & 0xFF
        buff[2] = cmd & 0xFF

        self.pi.i2c_write_device(self.handle, buff)  # Send read command

        time.sleep(self.waitTime)   # Wait for data to be ready

        data = self.pi.i2c_read_word_data(self.handle, CONVERSION_REG)    # Read Data
        data = struct.unpack('h', struct.pack('>H', data))[0]   # Swaps endianness of data

        return data


    # converts adc raw reading to voltage
    def raw_to_voltage(self, data):
        return data * self.maxVoltage / 0x7FFF


if __name__ == "__main__":

    import pigpio
    import sys
    pi = pigpio.pi()

    def test():

        device = ads1115(pi, 0x48)

        adcValue1 = device.read(0)
        adcVoltage1 = device.raw_to_voltage(adcValue1)

        adcVoltage2 = device.getVoltage(0)

        print("The ADC read a value of {:d}, which is {:3.2f} at the current gain settings".format(adcValue1, adcVoltage1))
        print("The ADC read a second voltage of {:3.2f}".format(adcVoltage2))

        device.stop()
        pi.stop()

    mSensor = ADS1115(pi, 0x48, [int(sys.argv[1])])
    mData = mSensor.readAll()
    for i in mData:
        print(mData[i])
    #ADS1115.checkData(mData, notify, 15000)