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
        self.index = 0
        for line in self.file.readlines():
            self.addPrompt(line)
        self.file.close()

    def addPrompt(self, text):
        tags = set(re.findall("#\(([^\)]+)\)", text))
        tags.update(re.findall("#([^\(\s]+)", text))
        source = re.findall("@\(([^\)]+)\)", text)
        text = (re.sub("#(\S*)", "", text)).strip()
        text = (re.sub("@\((.*)\)", "", text)).strip()
        newPrompt = Prompt(text, tags, source)
        self.prompts.append(newPrompt)
        index = self.prompts.index(newPrompt)
        self.index = index
        for tag in tags:
            if tag in self.categories:
                self.categories[tag].append(index)
            else:
                self.categories[tag] = [index]
    
    def addTags(self, tags, index = ""):
        if not index:
            index = self.index
        self.prompts[index].tags.update(tags)
        for tag in tags:
            if tag in self.categories:
                self.categories[tag].append(index)
            else:
                self.categories[tag] = [index]

    def addSource(self, source, index = ""):
        if not index:
            index = self.index
        self.prompts[index].source.extend(source)

    def getTags(self, index = ""):
        if not index:
            index = self.index
        tags = '; '.join(self.prompts[index].tags)
        if tags:
            return tags
        else:
            return "No tags."
    
    def getSource(self, index = ""):
        if not index:
            index = self.index
        source = '; '.join(self.prompts[index].source)
        if source:
            return source
        else:
            return "No source given."

    def getIndex(self, index = ""):
        if not index:
            index = self.index
        return "Prompt #%d" % (self.index)

    def last(self):
        return self.prompts[self.index].text

    def randomPrompt(self):
        self.index = choice(range(0, len(self.prompts)))
        return self.prompts[self.index].text
        
    def promptByTag(self, tag):
        if tag in self.categories:
            self.index = choice(self.categories[tag])
            return self.prompts[self.index].text
        else:
            return "None."

    def promptByIndex(self, index):
        self.index = index
        return self.prompts[self.index].text

    def listAllCategories(self):
       msg = ', '.join(self.categories.keys())
       return msg

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

