
import sys, os, shutil
sys.path.insert(0, "..")

def setup():
    print "package setup"
    shutil.rmtree("temp_output", ignore_errors=True)
    os.mkdir("temp_output")

def teardown():
    print "package teardown"
    shutil.rmtree("temp_output", ignore_errors=True)

