import tplink_protocol as plugs
import cTime

# Predefined Smart Plug Commands
# For a full list of commands, consult tplink_commands.txt
commands = {'info'     : '{"system":{"get_sysinfo":{}}}',
            'on'       : '{"system":{"set_relay_state":{"state":1}}}',
            'off'      : '{"system":{"set_relay_state":{"state":0}}}',
            'cloudinfo': '{"cnCloud":{"get_info":{}}}',
            'wlanscan' : '{"netif":{"get_scaninfo":{"refresh":0}}}',
            'time'     : '{"time":{"get_time":{}}}',
            'schedule' : '{"schedule":{"get_rules":{}}}',
            'countdown': '{"count_down":{"get_rules":{}}}',
            'antitheft': '{"anti_theft":{"get_rules":{}}}',
            'reboot'   : '{"system":{"reboot":{"delay":1}}}',
            'reset'    : '{"system":{"reset":{"delay":1}}}',
            'energy'   : '{"emeter":{"get_realtime":{}}}'
}

class Smartplug:
    def __init__(self, ip):
        self.ip = ip
        self.state = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["relay_state"]


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
            if plugs.send(self.ip, commands["off"])["system"]["set_relay_state"]["err_code"] == 0:
                print(cTime.nowf() + " - ACTION: Lights Off")
                self.state = 0
                return 0
            else:
                print(cTime.nowf() + " - ALERT: Failed to turn lights off", file=sys.stderr)

    def getState(self):
        return self.state


    def updateState(self):
        self.state = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["relay_state"]
        return self.state


    def getTimeOn(self):
        return plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["on_time"]
