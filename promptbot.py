#!/usr/bin/python3.7
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from collections import defaultdict
from random import choice
import sys, re

class Prompt(object):
    def __init__(self, text, tags, source):
        self.text = text
        self.tags = tags
        self.source = source

class PromptBot:
    def __init__(self, infile, outfile):
        self.infile = infile
        self.categories = {}
        self.prompts = list()
        self.indices = defaultdict(int)
        #Keeps track of the last prompt accessed per channel by using the
        #channel name as a key. Defaults to last prompt in list.
        for line in self.infile.readlines():
            self.addPrompt(line, "promptbot")
        self.infile.close()

    def addPrompt(self, text, channel, dupeCheck=False):
        tags = set(re.findall("#\(([^\)]+)\)", text))
        tags.update(re.findall("#([^\(\s]+)", text))
        source = re.findall("@\(([^\)]+)\)", text)
        text = (re.sub("#\(([^\)]+)\)", "", text)).strip()
        text = (re.sub("#([^\(\s]+)", "", text)).strip()
        text = (re.sub("@\((.*)\)", "", text)).strip()
        if dupeCheck:
        #duplicate check
            for i in range(0, len(self.prompts)):
                if text == self.prompts[i].text:
                    return
        newPrompt = Prompt(text, tags, source)
        self.prompts.append(newPrompt)
        index = self.prompts.index(newPrompt)
        self.indices[channel] = index
        for tag in tags:
            if tag in self.categories:
                self.categories[tag].append(index)
            else:
                self.categories[tag] = [index]
   
    def loadPrompts(self, infile):
        for line in infile.readlines():
            self.addPrompt(line, "promptbot", True)
        self.infile.close()

    def addTags(self, tags, channel, index = ""):
        if not index:
            index = self.indices[channel]
        self.prompts[index].tags.update(tags)
        for tag in tags:
            if tag in self.categories:
                self.categories[tag].append(index)
            else:
                self.categories[tag] = [index]

    def addSource(self, source, channel, index = ""):
        if not index:
            index = self.indices[channel]
        self.prompts[index].source.extend(source)

    def getTags(self, channel, index = ""):
        if not index:
            index = self.indices[channel]
        tags = '; '.join(self.prompts[index].tags)
        if tags:
            return tags
        else:
            return "No tags."
    
    def getSource(self, channel, index = ""):
        if not index:
            index = self.indices[channel]
        source = '; '.join(self.prompts[index].source)
        if source:
            return source
        else:
            return "No source given."

    def getIndex(self, channel, index = ""):
        if not index:
            index = self.indices[channel]
        return "Prompt #%d" % (index)

    def last(self, channel):
        return self.prompts[self.indices[channel]].text

    def randomPrompt(self, channel):
        index = choice(range(0, len(self.prompts)))
        self.indices[channel] = index
        return self.prompts[index].text
        
    def promptByTag(self, tag, channel):
        if tag in self.categories:
            index = choice(self.categories[tag])
            self.indices[channel] = index
            return self.prompts[index].text
        else:
            return "None."

    def promptByIndex(self, index, channel):
        if index < len(self.prompts):
            self.indices[channel] = index
            return self.prompts[index].text
        else:
            return "I only contain %s prompts." % len(self.prompts)

    def listAllCategories(self):
       msg = ', '.join(self.categories.keys())
       return msg

    def backup(self, outfile):
        for prompt in self.prompts:
            line = prompt.text
            for tag in prompt.tags:
                line += " #(" + tag + ")"
            for source in prompt.source:
                line += " @(" + source + ")"
            line += "\n"
            outfile.write(line)
        outfile.close()

