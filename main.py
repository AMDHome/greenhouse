#!/usr/bin/env python

import cTime
import pigpio as gpio
import sys
from ads1115_singleshot_pigpio import ADS1115 as ADS1115C
from DHTWrapper import DHT as DHTC
from fan import Fan as fanC
from servo import Servos as servosC
from smartplug import Smartplug as smartplugC
from smartstrip import Smartstrip as smartstripC
from notify_run import Notify
import os.path


# Const values to make my life easier
ON = 1
OFF = 0
SPCHECK_INTERVAL = 3600             # Time in seconds to update smartplug state data
SYSTEM_LOOP_INTERVAL = 180          # Time in seconds between each iteration of main loop
MOISTURE_SENSOR_CHK_INTERVAL = 900  # Time in seconds between each check of the moisture sensor
PLUG_ADDR = "192.168.2.23"
HEATPAD_ADDR = "192.168.2.24"
HEATPAD_ID = "8006243BBCE51D149484EDC4D45C79131C5EAAE102"
SERVOS = [("right", 18, (870, 1900)),       # (Name, Pin, (Open [up], Close))
          ("left", 13, (2195, 1300))]              
DHT = [("right", "AM2320", 23, True),       # (Name, Model, Pin, Pullup)
       ("left", "AM2320", 6, True),
       ("light", "DHT11", 22, False)]
FAN_PIN = 26
TEMP_DIFF_FAN = 4
RH_DIFF_FAN = 12
TEMP_THRESH = (2, 4)                        # Delta from set temp before action is taken (response, emergency)
INSTALLED_MOISTURE_SENSORS = [0, 1, 2]
SOIL_THRESH = 17920                         # Threshold (Dry = 23200, Wet = 10000)
SOIL_LIMITS = [23200, 10000]
SOIL_DELTA = 13200
LIGHT_MAX_TEMP = 110
DHT_LOG = "/home/amdhome/greenhouse/logs/DHT.log"
MOISTURE_LOG = "/home/amdhome/greenhouse/logs/theta.log"

lastCheckL = None   # Last check for light
lastCheckM = None   # Last check for moisture sensor
lastState = None    # State of system since last run (-1: cold, 0: normal, 1 hot)

# Settings
runTime = [ "07:00:00", "22:00:00" ]
tempGraceTime = [ "09:00:00", "00:01:00" ]  # Time in which temp notifications wont be sent
tempSet = [ 78,  None ]

# Object variables
pi = None
DHTSensors = None
fan = None
heatpad = None
light = None
servos = None
mSensor = None
notify = None
logFileDHT = None
logFileM = None

targetTemp = None
cycle = None

queueNotification = None


def init():
    global lastCheckL, lastCheckM, cycle
    global pi, DHTSensors, fan, light, servos, mSensor, notify, logFileDHT, logFileM, heatpad

    print("Initializing...")

    # create pigpio instance
    pi = gpio.pi()

    # init Notify
    notify = Notify()

    # open logFiles
    file_exists = os.path.isfile(DHT_LOG)
    logFileDHT = open(DHT_LOG, "a+", buffering=1)
    if not file_exists:
        logFileDHT.write("time, tempLeft, tempRight, tempLight, avgTemp, RHLeft, RHRight, RHLight\n")

    file_exists = os.path.isfile(MOISTURE_LOG)
    logFileM = open(MOISTURE_LOG, "a+", buffering=1)
    if not file_exists:
        logFileM.write("time, potLeft, rawLeft, potMid, rawMid, potRight, rawRight\n")

    # init Sensors
    pi.set_mode(5, gpio.OUTPUT)
    pi.write(5, 1)
    DHTSensors = DHTC(pi, DHT)

    # init Fan
    fan = fanC(pi, FAN_PIN)

    # init ADC for moisture sensor
    mSensor = ADS1115C(pi, 0x48, INSTALLED_MOISTURE_SENSORS)
    mData = mSensor.readAll()
    logSoilData(cTime.nowf(), mData)
    #ADS1115C.checkData(mData, notify, SOIL_THRESH)
    lastCheckM = cTime.now()

    # init Servos
    servos = servosC(pi, SERVOS, fan)
    
    # init Smartplug
    light = smartplugC(PLUG_ADDR)
    lastCheckL = cTime.now()

    heatpad = smartstripC(HEATPAD_ADDR, HEATPAD_ID)

    # init State
    lastState = -1
    if cTime.between(cTime.nowf(), runTime):
        cycle = 1
        light.set(ON)
    else:
        cycle = 0
        light.set(OFF)

    fan.set(OFF)
    servos.all(OFF)


