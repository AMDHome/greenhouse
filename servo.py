#!/usr/bin/env python
import pigpio as gpio
import cTime


# Collection of servos. In main program create this class
class Servos:

    def __init__(self, pi, devices, fan=False):
        self.servos = {}

        for i in devices:
            self.servos[i[0]] = Servo(pi, i, fan)


    def set(self, name, newstate):
        self.servos[name].chgStateN(newState)


    def all(self, newState):
        if newState >= 500:
            for i in self.servos:
                self.servos[i].chgStateN(newState)
        else:
            for i in self.servos:
                self.servos[i].chgState(newState)



# Indivisual servos
class Servo:
    def __init__(self, pi, device, fan):
        self.pi = pi
        self.pi.set_mode(device[1], gpio.OUTPUT)
        self.fan = fan
        
        self.name = device[0]
        self.pin = device[1]
        self.states = [device[2][2], device[2][0]]
        self.threshold = device[2][1]
        self.state = 0

        self.set(0)

        
    def set(self, newState):
        if newState == 1:
            self.open()
        elif newState == 0:
            self.close()


    def open(self):
        self.chgState(self.states[1])
        print(cTime.nowf() + " - ACTION Servo " + self.name + " Open")
        self.state = 1


    def close(self):
        self.chgState(self.states[0])
        print(cTime.nowf() + " - ACTION Servo " + self.name + " Closed")
        self.state = 0
    

    # Does not change the self.state variable. Please use set(), open(), or close()
    def chgState(self, newState, hold=False):
        if self.fan:
            fstate = self.fan.state()
            self.fan.off()

        self.pi.set_servo_pulsewidth(self.pin, self.states[newState])
        if not hold:
            cTime.sleep(1)
            self.pi.set_servo_pulsewidth(self.pin, 0)

        if self.fan:
            self.fan.set(fstate)


    # Does not change the self.state variable. Please run set(0) or close() when finished
    def chgStateN(self, newState, hold=False):
        if self.fan:
            fstate = self.fan.state()
            self.fan.off()

        self.pi.set_servo_pulsewidth(self.pin, newState)
        if not hold:
            cTime.sleep(1)
            self.pi.set_servo_pulsewidth(self.pin, 0)

        if self.fan:
            self.fan.set(fstate)


    def getState(self):
        return self.state