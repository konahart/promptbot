#!/usr/bin/python3.7
from collections import defaultdict
from random import choice
import sys, re

class Entry(object):
    def __init__(self, text, tags, source):
        self.text = text
        self.tags = tags
        self.source = source

class List(object):
    def __init__(self):
        self.entries = list()
        self.tags = {}

class ListBot:
    def __init__(self):
        self.indices = defaultdict(lambda: defaultdict(int))
        #Keeps track of the last element accessed per list per channel by
        #using the channel name as a key.
        self.lists = {}

    def addList(self, listName):
        if listName in self.lists:
            return "There is already a list with that name."
        else:
            self.lists[listName] = List()
            for channel in self.indices:
                self.indices[channel][listName] = 0
            return "List %s added." % listName

    def addEntry(self, listName, entryText, channel, dupCheck=False):
        tags = set(re.findall("#\(([^\)]+)\)", entryText))
        tags.update(re.findall("#([^\(\s]+)", entryText))
        source = re.findall("@\(([^\)]+)\)", entryText)
        entryText = (re.sub("#\(([^\)]+)\)", "", entryText)).strip()
        entryText = (re.sub("#([^\(\s]+)", "", entryText)).strip()
        entryText = (re.sub("@\((.*)\)", "", entryText)).strip()
        if dupCheck:
        #duplicate check
            for i in range(0, len(self.lists[listName].entries)):
                for entry in self.lists[listName].entries:
                    if entryText == entry.text:
                        return
        newEntry = Entry(entryText, tags, source)
        self.lists[listName].entries.append(newEntry)
        index = self.lists[listName].entries.index(newEntry)
        for tag in tags:
            if tag in self.lists[listName].tags:
                self.lists[listName].tags[tag].append(index)
            else:
                self.lists[listName].tags[tag] = [index]
        self.indices[channel][listName] = index
   
    def loadEntries(self, listName, inf):
        try:
            with open(inf, "r"):
                i = 0
                for line in open(inf, "r").readlines():
                    self.addEntry(listName, line, "listbot", True)
                    i += 1
                open(inf, "r").close()
                return "%d %s entries in %s loaded." % (i, listName, inf)
        except IOError: 
            return "No such file '%s'" % (inf)

    def addTags(self, listName, tags, channel, index = ""):
        if not index:
            index = self.indices[channel][listName]
        for tag in tags:
            if tag in self.lists[listName].tags:
                self.lists[listName].tags[tag].append(index)
            else:
                self.lists[listName].tags[tag] = [index]
        self.lists[listName].entries[index].tags.update(tags)

    def addSource(self, listName, source, channel, index = ""):
        if not index:
            index = self.indices[channel][listName]
        self.lists[listName].entries[index].source.extend(source)

    def rewriteEntry(self, listName, text, channel, index=""):
        if not index:
            index = self.indices[channel][listName]
        self.lists[listName].entries[index].text = text

    def removeTags(self, listName, tags, channel, index = ""):
        if not index:
            index = self.indices[channel][listName]
        for tag in tags:
            if tag in self.lists[listName].tags:
                if index in self.lists[listName].tags[tag]:
                    self.lists[listName].tags[tag].remove(index)
                    self.lists[listName].entries[index].tags.remove(tag)

    def removeSource(self, listName, source, channel, index = ""):
        if not index:
            index = self.indices[channel][listName]
        for s in source:
            if s in self.lists[listName].entries[index].source:
                self.lists[listName].entries[index].source.remove(s)

    def getTags(self, listName, channel, index = ""):
        if not index:
            index = self.indices[channel][listName]
        if len(self.lists[listName].entries) > 0:
            tags = '; '.join(self.lists[listName].entries[index].tags)
            if tags:
                return tags
            else:
                return "No tags."
        else:
            return "No %s entries to have tags." % listName
    
    def getSource(self, listName, channel, index = ""):
        if not index:
            index = self.indices[channel][listName]
        if len(self.lists[listName].entries) > 0:
            source = '; '.join(self.lists[listName].entries[index].source)
            if source:
                return source
            else:
                return "No source given."
        else:
            return "No %s entries to have sources." % listName

    def getIndex(self, listName, channel, index = ""):
        if not index:
            index = self.indices[channel][listName]
        if len(self.lists[listName].entries) > 0:
            return "%s #%d" % (listName.capitalize(), index)
        else:
            return "No %s entries to have indexes." % listName

    def last(self, listName, channel):
        index = self.indices[channel][listName]
        if len(self.lists[listName].entries) > 0:
            return self.lists[listName].entries[index].text
        else:
            return "%s has no entries." % listName.capitalize()

    def randomEntry(self, listName, channel):
        l = len(self.lists[listName].entries)
        if l > 0:
            index = choice(range(0, len(self.lists[listName].entries)))
            self.indices[channel][listName] = index
            return self.lists[listName].entries[index].text
        else:
            return "%s has no entries." % listName
        
    def completelyRandomEntry(self, channel):
        lists = []
        for l in self.lists:
           if len(self.lists[l].entries) > 0:
               lists.append(l)
        if lists:
            randomList = choice(lists)
            entry = choice(range(0, len(self.lists[randomList].entries)))
            self.indices[channel][randomList] = entry
            return self.lists[randomList].entries[entry].text
        else:
            return "there are no entries."
    
    def entryByTag(self, listName, tag, channel):
        if tag in self.lists[listName].tags:
            index = choice(self.lists[listName].tags[tag])
            self.indices[channel][listName] = index
            return self.lists[listName].entries[index].text
        else:
            return "No entries have tag %s." % tag

    def entryByIndex(self, listName, index, channel):
        if index < len(self.lists[listName].entries):
            self.indices[channel][listName] = index
            return self.lists[listName].entries[index].text
        else:
            return "I only contain %s %s entries." % (len(self.lists[listName].entries),listName)
    
    def listTags(self, listName):
        if len(self.lists[listName].tags) > 0:
            msg = ', '.join(self.lists[listName].tags.keys())
        else:
            msg = "%s has no tags." % (listName.capitalize())
        return msg

    def listAllTags(self):
        msg = ""
        for listName in self.lists:
            tags = ', '.join(self.lists[listName].tags.keys())
            tags = listName + ": " + tags + "\n"
            msg += tags
        return msg

    def backup(self, listName, outfile):
        if len(self.lists) == 1:
            outname = outfile 
        else:
            outname = outfile + "." + listName 
        out = open(outname, "w")
        for entry in self.lists[listName].entries:
            line = entry.text
            for tag in entry.tags:
                line += " #(" + tag + ")"
            for source in entry.source:
                line += " @(" + source + ")"
            line += "\n"
            out.write(line)
        out.close()
        return outname

    def backupAll(self, outfile):
        for listName in self.lists:
            if len(self.lists) == 1:
                out = open(outfile, "w")
            else:
                out = open(outfile + "." + listName, "w")
            for entry in self.lists[listName].entries:
                line = entry.text
                for tag in entry.tags:
                    line += " #(" + tag + ")"
                for source in entry.source:
                    line += " @(" + source + ")"
                line += "\n"
                out.write(line)
            out.close()

