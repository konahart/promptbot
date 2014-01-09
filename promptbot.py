#!/usr/bin/python2.7
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl
from twisted.internet.task import LoopingCall, deferLater
from collections import defaultdict
from random import shuffle, choice
import sys, re, argparse
from datetime import *
from selectTopic import *
import listbot

class ircPromptBot(irc.IRCClient):
    """A bot that gives and takes prompts on request."""
    """Strongly based on ircLogBot example by Twisted Matrix Laboratories."""
    def __init__(self, factory):
        self.factory = factory
        self.nickname = self.factory.nick
        self.password = self.factory.password
        self.channels = self.factory.channels
        self.outfile = self.factory.outfile 
        self.lastLists = defaultdict(lambda: "prompt")
        #Keeps track of the last list accessed per channel
        self.indices = defaultdict(lambda: defaultdict(int))
        #Keeps track of the last element accessed per list per channel by
        #using the channel name as a key.
        self.response = ["Eh? Try asking me for a prompt.", "Whatcha tryin'a do, bub?", "You might need to see '%s, help'" % self.nickname]
        self.promptbot = listbot.ListKeeper()
        self.topics = {}
        self.commands = {"help": "self.help(msg, user, channel)",
                    "github": 'self.github(user, channel)',
                    "join": "self.joinChan(msg)", 
                    "leave": "self.leave(channel)",
                    "nick": "self.nick(msg)",
                    "change nick": "self.nick(msg)",
                    "about": "print 'about'", 
                    "random": "self.random(user, channel)", 
                    "topic": "self.setTopic(channel)",
                    "start topic": "self.startTopic(channel)",
                    "stop topic": "self.stopTopic(channel)",
                    "lists": "self.listLists(channel)",
                    "backup": "self.backup(msg, user)",
                    "tag": "self.allTags(msg, user, channel)", #for "tag counts"
                    "tags": "self.allTags(msg, user, channel)",
                    "add": "self.addRemoveCommands(msg, user, channel, True)",
                    "remove": "self.addRemoveCommands(msg, user, channel, False)",
                    "last": "self.last(msg, channel, user)",
                    "load": "self.load(msg, channel)",
                    "tags?": "self.entryTags(channel)",
                    "index?": "self.entryIndex(channel)",
                    "source?": "self.entrySource(channel)",
                    "info": ""  }
        #want prompt to be first in list of lists
        self.lists = []
        self.addList("prompt", "", False)
        self.promptbot.addList("prompt")
        files = self.factory.lists.pop("prompt", None)
        if files:
            for f in files:
                self.loadEntries("prompt",f)
        for l in self.factory.lists:
            self.addList(l, "", False)
            if self.factory.lists[l]:
                for f in self.factory.lists[l]:
                    if f:
                        self.loadEntries(l, f)
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        if self.promptbot:
            self.promptbot.backupAll(self.factory.outfile)
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.setNick(self.nickname)
        if self.channels:
            for c in self.channels:
                self.join(c)
        #start hourly backup of all lists
        lc = LoopingCall(self.promptbot.backupAll, self.factory.outfile)
        lc.start(3600, False)

    def joined(self, channel):
        for l in self.lists:
            self.indices[channel][l] = 0
        self.lastLists[channel] = "prompt"

    def alterCollidedNick(self, nickname):
        return "not" + nickname.capitalize()

    def addList(self, listName, channel, joined = True):
        for l in self.lists:  
        #make sure list names don't overlap, nor list names in plural
        #form (e.g., "prompt"/"prompts")
            if listName == l or listName == l+"s":
                self.msg(channel, "New list name %s overlaps with existing list name %s. Cannot create list %s." % (listName, l, listName))
                return
        for c in self.commands:
            if listName == c or listName == c+"s":
                self.msg(channel, "New list name %s overlaps with existing command %s. Cannot create list %s." % (listName, c, listName))
                return
        result = self.promptbot.addList(listName)
        if result:
            self.lists.append(listName)
            for channel in self.indices:
                self.indices[channel][listName] = 0
            self.commands[listName] = "self.listCommands('%s', msg, channel, user)" % (listName)
            msg = "New %s list added." % (listName)
        else:
            msg = "Unable to add %s list." % (listName)
        if joined:
            self.msg(channel, msg)

    def setTopic(self, channel, strict=False):
        topic = selectTopic(self.promptbot)
        if topic == "":
            if strict:
                self.topic(channel, topic)
        else:
            self.topic(channel, topic)

    def startTopic(self, channel):
        #will try to set the topic every day at midnight until stopTopic is called.
        if not channel in self.topics:
            lc = LoopingCall(self.setTopic, channel)
            delay = self.secondsToMidnight()
            d = deferLater(reactor, delay, lc.start, 86400)
            #figure out time til midnight for delay, then should loop every 24 hours (86400 seconds).
            self.topics[channel] = lc
            return True
        else:
            return False

    def secondsToMidnight(self):
        nextMidnight = datetime.combine(date.today() + timedelta(1), time(0,1))
        return (nextMidnight - datetime.now()).seconds

    def stopTopic(self, channel):
        if channel in self.topics:
            if self.topics[channel].running:
                self.topics[channel].stop()
                return True
            else:
                return False
        else:
            return False
   
    def tagsFromText(self, text):
        tags = set(re.findall("#\(([^\)]+)\)", text))
        tags.update(re.findall("#([^\(\s]+)", text))
        text = (re.sub("#\(([^\)]+)\)", "", text)).strip()
        text = (re.sub("#([^\(\s]+)", "", text)).strip()
        return text, list(tags)

    def sourceFromText(self, text):
        source = re.findall("@\(([^\)]+)\)", text)
        source.extend(re.findall("@([^\(\s]+)", text))
        text = (re.sub("@\(([^\)]+)\)", "", text)).strip()
        text = (re.sub("@([^\(\s])", "", text)).strip()
        return text, source
    
    def loadEntries(self, listName, infile):
        try:
            with open(infile, "r"):
                load = add = dup = 0
                for line in open(infile, "r").readlines():
                    text, tags = self.tagsFromText(line)
                    text, source = self.sourceFromText(text)
                    copy, index = self.promptbot.addEntry(listName, text, tags, source, True)
                    if copy:
                        dup += 1
                    else:
                        add += 1
                    load += 1
                open(infile, "r").close()
                return "%d %s entries in %s loaded, %d added, %d duplicates" % (load, listName, infile, add, dup)
        except IOError: 
            return "No such file '%s'" % (infile)
     
    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if channel == self.nickname:
            channel = user
        if msg.startswith("!"): #really stupid, temporary patch to allow for 
            msg = re.sub("!", self.nickname+" ", msg) # !command
        if msg.startswith(self.nickname) or channel == user:
            pattern = self.nickname + "\W( )?"
            msg = re.sub(pattern, '', msg)
            if msg == "":
                msg = "Yes, %s?" % user
                self.msg(channel, msg)
            for command in self.commands.keys():
                if command in re.findall("^"+command+"[\S]*", msg):
                    msg = re.sub(command+"\s*", "", msg)
                    exec(self.commands[command])
                    return
            msg = choice(self.response)
            if "%s" in msg:
                msg = msg % user
            self.msg(channel, msg)

    def respond(self, target, user, msg, prepend=""):
        f = re.findall("_{(.*)}", msg)
        if f:
        #fill-in mode
            msg = "%s: %s%s" % (user, prepend, msg) #temp
            self.msg(target, msg) #temp
        elif msg.startswith("/me"):
            action = re.sub("/me(\s)*","",msg)
            self.describe(target, action)
        else:
            msg = "%s: %s%s" % (user, prepend, msg)
            self.msg(target, msg)
    
    def addEntry(self, listName, text, user, target):
        text, tags = self.tagsFromText(text)
        text, source = self.sourceFromText(text)
        dup, index = self.promptbot.addEntry(listName, text, tags, source)
        if not dup:
            defaultSource = ["added by %s" % user]
            self.promptbot.addSource(listName, index, defaultSource)
            msg = (listName+" added.").capitalize()
            self.indices[target][listName] = index
        else:
            msg = ("That "+listName+" is a duplicate. See "+listName+" #"+str(index+1)) 
        self.msg(target, msg) 

    def index(self, listName, result, failure, target, user):
        if result:
            self.respond(target, user, result)
        else:
            self.msg(target, failure)
        return 

    def help(self, msg, user, channel):
        if "help prompts" in msg:
            self.msg(user, "'tag' for a prompt with that tag. Multiple tags will give a prompt with a tag randomly selected from those provided.\nsuch as 'promptbot, worldbuilding theme'\nUsing a number when talking to promptbot will return the prompt with that index. The last entry's index can be retrieved with 'index?'\nFor a random prompt, just use the word 'prompt'\n such as 'promptbot, prompt'\n'last prompt' will reprint the last prompt.")
        elif "help tags" in msg:
            self.msg(user, "'tags?' will give the list of tags for the last given entry.\n'add tag(s) #tag #(tag with spaces)' will add those tags to the last given entry.\n'remove tag(s) #tag #(tag with space)' will remove those tags from the last given entry.")
        elif "help sources" in msg:
            self.msg(user, "'source?' will give the source for the last given entry.\n'add source @source @(source with spaces)' will add that source to the last given entry.\n'remove source @source @(source with spaces)' will remove that source from the last given entry.")
        else:
            self.msg(channel, "PMing you with the info, %s" % user)
            self.msg(user,"Help topics include: 'prompts', 'tags', 'sources' \nType 'help $TOPIC' for more info.\nView promptbot's code at https://github.com/konayashi/promptbot")

    def joinChan(self, text):
        text = text.split()
        if len(text) >= 2:
        #if there's a channel key
            self.join(text[0], text[1])
        else:
            self.join(text[0])

    def github(self, user, channel):
        msg = "%s: %s" % (user, "https://github.com/konayashi/promptbot")
        self.msg(channel, msg)

    def nick(self, text):
        newNick = text.split()[0]
        self.nickname = newNick
        self.setNick(newNick)

    def random(self, user, channel):
        index, listName, prompt = self.promptbot.completelyRandomEntry()
        self.lastList = listName
        self.indices[channel][listName] = index
        self.respond(channel, user, prompt)

    def listLists(self, channel):
        self.msg(channel, ", ".join(self.lists))

    def backup(self, text, channel):
        if text.split():
            l = text.split()[0]
            if l in self.lists:
                out = self.promptbot.backup(l, self.factory.outfile)
                msg = "%d %s entries backed up to %s." % (self.promptbot.listLength(l), l, out)
            else:
                msg = "I do not have a %s list." % (l)
        else:
            out = self.promptbot.backupAll(self.factory.outfile)
            msg = "All lists backed up."
        self.msg(channel, msg)

    def addRemoveCommands(self, text, user, channel, add = True):
        t = text.split()
        if len(t) > 1:
            if t[0] in self.lists:
                self.lastLists[channel] = t[0] 
                if t[1]:
                    self.addEntry(t[0], t[1], user, channel)
            elif t[0] == "tag" or t[0] == "tags":
                l = self.lastLists[channel]
                index = self.indices[channel][l]
                tags = re.findall("#?\((.+)\)", text)
                tags.extend(re.findall("#?([^\(\s]+)", text))
                if tags:
                    t = "tag"
                    if len(tags) > 1:
                        t += "s"
                    if add:
                        result = self.promptbot.addTags(l, index, tags)
                    else:
                        result = self.promptbot.removeTags(l, index, tags)
                    if result:
                        if add:
                            self.msg(channel, "%s added." % (t.capitalize()))
                        else:
                            self.msg(channel, "%s removed." % (t.capitalize()))
                    else:
                        if add:
                            self.msg(channel, "Failed to add %s." % t)
                        else:
                            self.msg(channel, "Failed to remove %s." % t)
                else:
                    if add:
                        self.msg(channel, "No tags found. Try 'add tag(s) #tag or #(tag with spaces)', or 'see %s help' for more details." % self.nickname)
                    else:
                        self.msg(channel, "No tags found. Try 'remove tag(s) #tag or #(tag with spaces)', or 'see %s help' for more details." % self.nickname)
            elif t[0] == "source" or t[0] == "sources":
                l = self.lastLists[channel]
                index = self.indices[channel][l]
                text, source = self.sourceFromText(text)
                if source:
                    s = "source"
                    if len(source) > 1:
                        s += "s"
                    if add:
                        result = self.promptbot.addSource(l, index, source)
                    else:
                        result = self.promptbot.removeSource(l, index, source)
                    if result:
                        if add:
                            self.msg(channel, "%s added." % (s.capitalize()))
                        else:
                            self.msg(channel, "%s removed." % (s.capitalize()))
                    else:
                        if add:
                            self.msg(channel, "Failed to add %s." % s)
                        else:
                            self.msg(channel, "Failed to remove %s." % s)
                else:
                    if add:
                        self.msg(channel, "No source found. Try 'add source(s) @source or @(source with spaces)', or see '%s help' for more details." % self.nickname)
                    else:
                        self.msg(channel, "No source found. Try 'remove source(s) @source or @(source with spaces)', or see '%s help' for more details." % self.nickname)
        else:
            if add:
                self.msg(channel, "Try 'add (list) text', 'add tag #tag', or 'add source @(source)")
            else:
                self.msg(channel, "Try 'remove (list) text', 'remove tag #tag', or 'remove source @(source)")

    def last(self, text, channel, user): 
        l = self.lastLists[channel] 
        index = self.indices[channel][l]
        if text:
            for l in self.lists:
                if l in text:
                    text = re.sub(l+"\s*", "", text)
                    index = self.indices[channel][l]
                    result = self.promptbot.entryByIndex(l, index)
                    failure = "No last %s." % (l)
                    self.index(l, result, failure, channel, user)
                    return
            self.listCommands(l, text, channel, user)
        else:
            failure = "No last %s." % (l)
            result = self.promptbot.entryByIndex(l, index)
            self.index(l, result, failure, channel, user)

    def load(self, text, channel):
        text = text.split()
        l = text[0]
        if l: 
            if l in self.lists:
                if text[1]:
                    msg = self.loadEntries(l, text[1])
                else:
                    msg = "Please provide a filename to load."
            else:
                msg = "I do not have a %s list." % (l)
            self.msg(channel, msg)

    def allTags(self, text, user, channel):
        tagcounts = self.promptbot.listAllTags()
        if re.search("counts", text):
            msg = ""
            for l in tagcounts:
                msg += "%s: " % (l)
                tags = []
                for tag, count in tagcounts[l].items():
                    tags.append("%s:%s" % (tag, count))
                msg += ", ".join(tags)
                msg += '\n'
        else:
            msg = ""
            for l in tagcounts:
                msg += "%s: " % (l)
                msg += ", ".join(tagcounts[l])
                msg += '\n'
        adjectives = ["long", "long", "long", "long", "strongly-worded"]
        self.msg(channel, "Sending %s message to you in PM, %s." % (choice(adjectives), user))
        self.msg(user, msg)

    def listCommands(self, l, text, channel, user):
        if text:
            if re.search("^tags", text):
                self.listTags(l, text, channel)
            elif re.search("^length", text):
                self.listLength(l, channel)
            elif re.search("^info", text): 
                adjectives = ["long", "long", "long", "long", "strongly-worded"]
                self.msg(channel, "Sending %s message to you in PM, %s." % (choice(adjectives), user))
                self.listLength(l, user)
                self.listTags(l, "^counts", user)
            elif text.isdigit():
                msg = self.promptbot.entryByIndex(l, text)
                count = self.promptbot.listLength(l)
                failure =  "I only have %d %s entries" % (count, l)
                #off by 1
                result = self.promptbot.entryByIndex(l, int(index[0])-1)
                self.index(l, result, failure, channel, user) 
            else:
                text, tags = self.tagsFromText(text)
                if tags:
                    i = 0
                    shuffle(tags)
                    prompt = None
                    while not prompt and i < len(tags):
                        index, prompt = self.promptbot.entryByTag(self.lastLists[channel], tags[i])
                        i += 1
                    if prompt:
                        prepend = tags[i-1].capitalize() + ": "
                        self.indices[channel][l] = index
                        self.respond(channel, user, prompt, prepend)
                    else:
                        self.msg(channel, user+": Could not find "+l+" matching request.")
        else:
            index, prompt = self.promptbot.randomEntry(l) 
            self.indices[channel][l] = index
            self.respond(channel, user, prompt)

    def listTags(self, l, text, channel):
        tagcounts = self.promptbot.listTags(l)
        if re.search("counts", text):
            text = ""
            tags = []
            for tag, count in tagcounts.items():
                tags.append("%s:%s" % (tag, count))
            text += ", ".join(tags)
        else:
             text = ("%s: " % (l)) + ", ".join(tagcounts) + "\n"
        self.msg(channel, text)

    def listLength(self, l, channel):
        count = self.promptbot.listLength(l)
        msg = "I have %d %s entries." % (count, l)
        self.msg(channel, msg)

    def entryTags(self, channel):
        l = self.lastLists[channel] 
        index = self.indices[channel][l]
        tags = self.promptbot.getTags(l, index)
        if tags:
            msg = ", ".join(tags) 
        else:
            msg = "No tags."
        self.msg(channel, msg) 

    def entrySource(self, channel):
        l = self.lastLists[channel] 
        index = self.indices[channel][l]
        source = self.promptbot.getSource(l, index)
        if source:
            msg = "; ".join(source) 
        else:
            msg = "No sources given."
        self.msg(channel, msg) 

    def entryIndex(self, channel):
        l = self.lastLists[channel] 
        index = self.indices[channel][l]
        msg = "%s #%d" % (l.capitalize(), index)

