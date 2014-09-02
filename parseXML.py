#!/usr/bin/python

"""

Downloads and parses the XML Data from F-Droid.

Builds the python objects for analysis
"""


import xml.etree.ElementTree as ET


tree = ET.parse('../Example_Data.xml')
root = tree.getroot()


def extractURLDomain(url):
	baseurl = ""
	# Determine https vs http

	if(url.find("https://") != -1):
		baseurl = url[8:]
	else:
		baseurl = url[7:]
	endIndex = baseurl.find("/")

	# Just grab the domain for the url
	baseurl = baseurl[:endIndex]

	return baseurl


def getAppStats():

	count = 0

	# Dict with the domain then the count
	repoLocations = {}
	noData = 0


	for children in root:
		if(children.tag == "application"):
			count += 1
			url = children.find("source").text

			if(url == None):
				noData += 1
				continue

			baseurl = extractURLDomain(url)

			if(baseurl in repoLocations):
				repoLocations[baseurl] += 1
			else:
				repoLocations[baseurl] = 1

	# Sort the repo list for easier reading
	repoLocationsSorted = sorted(repoLocations.items(), key=lambda x: x[1], reverse=True)

	print("Application Count: " + str(count))

	print("Repo Stats:")
	for item in repoLocationsSorted:
		print(item[0] + " : " + str(item[1]))
	print("==========================================================")
	print("No Data Available: " + str(noData))

getAppStats()