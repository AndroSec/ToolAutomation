#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Downloads and parses the XML Data from F-Droid.

Builds the python objects for analysis
"""
import xml.etree.ElementTree as ET
import os
import codecs
import subprocess
import sys
from db import DB
from git import *
from global_vars import *


def run_parallels(cmd, args_list, secundary_args_list = [], num_jobs = 4):
	'''
	Runs a command under the parallel tool.
	- cmd 
			The command to execute
	- args_list
			A list of arguments to pass the program to be run in parallel
	- num_jobs
			Number of concurrent jobs to run 
	'''

	build_call_list = ["parallel", "--gnu" ,"--progress", "--eta", "-j", str(num_jobs)]
	if len(secundary_args_list) > 0:
		build_call_list += ["--xapply"] # --x-apply for more modern systems

	build_call_list += cmd.split() + [":::"]

	for i in args_list:
		build_call_list.append(i)

	if len(secundary_args_list) > 0:
		build_call_list += [":::"]

		for i in secundary_args_list:
			build_call_list.append(i)



	print(build_call_list)
	input("Continue?")

	process = subprocess.call(build_call_list)

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


def parseFDroidRepoData():
	metadata = {}
	
	repo_type = {}
	rootMetadataFolder = GIT_CLONE_LOCATION + "/" + F_Droid_Metadata_Repo + "/metadata/"
	for children in root:
		
		if(children.tag == "application"):
			package_name = children.attrib["id"]
			app_metadata = {}
			app_metadata["package"] = package_name
			
			try:
				f = codecs.open(rootMetadataFolder + package_name + ".txt", "r", "utf-8")
			except Exception as e:
				print("Error in " + package_name)
			else:
				for line in f:
					if (line[:10] == "Repo Type:"):
						repo = line[10:].strip()

						# Keep track of the numbers
						if(repo in repo_type):
							repo_type[repo] += 1
						else:
							repo_type[repo] = 1

						app_metadata["RepoType"] = repo

					elif (line[:5] == "Repo:"):
						app_metadata["RepoURL"] = line[5:].strip()
					elif (line[:6] == "Build:"):
						version_string = line[6:]
						version,build_number = version_string.split(',')

						if(not("version" in app_metadata)):
							app_metadata["version"] = {}
						
						app_metadata["version"][version] = int(build_number)
					elif line.startswith("Auto Name:"):
						app_metadata["name"] = line[10:].strip()
					elif line.startswith("License:"):
						app_metadata["license"] = line[8:].strip()
					elif line.startswith("Current Version:"):
						app_metadata["current_version"] = line[16:].strip()
					elif line.startswith("Current Version Code:"):
						app_metadata["current_build_number"] = int(line[21:].strip())
					elif line.startswith("Summary:"):
						app_metadata["summary"] = line[8:].strip()
					elif line.startswith("Web Site:"):
						app_metadata["website"] = line[9:].strip()

				f.close()

			if not "name" in app_metadata.keys():
				app_metadata["name"] = app_metadata["package"]

			metadata[package_name] = app_metadata

	#print(repo_type)
	return metadata

def getAPKs(metadata, quiet_mode = False, dry_run = False):
	urls_to_download = []
	download_locations = []
	for key in metadata.keys():
		app = metadata[key]

		if(not("RepoType" in app and "RepoURL" in app)):
			print(key + " doesn't have valid metadata")
			continue

		versions = app["version"]
		print(key)
		# https://f-droid.org/repo/org.zeroxlab.zeroxbenchmark_9.apk
		for i in versions.values():
			url = "https://f-droid.org/repo/" + key + "_" + str(i) + ".apk"
			print(url)
			urls_to_download.append(url)
			download_locations.append(APK_DOWNLOAD_DIR + "/" + key + "_" + str(i) + ".apk")

	if dry_run:
		for i in range(len(urls_to_download)):
			print(urls_to_download[i])
			print(download_locations[i])
	else:
		run_parallels("wget -c -P " + APK_DOWNLOAD_DIR, urls_to_download, num_jobs=8)

def numberOfVersions(app_data):
	if("version" in app_data):
		return len(app_data["version"].keys())
	else:
		return 0

def getAppStats():
	count = 0

	# Dict with the domain then the count
	repoLocations = {}
	noData = 0

	for children in root:
		if(children.tag == "application"):
			count += 1
			
			package_name = children.attrib['id']
			app_packages.add(package_name)

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

def _set_env_variables():
	if len(sys.argv) > 2 and sys.argv[2] == "production":
		# Set location of all repos
		global GIT_CLONE_LOCATION
		GIT_CLONE_LOCATION = '/home/androsec/repos'

		global is_dev
		is_dev = True

		global APK_DOWNLOAD_DIR
		APK_DOWNLOAD_DIR = '/home/androsec/apks'

		global TMP_OUTPUT_DIR
		TMP_OUTPUT_DIR = '/home/androsec/output'

		global TOOLS_LOCATION
		TOOLS_LOCATION = '/home/androsec/tools'

		global DB_LOCATION
		DB_LOCATION = '/home/androsec/db.sqlite3'

def is_app_valid(app_metadata):
	'''
	Checks to see if an app has all the required fields
	'''

	if not "name" in app_metadata.keys():
		return False
	elif not "package" in app_metadata.keys():
		return False
	elif not "RepoURL" in app_metadata.keys():
		return False
	elif not "RepoType" in app_metadata.keys():
		return False
	elif not "version" in app_metadata.keys():
		return False
	else:
		return True

def init_cmd():
	print("Downloading all metadata and source control repositories")
	dev_mode = False

	if len(sys.argv) >= 3:
		print("Running in production mode")
		if not(len(sys.argv) == 4 and (sys.argv[3] == "-q" or sys.argv[3] == "--quiet")):
			input("Press enter to continue (Crt+C to Cancel)")
	else:
		print("Running in development mode, no source control repos cloning")
		dev_mode = True

	_set_env_variables()

	# Only print stats in dev mode
	if dev_mode:
		getAppStats()

	print("Cloning FDroid metadata repository")
	getFDroidRepoData()
	metadata = parseFDroidRepoData()
	print("Clone completed")

	print("Saving data to db")
	db = DB(DB_LOCATION)
	db.create_db()
	for app in metadata.keys():
		if is_app_valid(metadata[app]):
			db.add_new_app(metadata[app], commit_on_call = False)
	db.commit()
	print("Getting source control urls to retrieve")
	if not dev_mode:
		cloneRepos(metadata)
	else:
		cloneRepos(metadata, dry_run = True)

	if dev_mode:
		getAPKs(metadata, dry_run = True)
	else:
		getAPKs(metadata)

	print("Checkout out of source control complete!")

def help_cmd():
	print("HELP HERE")

def find_apks(package_name):
	'''
	Returns a list of all the apk files we have on record for 
	the current application.

	TODO: Add caching of the os.listdir, may be a bottle neck?
	'''
	list_of_apks = os.listdir(APK_DOWNLOAD_DIR)

	ret = []
	for apk in list_of_apks:
		if apk.startswith(package_name):
			#print(apk)

			ret.append(apk)

	return ret


def run_stowaway(metadata):
	primary_parallel_args = []
	secundary_parallel_args = []
	for app in metadata:
		app_metadata = metadata[app]

		print("Running Stowaway on : " + app_metadata["name"])
		apks_downloaded = find_apks(app_metadata["package"])

		# Check if there's enough apks to run this process
		if(len(apks_downloaded) == 0):
			print("No apks found for " + app_metadata["package"])
			print("Try running the downloader again?")
			continue

		print("Found " + str(len(apks_downloaded)) + " versions of the app.")

		# Create temp dir for output
		for apk_name in apks_downloaded:
			subprocess.call(['mkdir', '-p', TMP_OUTPUT_DIR + '/' + apk_name])

			primary_parallel_args.append(APK_DOWNLOAD_DIR + '/' + apk_name)
			secundary_parallel_args.append(TMP_OUTPUT_DIR + '/' + apk_name)

	# Change the current working directory to the stowaway one, since it uses relative paths
	os.chdir(TOOLS_LOCATION + '/stowaway')
	# Run through the parallels tool, but only use 1 core. The app itself uses a bit more than 1 CPU, so for our
	# current system it slows the whole thing down a bit.
	# If we get a more powerful system, bump this up to 2
	run_parallels(TOOLS_LOCATION + '/stowaway/stowaway.sh', primary_parallel_args, secundary_parallel_args, num_jobs=1)

	read_stowaway_data(metadata)


def read_stowaway_data(metadata):
	'''
	Reads data from the output directory for stowaway.

	The data will be stored in a database after its read, then deleted.
	'''

	print("NOT YET IMPLEMENTED")






def analysis_cmd(analysis = "Stowaway"):
	#print("Running analysis on all downloaded projects")
	print("Calculating analysis count")

	# Setup env variables
	_set_env_variables()

	cloned_repos = os.listdir(GIT_CLONE_LOCATION)

	metadata = parseFDroidRepoData()
	new_metadata = {}
	# Remove our only non source code repo
	cloned_repos.remove("fdroiddata")

	for i in cloned_repos:
		# If this throws a key error we have a serious problem with our data
		new_metadata[i] = metadata[i]
	

	print("Running analysis on " + str(len(new_metadata.keys())) + " applications")
	if is_dev:
		input("Press enter to continue (Crtl+C to Cancel)")

	# RUN ANALYSIS

	
	if(analysis == "Stowaway"):
		run_stowaway(new_metadata)




def main():
	if len(sys.argv) == 1:
		print("Usage: python parseXML.py <init | analysis | stats | help> <production | dev> <extra args>")
		return

	if sys.argv[1] == "help":
		help_cmd()
	elif sys.argv[1] == "init":
		init_cmd()
	elif sys.argv[1] == "analysis":
		analysis_cmd()
	elif sys.argv[1] == "stats":
		print(parseFDroidRepoData())

			

if __name__ == '__main__':
	main()