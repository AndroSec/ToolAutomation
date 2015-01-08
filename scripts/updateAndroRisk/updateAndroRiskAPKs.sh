#!/bin/bash

clear

	DBName=AndrosecDatabase2.sqlite

	mkdir -p logs
	logLocation=logs/updateList.log
	rm $logLocation

	touch $logLocation

	### Get input file
	apkInputList=apklist.txt


	# function to split the read line 
	SplitLine () {
#  		echo $1 


		rev=`echo $1 | rev`
   	
		rev=`echo $rev | awk -F'_' '{print $1}'`
   		Part2=`echo $rev | rev`	
		Part1=${1//_$Part2/""}   	
		Part2=${Part2//.apk/""}

#		echo $Part1
#		echo $Part2 


#   		Part2=${Part2//.apk/""}
#		echo $Part2



   		#rev=`echo $1 | rev`
   		#echo $rev
   		#awk -F_ '{OFS="_";NF--;print $1;}'
   		#IFS='_' read -a array <<< "$rev"


		#Part1="${array[0]}"
		#Part2="${array[1]}"


		## Reverse back
		#Part1=`echo $Part1 | rev`
		#Part2=`echo $Part2 | rev`

		#Part1=${Part1//.apk/""}

		#echo $Part1
		#echo $Part2

#   		echo "_____"


### Find the appID based on Part 1
		
		appID=`sqlite3 $DBName "SELECT appID FROM appdata WHERE name='$Part1';"`
		# echo $appID

		### Find the versionID based on Part 2 
		versionID=`sqlite3 $DBName "SELECT versionID FROM version WHERE appID =$appID and build_number=$Part2;"`

		echo Update: $versionID

		# If found, update the row
		sqlite3 $DBName  "UPDATE version SET isAPKExists=1 WHERE versionID=$versionID;"
		# update version set isAPKExists =1 where versionID = 3897
		# Make the necessary log updates




		### Add a counter - put apk information on same line



	}





	### Loop through every row of the input file
	#file="/home/vivek/data.txt"
	while IFS= read -r line
	do
        # display $line or do somthing with $line
			#		echo "$line"

		echo "Reading $line:" >> $logLocation
## Add split file contents		echo "*****:" >> $logLocation


		SplitLine $line

	done <"$apkInputList"





#### Todo
# Create logging
# Check into GH


