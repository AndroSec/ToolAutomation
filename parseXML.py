#!/usr/bin/python

"""

Downloads and parses the XML Data from F-Droid.

Builds the python objects for analysis
"""


import xml.etree.ElementTree as ET


tree = ET.parse('../Example_Data.xml')
root = tree.getroot()



def getAppStats():

	count = 0

	# Dict with the domain then the count
	repo_locations = {}

	for children in root:
		if(children.tag == "application"):
			count += 1
			url = children.find("source").text

			# Print for debugging purposes
			print(url)

			if(url == None):
				print(children.attrib)
				continue

			baseurl = ""
			# Determine https vs http

			if(url.find("https://") != -1):
				baseurl = url[8:]
			else:
				baseurl = url[7:]
			endIndex = baseurl.find("/")

			# Just grab the domain for the url
			baseurl = baseurl[:endIndex]
			print(baseurl)

			if(baseurl in repo_locations):
				repo_locations[baseurl] += 1
			else:
				repo_locations[baseurl] = 1

	print("Application Count: " + str(count))

	print("Repo Stats:")

	for key in repo_locations.keys():
		print(key + " : " + str(repo_locations[key]))

getAppStats()