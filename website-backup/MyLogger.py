import logging

"""
Basic implementation of logger
"""
class MyLogger(object):
    
    def __init__(self):
        self.doLog("My logger has started")
        
    def doLog(self, line, level=logging.DEBUG):
        #For now only print
        print line
    
    def niceLog(log, cmd_name, level="INFO"):
      """
        This method print nicely formatted command output.
      """
      PREFIX   = "%5s - " % level
      PREFIX_2 = ' ' * len(PREFIX)
      print "%s%s output:\n%s%s" % (PREFIX, cmd_name, PREFIX_2, log.replace('\n', "\n%s" % PREFIX_2))
