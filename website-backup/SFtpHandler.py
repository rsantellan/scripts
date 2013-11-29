#!/usr/bin/python

from MyLogger import MyLogger
from BackupUtils import BackupUtils


class SFtpHandler(object):

    def __init__(self, logger=None):
        self.logger = logger or MyLogger()
        self.paramiko = __import__('paramiko')
        self.stat = __import__('stat')
        self.os = __import__('os')
        self.BackupUtils = BackupUtils()

    """
    Sftp Directory transversal
    """
    def sftpWalk(self, sftp, remotepath, remote_dir, backup_folder_mirror, files=[], folders=[]):
        for f in sftp.listdir_attr(remotepath):
            fullFilePath = remotepath + "/" + f.filename
            localFilePath = fullFilePath.replace(remote_dir,
                backup_folder_mirror)
            if self.stat.S_ISDIR(f.st_mode):
                if f.filename != ".svn":
                    self.BackupUtils.createDirectory(localFilePath)
                    folders.append(fullFilePath)
                    self.sftpWalk(sftp, fullFilePath, remote_dir,
                        backup_folder_mirror, files, folders)
            else:
                files.append(fullFilePath)
                self.logger.doLog("Retrieving file from %s to %s" %
                (fullFilePath, localFilePath))
                sftp.get(fullFilePath, localFilePath)
        return (remotepath, folders, files)