class BotFactory(protocol.ClientFactory):
    def __init__(self, nick, password, channels, lists, output):
        self.nick = nick
        self.password = password
        self.channels = channels
        self.lists = lists
        self.outfile = output 

    def buildProtocol(self, addr):
        p = ircPromptBot(self)
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

def listsToDict(listArgs):
    lists = {}
    for l in listArgs:
        if len(l) == 1:
            lists[l[0]] = None
        elif len(l) > 1:
            lists[l[0]] = l[1:]
    return lists

def main():
    parser = argparse.ArgumentParser(description="An irc bot that gives writing prompts on command.")
    parser.add_argument("-s", "--server", default="irc.freenode.net", help="server to connect to")
    parser.add_argument("-p", "--port", default=6667, type=int, help="port to connect to")
    parser.add_argument("--ssl", action="store_true")
    parser.add_argument("-c", "--channel", nargs="+", dest="channels", help="channel(s) to join")
    parser.add_argument("-n", "--nick", "--nickname", default="promptbot", help="nick of bot")
    parser.add_argument("--pass", "--password", default="promptbot", dest="password")
    parser.add_argument("-l", "--list", nargs="+", default=[], action="append", help="listname [input files]")
    parser.add_argument("-o", "--output", default="prompbot.pb", help="output file name")
    if len(sys.argv) == 1:
    #if there are no arguments, check if there's an init file
        try:
            with open('init.pb') as f:
                s = []
                for line in f.readlines():
                    s.extend(line.split())
                settings = parser.parse_args(s)
        except IOError:
            settings = parser.parse_args() #all defaults (no channels)
    elif len(sys.argv) == 2:
    #if there are no arguments, check if there's an init file
        try:
            with open(sys.argv[1]) as f:
                s = []
                for line in f.readlines():
                    s.extend(line.split())
                settings = parser.parse_args(s)
        except IOError:
            settings = parser.parse_args() #all defaults (no channels)
    lists = listsToDict(settings.list)
    f = BotFactory(settings.nick, settings.password, settings.channels, lists, settings.output)
    if settings.ssl:
        reactor.connectSSL(settings.server, settings.port, f, ssl.ClientContextFactory())
    else:
        reactor.connectTCP(settings.server, settings.port, f)
    reactor.run()

if __name__ == '__main__':
    main()