def logSoilData(currTime, data):
    global logFileM
    print("Soil Moisture Sensors Report: {:.2f}% [{}], {:.2f}% [{}], and {:.2f}% [{}]".format(
                                        (1 - ((data[0] - SOIL_LIMITS[1]) / SOIL_DELTA)) * 100, data[0],
                                        (1 - ((data[1] - SOIL_LIMITS[1]) / SOIL_DELTA)) * 100, data[1],
                                        (1 - ((data[2] - SOIL_LIMITS[1]) / SOIL_DELTA)) * 100, data[2]))
    logFileM.write("{}, {:.2f}, {}, {:.2f}, {}, {:.2f}, {}\n".format(currTime, 
                                        (1 - ((data[0] - SOIL_LIMITS[1]) / SOIL_DELTA)) * 100, data[0],
                                        (1 - ((data[1] - SOIL_LIMITS[1]) / SOIL_DELTA)) * 100, data[1],
                                        (1 - ((data[2] - SOIL_LIMITS[1]) / SOIL_DELTA)) * 100, data[2]))


def sendNotification(msg, outfile=sys.stdout):
    global notify
    print(msg, file=outfile)
    notify.send("Greenhouse - " + msg)


def printReturn(avgTemp):
    msg = cTime.nowf() + " - INFO: TEMP VALUES HAVE RETURNED TO NORMAL: {:.2f}°F".format(avgTemp)
    sendNotification(msg)


def printHigh(avgTemp):
    msg = cTime.nowf() + " - ALERT: TEMP VALUES ABOVE E LEVELS: {:.2f}°F".format(avgTemp)
    sendNotification(msg, outfile=sys.stderr)


def printLow(avgTemp):
    msg = cTime.nowf() + " - ALERT: TEMP VALUES BELOW E LEVELS: {:.2f}°F".format(avgTemp)
    sendNotification(msg, outfile=sys.stderr)


def processesNotif(avgTemp):
    global queueNotification

    currentTime = cTime.nowf()

    # If between quiet hours
    if cTime.between(currentTime, [runTime[0], tempGraceTime[0]]) or cTime.between(currentTime, [runTime[1], tempGraceTime[1]]):
        return

    else:
        if queueNotification == "high":
            printHigh(avgTemp)
            queueNotification = None
        elif queueNotification == "low":
            printLow(avgTemp)
            queueNotification = None
        elif queueNotification == "return":
            printReturn(avgTemp)
            queueNotification = None


