#!/usr/bin/python2.7
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from random import choice
import time, sys, re

class Prompt(object):
    def __init__(self, text, tags, source):
        self.text = text
        self.tags = tags
        self.source = source

class PromptBot:
    def __init__(self, file):
	self.file = file
        self.categories = {}
        self.prompts = list()
        for line in self.file.readlines():
            self.addPrompt(line)
        self.file.close()

    def addPrompt(self, text):
        tags = set(re.findall("#\((.*)\)#", text))
        tags.update(re.findall("#([^\(\s]*)", text))
        source = re.findall("@\((.*)\)", text)
        text = (re.sub("#(\S*)", "", text)).strip()
        newPrompt = Prompt(text, tags, source)
        self.prompts.append(newPrompt)
        index = self.prompts.index(newPrompt)
        for tag in tags:
            if tag in self.categories:
                self.categories[tag].append(index)
            else:
                self.categories[tag] = [index]

    def randomPrompt(self):
        return choice(self.prompts).text
        
    def promptByTag(self, tag):
        if tag in self.categories:
            index = choice(self.categories[tag])
            print self.prompts[index].text
        else:
            return "None."

    def backup(self, file):
        self.file = file
        for prompt in self.prompts:
            line = prompt.text
            for tag in prompt.tags:
                line += " #(" + tag + ")"
            for source in prompt.source:
                line += " @(" + source + ")"
            line += "\n"
            file.write(line)
        self.file.close()

