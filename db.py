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
                    INSERT INTO AppData (name, auto_name, source_code, repo_type, license, current_version, current_build_number, website) values (?,?,?,?,?,?,?,?)
            ''', (app_metadata["package"], app_metadata["name"], app_metadata["RepoURL"], app_metadata["RepoType"], license, current_version, current_build_number, website))

        if(commit_on_call):
            self.db.commit()

        # Also add the versions we know about
        self.add_new_app_version(app_metadata, commit_on_call)

    def add_new_app_version(self, app_metadata, commit_on_call = True):
        app_id = self.get_app_id(app_metadata)

        c = self.db.cursor()
        for version in app_metadata["version"].keys():
            build_number = app_metadata["version"][version]
            
            c.execute('''
                        INSERT INTO Version (appId, version, build_number) values (?,?,?)
                ''', (app_id,version,build_number))

        if(commit_on_call):
            self.db.commit()

    def get_app_id(self, app_metadata):
        c = self.db.cursor()

        c.execute('''SELECT * FROM AppData WHERE name=:name and auto_name=:auto_name''', 
            {"name" : app_metadata["package"], "auto_name" : app_metadata["name"]})

        return c.fetchone()[0] # The first item here is the appId

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
                    CREATE TABLE Bug (
                      bugID int PRIMARY KEY NOT NULL,
                      versionID int NOT NULL,
                      line_number int,
                      line_content text,
                      tool_found_in text,
                      file_located text
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE Intent (
                      intentID int PRIMARY KEY NOT NULL,
                      name text
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE Intent_Version (
                      intentID int NOT NULL,
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
                      build_number INTEGER
                    )
            ''')

        c.execute('''
                    CREATE TABLE Vulnerability (
                      vulnerabilityID int PRIMARY KEY NOT NULL,
                      versionID int NOT NULL,
                      fuzzy_risk int
                    )
            ''')

        c.execute(''' 
                    CREATE TABLE coding_standard (
                      coding_standardID int PRIMARY KEY NOT NULL,
                      versionID int NOT NULL,
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
        if(commit_on_call):
            self.db.commit()


if __name__ == '__main__':
    DB("db.sqlite3").create_db()