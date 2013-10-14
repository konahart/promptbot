#!/usr/bin/python2.7
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from random import choice
import time, sys, re
import promptbot

class Bot(irc.IRCClient):
    """A bot that gives and takes prompts on request."""
    """Strongly based on ircLogBot example by Twisted Matrix Laboratories."""
    
    nickname = "promptbot"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.promptbot = promptbot.PromptBot(open(self.factory.file, "r"))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if msg.startswith(self.nickname):
            pattern = self.nickname + "\W( )?"
            msg = re.sub(pattern, '', msg)
            #check for command
            target, msg = self.commands(msg, user, channel)
            self.msg(target, msg)

    def commands(self, msg, user, target):
        #prompt commands
        if msg.startswith("add prompt"):
            msg = re.sub("add prompt\W( )?", '', msg)
            #add rest of msg to list of prompts
            self.promptbot.addPrompt(msg)
            msg = "Prompt added."
            return (target, msg) 
        elif msg.startswith("last prompt"):
            msg = self.promptbot.last()
            return (target, msg)
        elif msg.startswith("backup prompts"):
            self.promptbot.backup(open(self.factory.file, "w"))
            msg = "%d prompts backed up." % (len(self.promptbot.prompts))
            target = user
            return (target, msg)
        elif "prompt" in msg:
            tags = re.findall("#\((.*)\)#", msg)
            tags.extend(re.findall("#([^\(\s]*)", msg))
            if tags:
                i = 0
                msg = "None."
                while msg == "None." and i < len(tags):
                    msg = "%s: %s" % (user, self.promptbot.promptByTag(tags[i]))
                    i += 1
                if msg == "None.":
                    msg = "Not able to find any matching prompts."
            else:
                msg = "%s: %s" % (user, self.promptbot.randomPrompt())
            return (target, msg)
        #tag commands
        elif msg.startswith("tags"):
            msg = self.promptbot.listAllCategories()
            return (target, msg)
        elif "add tags" in msg:
            if msg.split()[0] == "":
            else:
                
        #source commands
        elif 
        else: 
            msg = "Eh? Try asking me for a prompt."
            return (channel, msg)

class BotFactory(protocol.ClientFactory):
    def __init__(self, channel, filename):
        self.channel = channel
        self.file = filename

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
    f = BotFactory(sys.argv[1], sys.argv[2])
    reactor.connectTCP("irc.cat.pdx.edu", 6667, f)
    reactor.run()
