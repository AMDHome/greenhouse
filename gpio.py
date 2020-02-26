import pigpio as gpio

pi = None

def init():
    global pi
    pi = gpio.pi()
    return pi

def getPi():
    return pi