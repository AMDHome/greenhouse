import pigpio as gpio
import cTime

class Fan:
    def __init__(self, pi, pin):
        self.pi = pi
        self.pin = pin

        self.pi.set_mode(self.pin, gpio.OUTPUT)
        self.pi.write(self.pin, 0)


    def on(self, silent=False):
        if self.state() == 0:
            self.pi.write(self.pin, 1)
            if not silent:
                print(cTime.nowf() + " - ACTION: Fan On")

    def off(self, silent=False):
        if self.state() == 1:
            self.pi.write(self.pin, 0)
            if not silent:
                print(cTime.nowf() + " - ACTION: Fan Off")

    def state(self):
        return self.pi.read(self.pin)

    def set(self, state, silent=False):
        self.pi.write(self.pin, state)
        if not silent:
            if state == 0 and self.state() == 1:
                print(cTime.nowf() + " - ACTION: Fan Off")
            elif state == 1 and self.state() == 0:
                print(cTime.nowf() + " - ACTION: Fan On")


if __name__ == "__main__":
    import sys

    pi = gpio.pi()
    fan = Fan(pi, int(sys.argv[1]))

    if sys.argv[2] == "off":
        fan.off()
    elif sys.argv[2] == "on":
        fan.on()

    print("pin: {}".format(int(sys.argv[1])))
    print("value: {}".format(pi.read(int(sys.argv[1]))))
