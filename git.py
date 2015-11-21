from global_vars import *
import subprocess
import os
from parseXML import *

def cloneGitRepo(url, destName=None):
    destPath = ""
    if(destName != None):
        destPath = GIT_CLONE_LOCATION + "/" + destName

    process = subprocess.check_call(["git", "clone", "-q", url, destPath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #print(process.communicate())

def getFDroidRepoData():
    cloneGitRepo("https://gitlab.com/fdroid/fdroiddata.git", F_Droid_Metadata_Repo)


def getGitHistory(path):
    os.chdir(path)

    process = subprocess.Popen(["git", "--no-pager", "log", "--pretty=%H %aN <%aE> %ct %n%s"], stdout=subprocess.PIPE)

    return process.communicate()[0]

def checkoutVersion(path, commit):
    '''
    Changes the git repo at the specified path to the specified commit
    '''
    os.chdir(path)

    subprocess.call(["git", "checkout", commit])

def checkoutLatestVersion(path):
    checkoutVersion("master")


### Clone all the repos. 
###     Written by DK to take place of the pareleel function that I could not get working
def cloneAllRepos(repos_to_clone, dest_clones):


    #print(repos_to_clone)
    #print(dest_clones)

    for i in range(len(repos_to_clone)):       
        #print(repos_to_clone[i])
        Repo.clone_from(repos_to_clone[i], "dir")
    print("**********************************************clone all repos")
    exit()



def cloneRepos(metadata, quiet_mode = False, dry_run = False):
    '''
    Clones a set of repos based on the metadata passed in.

    The metadata is in the following format.

    key -> Folder Name
    value -> Dict
        This dict has 2 required keys
        - RepoType: (git-svn, git, hg, bzr)
        - RepoURL: Remote url for the repository
    '''
    quiet_mode=True  ## DK
    repos_to_clone = []
    dest_clones = []
    for key in metadata.keys():
        app = metadata[key]
        
        if(not("RepoType" in app and "RepoURL" in app)):
            print(key + " doesn't have valid metadata")
            continue
        # Check the different repo types
        if (app["RepoType"] == "git"):
            if dry_run:
                print("Cloning Git Repo")
                print(app["RepoURL"] + " -> " + GIT_CLONE_LOCATION)
            repos_to_clone.append(app["RepoURL"])
            dest_clones.append(GIT_CLONE_LOCATION + "/" + key)

        elif (app["RepoType"] == "git-svn"):
            if dry_run:
                print("git-svn not implemented yet")
        elif (app["RepoType"] == "hg"):
            if dry_run:
                print("hg not implemented yet")
        elif (app["RepoType"] == "bzr"):
            if dry_run:
                print("bzr not implemented yet")
        else:   
            if dry_run:
                print("Unknown repo type: " + str(app["RepoType"]))
    if not quiet_mode and not dry_run:
        try:
            input("About to clone " + str(len(repos_to_clone)) + " repositories. Continue? (Ctrl+C to Cancel)")
        except KeyboardInterrupt as e:
            print()
            exit()



    if dry_run:
        print("Prepared to clone " + str(len(repos_to_clone)))
    else:
        run_parallels("git clone -q", repos_to_clone, dest_clones)
        #cloneAllRepos(repos_to_clone, dest_clones)