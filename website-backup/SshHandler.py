#!/usr/bin/python
from MyLogger import MyLogger
from BackupUtils import BackupUtils
from SFtpHandler import SFtpHandler

class SshHandler(object):
    
    def __init__(self, user, password, host, port, remote_dir, backup_folder_mirror, backup_folder_diff, backup_folder_archive, logger = None):
        self.logger = logger or MyLogger()
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.remote_dir = remote_dir
        self.backup_folder_mirror = backup_folder_mirror
        self.backup_folder_diff = backup_folder_diff
        self.backup_folder_archive = backup_folder_archive
        self.paramiko = None
        self.stat = None
        self.BackupUtils = BackupUtils()
        self.paramiko = __import__('paramiko')
        self.sftpHandler = SFtpHandler(logger)
        #self.pexpect = __import__('pexpect')

    """
    Basic function to be called to do mirroring
    """    
    def doMirror(self):
        s = self.paramiko.SSHClient()
        s.set_missing_host_key_policy(self.paramiko.AutoAddPolicy())
        s.connect(self.host,self.port,username=self.user,password=self.password,timeout=4)
        sftp = s.open_sftp()
        self.sftpHandler.sftpWalk(sftp, self.remote_dir, self.remote_dir, self.backup_folder_mirror)
        sftp.close()
        s.close()
        
    def doDiff(self):
        self.BackupUtils.doRdiffBackupCall(self.backup_folder_mirror, self.backup_folder_diff)
        
    def doBackup(self):
        # Generate monthly archive name
        current_year, current_month = self.BackupUtils.returnBasicDateInfo()
        monthly_archive = self.retriveMonthlyArchive(current_year, current_month)
        print monthly_archive
        snapshot_date = "%04d-%02d-01" % (current_year, current_month)
        self.BackupUtils.doBackup(monthly_archive, snapshot_date, self.backup_folder_diff, self.backup_folder_archive)

    def retriveMonthlyArchive(self, currentYear, currentMonth):
        return self.BackupUtils.returnFormatedMonthlyArchive(self.backup_folder_archive, currentYear, currentMonth)
