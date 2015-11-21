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
import shutil
import requests
import re
import sqlite3
import time
import sys
import argparse


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
	print("39")
	if len(secundary_args_list) > 0:
		build_call_list += ["--xapply"] # --x-apply for more modern systems

	build_call_list += cmd.split() + [":::"]

	for i in args_list:
		build_call_list.append(i)

	if len(secundary_args_list) > 0:
		build_call_list += [":::"]

		for i in secundary_args_list:
			build_call_list.append(i)


	#if is_dev:
	#	print(" ".join(build_call_list))
	#	input("Continue?")
	#else:
	#	print("Running parallel...")

	process = subprocess.Popen(build_call_list)
	#print(process.communicate()[0])
	print("62")

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
				print(e)
				print("Error in " + package_name)
			else:
				
				# New parser
				# The new parser uses regular expressions instead of matching line by line
				# Might be a bit slower, but its required for the build and description fields
				file_string = f.read()
				
				# Get the app category
				regex = re.compile(".*Categories:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				category = r[0][11:].strip()
				app_metadata["category"] = category

				# Get the app license
				regex = re.compile(".*License:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				license = r[0][8:].strip()
				app_metadata["license"] = license

				# Get the app website
				regex = re.compile(".*Web Site:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				website = r[0][9:].strip()
				app_metadata["website"] = website

				# Get the app name
				regex = re.compile(".*Auto Name:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				if len(r) != 0:
					name = r[0][10:].strip()
					app_metadata["name"] = name

				# Get the app summary
				regex = re.compile(".*Summary:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				summary = r[0][8:].strip()
				app_metadata["summary"] = summary

				# Get the app description
				regex = re.compile("Description:.*\n\.\n",re.UNICODE|re.DOTALL)
				r = regex.findall(file_string)
				description = r[0][12:].strip()
				app_metadata["description"] = description

				# Get the app repo type
				regex = re.compile(".*Repo Type:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				if len(r) != 0:
					RepoType = r[0][10:].strip()
					app_metadata["RepoType"] = RepoType

				# Get the app repo url
				regex = re.compile(".*Repo:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				if len(r) != 0:
					RepoURL = r[0][5:].strip()
					app_metadata["RepoURL"] = RepoURL

				# Get the app versions and commit info
				regex = re.compile("Build:.*\n.*\n",re.UNICODE)
				r = regex.findall(file_string)
				app_metadata["version"] = {}
				for build in r:
					version_build_string = build[6:].split('\n')[0]
					#print(version_build_string)
					version,build_number = version_build_string.split(',')
					commit_string = build.split('\n')[1].strip()
					if commit_string[:6] == "commit":
						app_metadata["version"][version] = {'build': int(build_number), 'commit': commit_string[7:]}

				# Get the app current version
				regex = re.compile(".*Current Version:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				if len(r) != 0:
					current_version = r[0][16:].strip()
					app_metadata["current_version"] = current_version

				# Get the app current build
				regex = re.compile(".*Current Version Code:.*\n",re.UNICODE)
				r = regex.findall(file_string)
				if len(r) != 0:
					current_build_number = r[0][21:].strip()
					app_metadata["current_build_number"] = int(current_build_number)
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
			url = "https://f-droid.org/repo/" + key + "_" + str(i["build"]) + ".apk"
			#print(url)
			urls_to_download.append(url)
			download_locations.append(APK_DOWNLOAD_DIR + "/" + key + "_" + str(i["build"]) + ".apk")

	if dry_run:
		for i in range(len(urls_to_download)):
			print(urls_to_download[i])
			print(download_locations[i])
	else:
		print("181")
		#print("183")
		#print("wget -c -P " + APK_DOWNLOAD_DIR)
		#run_parallels("wget -c -P apk/", urls_to_download, num_jobs=8)

		### DK. Just loop through things and download it all manually

		#print("here")
		#print(urls_to_download)



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
		#GIT_CLONE_LOCATION = 'repos'
		GIT_CLONE_LOCATION = 'gitClones'

		global is_dev
		is_dev = False

		global APK_DOWNLOAD_DIR
		APK_DOWNLOAD_DIR = 'apks'

		global TMP_OUTPUT_DIR
		TMP_OUTPUT_DIR = 'output'

		global TOOLS_LOCATION
		TOOLS_LOCATION = 'tools'

		global DB_LOCATION
		DB_LOCATION = 'db.sqlite3'

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
		#if not(len(sys.argv) == 4 and (sys.argv[3] == "-q" or sys.argv[3] == "--quiet")):
			#input("Press enter to continue (Crt+C to Cancel)")
	else:
		print("Running in development mode, no source control repos cloning")
		dev_mode = True

	_set_env_variables()

	# Only print stats in dev mode
	if dev_mode:
		getAppStats()

	print("Cloning FDroid metadata repository")
	#getFDroidRepoData()
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
	'''
	list_of_apks = os.listdir(APK_DOWNLOAD_DIR)

	ret = []
	for apk in list_of_apks:
		if apk.startswith(package_name):
			#print(apk)

			ret.append(apk)

	return ret

def read_git_history(metadata):

	db = DB(DB_LOCATION)

	repos = os.listdir(GIT_CLONE_LOCATION)

	repos.remove('fdroiddata')
	print("Starting git history collection")
	commit_metadata = {}

	count = 1
	total_count = len(repos)
	for package_name in repos:
		print_processing(count, total_count)
		path = GIT_CLONE_LOCATION + "/" + package_name
		#print(path)

		history = getGitHistory(path)
		history = codecs.decode(history, "utf-8", "ignore") #Ignore any errors

		# Regex to identify commit
		commit_regex = re.compile("(.*\n.*\n)", re.UNICODE)

		# Regex for each item in the commit line
		fields_regex = re.compile("(^.*)( .*)( <.*>)( \d*)(\s*.*)", re.UNICODE)
		commits = []
		for commit_line in commit_regex.findall(history):
			fields = fields_regex.findall(commit_line)

			if len(fields) == 0:
				continue

			commit_data = {}

			fields = fields[0]

			commit_data["commit"] 	= fields[0]
			commit_data["author"] 	= fields[1]
			commit_data["email"]	= fields[2]
			commit_data["time"] 	= fields[3]
			commit_data["summary"] 	= fields[4].strip()

			commits.append(commit_data)

			db.add_commit_item(metadata[package_name], commit_data, commit_on_call=False)

		commit_metadata[package_name] = commits
		count += 1
	
	db.commit()



def analysis_cmd(analysis = "AllReadSonar"):
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

		read_git_history(new_metadata)

		

def update_cmd(update_type = "AppData"):
	print("Updating " + update_type)

	_set_env_variables()
	
	db = DB(DB_LOCATION)

	metadata = parseFDroidRepoData()
	
	for app in metadata.keys():
		if is_app_valid(metadata[app]):
			db.update_app(metadata[app], commit_on_call = False)

	db.commit()


def main():

	#### DK - Remove the SQLite file if it exists
	db = "db.sqlite3"	## Should tie this into the global variable
	if os.path.exists(db):
		os.remove(db)

	if len(sys.argv) == 1:
		print("Usage: python parseXML.py <init | analysis | stats | help> <production | dev> <extra args>")
		return

	if sys.argv[1] == "help":
		help_cmd()
	elif sys.argv[1] == "init":
		init_cmd()
	elif sys.argv[1] == "analysis":
		analysis_cmd()
	elif sys.argv[1] == "update":
		update_cmd()
	elif sys.argv[1] == "stats":
		print(parseFDroidRepoData())
	elif sys.argv[1] == "dan":
		print("Run dans code")
		metadata = parseFDroidRepoData()
		getAPKs(metadata)
		print("937")

			

if __name__ == '__main__':
	main()
