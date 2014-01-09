#!/usr/bin/python2.7
from datetime import *

def selectTopic(promptbot):
    today = datetime.today()
    day = today.weekday()
    topic = ""
    if today.month == 10: 
        topic = "%d days until NaNoWriMo " % (31 - today.day)
    elif today.month == 11:
        topic = "Do you have your %d words yet? " % (int(float(50000)/30*today.day))
    if day == 2:
        if not topic == "":
            topic += "| "
        topic += "Worldbuilding Wednesday: "
        index, prompt = promptbot.entryByTag("prompt","worldbuilding")
        if prompt:
            topic += prompt
    elif day == 0:
        if not topic == "":
            topic += "| "
        topic += "Characterbuilding Monday: "
        index, prompt = promptbot.entryByTag("prompt","character")
        if prompt:
            topic += prompt
    elif day == 3:
        if not topic == "":
            topic += "| "
        topic += "Theme Thursday: "
        prompt = promptbot.entryByTag("prompt","theme")
        if prompt:
            topic += prompt
    else:
        index, l, prompt = promptbot.completelyRandomEntry()
        if prompt:
            topic += prompt
    return topic

