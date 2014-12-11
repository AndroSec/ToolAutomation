from global_vars import *
import sqlite3

class DB(object):

    def __init__(self, db_location):
        self.location = db_location
        self.db = sqlite3.connect(self.location)

    def add_new_app(self, app_metadata, commit_on_call = True):
        '''
        Adds new app with its associated metadata. 
        Set commit_on_call to false when doing massive operations.
        Below is a description of the mapping

           key     ->       column
        package          name
        name             auto_name


        TODO Add all mappings, to code and docs
        '''
        c = self.db.cursor()

        license = ""

        if 'license' in app_metadata.keys():
            license = app_metadata['license']

        current_version = ""
        if "current_version" in app_metadata.keys():
            current_version = app_metadata["current_version"]

        current_build_number = -1 # Default to -1 for no versions available
        if 'current_build_number' in app_metadata.keys():
            current_build_number = app_metadata['current_build_number']

        website = ""
        if 'website' in app_metadata.keys():
            website = app_metadata["website"]


        c.execute('''
                    INSERT INTO AppData (name, auto_name, source_code, repo_type, license, current_version, current_build_number, website, categories) values (?,?,?,?,?,?,?,?,?)
            ''', (app_metadata["package"], app_metadata["name"], app_metadata["RepoURL"], app_metadata["RepoType"], license, current_version, current_build_number, website, app_metadata["category"]))

        if(commit_on_call):
            self.db.commit()

        # Also add the versions we know about
        self.add_new_app_version(app_metadata, commit_on_call)

    def update_app(self, app_metadata, commit_on_call = True):
        '''
        Updates app with its associated metadata. 
        Set commit_on_call to false when doing massive operations.
        Below is a description of the mapping

           key     ->       column
        package          name
        name             auto_name


        TODO Add all mappings, to code and docs
        '''
        c = self.db.cursor()

        app_id = self.get_app_id(app_metadata)

        license = ""

        if 'license' in app_metadata.keys():
            license = app_metadata['license']

        current_version = ""
        if "current_version" in app_metadata.keys():
            current_version = app_metadata["current_version"]

        current_build_number = -1 # Default to -1 for no versions available
        if 'current_build_number' in app_metadata.keys():
            current_build_number = app_metadata['current_build_number']

        website = ""
        if 'website' in app_metadata.keys():
            website = app_metadata["website"]


        c.execute('''
                    UPDATE AppData SET name=:name, auto_name=:auto_name, source_code=:source_code, repo_type=:repo_type, 
                            license=:license, current_version=:current_version, current_build_number=:current_build_number, website=:website, 
                            categories=:categories WHERE appID=:app_id''', 
                            {'name': app_metadata["package"], 'auto_name': app_metadata["name"], 'source_code':app_metadata["RepoURL"], 
                            'repo_type': app_metadata["RepoType"],'license': license,'current_version': current_version, 
                            'current_build_number': current_build_number,'website': website,'categories': app_metadata["category"], 'app_id': app_id})

        if(commit_on_call):
            self.db.commit()

        # Also add the versions we know about
        self.add_new_app_version(app_metadata, commit_on_call)

    def add_new_app_version(self, app_metadata, commit_on_call = True):
        app_id = self.get_app_id(app_metadata)

        c = self.db.cursor()
        for version in app_metadata["version"].keys():
            build_number = app_metadata["version"][version]["build"]
            commit = app_metadata["version"][version]["commit"]
            
            c.execute('''
                        INSERT INTO Version (appId, version, build_number, build_commit) values (?,?,?,?)
                ''', (app_id,version,build_number,commit))

        if(commit_on_call):
            self.db.commit()

    def add_new_underpermission(self, app_metadata, version, permission, commit_on_call = True):
        app_id = self.get_app_id(app_metadata)

        permission_id = self.get_permission_id(permission)

        if(permission_id == -1):
            permission_id = self.add_permission(permission)

        version_id = self.get_version_id(app_metadata, version)

        c = self.db.cursor()

        c.execute('''
                      INSERT INTO UnderPermission values (?, ?)
            ''', (permission_id, version_id))

        if commit_on_call:
            self.db.commit()

    def add_new_overpermission(self, app_metadata, version, permission, commit_on_call = True):
        app_id = self.get_app_id(app_metadata)

        permission_id = self.get_permission_id(permission)

        if(permission_id == -1):
            permission_id = self.add_permission(permission)

        version_id = self.get_version_id(app_metadata, version)

        c = self.db.cursor()

        c.execute('''
                      INSERT INTO OverPermission values (?, ?)
            ''', (permission_id, version_id))

        if commit_on_call:
            self.db.commit()

    def add_stowaway_run(self, app_metadata, version, commit_on_call = True):
        version_id = self.get_version_id(app_metadata, version)

        if version_id == -1:
            self.add_new_app_version(app_metadata)
            version_id = self.get_version_id(app_metadata, version)

        c = self.db.cursor()

        c.execute(''' INSERT INTO StowawayRun values (?) ''', (version_id,))

        if commit_on_call:
            self.db.commit()

    def add_androrisk_run(self, app_metadata, version, commit_on_call = True):
        version_id = self.get_version_id(app_metadata, version)

        if version_id == -1:
            self.add_new_app_version(app_metadata)
            version_id = self.get_version_id(app_metadata, version)

        c = self.db.cursor()

        c.execute(''' INSERT INTO AndroriskRun values (?) ''', (version_id,))

        if commit_on_call:
            self.db.commit()

    def add_sonar_run(self, app_metadata, version, commit_on_call = True):
        version_id = self.get_version_id(app_metadata, version)

        if version_id == -1:
            self.add_new_app_version(app_metadata)
            version_id = self.get_version_id(app_metadata, version)

        c = self.db.cursor()

        c.execute(''' INSERT INTO SonarRun values (?) ''', (version_id,))

        if commit_on_call:
            self.db.commit()         

    def add_permission(self, permission):
        c = self.db.cursor()

        c.execute('''
                    INSERT INTO Permission (name) values (?)
            ''', (permission,))
        self.commit()

        return self.get_permission_id(permission)

    def get_version_id(self, app_metadata, version):
        c = self.db.cursor()

        app_id = self.get_app_id(app_metadata)

        c.execute(''' SELECT * FROM Version where appId=:appId and version=:version ''', 
                  {"appId" : app_id, "version": version})

        result = c.fetchone()

        if result != None:
            return result[0] # The first itme here is the version id
        else:
            return -1


    def get_permission_id(self, permission):
        c = self.db.cursor()

        c.execute(''' SELECT * FROM Permission where name=:name ''', {"name": permission})

        result = c.fetchone()

        if result != None:
            return result[0] # The first item here is the permission id
        else:
            return -1 # This signals that its not created yet

    def get_app_id(self, app_metadata):
        '''
        Returns the app id for the associated application metadata

        This method assumes the app was already added to the database
        '''
        c = self.db.cursor()

        c.execute('''SELECT * FROM AppData WHERE name=:name and auto_name=:auto_name''', 
            {"name" : app_metadata["package"], "auto_name" : app_metadata["name"]})

        return c.fetchone()[0] # The first item here is the appId

    def add_sonar_results(self, app_metadata, project_data, version, commit_on_call=True):
        '''
        Adds a new row into our database based on sonar results.

        project_data -  Dict with all the results for the specified project. 
                        Missing fields will be left as null in the db.
        '''
        version_id = self.get_version_id(app_metadata, version)

        if version_id == -1:
            self.add_new_app_version(app_metadata)
            version_id = self.get_version_id(app_metadata, version)


        c = self.db.cursor()

        fields_expected = ["classes", "ncloc", "functions", 
                          "duplicated_lines", "test_errors", "skipped_tests", 
                          "complexity", "class_complexity", "function_complexity", 
                          "comment_lines", "comment_lines_density", 
                          "duplicated_lines_density", "files", "directories", 
                          "file_complexity", "violations", "duplicated_blocks", 
                          "duplicated_files", "lines", "blocker_violations", 
                          "critical_violations", "major_violations", "minor_violations", 
                          "commented_out_code_lines", "line_coverage", "branch_coverage", 
                          "build_average_time_to_fix_failure", "build_longest_time_to_fix_failure", 
                          "build_average_builds_to_fix_failures", "generated_lines"]
        clean_project_data = {}
        # Check that all the fields are there, otherwise set them to null
        for field in fields_expected:
            if not field in project_data.keys():
              project_data[field] = None

        project_data["versionID"] = version_id

        # Build the query, this is bad and I feel bad :(
        columns = ', '.join(project_data.keys())
        placeholders = ':'+', :'.join(project_data.keys())
        query = 'INSERT INTO CodingStandard (%s) VALUES (%s)' % (columns, placeholders)
        

        c.execute(query, project_data)

        if commit_on_call:
            self.commit()

    def add_commit_item(self, app_metadata, commit_data, commit_on_call=True):
        c = self.db.cursor()

        app_id = self.get_app_id(app_metadata)

        c.execute(''' INSERT INTO GitHistory (appID, commit_hash, author, email, time, summary) VALUES (?,?,?,?,?,?) ''', (app_id, commit_data["commit"], commit_data["author"], commit_data["email"], int(commit_data["time"]), commit_data["summary"]))

        if commit_on_call:
            self.commit()


    def add_fuzzy_risk(self, app_metadata, version, fuzzy_risk, commit_on_call=True):
        c = self.db.cursor()

        version_id = self.get_version_id(app_metadata, version)

        if version_id == -1:
            self.add_new_app_version(app_metadata)
            version_id = self.get_version_id(app_metadata, version)

        c.execute(''' INSERT INTO Vulnerability (versionID, fuzzy_risk) values (?,?) ''', (version_id, fuzzy_risk))

        if commit_on_call:
            self.commit()

    # Add a new intent to the Intent_Version join table
    def add_new_intent_version(self, app_metadata, version, intent, commit_on_call = True):
        app_id = self.get_app_id(app_metadata)
        
        intent_id = self.get_intent_id(intent)
        
        if(intent_id == -1):
            intent_id = self.add_intent(intent)
                
        version_id = self.get_version_id(app_metadata, version)

        c = self.db.cursor()
    
        c.execute('''
            INSERT INTO Intent_Version values (?, ?)
            ''', (intent_id, version_id))
    
    # Get the database id of an intent with a given name
    def get_intent_id(self, intent, commit_on_call = True):
        c = self.db.cursor()
        
        c.execute(''' SELECT * FROM Intent where name=:name ''', {"name": intent})
        
        result = c.fetchone()
        
        if result != None:
            return result[0] # The first item here is the intent id
        else:
            return -1 # This signals that its not created yet
    
    # Add a brand new intent to the Intent table
    def add_intent(self, intent, commit_on_call = True):
        c = self.db.cursor()
        
        c.execute('''
            INSERT INTO Intent (name) values (?)
            ''', (intent,))
        self.commit()
        
        return self.get_intent_id(intent)




    def commit(self):
        self.db.commit()

    def create_db(self, commit_on_call = True):
        c = self.db.cursor()
        # SQL commands to create all the tables that make up our db
        # Should find a better place for these
        c.execute('''
                    CREATE TABLE AppData (
                      appId INTEGER PRIMARY KEY AUTOINCREMENT,
                      name varchar(40) NOT NULL,
                      description text,
                      categories text,
                      license text,
                      auto_name text,
                      provides text,
                      website text,
                      source_code text,
                      issue_tracker text,
                      donate text,
                      flattrid integer,
                      bitcoin text,
                      litecoin text,
                      summary varchar(50),
                      maintainer_notes text,
                      repo_type text,
                      antifeatures text,
                      disabled boolean,
                      requires_root boolean,
                      archive_policy text,
                      update_check_mode text,
                      vercode_operation text,
                      update_check_ignore text,
                      auto_update_mode text,
                      current_version text,
                      current_build_number INTEGER,
                      no_source_since text
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE Intent (
                      intentID INTEGER PRIMARY KEY AUTOINCREMENT,
                      name text
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE Intent_Version (
                      intentID INTEGER,
                      versionID int NOT NULL,
                      PRIMARY KEY(intentID, versionID)
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE OverPermission (
                      permissionID int NOT NULL,
                      versionID int NOT NULL,
                      PRIMARY KEY(permissionID, versionID)
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE Permission (
                      permissionID INTEGER PRIMARY KEY AUTOINCREMENT,
                      name text NOT NULL
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE UnderPermission (
                      permissionID int NOT NULL,
                      versionID int NOT NULL,
                      PRIMARY KEY(permissionID, versionID)
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE Version (
                      versionID INTEGER PRIMARY KEY AUTOINCREMENT,
                      appID NOT NULL,
                      version text,
                      build_number INTEGER,
                      build_commit text
                    )
            ''')

        c.execute('''
                    CREATE TABLE Vulnerability (
                      versionID int NOT NULL,
                      fuzzy_risk real,
                      PRIMARY KEY(versionID, fuzzy_risk)
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE CodingStandard (
                      versionID int NOT NULL PRIMARY KEY,
                      classes int,
                      ncloc int,
                      functions int,
                      duplicated_lines int,
                      test_errors int,
                      skipped_tests int,
                      complexity int,
                      class_complexity real,
                      function_complexity real,
                      comment_lines int,
                      comment_lines_density real,
                      duplicated_lines_density real,
                      files int,
                      directories int,
                      file_complexity real,
                      violations int,
                      duplicated_blocks int,
                      duplicated_files int,
                      lines int,
                      blocker_violations int,
                      critical_violations int,
                      major_violations int,
                      minor_violations int,
                      commented_out_code_lines int,
                      line_coverage real,
                      branch_coverage real,
                      build_average_time_to_fix_failure real,
                      build_longest_time_to_fix_failure real,
                      build_average_builds_to_fix_failures int,
                      generated_lines int
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE GitHistory (
                      commitID INTEGER PRIMARY KEY AUTOINCREMENT,
                      appID INTEGER,
                      commit_hash text,
                      author text,
                      email text,
                      time int,
                      summary text
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE StowawayRun (
                      versionID int NOT NULL PRIMARY KEY
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE AndroriskRun (
                      versionID int NOT NULL PRIMARY KEY
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE SonarRun (
                      versionID int NOT NULL PRIMARY KEY
                    )
            ''')

        c.execute(''' 
                    CREATE INDEX GitAppID ON GitHistory (appID)
            ''')

        if(commit_on_call):
            self.db.commit()


if __name__ == '__main__':
    DB("db.sqlite3").create_db()