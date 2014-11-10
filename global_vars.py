import xml.etree.ElementTree as ET

"""
Global config variables
"""
GIT_CLONE_LOCATION = "/tmp/gitClones"
APK_DOWNLOAD_DIR = "/tmp/apk"
TMP_OUTPUT_DIR = "/tmp/output"
TOOLS_LOCATION = "../../tools"
DB_LOCATION = "../db.sqlite3"
SONAR_HOST = "http://vm-009.casci.rit.edu:9000"

F_Droid_Metadata_Repo = "fdroiddata"
F_Droid_XML_Location = "../Example_Data.xml"

is_dev = True

app_packages = set()

tree = ET.parse(F_Droid_XML_Location)
root = tree.getroot()