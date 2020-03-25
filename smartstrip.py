from smartplug import Smartplug
import tplink_protocol as plugs
import cTime

commands = {'info'     : '{"system":{"get_sysinfo":{}}}',
            'on'       : '"system":{"set_relay_state":{"state":1}}}',
            'off'      : '"system":{"set_relay_state":{"state":0}}}',
}

class Smartstrip(Smartplug):
	def __init__(self, ip, plugID):
		self.ip = ip
		self.id = plugID

		plugJSON = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]

		self.location = None
		for i in plugJSON["children"]:
			if i["id"] == plugID:
				self.location = i
				break

		if self.location == None
			print(cTime.nowf() + " - ALERT: id number " + self.id + " not found on device" + ip, file=sys.stderr)
			exit()

		self.state = plugJSON["children"][self.location]["state"]
        self.pastRuntime = int(plugJSON["children"][self.location]["on_time"])
        self.maxOn = False


    def generateCMD(self, cmd):
    	return '{"context":{"child_ids":["' + self.id + '"]},' + commands[cmd]


	def on(self, ip):
        if self.state == 0:
            if plugs.send(self.ip, generateCMD("on"))["system"]["set_relay_state"]["err_code"] == 0:
                print(cTime.nowf() + " - ACTION: HeatPad On")
                self.state = 1 
                return 0
            else:
                print(cTime.nowf() + " - ALERT: Failed to turn on HeatPad", file=sys.stderr)


    def off(self, ip):
        if self.state == 1:
            currRuntime = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["children"][self.location]["on_time"]
            if plugs.send(self.ip, generateCMD("off"))["system"]["set_relay_state"]["err_code"] == 0:
                print(cTime.nowf() + " - ACTION: HeatPad Off")
                self.state = 0
                self.pastRuntime += int(currRuntime)
                return 0
            else:
                print(cTime.nowf() + " - ALERT: Failed to turn off HeatPad", file=sys.stderr)


    def timeReset(self):
        plugJSON = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["children"][self.location]
        currState = plugJSON["state"]

        if currState == 1:
            plugs.send(self.ip, generateCMD("off"))

        self.pastRuntime = 0
        self.maxOn = False

        if currState == 1:
            plugs.send(self.ip, generateCMD("on"))


    def updateState(self):
        self.state = plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["children"][self.location]["state"]
        return self.state


    def getTimeOn(self):
        return plugs.send(self.ip, commands["info"])["system"]["get_sysinfo"]["children"][self.location]["on_time"]