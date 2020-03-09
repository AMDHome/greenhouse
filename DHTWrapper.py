import time
from DHTSensor import sensor as sensorC


# Class for a collection of sensor objects
class DHT:

    def __init__(self, pi, listing):
        self.sensors = {}
        self.data = {}

        for i in listing:
            self.sensors[i[0]] = sensorC(pi, i[2], i[1], pullup=i[3])


    # Prints last avaliable data (does not update the data before printing)
    def output(self):
        print(self.data)


    # Get all data
    def getData(self):
        self.data = {}
        next_reading = time.time() + 3

        for i in self.sensors:
            self.query(self.sensors[i])

        time.sleep(next_reading - time.time())

        for i in self.sensors:
            self.data[i] = self.query(self.sensors[i])

        return self.data


    # Get data by object
    def query(self, sensor):
        sensor.trigger()
        time.sleep(0.2)

        return {"temp": sensor.temperature(), "RH": sensor.humidity()}


    # Analyze data in object. Does not refresh data.
    def getTempSummary(self, ignore=[]):
        array = []

        for i in self.data:
            if i not in ignore:
                array.append(self.data[i]["temp"])

        return min(array), max(array), sum(array)/len(array)


    def getRHSummary(self, ignore=[]):
        array = []

        for i in self.data:
            if i not in ignore:
                array.append(self.data[i]["RH"])

        return min(array), max(array)


if __name__ == "__main__":
    import pigpio as gpio
    import cTime

    DHTList = [       # (Name, Model, Pin)
       ("left", "AM2320", 6, True),
       ("right", "AM2320", 23, True),
       ("light", "DHT11", 22, False)]

    pi = gpio.pi()
    currentTime = cTime.nowf()

    pi.set_mode(5, gpio.OUTPUT)
    pi.write(5, 1)
    
    DHTSensors = DHT(pi, DHTList)

    DHTData = DHTSensors.getData()

    minTemp, maxTemp, avgTemp = DHTSensors.getTempSummary(ignore=["light"])
    minRH, maxRH = DHTSensors.getRHSummary()

    print("Current Time: {}".format(currentTime))
    print("Tempretures are: {:3.2f}, {:3.2f}, Light: {:3.2f}".format(DHTData["left"]["temp"], DHTData["right"]["temp"], DHTData["light"]["temp"]))
    print("RH Values are: {:3.2f}, {:3.2f}, Light: {:3.2f}".format(DHTData["left"]["RH"], DHTData["right"]["RH"], DHTData["light"]["RH"]))
    print("")
    print("Calculated Temp Values are: MinT: {:3.2f}, MaxT: {:3.2f}, AvgT: {:3.2f}".format(minTemp, maxTemp, avgTemp))
    print("Calculated RH Values are: MinRH: {:3.2f}, MaxRH: {:3.2f}".format(minRH, maxRH))