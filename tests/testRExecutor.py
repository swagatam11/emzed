from libms.RConnect.RExecutor import *
from libms.RConnect.XCMSConnector import *


def testOne():
    RExecutor().run_test()
    RExecutor.parse_path_variable()

def testTwo():
    installXcmsIfNeeded()



