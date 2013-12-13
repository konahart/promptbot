#!/usr/bin/python2.7
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl
from twisted.internet.task import LoopingCall, deferLater
from collections import defaultdict
from random import shuffle
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
        self.lists = self.factory.lists
        self.outfile = self.factory.outfile 
        self.lastLists = defaultdict(lambda: "prompt")
        self.promptbot = listbot.ListBot()
        self.topics = {}
        for l in self.lists:
            self.promptbot.addList(l)
            for f in self.lists[l]:
                if not f == "":
                    self.promptbot.loadEntries(l, f)
        self.lists = self.lists.keys()
        if not "prompt" in self.lists:
            self.promptbot.addList("prompt")
            self.lists.append("prompt")
    
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

    def alterCollidedNick(self, nickname):
        return "not" + nickname.capitalize()

    def setTopic(self, channel, strict=False):
        topic = selectTopic(self.promptbot, channel)
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

    def secondsToMidnight(self):
        nextMidnight = datetime.combine(date.today() + timedelta(1), time(0,1))
        return (nextMidnight - datetime.now()).seconds

    def stopTopic(self, channel):
        if channel in self.topics:
            if self.topics[channel].running:
                self.topics[channel].stop()
    
    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if channel == self.nickname:
            channel = user
        if msg.startswith(self.nickname) or channel == user:
            pattern = self.nickname + "\W( )?"
            msg = re.sub(pattern, '', msg)
            if msg == "":
                msg = "Yes, %s?" % user
                self.msg(channel, msg)
            if "help" in msg:
                self.helpMenu(msg, user, channel)
            elif msg == "github":
                msg = "%s: %s" % (user, "https://github.com/konayashi/promptbot")
                self.msg(channel, msg)
            elif msg.startswith("change nick"):
                newNick = msg.split()[2]
                newNick = re.sub("change nick(\s)*","", msg)
                self.setNick(newNick)
            elif msg.startswith("join"):
                msg = msg.split()
                if len(msg) >= 3:
                #if there's a channel key
                    self.join(msg[1], msg[2])
                else:
                    self.join(msg[1])
            elif msg.startswith("leave"):
                self.leave(channel)
            else:
                #check for promptbot-specific command
                self.commands(msg, user, channel)

    def msgOrMe(self, target, user, msg, prepend=""):
        if msg.startswith("/me"):
            action = re.sub("/me(\s)*","",msg)
            self.describe(target, action)
        else:
            msg = "%s: %s%s" % (user, prepend, msg)
            self.msg(target, msg)
    
    def commands(self, msg, user, target):
        m = msg.split()
        for l in self.lists: 
            if len(m) >= 2 and re.search(l+"(s)?", ' '.join(m[:2])):
                self.lastLists[target] = l 
                if msg.startswith("add "+l):
                    msg = re.sub("add "+l+"\W( )?", '', msg)
                    #add rest of msg to list
                    defaultSource = " @(added by %s)" % user
                    msg = msg + defaultSource
                    self.promptbot.addEntry(l, msg, target)
                    msg = (l+" added.").capitalize()
                    self.msg(target, msg) 
                    return
                elif msg.startswith("last "+l):
                    msg = self.promptbot.last(l, target)
                    self.msgOrMe(target, user, msg)
                    return
                elif msg.startswith(l+" tags"):
                    self.msg(target, self.promptbot.listTags(l))
                    return
                elif msg.startswith("backup "+l):
                    out = self.promptbot.backup(l, self.factory.outfile)
                    msg = "%d %s entries backed up to %s." % (len(self.promptbot.lists[l].entries), l, out)
                    target = user
                    self.msg(target, msg)
                    return
                elif msg.startswith("load "+l):
                    msg = re.sub("load "+l+"s?(\s)?", '', msg)
                    msg = self.promptbot.loadEntries(l, msg)
                    self.msg(target, msg)
                    return
                msg = re.sub(l,'', msg)
                tags = re.findall("#?\((.+)\)", msg)
                tags.extend(re.findall("#?([^\(\s]+)", msg))
                if tags:
                    i = 0
                    shuffle(tags)
                    prompt = "No entries"
                    while "No entries" in prompt and i < len(tags):
                        prompt = self.promptbot.entryByTag(self.lastLists[target], tags[i], target)
                        i += 1
                    if not "No entries" in prompt:
                        prepend = tags[i-1].capitalize() + ": "
                        self.msgOrMe(target, user, prompt, prepend)
                        return
                index = re.findall('[0-9]+', msg)
                if index:
                    self.msgOrMe(target, user, self.promptbot.entryByIndex(l, int(index[0]),target))
                    return
                self.msgOrMe(target, user, self.promptbot.randomEntry(l, target))
                return
            elif l in m[0]:
                self.lastLists[target] = l 
                self.msgOrMe(target, user, self.promptbot.randomEntry(l, target))
                return
        else: 
            if msg.startswith("last"):
                prompt = self.promptbot.last(self.lastLists[target], target)
                self.msgOrMe(target, user, prompt)
                return
            elif msg.startswith("add tag"):
            #add a tag to last entry printed
                tags = re.findall("#?\((.+)\)", msg)
                tags.extend(re.findall("#?([^\(\s]+)", msg))
                if tags:
                    self.promptbot.addTags(self.lastLists[target], tags, target)
                    if len(tags) > 1:
                        self.msg(target, "Tags added.")
                    else:
                        self.msg(target, "Tag added.")
                else:
                    self.msg(target, "No tags found. Try 'add tag(s) #tag or #(tag)'.")
                return
            elif msg.startswith("add source"):
            #add a source to last entry printed
                source = re.findall("@\((.+)\)", msg)
                source.extend(re.findall("@([^\(\s]+)", msg))
                if source:
                    self.promptbot.addSource(self.lastLists[target], source, target)
                    if len(source) > 1:
                        self.msg(target, "Sources added.")
                    else:
                        self.msg(target, "Source added.")
                else:
                    self.msg(target, "No source found. Try 'add source(s) @source or @(source with spaces)'.")        
                return
            elif msg.startswith("tags?"):
            #get all tags for last entry printed
                self.msg(target, self.promptbot.getTags(self.lastLists[target], target)) 
                return
            elif msg.startswith("source?"):
            #get all sources for last entry printed
                self.msg(target, self.promptbot.getSource(self.lastLists[target], target)) 
                return
            elif msg.startswith("index?"):
            #get index for last entry printed
                self.msg(target, self.promptbot.getIndex(self.lastLists[target],target)) 
                return 
            elif msg.startswith("remove tag"):
            #remove a tag from last entry printed
                tags = re.findall("#?\((.+)\)", msg)
                tags.extend(re.findall("#?([^\(\s]+)", msg))
                if tags:
                    self.promptbot.removeTags(self.lastLists[target], tags, target)
                    if len(tags) > 1:
                        self.msg(target, "Tags removed.")
                    else:
                        self.msg(target, "Tag removed.")
                else:
                    self.msg(target, "No tags found. Try 'remove tag(s) #tag or #(tag with spaces)'.")
                return
            elif msg.startswith("remove source"):
            #remove a source from last entry printed
                source = re.findall("@\((.+)\)", msg)
                source.extend(re.findall("@([^\(\s]+)", msg))
                if source:
                    self.promptbot.removeSource(source, target)
                    if len(source) > 1:
                        self.msg(target, "Sources removed.")
                    else:
                        self.msg(target, "Source removed.")
                else:
                    self.msg(target, "No source found. Try 'remove source(s) @source or @(source with spaces)'.")        
                return
            elif msg.startswith("backup"):
                out = self.promptbot.backupAll(self.factory.outfile)
                msg = "All lists backed up."
                target = user
                self.msg(target, msg)
                return
            elif msg.startswith("add list"):
            #add a new list
                msg = re.sub("add list(\s)?", '', msg)
                for l in self.lists:  
                #make sure list names don't overlap, nor list names in plural
                #form (e.g., "prompt"/"prompts")
                    if msg == l or msg == l+"s":
                        self.msg(target, "New list name %s overlaps with existing list name %s. Cannot create list %s." % (msg, l,  msg))
                        return
                self.promptbot.addList(msg)
                self.lists.append(msg)
                self.msg(target, "New %s list added." % (msg))
                self.lastLists[target] = msg 
                return
            elif msg.startswith("tags"):
                msg = self.promptbot.listAllTags()
                self.msg(target, msg)
                return
            if msg.startswith("start topic"):
                self.startTopic(target)
                self.msg(target, "I will try to set the topic every night at midnight.")
                return
            if msg.startswith("stop topic"):
                self.stopTopic(target)
                self.msg(target, "I will stop trying to set the topic.")
                return
            if msg.startswith("topic"):
                self.setTopic(target)
                return
            tags = re.findall("#\((.+)\)", msg)
            tags.extend(re.findall("#([^\(\s]+)", msg))
            if tags:
                self.lastLists[target] = "prompt"
                i = 0
                shuffle(tags)
                prompt = "No entries"
                while "No entries" in prompt and i < len(tags):
                    prompt = self.promptbot.entryByTag(self.lastLists[target], tags[i], target)
                    i += 1
                if not "No entries" in prompt:
                    prepend = tags[i-1].capitalize() + ": "
                    self.msgOrMe(target, user, prompt, prepend)
                    return
            index = re.findall('[0-9]+', msg)
            if index:
                prompt = self.promptbot.entryByIndex(self.lastLists[target], int(index[0]),target)
                self.msgOrMe(target, user, prompt)
                return
            elif "random" in msg:
                prompt = self.promptbot.completelyRandomEntry(target)
                self.msgOrMe(target, user, prompt)
                return 
            else: 
                msg = "Eh? Try asking me for a prompt."
                self.msg(target, msg)
                return

    def helpMenu(self, msg, user, channel):
        if "help prompts" in msg:
            self.msg(channel, "'tag' for a prompt with that tag. Multiple tags will give a prompt with a tag randomly selected from those provided.\n\t'promptbot, I want a prompt from worldbuilding or theme' or 'promptbot, worldbuilding theme'\nUsing a number when talking to promptbot will return the prompt with that index. The last entry's index can be retrieved with 'index?'\nFor a random prompt, just use the word 'prompt'\n\t'promptbot, gimme a prompt' or 'promptbot, prompt'\n'last prompt' will reprint the last prompt.")
        elif "help tags" in msg:
            self.msg(channel, "'tags?' will give the list of tags for the last given entry.\n'add tag(s) #tag #(tag with spaces)' will add those tags to the last given entry.\n'remove tag(s) #tag #(tag with space)' will remove those tags from the last given entry.")
        elif "help sources" in msg:
            self.msg(channel, "'source?' will give the source for the last given entry.\n'add source @source @(source with spaces)' will add that source to the last given entry.\n'remove source @source @(source with spaces)' will remove that source from the last given entry.")
        else:
            self.msg(channel,"Help topics include: 'prompts', 'tags', 'sources' \nType 'help $TOPIC' for more info.\nView promptbot's code at https://github.com/konayashi/promptbot")

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
            lists[l[0]] = ""
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
    parser.add_argument("--pass", "--password", default="promptbot", dest="password", help="nick of bot")
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
