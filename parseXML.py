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
	if len(secundary_args_list) > 0:
		build_call_list += ["--xapply"] # --x-apply for more modern systems

	build_call_list += cmd.split() + [":::"]

	for i in args_list:
		build_call_list.append(i)

	if len(secundary_args_list) > 0:
		build_call_list += [":::"]

		for i in secundary_args_list:
			build_call_list.append(i)


	if is_dev:
		print(" ".join(build_call_list))
		input("Continue?")
	else:
		print("Running parallel...")

	process = subprocess.Popen(build_call_list, stdout=subprocess.DEVNULL)
	print(process.communicate()[0])

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
			print(url)
			urls_to_download.append(url)
			download_locations.append(APK_DOWNLOAD_DIR + "/" + key + "_" + str(i["build"]) + ".apk")

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
		is_dev = False

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

		if is_dev:
			print("Running Stowaway on : " + app_metadata["name"])
		apks_downloaded = find_apks(app_metadata["package"])

		# Check if there's enough apks to run this process
		if(len(apks_downloaded) == 0):
			print("No apks found for " + app_metadata["package"])
			print("Try running the downloader again?")
			continue
		if is_dev:
			print("Found " + str(len(apks_downloaded)) + " versions of the app.")

		# Setup the parallel tool
		for apk_name in apks_downloaded:
			#subprocess.call(['mkdir', '-p', TMP_OUTPUT_DIR + '/' + apk_name])

			primary_parallel_args.append(APK_DOWNLOAD_DIR + '/' + apk_name)
			secundary_parallel_args.append(TMP_OUTPUT_DIR + '/' + apk_name)

	# Change the current working directory to the stowaway one, since it uses relative paths
	os.chdir(TOOLS_LOCATION + '/stowaway')

	# Since stowaway takes so long, split it in runs of 20
	increment = 20
	# Keep track of the current index
	count = 0

	# A makeshift loop that goes in intervals of increment till it completes the list
	# of apks to analyze
	while count < len(primary_parallel_args):

		first_list = []
		second_list = []
		if count + increment < len(primary_parallel_args):
			first_list = primary_parallel_args[count : count + increment]
			second_list = secundary_parallel_args[count : count + increment]
		else:
			first_list = primary_parallel_args[count : ]
			second_list = secundary_parallel_args[count : ]

		# Create the output directories
		for directory in second_list:
			subprocess.call(['mkdir', '-p', directory])

		print("Running batch of " + str(count + increment) + " out of " + str(len(primary_parallel_args)))
		# Run through the parallels tool, but only use 1 core. The app itself uses a bit more than 1 CPU, so for our
		# current system it slows the whole thing down a bit.
		# If we get a more powerful system, bump this up to 2
		run_parallels(TOOLS_LOCATION + '/stowaway/stowaway.sh', first_list, second_list, num_jobs=2)

		read_stowaway_data(metadata)

		count += increment


def read_stowaway_data(metadata):
	'''
	Reads data from the output directory for stowaway.

	The data will be stored in a database after its read, then deleted.
	'''
	# Start the DB
	db = DB(DB_LOCATION)
	# Get directory packages
	packages = os.listdir(TMP_OUTPUT_DIR)

	# Go through all the results in the output dir
	for pkg in packages:
		
		pkg_name = '_'.join(pkg.split("_")[:-1])
		build_num = int(pkg.split("_")[-1].split('.')[0])
		print(pkg_name + " | " + str(build_num))

		if not pkg_name in metadata.keys():
			continue

		app_metadata = metadata[pkg_name]

		versions = app_metadata["version"]
		version = -1

		# Find the version that we are looking at based on the build number
		for k in versions.keys():
			if versions[k]["build"] == build_num:
				print("Version: " + k + " Build: " + str(versions[k]["build"]))
				version = k
				break

		if version == -1:
			print("ERROR: Something went really wrong here")
			print("Problem at: " + pkg_name + " | " + str(build_num))
			continue

		file_path = TMP_OUTPUT_DIR + '/' + pkg
		
		if os.path.isfile(file_path + "/Overprivilege"):
			for line in open(file_path + "/Overprivilege"):
				try:
					db.add_new_overpermission(app_metadata, version, line, commit_on_call=False)
				except Exception as e:
					print("Problem adding overpermission")
					print(e)
					print("Permission: " + line)
					print("App: " + pkg_name)
					print("Version: " + version)
				
		else:
			print("No over permissions for " + pkg_name)

		if os.path.isfile(file_path + "/Underprivilege"):
			for line in open(file_path + "/Underprivilege"):
				try:
					db.add_new_underpermission(app_metadata, version, line, commit_on_call=False)
				except Exception as e:
					print("Problem adding underpermission")
					print(e)
					print("Permission: " + line)
					print("App: " + pkg_name)
					print("Version: " + version)
		else:
			print("No under permissions for " + pkg_name)

		# Look through all intents and attempt to add them to the database
		if os.path.isfile(file_path + "/IntentResults/allActions.txt"):
			for line in open(file_path + "/IntentResults/allActions.txt"):
				try:
					db.add_new_intent_version(app_metadata, version, line, commit_on_call=False)
				except Exception as e:
					print("Problem adding intent")
					print(e)
					print("Intent: " + line)
					print("App: " + pkg_name)
					print("Version: " + version)
				else:
					print("No intents found for " + pkg_name)
		try:
			db.add_stowaway_run(app_metadata, version, commit_on_call=False)
		except sqlite3.IntegrityError as e:
			pass

	# Save the results
	db.commit()

	print("Cleaning up the directory")
	shutil.rmtree(TMP_OUTPUT_DIR) # Deletes the dir completely

