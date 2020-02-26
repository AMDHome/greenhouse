#!/usr/bin/env python
import pigpio as gpio
import cTime


# Collection of servos. In main program create this class
class Servos:
    def __init__(self, pi, devices, fan=False):
        self.pi = pi
        self.fan = fan
        self.servos = {}

        for i in devices:
            Servos.servos[i[0]] = Servo(i)
            Servos.pi.set_mode(i[1], gpio.OUTPUT)


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
    def __init__(self, device):
        self.name = device[0]
        self.pin = device[1]
        self.state = [device[2][2], device[2][0]]
        self.threshold = device[2][1]
        self.up = device[2][3]

        
    def set(self, newState):
        if newState == 1:
            self.open()
        elif newState == 0:
            self.close()


    def open(self):
        self.chgState(self.state[1])
        print(cTime.nowf() + " - ACTION Servo " + self.name + " Open")


    def close(self):
        self.chgState(self.state[0])
        print(cTime.nowf() + " - ACTION Servo " + self.name + " Closed")
    

    def chgState(self, newState, hold=False):
        if Servos.fan:
            fstate = Servos.fan.state()
            Servos.fan.off()

        Servos.pi.set_servo_pulsewidth(self.pin, self.state[newState])
        if not hold:
            cTime.sleep(1)
            Servos.pi.set_servo_pulsewidth(self.pin, 0)

        if Servos.fan:
            Servos.fan.set(fstate)


    def chgStateN(self, newState, hold=False):
        if Servos.fan:
            fstate = Servos.fan.state()
            Servos.fan.off()

        Servos.pi.set_servo_pulsewidth(self.pin, newState)
        if not hold:
            cTime.sleep(1)
            Servos.pi.set_servo_pulsewidth(self.pin, 0)

        if Servos.fan:
            Servos.fan.set(fstate)


    def getState(self):
        return 1 if Servos.pi.get_servo_pulsewidth(self.name) > Servos.threshold else 0