#!/usr/bin/python
from MyLogger import MyLogger
from BackupUtils import BackupUtils
from SFtpHandler import SFtpHandler
#from urllib import quote
#from urllib import quote_plus

class FtpHandler(object):
    
    def __init__(self, user, password, host, port, remote_dir, is_ftps, backup_folder_mirror, backup_folder_diff, backup_folder_archive, logger = None):
        self.logger = logger or MyLogger()
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.remote_dir = remote_dir
        self.is_ftps = is_ftps
        self.backup_folder_mirror = backup_folder_mirror
        self.backup_folder_diff = backup_folder_diff
        self.backup_folder_archive = backup_folder_archive
        self.urllib = __import__('urllib')
        self.paramiko = None
        self.stat = None
        self.BackupUtils = BackupUtils()
        self.sftpHandler = None
        self.ftputil = None
        if self.is_ftps:
            self.paramiko = __import__('paramiko')
            self.stat = __import__('stat')
            self.os = __import__('os')
            self.sftpHandler = SFtpHandler(logger)
        else:
            self.ftputil = __import__('ftputil')
            
    """
    Basic function to be called to do mirroring
    """    
    def doMirror(self):
        remote_url = "ftp://%s:%s@%s:%s/%s" % ( self.urllib.quote_plus(self.user)
                                            , self.urllib.quote_plus(self.password)
                                            , self.urllib.quote_plus(self.host)
                                            , self.port
                                            , self.urllib.quote(self.remote_dir)
                                            )
        # Force SSL layer for secure FTP
        secure_options = ''
        if self.is_ftps:
            secure_options = 'set ftp:ssl-force true && set ftp:ssl-protect-data true && '
        # Get a copy of the remote directory
        ftp_backup = """lftp -c '%sset ftp:list-options -a && open -e "mirror -e --verbose=3 --parallel=2 . %s" %s'""" % (secure_options, self.backup_folder_mirror, remote_url)
        self.logger.doLog("Going to mirror with command: %s " % ftp_backup)
        #print self.getstatusoutput(ftp_backup)
        if self.is_ftps:
            #do ftps things
            self.doMirrorSFtp()
        else:
            #do non ftps things
            self.doMirrorFtp()
        #finishing do mirror
    
    """
    Actual Ftp mirroring
    """     
    def doMirrorFtp(self):
        if int(self.port) != 21:
            self.logger.doLog("For now only port 21")
        else:
            with self.ftputil.FTPHost(self.host, self.user, self.password) as host:
                print host.curdir
                for root, dirs, files in host.walk(self.remote_dir):
                    localDirectoryRoot = root.replace(self.remote_dir, self.backup_folder_mirror)
                    for directory in dirs:
                        if directory != ".svn":
                            self.BackupUtils.createDirectory(localDirectoryRoot + "/" + directory)
                    for remoteFile in files:
                        if remoteFile not in ['.ftpquota', '.DS_Store']:
                            if not remoteFile.startswith("log-"):
                                try:
                                    self.logger.doLog("Retrieving file from %s to %s" % (root + "/" + remoteFile, localDirectoryRoot + "/" + remoteFile))
                                    host.download(root + "/" + remoteFile, localDirectoryRoot + "/" + remoteFile)
                                except Exception as fileE:
                                    print fileE
                            else:
                                self.logger.doLog("Log file %s will not be downloaded" % remoteFile)
                print " =============================== "
    
    """
    Actual SFtp mirroring
    """    
    def doMirrorSFtp(self):
        #doing stuff
        transport = self.paramiko.Transport((self.host, int(self.port)))
        transport.connect(username = self.user, password = self.password)
        sftp = self.paramiko.SFTPClient.from_transport(transport)
        print self.remote_dir
        #print sftp.listdir(self.remote_dir)
        self.sftpHandler.sftpWalk(sftp, self.remote_dir, self.remote_dir, self.backup_folder_mirror)
        #Do full backup
        sftp.close()
        transport.close()
    
    def doDiff(self):
        self.BackupUtils.doRdiffBackupCall(self.backup_folder_mirror, self.backup_folder_diff)
        
    def retriveMonthlyArchive(self, currentYear, currentMonth):
        return self.BackupUtils.returnFormatedMonthlyArchive(self.backup_folder_archive, currentYear, currentMonth)
        
    def doBackup(self):
        # Generate monthly archive name
        current_year, current_month = self.BackupUtils.returnBasicDateInfo()
        monthly_archive = self.retriveMonthlyArchive(current_year, current_month)
        print monthly_archive
        snapshot_date = "%04d-%02d-01" % (current_year, current_month)
        self.BackupUtils.doBackup(monthly_archive, snapshot_date, self.backup_folder_diff, self.backup_folder_archive)
