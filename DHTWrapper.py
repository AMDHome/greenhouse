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

        return min(array), max(array), mean(array)


    def getRHSummary(self, ignore=[]):
        array = []

        for i in self.data:
            if i not in ignore:
                array.append(self.data[i]["RH"])

        return min(array), max(array)