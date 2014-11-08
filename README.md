Please note that the code in this repository is quite a bit out of date. Stayed tuned for a new release, coming soon.

##Promptbot
=========

An irc bot for writers.

###Introduction

Someday, there will be some manner of introductory paragraph here. Today is not that day, however.

Promptbot is currently active in [#WritingPrompts on SnooNet](https://kiwiirc.com/client/irc.snoonet.org/writingprompts).

###Commands

To give Promptbot a command, type either "promptbot, &lsaquo;command&rsaquo;" or "!&lsaquo;command&rsaquo;"

####General commands

* **lists** &raquo; lists names of all lists currently in promptbot
* **random** &raquo; random entry from any list in promptbot

####List commands

The following commands apply to any list. To specify the list, replace &lsaquo;listname&rsaquo; with the name of the list. Usually the list you'll want is "prompt." See example usage for further clarification.

* **&lsaquo;listname&rsaquo;** &raquo; random entry from list
* **&lsaquo;listname&rsaquo; &lsaquo;keyword&rsaquo;** &raquo; entry from list that has been tagged with &lsaquo;keyword&rsaquo;
  * Multiple keywords can be given, and it will return an entry tagged with at least one of the keywords.
  * If a match is found, the response will begin with the keyword. If no match is found, it will return a random entry from the list.
* **&lsaquo;listname&rsaquo; &lsaquo;#&rsaquo;** &raquo; entry number # from list. Replace &lsaquo;#&rsaquo; with an actual number (integers only).
* **last &lsaquo;listname&rsaquo;** &raquo; repeat most recently given entry from list

####List commands example: prompt list

* **To get a random entry from prompt list** &raquo; prompt
* **To get a prompt about worldbuilding** &raquo; prompt worldbuilding
  * Note: there may or may not actually be any prompts tagged with worldbuilding.
* **To get prompt #10** &raquo; prompt 10
* **To repeat the most recent prompt** &raquo; last prompt

####Entry commands

* **add &lsaquo;listname&rsaquo;** &raquo; add new entry to list
  * Syntax: entry text #tag #(tag with spaces) @(source)
* **index?** &raquo; number of the most recently given entry
* **tags?** &raquo; tags of the most recently given entry
* **source?** &raquo; source of the most recently given entry
* **add tag &lsaquo;keyword&rsaquo;** &raquo; add a tag to the most recently given entry
* **add source @(&lsaquo;source text&rsaquo;)** &raquo; add a source to the most recently given entry
* **remove tag &lsaquo;keyword&rsaquo;** &raquo; remove a tag from the most recently given entry
* **remove source @(&lsaquo;source text&rsaquo;)** &raquo; remove a source from the most recently given entry

####Entry commands example: prompt

* **To add a prompt with text "Describe the entirety of a single characters life. 20 word limit." tagged "Flash Fiction" and "FF," and sourced to RyanKinder and www.amzn.com/B00JOVSYC2** &raquo; add prompt Describe the entirety of a single characters life. 20 word limit. #(Flash Fiction) #FF @(RyanKinder) @(www.amzn.com/B00JOVSYC2)

####Sprint commands

Sprints are informal competitions against other writers in the chatroom to write as much as you can within a certain period of time. Typically, sprints last 15 to 30 minutes. You are not required to share whatever you write during the sprint, though you are free to do so! Word counts are self-reported, but since there are no prizes for wordsprints, lying or making up ridiculous numbers would really only be cheating yourself (and annoying others).

* **sprint &lsaquo;delay #&rsaquo; &lsaquo;duration #&rsaquo;** &raquo; start a &lsaquo;duration #&rsaquo; minute-long wordsprint in &lsaquo;delay #&rsaquo; minutes
  * Promptbot will give 1-minute warnings before the start and end of the sprint.
  * Winners are announced 1 &rsaquo; &lsaquo;duration #&rsaquo;/5 &lsaquo; 10 minutes after the sprint ends.
* **join &lsaquo;#&rsaquo;** &raquo; join a wordsprint with a starting count of &lsaquo;#&rsaquo; words
  * You don't need to use join to join a wordsprint, but otherwise promptbot will assume your starting wordcount is 0.
  * This command can be used at any time during the sprint to change your starting wordcount.
* **wordcount &lsaquo;#&rsaquo;** &raquo; update your wordcount to &lsaquo;#&rsaquo;
  * **wc &lsaquo;#&rsaquo;** performs the same command.
  * Before the sprint begins, this will set your starting count. Once the sprint starts, it will set your current wordcount.
  * Promptbot will tell you the number of words you've written since your last update, and the total words written so far in the sprint.
* **wordcount** 	 &raquo; check the total number of words you have written so far for the current sprint
  * **wc** performs the same command.
* **wordcount &lsaquo;username&rsaquo;** &raquo; check &lsaquo;username&rsaquo;'s wordcount for the current sprint
  * **wc &lsaquo;username&rsaquo;** performs the same command.
* **cancel** &raquo; cancel a wordsprint
  * Only channel ops and the person who started the sprint can cancel it.

####Miscellaneous

* **smite &lsaquo;user&rsaquo;** &raquo; this command does not exist, and probably never will if socialdisorder keeps bugging me about it ;)
