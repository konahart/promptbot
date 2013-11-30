ircPromptBot
=========

An irc bot that gives writing prompts on command.

Usage: ircPromptBot host channel <input prompt file> [prompt output file]"

Defaults:

nickname = "promptbot"

lists = prompt, advice, praise

Common Commands:

list

	gives a random entry from list
	
tag

	gives an entry from the default list (prompt) with that tag
	
000

	gives the entry from the default list (prompt) with that index (000 being any integer)
	
list tag

	gives an entry that has that tag
	
list tag1 ... tagn

	gives an entry with one of the given tags
	
list 000

	gives the list entry with that index (000 being any integer)
	
add list text #tag #(tag with spaces) @source @(source with space)

	adds prompt to list of prompts (tags and sources being optional)
	
last

	repeats the last entry given (from whatever list was last accessed)
	
last list

	repeats last entry given from specific list
	
tags?

	lists the tags from the last entry given
	
source?

	lists the source from the last entry given
	
index?

	gives the index of the last entry given
	
add tag	#tag #(tag with spaces)

	adds given tags to the last entry given
	
add source @source @(source with space)

	adds sources to the last entry given
	
remove tag #tag1 ... #tagn

	removes these tags from the last entry given
	
remove source @source @(source with space)

	removes these sources from the last entry given
	
tags

	lists all tags in all lists
	
list tags

	lists all tags for that list
	
add list

	add a new list. The above commands can then be used on new list.
	
topic

	tries to set the topic
	
start topic

	will try to set the topic every night at midnight
	
stop topic

	(not yet implemented) will stop trying to set the topic every night at midnight
	
help

	shows interactive help menu
	
github

	links to https://github.com/konayashi/promptbot
	

Example Usage:

Kona: prompt

promptbot: Kona: A famous religious leader enters the afterlife. It 
            turns out their religion wasn't the right one.
            
Kona: tags?

promptbot: religion; death

Kona: source?

promptbot: reddit; r/WritingPrompts; http://redd.it/1pqtc1

Kona: index?

promptbot: Prompt #735

Kona: advice

promptbot: Kona: Enter contests. Submit to periodicals. Get yourself 
            out there. Cultivate an identity.
            
Kona: source?

promptbot: http://prompts-and-pointers.tumblr.com/post/44554951694; 
            http://prompts-and-pointers.tumblr.com
            
Kona: index?

promptbot: Advice #89

Kona: last

promptbot: Enter contests. Submit to periodicals. Get yourself out 
            there. Cultivate an identity.
            
Kona: last prompt

promptbot: A famous religious leader enters the afterlife. It turns out 

            their religion wasn't the right one.

Kona: add list task

promptbot: New task list added.

Kona: task tags

promptbot: Task has no tags.

Kona: add task Get a beer. #beer

promptbot: Task added.

Kona: task tags

promptbot: beer

Kona: tags

promptbot: advice: quote, advice, challenge, sci-fi, description

promptbot: task: beer

promptbot: prompt: worldbuilding, dialogue, death, plot, character, 

            horror, Get Inside Your Character's Head, religion, theme, 

            anthropomorphization

promptbot: praise:



More Commands:

load list file

	loads a local file of entries into a list. See prompts/ for example format.

backup list

	backs up list to output file (if given) or inputfile.pb

backup

	backs up all lists to outputfile.list (if given) or inputfile.pb.list

