"""
 _                  _     
| |                | |    
| |__   _ __   ___ | |__  
| '_ \ | '_ \ / __|| '_ \ 
| | | || | | |\__ \| | | |
|_| |_||_| |_||___/|_| |_|
hacker news shell - version 2.1.2

hnsh lets you browse and read Hacker News[1] from the shell.

[1] http://news.ycombinator.com

Author: Scott Jackson (http://scottjackson.org/)
Contributor for the updating code: Tom Wanielista (http://www.dsm.fordham.edu/~wanielis/)
Special thanks to Ryan McGreal (http://github.com/quandyfactory) for the
code that makes hnsh work from behind a proxy.

======
hnsh is released under the GPL.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License (http://www.gnu.org/licenses/) for more details.
======
"""
import zipfile
import json
import urllib2
import urllib
import webbrowser
import sys
from BeautifulSoup import BeautifulSoup
import os, shutil
import time

from hnapi import *


class HTMLParser(HackerNewsAPI):
	"""
	The class for slicing and dicing the HTML and turning it into NewsStory objects.
	"""
	
	def getSource(self, url):
		"""
		Gets the HTML source code from Hacker News.
		"""
		try:
			f = urllib2.urlopen(url)
			source = f.read()
			f.close()
			return source
		except urllib2.URLError:
			proxyAddress = raw_input("Uh oh. Something went wrong, and it could be because you're using a proxy. If you're not using a proxy, enter 'n' (without the quotes). If you're using a proxy, enter its IP Address: ")
			if proxyAddress != "n":
				proxies = { 'http': proxyAddress }
				proxy_support = urllib2.ProxyHandler(proxies)
				opener = urllib2.build_opener(proxy_support)
				urllib2.install_opener(opener)
				f = urllib2.urlopen(url)
				source = f.read()
				f.close()
				return source
			else:
				print ""
				print ""
				print("hnsh failed to stories from Hacker News. One of two things could be wrong here:")
				print("    - Something might be up with your internet connection, or")
				print("    - HN could be down..")
				input = raw_input("Press Return to quit hnsh. When you think the problem has been solved, start it again.")
				self.quit = 1

		
		
	def getStories(self, source, alreadyReadList):
		"""
		Looks at source, makes NewsStory objects from it, returns the stories.
		"""
		
		stories = HackerNewsAPI.getStories(self, source)
		
		
		for i in range(0, HackerNewsAPI.numberOfStoriesOnFrontPage):
			story = stories[i]
			
			newStory = NewsStory()
			newStory.id = story.id
			newStory.number = story.number
			newStory.title = story.title
			newStory.domain = story.domain
			newStory.URL = story.URL
			newStory.score = story.score
			newStory.submitter = story.submitter
			newStory.commentCount = story.commentCount
			newStory.commentsURL = story.commentsURL
			if story.URL in alreadyReadList:
				newStory.hasBeenRead = 1
			stories[i] = newStory
				
		return stories
		
	def getLatestStories(self, newest, alreadyReadList):
		"""
		Gets the latest set of stories from Hacker News.
		"""
		url = "http://news.ycombinator.com"
		if newest == "newest":
			url += "/newest"
		source = self.getSource(url)
		stories  = self.getStories(source, alreadyReadList)
		return stories
		
		

