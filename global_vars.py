import xml.etree.ElementTree as ET

"""
Global config variables
"""
GIT_CLONE_LOCATION = "gitClones"
APK_DOWNLOAD_DIR = "apk"
TMP_OUTPUT_DIR = "output"
TOOLS_LOCATION = "../../tools"
DB_LOCATION = "../db.sqlite3"
SONAR_HOST = "http://vm-009.casci.rit.edu:9000"

F_Droid_Metadata_Repo = "fdroiddata"
F_Droid_XML_Location = "./Example_Data.xml"

is_dev = True

app_packages = set()

tree = ET.parse(F_Droid_XML_Location)
root = tree.getroot()

def runner():
    import sys
    import time
    for i in range(0, 70):
        sys.stdout.flush()
        counter = 0
        while(counter < i):
            sys.stdout.write('')
            counter += 1
        sys.stdout.write("#")
        time.sleep(10)

def print_processing(count, total):
    import sys
    sys.stdout.flush()
    sys.stdout.write('Processing %d / %d\r' % (count, total))

def clear_stdout():
    import sys
    sys.stdout.write('')