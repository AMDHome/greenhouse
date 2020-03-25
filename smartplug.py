import tplink_protocol as plugs
import cTime

# Predefined Smart Plug Commands
# For a full list of commands, consult tplink_commands.txt
commands = {'info'     : '{"system":{"get_sysinfo":{}}}',
            'on'       : '{"system":{"set_relay_state":{"state":1}}}',
            'off'      : '{"system":{"set_relay_state":{"state":0}}}',
}

class Smartplug:
    def __init__(self, ip):
        self.ip = ip
        plugJSON = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]
        self.state = plugJSON["relay_state"]
        self.pastRuntime = int(plugJSON["on_time"])
        self.maxOn = False


    def set(self, newState):
        if newState == 1:
            self.on(self.ip)
        elif newState == 0:
            self.off(self.ip)


    def on(self, ip):
        if self.state == 0:
            if plugs.send(self.ip, commands["on"])["system"]["set_relay_state"]["err_code"] == 0:
                print(cTime.nowf() + " - ACTION: Lights On")
                self.state = 1 
                return 0
            else:
                print(cTime.nowf() + " - ALERT: Failed to turn lights on", file=sys.stderr)


    def off(self, ip):
        if self.state == 1:
            currRuntime = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["on_time"]
            if plugs.send(self.ip, commands["off"])["system"]["set_relay_state"]["err_code"] == 0:
                print(cTime.nowf() + " - ACTION: Lights Off")
                self.state = 0
                self.pastRuntime += int(currRuntime)
                return 0
            else:
                print(cTime.nowf() + " - ALERT: Failed to turn lights off", file=sys.stderr)

    def getState(self):
        return self.state


    def getRunTime(self):
        return self.pastRuntime + int(getTimeOn)


    def checkMaxOn(self):
        if self.getRunTime() > 43200:
            self.maxOn = True


    def getMaxOn(self):
        return self.maxOn


    def timeReset(self):
        plugJSON = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]
        currState = plugJSON["relay_state"]

        if currState == 1:
            plugs.send(self.ip, commands["off"])

        self.pastRuntime = 0
        self.maxOn = False

        if currState == 1:
            plugs.send(self.ip, commands["on"])


    def updateState(self):
        self.state = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["relay_state"]
        return self.state


    def getTimeOn(self):
        return plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["on_time"]