class NewsStory(HackerNewsStory):
	"""
	A class representing a story on Hacker News.
	"""
	
	hasBeenRead = 0	# Whether or not you have read the story yet.
	
	def outputStory(self, showDomain, showFullTitle, shouldCollapse):
		"""
		Outputs the story in a nice format.
		
		Params:
			- showDomain: whether to show the domain of the story or the URL.
			- showFullTitle: whether to show the full title of the story make
							 the title fit into an 80-char terminal window
							 if necessary.
			- shouldCollapse: whether to collapse stories that have already
							  been read.
		"""

		# Always need to show a title.
		title = self.title
		if (not showFullTitle):
			# Shorten title if longer than terminal width.
			if len(self.title) >= 75: # 5 chars taken up by "{number} > "
				title = self.title[:72] + "..."
						
		if shouldCollapse:
			
			# Collapse the story if it has been read.
			
			if self.hasBeenRead:
				title = "[already read]"
				
			if self.number < 10:
				print str(self.number) + "  > " + title
			else:
				print str(self.number) + " > " + title
			
			if not self.hasBeenRead:
				whitespace = "     "
				if (showDomain):
					print whitespace + "(" + self.domain + ")"
				else:
					print whitespace + self.URL
				sIfNecessary = ""
				if self.commentCount > 1 or self.commentCount == 0:
					sIfNecessary = "s"
				
				sIfNecessary2 = ""
				if self.score > 1:
					sIfNecessary2 = "s"	
				
				print whitespace + str(self.score) + " point" + sIfNecessary2 + " / submitted by: " + self.submitter + " / " + str(self.commentCount) + " comment" + sIfNecessary
						
		else:
			# Totally normal story. Print as normal.
			if self.number < 10:
				print str(self.number) + "  > " + title
			else:
				print str(self.number) + " > " + title
			whitespace = "     "
			if (showDomain):
				print whitespace + "(" + self.domain + ")"
			else:
				print whitespace + self.URL
			sIfNecessary = ""
			if self.commentCount > 1 or self.commentCount == 0:
				sIfNecessary = "s"
				
			sIfNecessary2 = ""
			if self.score > 1:
				sIfNecessary2 = "s"	
			print whitespace + str(self.score) + " point" + sIfNecessary2 + " / submitted by: " + self.submitter + " / " + str(self.commentCount) + " comment" + sIfNecessary
			
		print ""


	
