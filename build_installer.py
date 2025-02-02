from version import version
import zipfile
import os
import fnmatch
import shutil
from version import version


files="""
    emzed.ico
    ms libms batches/ startup/ patched_modules/ emzed.pyw
    adducts.py
    patch_utils.py
    external_shell_patches.py
    spyder_app_patches.py
    tab.py db.py elements.py abundance.py
    config_logger.py configs.py convert_universals.py emzed_files/
    installConstants.py mass.py splash.png  userConfig.py
    version.py
    tables""".split()


def split(path):
    drive, path = os.path.splitdrive(path)
    parts = []
    while path and path != os.path.sep:
        path, basename = os.path.split(path)
        parts.insert(0, basename)

    if drive:
        parts.insert(0, drive)
    return parts

def buildZipFile(zip_name, files, exclude=[], relocate_path=".", prefixpath="."):

    zf = zipfile.ZipFile(zip_name, "w")

    relocate_path = os.path.abspath(relocate_path)
    nparts = len(split(relocate_path))

    print
    print "BUILD", zip_name

    for p in files:
        p = p.strip()
        print "    ADD", p
        full_path = os.path.join(relocate_path, p)
        assert os.path.exists(full_path), "%s does not exist" % full_path
        if os.path.isfile(full_path):
            zf.write(full_path, os.path.join(prefixpath, p))
        else:
            for dirname, _, filenames in os.walk(full_path):
                parts = split(dirname)[nparts:]
                if any(fnmatch.fnmatch(p, ex) for p in parts for ex in exclude):
                    continue
                for f in filenames:
                    if exclude is not None:
                        if any(fnmatch.fnmatch(f, ex) for ex in exclude):
                            continue

                    target_path = os.path.join(*parts)
                    file_path = os.path.join(dirname, f)
                    zip_path = os.path.join(prefixpath, os.path.join(target_path, f))

                    #print file_path, zip_path
                    zf.write(file_path, zip_path)

    zf.close()


emzed_files="emzed_files_%s.zip" % version

# todo: relocate_path mit files verwurschteldn ?
buildZipFile("installer_files/"+emzed_files, files, exclude = [".*", "*.pyc"])

buildZipFile(emzed_files, files, exclude = [".*", "*.pyc"], prefixpath="emzed")

emzedzip = "emzed_%s_for_windows.zip" % version
try:
    os.remove(emzedzip)
except:
    pass

shutil.copyfile("version.py", "installer_files/version.py")
buildZipFile(emzedzip, ["README",
                        "run_installer.py",
                        "run_installer_as_admin.py",
                        "_installer.py",
                        "License.txt",
                        emzed_files,
                        "version.py"],
            prefixpath="emzed_"+version, relocate_path="installer_files")