def loop():
    global lastCheckL, lastCheckM, lastState, cycle, targetTemp, queueNotification, logFileDHT

    currentTime, unformattedTime = cTime.all()
    fanState = fan.state()
    servoState = servos.state()
    lightState = light.getState()
    updateState = False

    DHTData = DHTSensors.getData()
    minTemp, maxTemp, avgTemp = DHTSensors.getTempSummary(ignore=["light"])
    minRH, maxRH = DHTSensors.getRHSummary(ignore=["light"])

    print("Current Time: {}".format(currentTime))
    print("Tempretures are: {:.2f}°F, {:.2f}°F, Light: {:.2f}°F - Average: {:.2f}°F".format(DHTData["left"]["temp"], DHTData["right"]["temp"], DHTData["light"]["temp"], avgTemp))
    print("RH Values are: {:.2f}%, {:.2f}%, Light: {:.2f}%".format(DHTData["left"]["RH"], DHTData["right"]["RH"], DHTData["light"]["RH"]))
    logFileDHT.write("{}, {:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}\n".format(currentTime, DHTData["left"]["temp"], DHTData["right"]["temp"], DHTData["light"]["temp"], avgTemp,
                                                                                         DHTData["left"]["RH"], DHTData["right"]["RH"], DHTData["light"]["RH"]))

    # If fan is already on, check if it was a special case
    # If it is, default to off for now.
    if fanState == ON:
        if lastState == 1 or lastState == -1:
            fanState = OFF

    # If daylight hours.
    if cTime.between(currentTime, runTime):

        if cycle == 1:
            # If there is no temp setting
            if tempSet[0] is None:
                targetTemp = None
                lightState = ON
                servoState = ON
                fanState = ON
            else:
                targetTemp = tempSet[0]
                lightState = ON
                fanState = OFF
                servoState = OFF
                
            heatpad.set(OFF)
            lastState = -1
            cycle = 0

    # Nighttime
    else:
        if cycle == 0:
            # If there is no temp setting
            if tempSet[1] is None:
                targetTemp = None
                servoState = OFF
                fanState = OFF
                lightState = OFF
            else:
                targetTemp = tempSet[1]
                servoState = OFF
                fanState = OFF
                lightState = OFF
                lastState = -1

            heatpad.set(OFF)
            lastState = -1
            cycle = 1

    if lastState != -3 and light.getMaxOn() == True and lightState == ON:
        lightState = OFF

    if targetTemp != None:
        # Get Current State
        # Hot Side
        if targetTemp <= avgTemp:                           # Normal
            newState = 1
            if targetTemp + TEMP_THRESH[0] < avgTemp:       # Hot
                newState = 2
                if targetTemp + TEMP_THRESH[1] < avgTemp:   # E-Hot
                    newState = 3

        # Cold Side
        elif targetTemp > avgTemp:                          # Normal
            newState = -1
            if targetTemp - TEMP_THRESH[0] > avgTemp:       # Cold
                newState = -2
                if targetTemp - TEMP_THRESH[1] > avgTemp:   # E-Cold
                    newState = -3

        # FSM Take action based on last state
        # State 3
        if lastState == -3:
            if newState == -1 and queueNotification != None:
                queueNotification = None
            elif newState == 1:
                if cycle == 1:          # If nighttime, turn off lights
                    lightState = OFF
                fanState = OFF
                if queueNotification == None:
                    queueNotification = "return"
                else:
                    queueNotification = None
                updateState = True
            elif newState == 2:
                if cycle == 1:          # If nighttime, turn off lights
                    lightState = OFF
                servoState = ON
                if queueNotification == None:
                    queueNotification = "return"
                else:
                    queueNotification = None
                updateState = True
            elif newState == 3:
                lightState, servoState = OFF, ON
                queueNotification = "high"
                updateState = True

        elif lastState == -2:
            if newState == -3:
                lightState = ON
                queueNotification = "low"
                updateState = True
            elif newState == 1:
                fanState = OFF
                updateState = True
            elif newState == 2:
                servoState = ON
                updateState = True
            elif newState == 3:
                lightState, servoState = OFF, ON
                queueNotification = "high"
                updateState = True

        elif lastState == -1 or lastState == 1:
            if newState == -3:
                if cycle == 1:
                    lightState = ON
                fanState = ON
                queueNotification = "low"
                updateState = True
            elif newState == -2:
                if not (cycle == 0 and light.getState == OFF):
                    fanState = ON
                updateState = True
            elif newState == 2:
                fanState, servoState = ON, ON
                updateState = True
            elif newState == 3:
                lightState, fanState, servoState = OFF, ON, ON
                queueNotification = "high"
                updateState = True

        elif lastState == 2:
            if newState == -3:
                if cycle == 1:
                    lightState = ON
                servoState = OFF
                queueNotification = "low"
                updateState = True
            elif newState == -2:
                servoState = OFF
                updateState = True
            elif newState == -1:
                fanState, servoState = OFF, OFF
                updateState = True
            elif newState == 3:
                lightState = OFF
                queueNotification = "high"
                updateState = True

        elif lastState == 3:
            if newState == -3:
                lightState, servoState = ON, OFF
                queueNotification = "low"
                updateState = True
            elif newState == -2:
                if cycle == 0:
                    lightState = ON
                servoState = OFF
                if queueNotification == None:
                    queueNotification = "return"
                else:
                    queueNotification = None
                updateState = True
            elif newState == -1:
                if cycle == 0:
                    lightState = ON
                fanState, servoState = OFF, OFF
                if queueNotification == None:
                    queueNotification = "return"
                else:
                    queueNotification = None
                updateState = True
            elif newState == 1 and queueNotification != None:
                queueNotification = None

        if newState == -2 or newState == -3:
            heatpad.set(ON)
        else:
            heatpad.set(OFF)
                                            

    # If fan is not already on, check if we need to mix the air
    if fanState != ON:
        # Check Temp/RH Delta
        if (maxTemp - minTemp) > TEMP_DIFF_FAN:
            fanState = ON
        if (maxRH - minRH) > RH_DIFF_FAN:
            fanState = ON

        # Check light temprature
        if DHTData["light"]["temp"] > LIGHT_MAX_TEMP:
            fanState = ON
        
    if queueNotification != None:
        processesNotif(avgTemp)

    # Check to see if we need to update smartplug data
    if cTime.diff(lastCheckL, unformattedTime) > SPCHECK_INTERVAL:
        lastCheckL = cTime.now()
        light.updateState()
        light.checkMaxOn()

    # Apply Changes
    light.set(lightState)
    servos.all(servoState)
    fan.set(fanState)

    if updateState:
        lastState = newState

    # Check moisture sensor
    if cTime.diff(lastCheckM, unformattedTime) > MOISTURE_SENSOR_CHK_INTERVAL:
        lastCheckM = cTime.now()
        mData = mSensor.readAll()
        logSoilData(currentTime, mData)
        ADS1115C.checkData(mData, notify, SOIL_THRESH)

    # Do nightly reset
    if currentTime < "00:03:00":
        light.timeReset()

    print("")
    cTime.sleep(SYSTEM_LOOP_INTERVAL - cTime.currSec())
    
    return


if __name__ == "__main__":
    init()

    print("")
    print("Starting Loop")
    
    while True:
        loop()
