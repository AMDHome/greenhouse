import tplink_protocol as plugs
import cTime


class Smartplug:
    def __init__(self, ip):
        self.ip = ip
        self.state = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["relay_state"]


    def set(self, newState):
        if newState == 1:
            on(self.ip)
        elif newState == 0:
            off(self.ip)


    def on(self, ip):
        if self.state == 0:
            if plugs.send(self.ip, commands["on"])["system"]["set_relay_state"]["err_code"] == 0:
                print(cTime.nowf() + " - ACTION Lights On")
                self.state = 1 
                return 0


    def off(self, ip):
        if self.state == 1:
            if plugs.send(self.ip, commands["off"])["system"]["set_relay_state"]["err_code"] == 0:
                print(cTime.nowf() + " - ACTION Lights Off")
                self.state = 0
                return 0


    def getState(self):
        return self.state


    def updateState(self):
        self.state = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["relay_state"]
        return self.state


    def getTimeOn(self):
        return plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["on_time"]