def read_sonar(metadata ):
	'''
	Reads the data collected from sonar
	'''
	# Init the db
	db = DB(DB_LOCATION)

	# Get the version information that sonar has for each version
	# This is used to make sure that the data is consistent since 
	# versions are not in any particular order
	VERSION_API_CALL = "/api/projects/index?versions=true"

	version_url = SONAR_HOST + VERSION_API_CALL

	r = requests.get(version_url)
	'''
	Version Data Format

	Version Data is a json array of data returned. Each item follows the same
	structure.

	item json hash table
		id - The id of the project (Useful inside of Sonar only)
		k  - The project key or package name (Used to map back to our data)
		nm - The application name (Useful for debugging)
		sc - The application scope (Not Used - Sonar Specific)
		qu - The application qualifier (Not used - Sonar Specific)
		lv - Latest version for the application (Only present if there's multiple versions)
		v  - Version information, see bellow

	Version Information hash table
		The version information table is a dynamic hash table where
		the keys are the version of the app the the values:
			sid - Internal version number (Unused)
			d   - A timestamp for the analysis of that version (Important)
	'''
	version_data = r.json()

	sonar_version_timestamps = {}
	print("Collecting version information")
	for i in version_data:
		package_name = i["k"]
		if "v" in i:
			versions_sonar = i["v"]
			sonar_version_timestamps[package_name] = {}
			for version in versions_sonar.keys():
				# Save the timestamps
				timestamp = versions_sonar[version]["d"]
				sonar_version_timestamps[package_name][timestamp] = version

	
	print("Version information collected")
	print("Processing individual projects")
	total_count = len(sonar_version_timestamps.keys())
	count = 1
	for project in sonar_version_timestamps.keys():
		print_processing(count, total_count)
		'''
		Time machine data is in the following format:
		cols  - Description of each field in the cells component
		cells - Dict containing details for every version

					d - Timestamp for the version
					v - The values corresponding to the cols above for this version 
		'''
		TIME_MACHINE_API_CALL = "/api/timemachine?resource=" + project + "&metrics=classes,ncloc,functions,duplicated_lines,test_errors,skipped_tests,complexity,class_complexity,function_complexity,comment_lines,comment_lines_density,duplicated_lines_density,files,directories,file_complexity,violations,duplicated_blocks,duplicated_files,lines,blocker_violations,critical_violations,major_violations,minor_violations,commented_out_code_lines,line_coverage,branch_coverage,build_average_time_to_fix_failure,build_longest_time_to_fix_failure,build_average_builds_to_fix_failures,generated_lines,version"

		raw_project_data = requests.get(SONAR_HOST + TIME_MACHINE_API_CALL).json()[0]

		cols = []

		for metric in raw_project_data["cols"]:
			cols.append(metric["metric"])

		# Build the project data objects for every version
		for version_data in raw_project_data["cells"]:
			timestamp = version_data["d"]

			project_data = {}

			# Build the project data dictionary
			for i in range(len(cols)):
				key = cols[i]
				val = version_data["v"][i]

				project_data[key] = val

			version = -1
			# If there's a time stamp missmatch lets try to make our best guess
			if not timestamp in sonar_version_timestamps[project]:
				# If there's only 1 version, then we can assume its the only one
				if len(metadata[project]["version"].keys()) == 1:
					# Get the first version we have on record
					version = list(metadata[project]["version"].keys())[0]
				elif len(metadata[project]["version"].keys()) - len(sonar_version_timestamps[project].keys()) == 1:
					# This means that sonar is missing 1 record for whatever reason, lets 
					# figure out which on it is
					for v in metadata[project]["version"].keys():
						if not v in sonar_version_timestamps[project].values():
							version = v
							break
				else:
					# If we hit this point its assumed that its bad data, discard the results
					# Printing stuff for future reference, but nothing to be done here
					print("Ran into an issue:")
					print(str(len(metadata[project]["version"].keys()) - len(sonar_version_timestamps[project].keys())))
					print(timestamp)
					print(raw_project_data["cells"])
					print(project)
					print(sonar_version_timestamps[project])
					print(metadata[project]["version"])
					continue # Skip this data set
					#input("Continue?")
			else:
				# Grab the version based on the timestamp
				version = sonar_version_timestamps[project][timestamp]
			try:
				db.add_sonar_results(metadata[project], project_data, version, commit_on_call=False)
				db.add_sonar_run(metadata[project], version, commit_on_call=False)
			except sqlite3.IntegrityError as e:
				# Ignore the error
				print("Duplicate detected in " + project + " (" + str(version) + " )")


		# Keep track of progress
		count += 1
	clear_stdout()
	print("Done reading sonar")
	db.commit()


