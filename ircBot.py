#!/usr/bin/python2.7
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.internet.task import LoopingCall, deferLater
from random import shuffle
import sys, re
from datetime import *
import promptbot

class Bot(irc.IRCClient):
    """A bot that gives and takes prompts on request."""
    """Strongly based on ircLogBot example by Twisted Matrix Laboratories."""
    
    nickname = "promptbot"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.promptbot = promptbot.PromptBot(open(self.factory.infile, "r"),self.factory.outfile)
    
    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)

    def joined(self, channel):
        lc = LoopingCall(self.setTopic, channel)
        delay = self.secondsToMidnight()
        d = deferLater(reactor, delay, lc.start, 86400) #figure out time til midnight for delay, then should loop every 24 hours (86400 seconds).
        d.addCallback(self.joined)

    def secondsToMidnight(self):
        nextMidnight = datetime.combine(date.today() + timedelta(1), time(0,1))
        return (nextMidnight - datetime.now()).seconds
    
    def secondsToHalfHour(self):
        if datetime.now().minute < 30:
            nextHalfHour = datetime.combine(date.today(), time(datetime.now().hour, 45))
        else:
            nextHalfHour = datetime.combine(date.today(), time(datetime.now().hour+1))
        return (nextHalfHour - datetime.now()).seconds

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if channel == self.nickname:
            channel = user
        if msg.startswith(self.nickname) or channel == user:
            pattern = self.nickname + "\W( )?"
            msg = re.sub(pattern, '', msg)
            if "help" in msg:
                self.helpMenu(msg, user, channel)
            elif msg == "github":
                msg = "%s: %s" % (user, "https://github.com/konayashi/promptbot")
                self.msg(channel, msg)
            else:
                #check for command
                self.commands(msg, user, channel)
    
    def setTopic(self, channel):
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
            prompt = self.promptbot.promptByTag("worldbuilding")
            topic += prompt
        elif day == 0:
            if not topic == "":
                topic += "| "
            topic += "Character Monday: "
            prompt = self.promptbot.promptByTag("character")
            topic += prompt
        elif day == 3:
            if not topic == "":
                topic += "| "
            topic += "Theme Thursday: "
            prompt = self.promptbot.promptByTag("theme")
            topic += prompt
        self.topic(channel, topic)

    def commands(self, msg, user, target):
        if msg.startswith("load"):
            msg = re.sub("load(\s)?", '', msg)
            self.promptbot.loadPrompts(open(msg, "r"))
            self.msg(target, "Prompts in %s added." % msg)
            return
        if msg.startswith("topic"):
            self.setTopic(target)
            return
        #tag commands
        elif msg.startswith("tags?"):
            self.msg(target, self.promptbot.getTags()) 
            return
        elif msg.startswith("tags"):
            msg = self.promptbot.listAllCategories()
            self.msg(target, msg)
            return
        elif msg.startswith("add tag"):
            tags = re.findall("#\((.+)\)", msg)
            tags.extend(re.findall("#([^\(\s]+)", msg))
            if tags:
                self.promptbot.addTags(tags)
                self.msg(target, "Tags added.")
                return
            else:
                self.msg(target, "No tags found. Try 'add tag(s) #tag or #(tag)'.")
                return
        #source commands
        elif msg.startswith("source?"):
            self.msg(target, self.promptbot.getSource()) 
            return
        elif msg.startswith("add source"):
            source = re.findall("@\((.+)\)", msg)
            if source:
                self.promptbot.addSource(source)
                self.msg(target, "Source added.")
                return
            else:
                self.msg(target, "No source found. Try 'add source @(source)'.")        
                return
	#prompt commands
        if msg.startswith("add prompt"):
            msg = re.sub("add prompt\W( )?", '', msg)
            #add rest of msg to list of prompts
            self.promptbot.addPrompt(msg)
            msg = "Prompt added."
            self.msg(target, msg) 
            return
        elif msg.startswith("last"):
            msg = self.promptbot.last()
            self.msg(target, msg)
            return
        elif msg.startswith("backup prompts"):
            self.promptbot.backup(open(self.factory.outfile, "w"))
            msg = "%d prompts backed up to %s." % (len(self.promptbot.prompts), self.factory.outfile)
            target = user
            self.msg(target, msg)
            return
        index = re.findall('[0-9]+', msg)
        if index:
            msg = "%s: %s" % (user, self.promptbot.promptByIndex(int(index[0])))
            self.msg(target, msg)
            return
        tags = re.findall("#\((.+)\)", msg)
        tags.extend(re.findall("#([^\(\s]+)", msg))
        if tags:
            i = 0
            prompt = "None."
            shuffle(tags)
            while prompt == "None." and i < len(tags):
                prompt = self.promptbot.promptByTag(tags[i])
                i += 1
            if prompt == "None.":
                msg = "Not able to find any matching prompts."
            else:
                msg = "%s: %s" % (user, prompt)
            self.msg(target, msg)
            return
        elif "prompt" in msg:
            msg = "%s: %s" % (user, self.promptbot.randomPrompt())
            self.msg(target, msg)
            return 
        elif msg.startswith("index?"):
            self.msg(target, self.promptbot.getIndex()) 
            return 
        else: 
            msg = "Eh? Try asking me for a prompt."
            self.msg(target, msg)
            return

    def helpMenu(self, msg, user, channel):
        if "help prompts" in msg:
            self.msg(channel, "'#(tag)' for a prompt with that tag. Multiple tags will give a prompt with a tag randomly selected from those provided.\n\t'promptbot, I want a prompt from #worldbuilding or #theme' or 'promptbot, #worldbuilding #theme'\nUsing a number when talking to promptbot will return the prompt with that index. The last prompt's index can be retrieved with 'index?'\nFor a random prompt, just use the word 'prompt'\n\t'promptbot, gimme a prompt' or 'promptbot, prompt'\n'last' will reprint the last prompt.")
        elif "help tags" in msg:
            self.msg(channel, "'tags?' will give the list of tags for the last given prompt.\n'add tag(s) #tag #(tag with spaces)' will add those tags to the last given prompt.")
        elif "help sources" in msg:
            self.msg(channel, "'source?' will give the source for the last given prompt.\n'add source @(source)' will add that source to the last given prompt.")
        else:
            self.msg(channel,"Help topics include: 'prompts', 'tags', 'sources' \nType 'help $TOPIC' for more info.\nView promptbot's code at https://github.com/konayashi/promptbot")

class BotFactory(protocol.ClientFactory):
    def __init__(self, channel, infile, outfile = ""):
        self.channel = channel
        self.infile = infile
        if outfile:
            self.outfile = outfile
        else:
            self.outfile = infile + ".pb"

    def buildProtocol(self, addr):
        p = Bot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

if __name__ == '__main__':
    if len(sys.argv) >= 4:
        f = BotFactory(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        f = BotFactory(sys.argv[1], sys.argv[2])
    reactor.connectTCP("irc.cat.pdx.edu", 6667, f)
    reactor.run()
