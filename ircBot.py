#!/usr/bin/python2.7
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from random import shuffle
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
                target, msg = self.commands(msg, user, channel)
                self.msg(target, msg)

    def commands(self, msg, user, target):
        #tag commands
        if msg.startswith("tags?"):
            return (target, self.promptbot.getTags()) 
        elif msg.startswith("tags"):
            msg = self.promptbot.listAllCategories()
            return (target, msg)
        elif msg.startswith("add tag"):
            tags = re.findall("#\((.+)\)", msg)
            tags.extend(re.findall("#([^\(\s]+)", msg))
            if tags:
                self.promptbot.addTags(tags)
                return (target, "Tags added.")
            else:
                return (target, "No tags found. Try 'add tag(s) #tag or #(tag)'.")
        #source commands
        elif msg.startswith("source?"):
            return (target, self.promptbot.getSource()) 
        elif msg.startswith("add source"):
            source = re.findall("@\((.+)\)", msg)
            if source:
                self.promptbot.addSource(source)
                return (target, "Source added.")
            else:
                return (target, "No source found. Try 'add source @(source)'.")        
	#prompt commands
        if msg.startswith("add prompt"):
            msg = re.sub("add prompt\W( )?", '', msg)
            #add rest of msg to list of prompts
            self.promptbot.addPrompt(msg)
            msg = "Prompt added."
            return (target, msg) 
        elif msg.startswith("last"):
            msg = self.promptbot.last()
            return (target, msg)
        elif msg.startswith("backup prompts"):
            self.promptbot.backup(open(self.factory.file, "w"))
            msg = "%d prompts backed up." % (len(self.promptbot.prompts))
            target = user
            return (target, msg)
        index = re.findall('[0-9]+', msg)
        if index:
            msg = "%s: %s" % (user, self.promptbot.promptByIndex(int(index[0])))
            return (target, msg)
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
            return (target, msg)
        elif "prompt" in msg:
            msg = "%s: %s" % (user, self.promptbot.randomPrompt())
            return (target, msg)
        elif msg.startswith("index?"):
            return (target, self.promptbot.getIndex()) 
        else: 
            msg = "Eh? Try asking me for a prompt."
            return (target, msg)

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