def run_sonar(metadata):
	start_time = time.time()
	git_repos = os.listdir(GIT_CLONE_LOCATION)
	git_repos.remove('fdroiddata')

	count = 0
	repos_with_src = []
	repos_with_modules = {}
	for repo in git_repos:
		#print(repo)
		listing = os.listdir(GIT_CLONE_LOCATION + '/' + repo)
		if 'src' in listing:
			count += 1
			repos_with_src.append(repo)
		else:
			# Try to find multi module projects
			modules = []
			for folder in listing:
				# Make sure it's a folder
				if not os.path.isdir(GIT_CLONE_LOCATION + '/' + repo + '/' + folder):
					continue

				folder_list = os.listdir(GIT_CLONE_LOCATION + '/' + repo + '/' + folder)
				if 'src' in folder_list:
					# We have found a sub-module, add it
					modules.append(folder)

			if len(modules) > 0:
				count += 1
				repos_with_modules[repo] = modules
				
	unknown_projects = len(git_repos) - count
	if unknown_projects > 0:
		print("Runnning sonar on " + str(count) + " projects.")
		print("Couldn't detect the folder structure of " + 
				str(unknown_projects) + " projects.")

	property_strings = {}

	# Build the property strings for simple projects and module
	# projects, since they share the same intial properties
	for repo in (repos_with_src + list(repos_with_modules.keys())):
		property_string = ""

		# Add the project key
		# Repo happens to be the pakcage name too!
		property_string += "sonar.projectKey=" + repo.replace(".", ":") + " \n" 

		# Add the project name
		property_string += "sonar.projectName=" + metadata[repo]["name"] + " \n"

		# Add the project version
		# For testing purposes leave as 1.0 until I can figure
		# out how to change versions in git here
		# For now only running the latest version
		#property_string += "sonar.projectVersion=1.0 \n"

		# Add the standard sources file
		property_string += "sonar.sources=src \n"

		# Add the project base dir
		#property_string += "sonar.projectBaseDir=" + GIT_CLONE_LOCATION + "/" + repo + " \n"

		# Add to the dictionary
		property_strings[repo] = property_string

	# Go over the module projects and add the modules property
	for repo in repos_with_modules.keys():
		# Get the already setup string of properties
		property_string = property_strings[repo]

		#Set the modules from the dicovery from before
		property_string += "sonar.modules=" + (",".join(repos_with_modules[repo])) + " \n"

		# Save the result
		property_strings[repo] = property_string

	print("Creating property files")
	# Write the property files
	'''
	for prop in property_strings.keys():
		# Write using UTF-8 due to UTF-8 charactes in project names
		print(GIT_CLONE_LOCATION + "/" + prop + "/sonar-project.properties")
		f = codecs.open(GIT_CLONE_LOCATION + "/" + prop + "/sonar-project.properties", "w", "UTF-8-sig")
		f.write(property_strings[prop])
		f.close()
	'''

	# Run sonar runner
	# This is something that can't be paralellized so run here
	count = 0
	total = len(property_strings.keys())
	errors = []
	timeouts = []
	for repo in property_strings.keys():
		os.chdir(GIT_CLONE_LOCATION + "/" + repo)
		count += 1
		
		print("Running " + str(count) + " out of " + str(total))
		#input("Continue?")
		# Pass the key as well since it seems to hate not having it
		for version in sorted(metadata[repo]["version"].keys()):
			commit = metadata[repo]["version"][version]["commit"]
			checkoutVersion(GIT_CLONE_LOCATION + "/" + repo, commit)
			# Write the props file
			f = codecs.open(GIT_CLONE_LOCATION + "/" + repo + "/sonar-project.properties", "w", "UTF-8-sig")
			f.write(property_strings[repo])
			f.close()

			try:
				# Try to run the analysis, timeout after 5 minutes since sometimes they can lock up
				subprocess.check_call([	"/home/androsec/tools/sonar-runner-2.4/bin/sonar-runner", "-e", "-Dsonar.projectKey=" + repo , 
										"-Dsonar.projectVersion=" + version ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300 )
			except subprocess.TimeoutExpired as e:
				print("Timeout on " + str(repo) + " (" + str(version) + ")")
				timeouts.append(str(repo) + " (" + str(version) + ")")
			except subprocess.CalledProcessError as e:
				print("Encountered error on " + str(repo) + " (" + str(version) + ")")
				errors.append(str(repo) + " (" + str(version) + ")")

			# Cleanup
			subprocess.check_call("git checkout . && git clean -f -d", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)

	# Calculate the time to run
	run_time = time.time() - start_time

	#print("Cleaning up changes")
	print("-------------------------")
	print("      Run Summary")
	print("-------------------------")
	print("Errors:   " + str(len(errors)))
	print("Timeouts: " + str(len(timeouts)))
	print("Completion Time: " + str(run_time)) + " s"
	print("-------------------------")

	'''
	# Cleanup start
	for prop in property_strings.keys():
		# Delete the property files and revert the git folder to defaut status
		os.chdir(GIT_CLONE_LOCATION + "/" + prop)
		subprocess.call("git checkout . && git clean -f -d", shell=True)
	'''
	# DONT READ YET
	# read_sonar(metadata)

def run_androrisk(metadata):
	print("Running androrisk")
	
	# Create the TMP_OUTPUT_DIR
	subprocess.call(['mkdir', '-p', TMP_OUTPUT_DIR])

	primary_parallel_args = []
	secundary_parallel_args = []
	for app in metadata.keys():
		app_metadata = metadata[app]

		apks = find_apks(app_metadata["package"])

		for i in apks:
			primary_parallel_args.append(APK_DOWNLOAD_DIR + "/" + i + " " + TMP_OUTPUT_DIR + "/" + i + ".txt")
	os.chdir('/home/androsec/tools/androguard')
	run_parallels('/home/androsec/tools/androguard/run_androguard.sh ', primary_parallel_args)
	read_androrisk(metadata)

def read_androrisk(metadata):
	# Start the db
	db = DB(DB_LOCATION)

	for i in os.listdir(TMP_OUTPUT_DIR):
		pkg = i[:-3]

		pkg_name = '_'.join(pkg.split("_")[:-1])
		build_num = int(pkg.split("_")[-1].split('.')[0])
		print(pkg_name + " | " + str(build_num))

		if not pkg_name in metadata.keys():
			continue

		app_metadata = metadata[pkg_name]

		versions = app_metadata["version"]
		version = -1

		# Find the version that we are looking at based on the build number
		for k in versions.keys():
			if versions[k]["build"] == build_num:
				# print("Version: " + k + " Build: " + str(versions[k]["build"]))
				version = k
				break

		if version == -1:
			print("ERROR: Something went really wrong here")
			print("Problem at: " + pkg_name + " | " + str(build_num))
			continue

		with open(TMP_OUTPUT_DIR + "/" + i) as f:
			for line in f:
				# Save the risk in the db
				db.add_fuzzy_risk(app_metadata, version, line, commit_on_call = False)
				db.add_androrisk_run(app_metadata, version, commit_on_call = False)
			f.close()
	db.commit()

	print("Cleaning up the directory")
	shutil.rmtree(TMP_OUTPUT_DIR) # Deletes the dir completely

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
	if analysis == "Stowaway":
		run_stowaway(new_metadata)
	elif analysis == "Sonar":
		run_sonar(new_metadata)
	elif analysis == "ReadSonar":
		read_sonar(new_metadata)
	elif analysis == "Androrisk":
		run_androrisk(new_metadata)
	elif analysis == "Git":
		read_git_history(new_metadata)
	elif analysis == "AllShort":
		run_androrisk(new_metadata)
		read_sonar(new_metadata)
		read_git_history(new_metadata)
	elif analysis == "AllReadSonar":
		run_stowaway(new_metadata)
		run_androrisk(new_metadata)
		read_sonar(new_metadata)
		read_git_history(new_metadata)
	elif analysis == "All":
		# Run all of them
		run_stowaway(new_metadata)
		run_sonar(new_metadata)
		run_androrisk(new_metadata)
		read_git_history(new_metadata)
	else:
		print("No valid analysis passed")
		

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

			

if __name__ == '__main__':
	main()
