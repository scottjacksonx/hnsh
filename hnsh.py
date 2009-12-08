"""
 _                  _     
| |                | |    
| |__   _ __   ___ | |__  
| '_ \ | '_ \ / __|| '_ \ 
| | | || | | |\__ \| | | |
|_| |_||_| |_||___/|_| |_|
hacker news shell - version 1.0.1

hnsh lets you browse and read Hacker News[1] from the shell.

[1] http://news.ycombinator.com

Author: Scott Jackson
Website: http://scottjackson.org/
"""

import urllib2
import urllib
import webbrowser
import sys
from BeautifulSoup import BeautifulSoup
import os


class HTMLParser:
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
		except URLError:
			proxyAddress = raw_input("Uh oh. Something went wrong, and it could be because you're using a proxy. If you're using a proxy, enter its IP Address:")
			proxies = { 'http': proxyAddress }
			proxy_support = urllib2.ProxyHandler(proxies)
			opener = urllib2.build_opener(proxy_support)
			urllib2.install_opener(opener)
			f = urllib2.urlopen(url)
			source = f.read()
			f.close()
			return source
		
	def getStoryNumber(self, source):
		"""
		Parses HTML and returns the number of a story.
		"""
		numberStart = source.find('>') + 1
		numberEnd = source.find('.')
		return source[numberStart:numberEnd]
		
	def getStoryURL(self, source):
		"""
		Gets the URL of a story.
		"""
		URLStart = source.find('href="') + 6
		URLEnd = source.find('">', URLStart)
		url = source[URLStart:URLEnd]
		# Check for "Ask HN" links.
		if url[0:4] == "item": # "Ask HN" links start with "item".
			url = "http://news.ycombinator.com/" + url
		
		# Change "&amp;" to "&"
		url = url.replace("&amp;", "&")
		
		# Remove 'rel="nofollow' from the end of links, since they were causing some bugs.
		if url[len(url)-13:] == "rel=\"nofollow":
			url = url[:len(url)-13]
			
		# Weird hack for URLs that end in '" '. Consider removing later if it causes any problems.
		if url[len(url)-2:] == "\" ":
			url = url[:len(url)-2]
		return url
	
	def getStoryDomain(self, source):
		"""
		Gets the domain of a story.
		"""
		domainStart = source.find('comhead">') + 10
		domainEnd = source.find('</span>')
		domain = source[domainStart:domainEnd]
		# Check for "Ask HN" links.
		if domain[0] == '=':
			domain = "(news.ycombinator.com)"
		return domain
		
	def getStoryTitle(self, source):
		"""
		Gets the title of a story.
		"""
		titleStart = source.find('>', source.find('>')+1) + 1
		titleEnd = source.find('</a>')
		title = source[titleStart:titleEnd]
		title = title.lstrip()	# Strip trailing whitespace characters.
		return title
		
	def getStoryScore(self, source):
		"""
		Get the score of a story.
		"""
		scoreStart = source.find('>', source.find('>')+1) + 1
		scoreEnd = source.find('</span>')
		return source[scoreStart:scoreEnd]
		
	def getSubmitter(self, source):
		"""
		Get the submitter of a story.
		"""
		submitterStart = source.find('user?id=') + 8
		submitterEnd = source.find('"', submitterStart)
		return source[submitterStart:submitterEnd]
		
	def getCommentCount(self, source):
		"""
		Get the comment count of a story.
		"""
		commentStart = source.find('item?id=') + 16
		commentEnd = source.find('</a>', commentStart)
		commentCount = source[commentStart:commentEnd]
		if commentCount == "discuss":
			return "0 comments"
		return commentCount
		
	def getCommentsURL(self, source):
		"""
		Get the comment URL of a story.
		"""
		urlStart = source.find('item?id=')
		urlEnd = source.find('"', urlStart)
		return "http://news.ycombinator.com/" + source[urlStart:urlEnd]
		
		
	def getStories(self, source, alreadyReadList):
		"""
		Looks at source, makes stories from it, returns the stories.
		"""
		
		# Create the empty stories.
		newsStories = []
		for i in range(0,30):
			story = NewsStory()
			newsStories.append(story)
		
		soup = BeautifulSoup(source)
		# Gives URLs, Domains and titles.
		story_details = soup.findAll("td", {"class" : "title"}) 
		# Gives score, submitter, comment count and comment URL.
		story_details_2 = soup.findAll("td", {"class" : "subtext"})

		# Get story numbers.
		storyNumbers = []
		for i in range(0,len(story_details) - 1, 2):
			story = str(story_details[i]) # otherwise, story_details[i] is a BeautifulSoup-defined object.
			storyNumber = self.getStoryNumber(story)
			storyNumbers.append(storyNumber)
			
		storyURLs = []
		storyDomains = []
		storyTitles = []
		storyScores = []
		storySubmitters = []
		storyCommentCounts = []
		storyCommentURLs = []

		for i in range(1, len(story_details), 2):
			story = str(story_details[i])
			storyURLs.append(self.getStoryURL(story))
			storyDomains.append(self.getStoryDomain(story))
			storyTitles.append(self.getStoryTitle(story))
			
		for i in range(0, len(story_details_2)):
			story = str(story_details_2[i])
			storyScores.append(self.getStoryScore(story))
			storySubmitters.append(self.getSubmitter(story))
			storyCommentCounts.append(self.getCommentCount(story))
			storyCommentURLs.append(self.getCommentsURL(story))
			
		
		# Associate the values with our newsStories.		
		for i in range(0, 30):
			newsStories[i].number = storyNumbers[i]
			newsStories[i].URL = storyURLs[i]
			newsStories[i].domain = storyDomains[i]
			newsStories[i].title = storyTitles[i]
			newsStories[i].score = storyScores[i]
			newsStories[i].submitter = storySubmitters[i]
			newsStories[i].commentCount = storyCommentCounts[i]
			newsStories[i].commentsURL = storyCommentURLs[i]
			if newsStories[i].URL in alreadyReadList:
				newsStories[i].hasBeenRead = 1
			
		return newsStories
		
	def getLatestStories(self, alreadyReadList):
		"""
		Gets the latest set of stories from Hacker News.
		"""
		source = self.getSource("http://news.ycombinator.com")
		stories  = self.getStories(source, alreadyReadList)
		return stories
		
		

