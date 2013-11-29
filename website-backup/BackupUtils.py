#! /usr/bin/python

from os.path  import abspath, exists, isfile, sep, split, join, basename
from os       import makedirs, mkdir, remove, system, rmdir, name, devnull, errno, pathsep, environ, access, X_OK
from MyLogger import MyLogger
import sys
import subprocess
import datetime
import time
import shutil
import tarfile

class BackupUtils(object):
    
    def __init__(self, logger = None):
        self.logger = logger or MyLogger()
        self.pythonMinVersion = (2, 4)
        self.checkedCommands = []
        self.required_commands = { 'FTP'          : 'lftp'
                , 'FTPS'         : 'lftp'
                , 'SSH'          : ['rsync', 'ssh']
                , 'MYSQLDUMP'    : 'mysqldump'
                , 'MYSQLDUMP+SSH': 'ssh' # TODO: How to check that 'mysqldump' is present on the distant machine ???
                }
        self.default_parameters = { 'FTP'          : {'port': 21}
                         , 'FTPS'         : {'port': 21}
                         , 'SSH'          : {'port': 22}
                         , 'MYSQLDUMP'    : {'db_port': 3306}
                         , 'MYSQLDUMP+SSH': {'port': 22, 'db_port': 3306}
                         }
                
    def returnBasicDateInfo(self):
        today_items   = datetime.date.today().timetuple()
        current_year  = today_items[0]
        current_month = today_items[1]
        print today_items
        return (current_year, current_month)
        
    def returnFormatedMonthlyArchive(self, path, currentYear, currentMonth):
        aux = abspath("%s%s%04d-%02d.tar.bz2" % (path, "/", currentYear, currentMonth))
        return aux
    
    """
    This will return the basic structure of the directories
    """
    def returnDirectoryList(self, backup_dir, local_dir):
        main_folder = abspath(sep.join([backup_dir, local_dir]))
        backup_folders = {
            'main'    : main_folder
          , 'archives': abspath(sep.join([main_folder, 'monthly-archives']))  # Contain monthly archives
          , 'diff'    : abspath(sep.join([main_folder, 'rdiff-repository']))  # Contain current month diferential backup
          , 'mirror'  : abspath(sep.join([main_folder, 'mirror']))            # Contain a mirror of the remote folder
          }
        return backup_folders
    
    
    def checkRootDirectory(self, root_backup_dir):
        #Check that backup dir is a directory in the os
        if not exists(abspath(root_backup_dir)):
            self.logger.doLog("FATAL - Main backup folder '%s' does't exist !" % backup_dir)
            sys.exit(1)
        else:
            self.logger.doLog("Backup Root Directory OK")
        
    """
    This function check all the necesary directories
    """
    def checkDirectories(self, backup_dir, local_dir, dry_run = False):
        # Create backup folder structure if needed
        backup_folders = self.returnDirectoryList(backup_dir, local_dir)
        for (folder_type, folder_path) in backup_folders.items():
            self.createDirectory(folder_path, dry_run)

    """
    Creating directory.
    1 - Check that not exists
    2 - if not dry run create it
    """
    def createDirectory(self, folder_path, dry_run = False):
        if not exists(folder_path):
            if not dry_run:
                makedirs(folder_path)
                self.logger.doLog(" INFO - '%s' folder created" % folder_path)
        
    """
    Checking python version
    """
    def checkPythonVersion(self):
        # Check python version
        if not hasattr(sys, 'version_info') or tuple(sys.version_info[:2]) < self.pythonMinVersion:
            self.logger.doLog("FATAL - This script require at least python %s" % '.'.join(self.pythonMinVersion))
            sys.exit(1)
        else:
            self.logger.doLog("Python Version OK")
        
    """
    Checking operative system
    """
    def checkOperativeSystem(self):
        # Check that we are running this script on a UNIX system
        if name != 'posix':
            self.logger.doLog("FATAL - This script doesn't support systems other than POSIX's")
            sys.exit(1)
        else:
            self.logger.doLog("Operative system OK")
    
    """
    This method check that the command list are available on the system.
    This method accept as parameter a string (to check only one command) 
    or a list/tuple (to check several commands)
    """
    def checkCommands(self, command_list=None):
        #Checking that you can do the commands
        if type(command_list) == type('a'):
            command_list = [command_list]
        if command_list != None and len(command_list) > 0:
            # Check that "which" command exist first
            command_list = ["which"] + command_list
            for command in command_list:
                # It is not required to check a found command twice
                if command not in self.checkedCommands:
                    if self.which(command) != None:
                        self.logger.doLog("Command found - %s " % command)
                        self.checkedCommands.append(command)
                    else:
                        self.logger.doLog("FATAL - '%s' command not found on this system: it is required by this script !" % command)
                        sys.exit(1)

    """
    Function to show is the command exists in the OS
    This function came from: http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    """
    def which(self, program):
        def is_exe(fpath):
            return isfile(fpath) and access(fpath, X_OK)

        fpath, fname = split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in environ["PATH"].split(pathsep):
                path = path.strip('"')
                exe_file = join(path, program)
                if is_exe(exe_file):
                    return exe_file
        return None
    
    """
    Parsing backup definition and adding defaults behavior
    """
    def parseBackupDefinition(self, definitionDictionary):
        # Normalize backup type
        backup_type = definitionDictionary['type'].lower().strip()
        if backup_type.find('ftps') != -1:
            backup_type = 'FTPS'
        elif backup_type.find('ftp') != -1:
            backup_type = 'FTP'
        elif backup_type == 'ssh':
            backup_type = 'SSH'
        elif backup_type.find('mysql') != -1:
            if backup_type.find('ssh') != -1:
                backup_type = 'MYSQLDUMP+SSH'
            else:
                backup_type = 'MYSQLDUMP'
        else:
            self.logger.doLog("ERROR - Backup type '%s' for '%s' is unrecognized: ignore it." % (definitionDictionary['type'], title))
            # Reset backup type
            definitionDictionary['type'] = ''
        definitionDictionary['type'] = backup_type
            # Check if pexpect is required
        if backup_type.find('SSH') != -1:
            is_pexpect_required = True
        # Check requirements
        self.checkCommands(self.required_commands[backup_type])
        # Set default parameters if missing
        default_config = self.default_parameters.get(backup_type, {}).copy()
        default_config.update(definitionDictionary)
        definitionDictionary.update(default_config)
        return definitionDictionary
    
    
    def doRdiffBackupCall(self, backup_folder_mirror, backup_folder_diff):
        rdiff_cmd = """rdiff-backup "%s" "%s" """ % (backup_folder_mirror, backup_folder_diff)
        # Run the actual backup.
        rdiff_backup = subprocess.Popen(rdiff_cmd, shell=True)
        rdiff_backup.wait()     # Wait for the backup to finish.
        
    def doBackup(self, monthly_archive, snapshot_date, backup_folder_diff, backup_folder_archive, dry_run = False):
        # If month started, make a bzip2 archive
        if not exists(monthly_archive):
            self.logger.doLog(" INFO - Generate archive of previous month (= %s 00:00 snapshot)" % snapshot_date)
            tmp_archives_path = abspath(backup_folder_archive + sep + "tmp")
            if exists(tmp_archives_path):
                shutil.rmtree(tmp_archives_path)
                self.logger.doLog(" INFO - Previous temporary folder '%s' removed" % tmp_archives_path)
            if not dry_run:
                mkdir(tmp_archives_path)
            self.logger.doLog(" INFO - Temporary folder '%s' created" % tmp_archives_path)
            rdiff_cmd = """rdiff-backup -r "%s" "%s" "%s" """ % ( snapshot_date
                                                          , backup_folder_diff
                                                          , tmp_archives_path
                                                          )
            rdiff_backup = subprocess.Popen(rdiff_cmd, shell=True)
            rdiff_backup.wait()     # Wait for the backup to finish.
            #run(rdiff_cmd, verbose, dry_run)
            self.make_tarfile(monthly_archive, tmp_archives_path)
            #run("tar c -C %s ./ | bzip2 > %s" % (tmp_archives_path, monthly_archive), verbose, dry_run)
            #Have to do compresion
            # Delete the tmp folder
            shutil.rmtree(tmp_archives_path)
            self.logger.doLog(" INFO - Removing temporary folder '%s'" % tmp_archives_path)
        else:
            self.logger.doLog(" INFO - No need to generate archive: previous month already archived")
            
        # Keep last 32 increments (31 days = 1 month + 1 day)
        self.logger.doLog(" INFO - Remove increments older than 32 days")
        rdiff_cmd = """rdiff-backup --force --remove-older-than 32B "%s" """ % backup_folder_diff
        rdiff_backup = subprocess.Popen(rdiff_cmd, shell=True)
        rdiff_backup.wait()     # Wait for the backup to finish.
        
     
 
    def make_tarfile(self, output_filename, source_dir):
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=basename(source_dir))           
    
    def getstatusoutput(cmd): 
        """Return (status, output) of executing cmd in a shell."""
        """This new implementation should work on all platforms."""
        import subprocess
        pipe = subprocess.Popen(cmd, shell=True, universal_newlines=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = str.join("", pipe.stdout.readlines()) 
        sts = pipe.wait()
        if sts is None:
            sts = 0
        return sts, output
    
