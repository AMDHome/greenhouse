#!/usr/bin/env python
import pigpio as gpio
import cTime


# Collection of servos. In main program create this class
class Servos:

    def __init__(self, pi, devices, fan=False):
        self.servos = {}

        for i in devices:
            self.servos[i[0]] = Servo(pi, i, fan)


    def set(self, name, newState):
        self.servos[name].chgStateN(newState)


    def all(self, newState):
        for i in self.servos:
            self.servos[i].set(newState)



# Indivisual servos
class Servo: 
    def __init__(self, pi, device, fan=None):
        self.pi = pi
        self.pi.set_mode(device[1], gpio.OUTPUT)
        self.fan = fan
        
        self.name = device[0]
        self.pin = device[1]
        self.states = [device[2][1], device[2][0]]
        self.openDir = device[2][0] - device[2][1]

        self.pi.set_servo_pulsewidth(self.pin, self.states[0])
        self.state = self.states[0]

        
    def set(self, newState):
        if newState == 1:
            self.open()
        elif newState == 0:
            self.close()


    def open(self):
        if self.state != self.states[1]:
            self.chgState(self.states[1])
            print(cTime.nowf() + " - ACTION: Servo " + self.name + " Open")


    def close(self):
        if self.state != self.states[0]:
            self.chgState(self.states[0])
            print(cTime.nowf() + " - ACTION: Servo " + self.name + " Closed")
    

    def chgState(self, newState, hold=False):
        if self.fan:
            fstate = self.fan.state()
            self.fan.off(silent=True)

        totalMovement = newState - self.state
        mvmtPtick = totalMovement // 100
        remainder = totalMovement % 100

        # calculate sleep time between smoothing
        if self.openDir > 0:
            sleepTime = 0.0030 if totalMovement > 0 else 0.009
        else:
            sleepTime = 0.009 if totalMovement > 0 else 0.0030

        for i in range(100):
            if i < remainder:
                self.state += mvmtPtick + 1
            else:
                self.state += mvmtPtick

            self.pi.set_servo_pulsewidth(self.pin, self.state)
            cTime.sleep(sleepTime)
        
        if not hold:
            cTime.sleep(0.1)
            self.pi.set_servo_pulsewidth(self.pin, 0)

        if self.fan:
            self.fan.set(fstate, silent=True)


    # Does not change the self.state variable. Please run set(0) or close() when finished
    @staticmethod
    def chgStateNS(pi, pin, newState, currState=500, dirOpen="cc", hold=False, fan=None):
        if fan:
            fstate = fan.state()
            fan.off(silent=True)

        if currState == 500:
            pi.set_servo_pulsewidth(pin, 500)

        sleep(0.25)

        totalMovement = newState - currState
        mvmtPtick = totalMovement // 100
        remainder = totalMovement % 100

        for i in range(100):
            if i < remainder:
                currState += mvmtPtick + 1
            else:
                currState += mvmtPtick
            
            pi.set_servo_pulsewidth(pin, currState)

            #if left > else right <
            if dirOpen == cc:
                if totalMovement > 0:
                    cTime.sleep(0.0030)
                else:
                    cTime.sleep(0.015)
            else:
                if totalMovement < 0:
                    cTime.sleep(0.0030)
                else:
                    cTime.sleep(0.015)

        if not hold:
            cTime.sleep(0.1)
            pi.set_servo_pulsewidth(pin, 0)

        if fan:
            fan.set(fstate, silent=True)


    # Does not change the self.state variable. Please run set(0) or close() when finished
    # Does not have smoothing implemented
    @staticmethod
    def chgStateN(pi, pin, newState, hold=False, fan=None):
        if fan:
            fstate = fan.state()
            fan.off(silent=True)

        pi.set_servo_pulsewidth(pin, newState)
        if not hold:
            cTime.sleep(2)
            pi.set_servo_pulsewidth(pin, 0)

        if fan:
            fan.set(fstate, silent=True)


    def getState(self):
        return self.state


if __name__ == "__main__":
    import sys

    SERVOS = [("right", 18, (870, 1900)),
              ("left", 13, (2195, 1300))]  

    pi = gpio.pi()
    servos = Servos(pi, SERVOS)

    if sys.argv[1] == "off":
        servos.all(0)
    elif sys.argv[1] == "on":
        servos.all(1)
    elif sys.argv[1] == "demo":
        while True:
            servos.all(1)
            cTime.sleep(2)
            servos.all(0)
            cTime.sleep(2)