class NewsStory:
	"""
	A class representing a story on Hacker News.
	"""
	
	number = ""	# What number story it is on HN.
	title = ""	# The title of the story.
	domain = ""	# The website the story is on.
	URL = ""	# The URL of the story.
	score = ""	# Current score of the story.
	submitter = ""	# The person that submitted the story.
	commentCount = ""	# How many comments the story has.
	commentsURL = ""	# The HN link for commenting (and upmodding).
	hasBeenRead = 0	# Whether or not you have read the story yet.
	
	def output(self, showDomain, showFullTitle, shouldCollapse):
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
				
			if int(self.number) < 10:
				print str(self.number) + "  > " + title
			else:
				print str(self.number) + " > " + title
			
			if not self.hasBeenRead:
				whitespace = "     "
				if (showDomain):
					print whitespace + self.domain
				else:
					print whitespace + self.URL
				print whitespace + self.score + " / submitted by: " + self.submitter + " / " + self.commentCount
						
		else:
			# Totally normal story. Print as normal.
			if int(self.number) < 10:
				print str(self.number) + "  > " + title
			else:
				print str(self.number) + " > " + title
			whitespace = "     "
			if (showDomain):
				print whitespace + self.domain
			else:
				print whitespace + self.URL

			print whitespace + self.score + " / submitted by: " + self.submitter + " / " + self.commentCount
			
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
	
	# User Preferences #
	userPrefsFileName = "hnsh_prefs.txt"
	showDomains = 1
	showFullTitles = 0
	collapseOldStories = 0
	alreadyReadList = []

	
	def printStories(self):
		"""
		Outputs all of the stories to the screen.
		"""
		for i in range(0,60):
			print ""
		for i in range(self.firstStoryToShow, self.lastStoryToShow):
			self.stories[i].output(self.showDomains, self.showFullTitles, self.collapseOldStories)
		
	
	def __init__(self):
		"""
		Constructor for main class.
		"""
		
		for i in range(1,31):
			self.oneToThirty.append(str(i))
			self.oneToThirtyComments.append("c" + str(i))
			self.oneToThirtyPlusComments.append(str(i) + "+")
		
		self.stories = self.h.getLatestStories(self.alreadyReadList)
		
		self.setPreferencesAtStartup()
		
		self.printStories()
		
		self.loop()
		
		
	def loop(self):
		"""
		Main loop. Gets user input and takes actions based on it.
		"""
		while (self.quit == 0):
			userInput = raw_input(">")
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
			self.stories = self.h.getLatestStories(self.alreadyReadList)
			self.printStories()
			
		elif userInput == "t":
			self.firstStoryToShow = 0
			self.lastStoryToShow = self.STORIES_PER_SCREEN
			self.printStories()
			
		elif userInput == "s":
			self.printStories()
			
		elif userInput == "d" or userInput == "w" or userInput == "l" or userInput == "o" or userInput == "c" or userInput == "e":
			self.setPreference(userInput)
			self.printStories()
			
		elif userInput == "u":
			self.checkForUpdates()
			
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
			
			
		else:
			input = raw_input("Invalid command. For help, press h and then Return at the prompt. Press Return to continue.")
			self.printStories()
			

	def setPreferencesAtStartup(self):
		"""
		Tries to open a file called hnsh_prefs.txt and sets preferences
		based on the contents of the file.
		"""
		if os.path.isfile(self.userPrefsFileName):
			prefs = open(self.userPrefsFileName, 'r')
			prefsLine = prefs.readline()
			
			for i in range(0,len(prefsLine)):
				c = prefsLine[i]
				self.processCommand(c)
			prefs.close()

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

			prefs = open(self.userPrefsFileName, 'w')
			prefs.write(prefsLine + newPreference)
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

		writeWentWell = self.writePreferenceToFile(newPreference)
		if not writeWentWell:
			input = raw_input("hnsh_prefs.txt not found. Preferences changed will only be kept until this program is closed. Press Return to continue.")


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
		print "======== COMMANDS ========"
		print "To enter a command, type the key and press return."
		print "NB: parentheses indicate which of two options is the default."
		print ""
		print "j/k -- show lower-ranked / higher-ranked stories."
		print "t -- go to the top of the list."
		#print "s -- clear screen and show current stories."
		print "r -- get the latest stories from Hacker News."
		print "q -- quit."
		print "h -- help."
		print "# -- open story number # in your web browser."
		print "c# -- open comments for story number # in your web browser."
		print "#+ -- open up story number # AND its comments in your web browser."
		print "d/w -- always show domains / webpages of stories. (d)"
		print "l/o -- always show full titles of stories / make titles fit an 80-char line. (o)"
		print "c/e -- collapse stories once you've read them / don't. (e)"
		print "u -- update hnsh to the latest version."
		print "=========================="
		input = raw_input("Press Return to go back to the Hacker News stories.")
		self.printStories()


	def checkForUpdates(self):
		"""
		Tells the user where they can get the latest version of hnsh.
		
		This is a temporary meausre until I can find a better way to update the program.
		"""
		input = raw_input("To update hnsh, go to http://github.com/scottjacksonx/hnsh and download the latest version. Press Return to continue:")
			self.printStories()
			
			
			

# Just instantiate a HackerNewsShell and let 'er rip!
hnsh = HackerNewsShell()