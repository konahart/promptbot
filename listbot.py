#!/usr/bin/python2.7
from random import choice
from collections import Counter
import sys, re, json

class SetToListEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) is set:
            return list(obj)
        return obj.__dict__

class Entry(object):
    def __init__(self, text, tags, source):
        self.text = text #string
        self.tags = tags #set
        self.source = source #list
        self.weight = 1.0

class ListKeeper:
    def __init__(self):
        self.lists = {}

#add list to listkeeper
#return success of adding list
    def addList(self, listName):
        if listName in self.lists:
            return False
        else:
            self.lists[listName] = []
            return True 

#add entry to list in listkeeper
#return index of new entry or index of duplicate
    def addEntry(self, listName, text, tags, source, dupCheck=False):
        if dupCheck:
        #duplicate check by text
            for i in range(0, len(self.lists[listName])):
                #add any new tags or sources if text matches
                if text == self.lists[listName][i].text:
                    self.lists[listName][i].tags.update(tags)
                    self.lists[listName][i].source.extend(tags)
                    return i
        newEntry = Entry(text, tags, source)
        self.lists[listName].append(newEntry)
        index = self.lists[listName].index(newEntry)
        return index

#add tag or tags to entry in list in listkeeper
#return False if index is out of list range
    def addTags(self, listName, index, tags):
        try:
            self.lists[listName][index].tags.update(tags)
            return True
        except StandardError:
            return False

#add source or sources to entry in list in listkeeper
#return False if index is out of list range
    def addSource(self, listName, index, source):
        try:
            self.lists[listName][index].source.extend(source)
            return True
        except StandardError:
            return False

#change text of entry in list in listkeeper
#return False if index is out of list range
    def rewriteEntry(self, listName, index, text):
        try:
            self.lists[listName][index].text = text
            return True
        except StandardError:
            return False

#remove tag or tags to entry in list in listkeeper
#return False if index is out of list range
    def removeTags(self, listName, index, tags):
        try:
            for t in tags:
                self.lists[listName][index].tags.discard(t)
            return True
        except StandardError:
            return False

#remove source or sources to entry in list in listkeeper
#return False if index is out of list range
    def removeSource(self, listName, index, source):
        try:
            for s in source:
                self.lists[listName][index].source.remove(s)
            return True
        except StandardError, ValueError:
            return False

#return tags of entry in list in listkeeper
#return False if index is out of list range
    def getTags(self, listName, index):
        try:
            tags = self.lists[listName][index].tags
            if tags:
                return list(tags)
            else:
                return []
        except StandardError:
            return False
    
#return sources of entry in list in listkeeper
#return False if index is out of list range
    def getSource(self, listName, index):
        try:
            source = self.lists[listName][index].source
            if source:
                return source
            else:
                return []
        except StandardError:
            return False

#get randomly-chosen entry from specific list in listkeeper
#return index and entry
    def randomEntry(self, listName):
        #l = sum(entry.weight for entry in self.lists[listName])
        l = len(self.lists[listName])
        if l > 0:
            index = choice(range(0, len(self.lists[listName])))
            return index, self.lists[listName][index].text
        else:
            return None, None
        
#get randomly-chosen entry from randomly-chosen list in listkeeper
#return index, list, and entry
    def completelyRandomEntry(self):
        lists = []
        #compile list of non-empty lists
        for l in self.lists:
           if len(self.lists[l]) > 0:
               lists.append(l)
        if lists:
            randomList = choice(lists)
            index = choice(range(0, len(self.lists[randomList])))
            return index, randomList, self.lists[randomList][index]
        else:
            return None, None, None
    
#return randomly-chosen entry that has tag from specific list in listkeeper
    def entryByTag(self, listName, tag):
        indices = range(0, len(self.lists[listName]))
        while not indices == []:
            index = choice(indices)
            if tag in self.lists[listName][index].tags:
                return index, self.lists[listName][index].text
            indices.remove(index)
        return None, None

#return entry with index in specific list in listkeeper
    def entryByIndex(self, listName, index):
        try:
            return self.lists[listName][index].text
        except StandardError:
            return False

#return length of specific list in listkeeper
    def listLength(self, listName):
        return len(self.lists[listName])
    
#return all tags in specific list in listkeeper    
    def listTags(self, listName):
        tags = Counter()
        for i in range(0, len(self.lists[listName])):
            tags.update(self.lists[listName][i].tags)
        return dict(tags)

#return all tags in all lists in listkeeper    
    def listAllTags(self):
        tags = {}
        for listName in self.lists:
            tags[listName] = self.listTags(listName)
        return tags

    def load(self, infile):
        loaded = {}
        data = json.loads(open(infile, "r").read())
        for listName in data:
            self.addList(listName)
            loaded[listName] = 0
            for entry in data[listName]:
                text = entry['text'] 
                tags = set(entry['tags'])
                source = entry['source']
                newEntry = Entry(text, tags, source)
                self.lists[listName].append(newEntry)
                loaded[listName] += 1
        return loaded 

#back up a specific list in listkeeper
    def backup(self, listName, outfile):
        try:
            with open("lists", "w") as out:
                s = json.dumps(self.lists, cls=SetToListEncoder)
                out.write(s)
                out.close()
        except IOError:
            return None

#back up all lists in listkeeper
    def backupAll(self, outfile):
        outnames = {}
        for listName in self.lists:
            outnames[listName] = self.backup(listName, outfile)
        return outnames
