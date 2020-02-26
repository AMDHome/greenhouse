#!/usr/bin/env python

import cTime
import gpio
from ads1115_singleshot_pigpio import ADS1115 as ADS1115C
from DHTWrapper import DHT as DHTC
from fan import Fan as fanC
from servo import Servos as servosC
from smartplug import Smartplug as smartplugC
from notify_run import Notify


# Const values to make my life easier
ON = 1
OFF = 0
SPCHECK_INTERVAL = 3600             # Time in seconds to update smartplug state data
SYSTEM_LOOP_INTERVAL = 180          # Time in seconds between each iteration of main loop
MOISTURE_SENSOR_CHK_INTERVAL = 900  # Time in seconds between each check of the moisture sensor
PLUG_ADDR = "192.168.2.23"
SERVOS = [("right", 18, (1350, 1500, 2250, 945)),   # (Name, Pin, (Open, Threshold, Close, Up))
          ("left", 13, (1650, 1000, 750, 2055))]              
DHT = [("right", "AM2320", 23, True),               # (Name, Model, Pin)
       ("left", "AM2320", 6, True),
       ("light", "DHT11", 22, False)]
FAN_PIN = 26
TEMP_DIFF_FAN = 4
RH_DIFF_FAN = 10
TEMP_THRESH = (2, 4)      # Delta from set temp before action is taken (response, emergency)
INSTALLED_MOISTURE_SENSORS = [0, 1, 2]
MOISTURE_SENSOR_THRESHOLD = 15000

lastCheckL = None   # Last check for lights
lastCheckM = None   # Last check for moisture sensor
prevState = 0       # State of system since last run (-1: cold, 0: normal, 1 hot)

# Settings
runTime = [ "07:00:00", "00:00:00" ]
tempSet = [ 77,  None ]

# Object variables
pi = None
DHTSensors = None
fan = None
lights = None
servos = None
mSensor = None
notify = None


def init():
    global lastCheckL, lastCheckM, pi, DHTSensors, fan, lights, servos, notify

    # create pigpio instance
    pi = gpio.init()

    # init Notify
    notify = Notify()

    # init Sensors
    DHTSensors = DHTC(pi, DHT)

    # init Fan
    fan = fanC(pi, FAN_PIN)

    # init ADC for moisture sensor
    mSensor = ADS1115C(pi, 0x48, INSTALLED_MOISTURE_SENSORS)
    mData = mSensor.readAll()
    ADS1115C.checkData(mData, notify, MOISTURE_SENSOR_THRESHOLD)
    lastCheckM = cTime.nowf()

    # init Servos
    servos = servosC(pi, SERVOS)
    
    # init Smartplug
    lights = smartplugC(PLUG_ADDR)
    lastCheckL = cTime.nowf()


def output():
    print(lights.updateState())
    DHTSensors.output()


def sendNotification


def loop():
    global lastCheckL, prevState

    currentTime, unformattedTime = cTime.all()
    fanState = servoState = OFF
    lightState = ON
    currState = 0

    DHTSensors.getData()
    minTemp, maxTemp, avgTemp = DHTSensors.getTempSummary(ignore=["light"])
    minRH, maxRH = DHTSensors.getRHSummary()

    # If daylight hours.
    if cTime.between(currentTime, runTime):
        lightState = ON

        # If there is no temp setting
        if tempSet[0] is None:
            servoState = ON

        # If there is a temp setting
        else:

            # Can't do much if too cold. The main heat source (Lights) are already on.
            # Turn on fan to generate heat if past emergency levels
            # If below "emergency" setting levels
            if tempSet[0] - TEMP_THRESH[1] > avgTemp:
                msg = cTime.nowf() + " - ALERT: TEMP VALUES BELOW E LEVELS"
                print(msg)
                fanState = ON
                if prevState == 0:
                    notify.send("Greenhouse - " + msg)
                    currState = -1

            # If too hot (avgTemp is above bounds)
            elif tempSet[0] + TEMP_THRESH[0] < avgTemp:
                servoState = ON     # VENT

                # If above "emergency" setting levels
                if tempSet[0] + TEMP_THRESH[1] < avgTemp:
                    msg = cTime.nowf() + " - ALERT: TEMP VALUES ABOVE E LEVELS"
                    print(msg)
                    fanState = ON       # Turn on forced ventilation
                    lightState = OFF    # Turn off heat source
                    if prevState == 0:
                        notify.send("Greenhouse - " + msg)
                        currState = 1

    # If night hours
    else:
        lightState = OFF

        # If there is no temp setting
        if tempSet[1] is None:
            servoState = ON

         # If there is a temp setting
        else:
            # Only turn on lights at night if we hit emergency levels of cold
            # If below "emergency" setting levels
            if tempSet[1] - TEMP_THRESH[1] > avgTemp:
                msg = cTime.nowf() + " - ALERT: TEMP VALUES BELOW E LEVELS"
                print(msg)
                lightState = ON
                fanState = ON
                if prevState == 0:
                    notify.send("Greenhouse - " + msg)
                    currState = -1

            # If avgTemp is above bounds
            elif tempSet[1] + TEMP_THRESH[0] < avgTemp:
                servoState = ON

                # If above "emergency" setting levels
                if tempSet[1] + TEMP_THRESH[1] < avgTemp:
                    msg = cTime.nowf() + " - ALERT: TEMP VALUES ABOVE E LEVELS"
                    print(msg)
                    fanState = ON     # Turn on forced ventilation
                    if prevState == 0:
                        notify.send("Greenhouse - " + msg)
                        currState = 1

    # If fan is not already on, check if we need to mix the air
    if fanState != ON:
        # Check Temp/RH Delta
        if maxTemp - minTemp > TEMP_DIFF_FAN:
            fanState = ON
        if maxRH - minRH > RH_DIFF_FAN:
            fanState = ON

    # Apply Changes
    lights.set(lightState)
    servos.all(servoState)
    fan.set(fanState)
    prevState = currState

    # Check to see if we need to update smartplug data
    if cTime.diff(lastCheckL, unformattedTime) > SPCHECK_INTERVAL:
        lastCheckL = cTime.nowf()
        lights.updateState(PLUG_ADDR)

    # Check moisture sensor
    if cTime.diff(lastCheckM, unformattedTime) > SPCHECK_INTERVAL:
        lastCheckM = cTime.nowf()
        mData = mSensor.readAll()
        ADS1115C.checkData(mData, notify, MOISTURE_SENSOR_THRESHOLD)

    cTime.sleep(SYSTEM_LOOP_INTERVAL - cTime.currSec())
    return


if __name__ == "__main__":
    init()

    while True:
        loop()