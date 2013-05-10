
import os, glob, subprocess, sys, re

import userConfig


from ..intern_utils import TemporaryDirectoryWithBackup

class RExecutor(object):

    # RExecutor is a Singleton:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RExecutor, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if sys.platform == "win32":
            self.rHome = RExecutor.findRHome()
            rExe  = RExecutor.findRExe(self.rHome)
            import win32api
            self.rExe = win32api.GetShortPathName(rExe)
        else:
            self.rExe = "R"

    @staticmethod
    def findRHome():
        assert sys.platform == "win32"
        import _winreg
        pathToR = None
        for finder in [
                       lambda : RExecutor.path_from(_winreg.HKEY_CURRENT_USER),
                       lambda : RExecutor.path_from(_winreg.HKEY_LOCAL_MACHINE),
                       lambda : os.environ.get("R_HOME"),
                       RExecutor.parse_path_variable,
                       ]:
            try:
                pathToR = finder()
                if pathToR != None:
                    break
            except (KeyError, WindowsError):
                pass
        if pathToR is None:
            raise Exception("install dir of R not found, neither in registry, nor is R_HOME set.")
        return pathToR

    @staticmethod
    def findRExe(rHome):

        found = glob.glob("%s/bin/R.exe" % rHome)
        if found:
            return found[0]
        else:
            found = glob.glob("%s/bin/*/R.exe" % rHome)
            if not found:
                raise Exception("could not find R.exe")
            if len(found)>1:
                print "found multiple R.exe !"
                for p in found:
                    print "    ", p
                print "I will take the first one !"

            return found[0]

    @staticmethod
    def parse_path_variable():
        for path in os.environ.get("PATH","").split(os.pathsep):
            # windows
            if os.path.exists(os.path.join(path, "R.exe")):
                print "Found R at", path
                return path
            # non windows:
            test = os.path.join(path, "R")
            if os.path.exists(test) and not os.path.isdir(test):
                return test
        return None

    @staticmethod
    def path_from(regsection):
        assert sys.platform == "win32"
        import _winreg
        key = _winreg.OpenKey(regsection, "Software\\R-core\\R")
        return _winreg.QueryValueEx(key, "InstallPath")[0]

    def run_test(self):
        status = self.run_command("q(status=123);")
        assert status == 123, repr(status)

    def run_script(self, path):

        with open(path, "r") as fp:
            # do not know why diff platforms behave differntly:
            if sys.platform == "win32":
                proc = subprocess.Popen(['%s' % self.rExe, '--vanilla', '--silent'],
                                        stdin = fp, stdout = sys.__stdout__,
                                        bufsize=0, shell=True)
            else:
                proc = subprocess.Popen(['%s --vanilla --silent' % self.rExe],
                                        stdin = fp, stdout = sys.__stdout__,
                                        bufsize=0, shell=True)
            out, err = proc.communicate()
            if err is not None:
                print err

        return proc.returncode

    def get_r_version(self):
        if sys.platform == "win32":
            proc = subprocess.Popen(['%s' % self.rExe, '--version', '--vanilla', '--silent'],
                                    stderr=subprocess.PIPE,
                                    bufsize=0, shell=True)
            out, err = proc.communicate()
	    answer = err
        else:
            proc = subprocess.Popen(['%s --version' % self.rExe],
                                    stdout = subprocess.PIPE,
                                    bufsize=0, shell=True)
            out, err = proc.communicate()
	    answer = out
        match = re.search("version\s+(\d+\.\d+\.\d+)", answer)
        if not match:
	    return None
        return match.groups(0)[0]


    def run_command(self, command, dir_=None):

        def run(dir_, command):
            fp = file(os.path.join(dir_, "script.R"), "w")
            print >> fp, command
            fp.close()
            fp2 = file(os.path.join(dir_, "R_exe"), "w")
            print >> fp2, os.path.abspath(self.rExe)
            fp2.close()
            return self.run_script(fp.name)

        if dir_ is not None:
            return run(dir_, command)

        else:
            with TemporaryDirectoryWithBackup() as dir_:
                return run(dir_, command)

r_version = RExecutor().get_r_version()
userConfig.setRVersion(r_version)

r_libs_folder = userConfig.getRLibsFolder()
print "SET R_LIBS ENVIRONMENT VARIABLE TO", r_libs_folder
if r_libs_folder is not None:
    r_libs=[path for path in os.environ.get("R_LIBS", "").split(":") if path]
    if r_libs_folder not in r_libs:
        if not os.path.exists(r_libs_folder):
            os.makedirs(r_libs_folder)
        r_libs.insert(0, r_libs_folder)
        os.environ["R_LIBS"] = ":".join(r_libs)
