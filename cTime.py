#!/usr/bin/env python
from datetime import datetime as datetime
import time

def all():
    t = datetime.now()
    return t.strftime("%H:%M:%S"), t

def now():
    return datetime.now()

def nowf():
    return datetime.now().strftime("%H:%M:%S")

def timeS():
    return int(time.time())

def currSec():
    return datetime.now().second

def sleep(seconds):
    time.sleep(seconds)

def between(time, time_range):
    if time_range[1] < time_range[0]:
        return time >= time_range[0] or time <= time_range[1]
    return time_range[0] <= time <= time_range[1]

def diff(earlier_time, curr_time):
    return (curr_time - earlier_time).seconds