class HackerNewsShell:
	"""
	The main class for the application.
	"""
	STORIES_PER_SCREEN = 5	#
	quit = 0	# Used in main loop.
	firstStoryToShow = 0
	lastStoryToShow = STORIES_PER_SCREEN
	h = HTMLParser()	# For getting the stories.
	stories = []
	oneToThirty = []	# List: "1", "2", ..., "30".
	oneToThirtyComments = [] # List: "c1", "c2", ..., "c30".
	oneToThirtyPlusComments = [] # List: "1+", "2+", ..., "30+"
	oneToThirtySubmitters = []	# List: "s1", "s2", ..., "s30"
	lastRefreshed = time.localtime()
	karmaChange = 0	# Whether or not the user's karma has changed since the last refresh.
	
	# User Preferences #
	userPrefsFileName = "hnsh_prefs.txt"
	showDomains = 1
	showFullTitles = 0
	collapseOldStories = 0
	alreadyReadList = []
	newestOrTop = "top"	# Whether or not to show the newest or the top stories.
	hnUserName = ""
	karma = -1000
	
	def outputStory(self, story, showDomain, showFullTitle, shouldCollapse):
		"""
		Outputs the story in a nice format.
		
		Params:
			- showDomain: whether to show the domain of the story or the URL.
			- showFullTitle: whether to show the full title of the story make
							 the title fit into an 80-char terminal window
							 if necessary.
			- shouldCollapse: whether to collapse stories that have already
							  been read.
		"""

		# Always need to show a title.
		title = story.title
		if (not showFullTitle):
			# Shorten title if longer than terminal width.
			if len(story.title) >= 75: # 5 chars taken up by "{number} > "
				title = story.title[:72] + "..."
						
		if shouldCollapse:
			
			# Collapse the story if it has been read.
			
			if story.hasBeenRead:
				title = "[already read]"
				
			if story.number < 10:
				print str(story.number) + "  > " + title
			else:
				print str(story.number) + " > " + title
			
			if not story.hasBeenRead:
				whitespace = "     "
				if (showDomain):
					print whitespace + "(" + story.domain + ")"
				else:
					print whitespace + story.URL
				sIfNecessary = ""
				if story.commentCount > 1 or story.commentCount == 0:
					sIfNecessary = "s"
				
				sIfNecessary2 = ""
				if story.score > 1:
					sIfNecessary2 = "s"	
				
				print whitespace + str(story.score) + " point" + sIfNecessary2 + " / submitted by: " + story.submitter + " / " + str(story.commentCount) + " comment" + sIfNecessary
						
		else:
			# Totally normal story. Print as normal.
			if story.number < 10:
				print str(story.number) + "  > " + title
			else:
				print str(story.number) + " > " + title
			whitespace = "     "
			if (showDomain):
				print whitespace + "(" + story.domain + ")"
			else:
				print whitespace + story.URL
			sIfNecessary = ""
			if story.commentCount > 1 or story.commentCount == 0:
				sIfNecessary = "s"
				
			sIfNecessary2 = ""
			if story.score > 1:
				sIfNecessary2 = "s"	
			print whitespace + str(story.score) + " point" + sIfNecessary2 + " / submitted by: " + story.submitter + " / " + str(story.commentCount) + " comment" + sIfNecessary
			
		print ""

	
	def getLastRefreshedTime(self):
		"""
		Returns the last-refreshed time in a human-readable format.
		"""
		months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
		month = months[self.lastRefreshed.tm_mon - 1][:3]
		
		hours = str(self.lastRefreshed.tm_hour)
		if self.lastRefreshed.tm_hour < 10:
			hours = "0" + hours
		
		minutes = str(self.lastRefreshed.tm_min)
		if self.lastRefreshed.tm_min < 10:
			minutes = "0" + minutes
			
		time = hours + ":" + minutes + ", " + month + " " + str(self.lastRefreshed.tm_mday)
		return time
	
	def printHeader(self):
		"""
		Prints the top line of the screen before the stories themselves.
		"""
		karmaDetails = ""
		if self.hnUserName != "":
			karmaDetails = " | " + self.hnUserName + " (" + str(self.karma) + ")"
	
		for i in range(0,60):
			print ""
		print "Showing " + self.newestOrTop + " stories. | Last updated " + self.getLastRefreshedTime() + karmaDetails
		print ""
		
		
	def printStories(self):
		"""
		Outputs all of the stories to the screen.
		"""
		self.printHeader()
		for i in range(self.firstStoryToShow, self.lastStoryToShow):
			self.outputStory(self.stories[i], self.showDomains, self.showFullTitles, self.collapseOldStories)
		
		if self.karmaChange:
			print self.hnUserName + "'s karma has changed since the last refresh."
		
	
	def __init__(self):
		"""
		Constructor for main class.
		"""
		
		print "Getting latest stories from Hacker News..."
		#try:
		self.stories = self.h.getLatestStories(self.newestOrTop, self.alreadyReadList)
		
		for i in range(1,self.h.numberOfStoriesOnFrontPage):
			self.oneToThirty.append(str(i))
			self.oneToThirtyComments.append("c" + str(i))
			self.oneToThirtyPlusComments.append(str(i) + "+")
			self.oneToThirtySubmitters.append("s" + str(i))
			
		self.setPreferencesAtStartup()

		if self.hnUserName != "":
			print "Getting " + self.hnUserName + "'s karma from HN..."
			user = HackerNewsUser(self.hnUserName)
			self.karma = user.karma

		self.printStories()
		
		#except:
		#	print "error"
		#	self.quit = 1

		self.loop()
		
		
	def loop(self):
		"""
		Main loop. Gets user input and takes actions based on it.
		"""
		while (self.quit == 0):
			userInput = raw_input("> ")
			self.processCommand(userInput)


	def processCommand(self, userInput):
		"""
		Does things based on an input string representing user input.
		The user input could come from the prompt from within hnsh,
		or it could come from the hnsh_prefs.txt file.
		"""
		if userInput == "q":
			self.quit = 1
		elif userInput == "h" or userInput == "help":
			self.showHelp()
			self.printStories()
			
		elif userInput == "j":
			if self.firstStoryToShow == 25:
				input = raw_input("Already at the bottom of the list. Press Return to continue.")
				self.printStories()
			else:
				self.firstStoryToShow += self.STORIES_PER_SCREEN
				self.lastStoryToShow += self.STORIES_PER_SCREEN
				self.printStories()
			
		elif userInput == "k":
			if self.firstStoryToShow == 0:
				input = raw_input("Already at the top of the list. Press Return to continue.")
				self.printStories()
			else:
				self.firstStoryToShow -= self.STORIES_PER_SCREEN
				self.lastStoryToShow -= self.STORIES_PER_SCREEN
				self.printStories()
			
		elif userInput == "r":
			print "Getting latest stories from Hacker News..."
			self.refreshStories()
			self.printStories()
			
		elif userInput == "t":
			self.firstStoryToShow = 0
			self.lastStoryToShow = self.STORIES_PER_SCREEN
			self.printStories()
			
		elif userInput == "p":
			self.printStories()
			
		elif userInput == "d" or userInput == "w" or userInput == "l" or userInput == "o" or userInput == "c" or userInput == "e":
			self.setPreference(userInput)
			self.printStories()
			
		elif userInput == "u":
			self.checkForUpdates()

		elif userInput == "new" or userInput == "newest":
			self.showNewestStories()
			
		elif userInput == "top":
			self.showTopStories()
			
		elif userInput[:5] == "user ":
			self.setPreference("/" + userInput[5:])
			self.refreshStories()
			self.printStories()
			
		elif userInput == "prefs":
			self.showPrefs()
			self.printStories()
			
		elif userInput in self.oneToThirty:
			i = int(userInput) - 1 # take one since indexing of self.stories starts at 0.
			if self.stories[i].URL not in self.alreadyReadList:
				self.alreadyReadList.append(self.stories[i].URL)
			self.stories[i].hasBeenRead = 1
			webbrowser.open_new_tab(self.stories[i].URL)
			self.printStories()
			
		elif userInput in self.oneToThirtyComments:
			i = int(userInput[1:]) - 1
			webbrowser.open_new_tab(self.stories[i].commentsURL)
			self.printStories()
			
		elif userInput in self.oneToThirtyPlusComments:
			plusIndex = userInput.find("+")
			i = int(userInput[:plusIndex]) - 1
			if self.stories[i].URL not in self.alreadyReadList:
				self.alreadyReadList.append(self.stories[i].URL)
			self.stories[i].hasBeenRead = 1
			webbrowser.open_new_tab(self.stories[i].commentsURL)
			webbrowser.open_new_tab(self.stories[i].URL)
			# Shows story first, but tab order goes "comments, story"
			self.printStories()
			
		elif userInput in self.oneToThirtySubmitters:
			i = int(userInput[1:]) - 1
			webbrowser.open_new_tab("http://news.ycombinator.com/user?id=" + self.stories[i].submitter)
			self.printStories()
			
			
		else:
			input = raw_input("Invalid command (" + userInput + "). For help, press h and then Return at the prompt. Press Return to continue.")
			self.printStories()
			
	def refreshStories(self):
		"""
		Gets the latest stories from HN, updates the lastRefreshed time and your HN karma (if you have a username)
		"""
		self.stories = self.h.getLatestStories(self.newestOrTop, self.alreadyReadList)
		self.lastRefreshed = time.localtime()
		if self.hnUserName != "":
			print "Getting " + self.hnUserName + "'s karma from HN..."
			user = HackerNewsUser(self.hnUserName)
			if self.karma != user.karma and self.karma != -1000:
				karmaChange = 1
			self.karma = user.karma

	def showNewestStories(self):
		"""
		Sets the stories to show to be the newest stories submitted to HN.
		"""
		if self.newestOrTop == "top":
			self.newestOrTop = "newest"
			print "Getting newest stories submitted to HN..."
			self.refreshStories()
		else:
			input = raw_input("Already showing newest stories. Press Return to continue.")
		self.printStories()

	def showTopStories(self):
		"""
		Sets the stories to show to be the top stories currently on HN.
		"""
		if self.newestOrTop == "newest":
			self.newestOrTop = "top"
			print "Getting the latest stories from HN..."
			self.refreshStories()
		else:
			input = raw_input("Already showing top stories. Press Return to continue.")
		self.printStories()

	def setPreferencesAtStartup(self):
		"""
		Tries to open a file called hnsh_prefs.txt and sets preferences
		based on the contents of the file.
		"""
		if os.path.isfile(self.userPrefsFileName):
			prefs = open(self.userPrefsFileName, 'r')
			prefsLine = prefs.readline()
			prefs.close()
			
			for i in range(0,len(prefsLine)):
				c = prefsLine[i]
				if c is not "/":
					self.setPreference(c)
				else:
					self.setPreference(prefsLine[i:])
					break
			

	def writePreferenceToFile(self, newPreference):
		"""
		Tries to write a new preference to a file.
		
		If the file doesn't exist, the new preference will only
		be kept for as long as the program is open.
		
		Returns whether or not the file-write went well.
		"""
		if (os.path.isfile(self.userPrefsFileName)):
			prefs = open(self.userPrefsFileName, 'r')
			prefsFromFile = prefs.readline()
			prefs.close()

			# Get rid of duplicates.
			prefsList = list(prefsFromFile)
			uniquePrefs = []
			for p in prefsList:
				if p not in uniquePrefs and p is not newPreference:	# see [1] below.
					if p == "/":
						break
					uniquePrefs.append(p)
					
			# [1]
			# "is not newPreference" ensures that the new preference
			# is always added to the end of the preferences list when
			# the list is written back to the file. This way, when
			# the application is opened up next time, the most recent
			# preference will be the last one to be set (your most recent
			# decision should have the final word).

			# Stitch the unique prefs back together as a string to be written to the file.
			prefsLine = ""
			for p in uniquePrefs:
				prefsLine += p

			username = ""
			if self.hnUserName != "" and newPreference[0] != "/":
				username = "/" + self.hnUserName

			prefs = open(self.userPrefsFileName, 'w')
			prefs.write(prefsLine + newPreference + username)
			prefs.close()
			return 1
		return 0

	def setPreference(self, newPreference):
		"""
		Sets a preference within the application and then tries to write
		it to a file.
		
		If the preference file doesn't exist, the preference is only kept
		until the program is closed.
		"""
		if newPreference == "d":
			self.showDomains = 1
		elif newPreference == "w":
			self.showDomains = 0
		elif newPreference == "l":
			self.showFullTitles = 1
		elif newPreference == "o":
			self.showFullTitles = 0
		elif newPreference == "c":
			self.collapseOldStories = 1
		elif newPreference == "e":
			self.collapseOldStories = 0
		elif newPreference[0] == "/":
			self.hnUserName = newPreference[1:]

		writeWentWell = self.writePreferenceToFile(newPreference)
		if not writeWentWell:
			input = raw_input("hnsh_prefs.txt not found. Preferences changed will only be kept until this program is closed. Press Return to continue. ")


	def showHelp(self):
		"""
		Prints a help screen.
		"""
		for i in range(0,20):
			print ""
		print " _                  _     "
		print "| |                | |    "
		print "| |__   _ __   ___ | |__  "
		print "| '_ \ | '_ \ / __|| '_ \ "
		print "| | | || | | |\__ \| | | |"
		print "|_| |_||_| |_||___/|_| |_|"
		print "A program by Scott Jackson"
		print ""
		print "To enter a command, type the key and press Return."
		print "NB: parentheses indicate which of two options is the default."
		print ""
		print "Basic Commands:"
		print "j / k -- show lower-ranked / higher-ranked stories."
		print "r -- get the latest stories from Hacker News."
		print "q -- quit."
		print "# -- open story number # in your web browser."
		print "c# -- open comments for story number # in your web browser."
		print "#+ -- open up story number # AND its comments in your web browser."
		print "top / new -- switch between showing the top and newest stories on HN. (top)"
		print "c / e -- collapse stories you've already read / don't collapse them. (e)"
		print "u -- update hnsh to the latest version."
		print "=========================="
		print "For more commands, see the man.txt file."
		input = raw_input("Press Return to go back to the Hacker News stories.")
		
		
	def showPrefs(self):
		"""
		Prints out the user's preferences.
		"""
		for i in range(0,20):
			print ""
		
		print "User Preferences"
		print "================"
		print ""
		
		if self.newestOrTop == "top":
			print "Currently viewing top stories on HN."
		else:
			print "Currently viewing newest stories on HN."
		print "--------------------------------------------------------------------------------"
			
		if self.hnUserName != "":
			print "HN username = " + self.hnUserName + ". Karma = " + str(self.karma)
			print "--------------------------------------------------------------------------------"
			
		if self.showDomains:
			print "d -- show domains of stories."
		else:
			print "w -- show webpage URLs of stories."
		print "--------------------------------------------------------------------------------"
		
		if self.showFullTitles:
			print "l -- always show full titles of stories."
		else:
			print "o -- truncate titles of stories to fit an 80-character terminal window."
		print "--------------------------------------------------------------------------------"
		
		if self.collapseOldStories:
			print "c -- collapse stories after reading."
		else:
			print "e -- don't collapse stories after reading."
		print "--------------------------------------------------------------------------------"
			
		print ""
		input = raw_input("Press Return to go back to the Hacker News stories.")


	def checkForUpdates(self):
		"""
		Downloads the latest version of the program.
		
		Big thanks to Tom Wanielista for contributing the meat of this awesome update code.
		"""
		# Get a definite yes or no answer from the user.
		input = ""
		while  input != "y" and input != "yes" and input != "n" and input != "no":
			print("  Download the latest version of hnsh? (y/n)")
			input = raw_input("> ")
		
		if input == "y" or input == "yes":
			print "\n  Downloading the latest version from GitHub repository..."
			serverFile = urllib.urlretrieve("http://github.com/scottjacksonx/hnsh/zipball/master", "hnsh_latest.zip", quickProgressBar)
			slash = "/"
			if sys.platform == "win32":
				slash = "\\"
			if os.path.isfile("hnsh_latest.zip"):
				print ""
				print "  The latest version of hnsh has been downloaded as:"
				print "  " + sys.path[0] + slash + "hnsh_latest.zip."
				print ""
				print "  Would you like to apply the update? (y/n)"
				if raw_input("> ") == ("y" or "yes" or "Y"):
					print "\n> Attempting to apply update ..."
					updateZip = zipfile.ZipFile(sys.path[0] + slash + "hnsh_latest.zip", "r")
					for name in updateZip.namelist():
						if (updateZip.getinfo(name).file_size > 0):
							updateZip.extract(name)
							shutil.copy(sys.path[0] + slash + name, sys.path[0] + slash + (name.rpartition("/")[2]))
							print " ", name, updateZip.getinfo(name).file_size, "bytes"
							os.remove(sys.path[0] + slash + name)
					os.remove(sys.path[0] + slash + "hnsh_latest.zip")
					os.rmdir(sys.path[0] + slash + name.rpartition("/")[0])
				else:
					print "\n> Download finished! Press enter to exit so you can manually update the files."
			else:
				print "Error trying to update automatically. To update manually, go to http://github.com/scottjacksonx/hnsh and download the latest version of hnsh."
			input = raw_input("\n> Done! Now press enter and re-run this program to use the new version.")
			self.quit = 1
		else:
			input = raw_input("Press Return to go back to stories.")
			self.printStories()
			

def quickProgressBar(blocksSoFar, blockSizeInBytes, totalFileSize):
	bytesLeft = totalFileSize - (blocksSoFar * blockSizeInBytes)
	if bytesLeft > 0:
		print " ", bytesLeft, " bytes left."	

# Just instantiate a HackerNewsShell and let 'er rip!
hnsh = HackerNewsShell()