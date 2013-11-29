#! /usr/bin/python
from BackupUtils import BackupUtils
from MyLogger import MyLogger
import logging
from FtpHandler import FtpHandler
from SshHandler import SshHandler

root_backup_dir = '/home/rodrigo/proyectos/backups'
backup_list = [
### FTP examples
#  { 'title'     : 'RCA FTP backup'
#  , 'type'      : 'FTPs'
#  , 'host'      : '192.168.1.123'
#  , 'remote_dir': '/home/proyectos/rca'
#  , 'user'      : 'root'
#  , 'password'  : 'inswitch'
#  , 'local_dir' : 'rca'
#  , 'port'      : '22'
#  },
#  { 'title'     : 'Simple FTP backup with exotic port'
#  , 'type'      : 'FTP'
#  , 'host'      : 'ftp2.website.com'
#  , 'port'      : '2100'  # Example with exotic FTP port
#  , 'remote_dir': '/kevin/htdocs'
#  , 'user'      : '<user>'
#  , 'password'  : '<password>'
#  , 'local_dir' : 'kevin'
#  },

### FTPs examples
#  { 'title'     : 'Simple FTPs (aka FTP over SSL) backup'
#  , 'type'      : 'FTPs'
#  , 'host'      : 'ftp.example.com'
#  , 'remote_dir': '/kevin/htdocs'
#  , 'user'      : '<user>'
#  , 'password'  : '<password>'
#  , 'local_dir' : 'ftps-test'
#  },

### SSH examples
#  { 'title'     : 'Simple SSH backup with password and exotic port'
#  , 'type'      : 'ssh'
#  , 'host'      : 'test.com'
#  , 'port'      : 2200
#  , 'remote_dir': '~/public_html'
#  , 'user'      : '<user>'
#  , 'password'  : '<password>'
#  , 'local_dir' : 'ssh+password-test'
#  },
#  { 'title'     : 'Rca SSH backup'
#  , 'type'      : 'SSH'
#  , 'host'      : '192.168.1.123'
#  , 'remote_dir': '/home/proyectos/rca'
#  , 'user'      : 'root'
#  , 'password'  : 'inswitch'
#  , 'local_dir' : 'rca-ssh'
#  },

### MySQL examples
#  { 'title'     : 'MySQL dump over SSH of a particular database with password'
#  , 'type'      : 'mysqldump+ssh'
#  , 'host'      : 'example.com'
#  , 'user'      : '<user>'
#  , 'password'  : '<ssh-password>'
#  , 'db_user'   : 'mysqlxxxx'
#  , 'db_pass'   : '<mysql-password>'
#  , 'db_host'   : 'localhost'
#  , 'db_name'   : 'mysqlxxxx'
#  , 'local_dir' : 'mysqldump+ssh-test'
#  },
#  { 'title'     : 'MySQL dump over password-less SSH of all databases'
#  , 'type'      : 'mysqldump+ssh'
#  , 'host'      : 'example.com'
#  , 'user'      : '<user>'
#  , 'db_user'   : 'mysqlxxxx'
#  , 'db_pass'   : '<mysql-password>'
#  , 'db_host'   : 'localhost'
#  , 'local_dir' : 'mysqldump+ssh-test'
#  },
#  { 'title'     : 'Direct MySQL dump with exotic MySQL server port'
#  , 'type'      : 'mysqldump'
#  , 'db_user'   : 'root'
#  , 'db_pass'   : '<mysql-password>'
#  , 'db_host'   : 'sql.machine.com'
#  , 'db_port'   : 9999
#  , 'local_dir' : 'mysqldump-test'
#  },
]

if __name__ == "__main__":
    logger = MyLogger()
    logger.doLog("starting!!")
    backupUtils = BackupUtils(logger)
    backupUtils.checkPythonVersion()
    backupUtils.checkOperativeSystem()
    backupUtils.checkRootDirectory(root_backup_dir)
    backupUtils.checkCommands(['rdiff-backup', 'rm', 'tar', 'bzip2'])
    backupObjectsList = []
    # Doing this right now is nicer to the user: thanks to this he doesn't need to wait the end of the (X)th backup to get the error about the (X+1)th
    for backup in backup_list:
        # Check datas and requirement for each backup
        backup = backupUtils.parseBackupDefinition(backup)
        backup_folders = backupUtils.returnDirectoryList(root_backup_dir, backup['local_dir'])
        backupUtils.checkDirectories(root_backup_dir, backup['local_dir'])
        if backup['type'] == '':
            continue
        if backup['type'] in ['FTP', 'FTPS']:
            is_ftps = False
            if backup['type'] == "FTPS":
                is_ftps = True
            ftp = FtpHandler(backup['user'], backup['password'], backup['host'], backup['port'], backup['remote_dir'], is_ftps, backup_folders['mirror'], backup_folders['diff'], backup_folders['archives'], logger)
            backupObjectsList.append(ftp)
        elif backup['type'] in ['SSH']:
            ssh = SshHandler(backup['user'], backup['password'], backup['host'], backup['port'], backup['remote_dir'], backup_folders['mirror'], backup_folders['diff'], backup_folders['archives'], logger)
            backupObjectsList.append(ssh)
            print 'ssh thing!'
    
    for backupObject in backupObjectsList:
        backupObject.doMirror()
        backupObject.doDiff()
        backupObject.doBackup()
        
        
        
