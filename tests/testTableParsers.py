from libms.RConnect import *
from libms.DataStructures.TableParser import *

def test_XCMSParser():
    import os
    print os.getcwd()
    lines = file("data/xcms_output.csv").readlines()
    table = XCMSFeatureParser.parse(lines)
    assert len(table.rows)==8, len(table.rows)
    assert len(table.getColNames())==11, len(table.getColNames())
    assert len(table.getColTypes())==11, len(table.getColTypes())
    # sometimes centwave delivers int values, which the parser
    # should convert to float (we put a integeger in the first row of
    # xcms_output.csv to test this !)
    assert all(type(v) == float for v in table.rtmax.values)

    table.storeCSV("temp_output/test.csv")
