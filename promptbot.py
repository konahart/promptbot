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
        #Keeps track of the last list accessed per channel
        self.lastLists = defaultdict(lambda: "prompt")
        #Keeps track of the last element accessed per list per channel by
        #using the channel name as a key.
        self.indices = defaultdict(lambda: defaultdict(int))
        self.response = ["Eh? Try asking me for a prompt.", "Whatcha tryin'a do, bub?", "You might need to see '%s, help'" % self.nickname]
        self.promptbot = listbot.ListKeeper()
        self.topics = {}
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
    
     
    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if msg.startswith(self.nickname) or msg.startswith("!") or channel == self.nickname:
            #promptbot, command, e.g., promptbot, prompt
            if msg.startswith(self.nickname):  
                pattern = "^" + self.nickname + "\W( )?"
            #!command, e.g., !prompt
            elif msg.startswith("!"): 
                pattern = "^!"
            #pm
            if channel == self.nickname:
                channel = user
                pattern = ""
            msg = re.sub(pattern, '', msg)
            if msg == "":
                msg = "Yes, %s?" % user
                self.msg(channel, msg)
            else:
                self.commandParser(msg)

    def respond(self, target, user, msg, prepend=""):
        if msg.startswith("/me"):
            action = re.sub("/me(\s)*","",msg)
            self.describe(target, action)
        else:
            msg = "%s: %s%s" % (user, prepend, msg)
            self.msg(target, msg)

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
    parser.add_argument("--logging", action="store_true")
    parser.add_argument("--op", action="append")
    parser.add_argument("--pre", "--prefix", action="append")
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
    lists = {}
    for l in settings.list:
        if len(l) == 1:
            lists[l[0]] = None
        elif len(l) > 1:
            lists[l[0]] = l[1:]
    f = BotFactory(settings.nick, settings.password, settings.channels, lists, settings.output)
    if settings.ssl:
        reactor.connectSSL(settings.server, settings.port, f, ssl.ClientContextFactory())
    else:
        reactor.connectTCP(settings.server, settings.port, f)
    reactor.run()

if __name__ == '__main__':
    main()
