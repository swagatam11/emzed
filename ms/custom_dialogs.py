#encoding:utf-8

def _normalize_network_paths(*paths):
    import sys
    if sys.platform == "win32":
        # sometimes probs with network paths like "//gram/omics/....":
        return [ p.replace("/", "\\") for p in paths ]
    return paths

def __fileDialog(startAt=None, onlyDirectories=False, anyFile=False,
                 multipleFiles=True, extensions=None, caption=None):

    import guidata
    from PyQt4.QtGui import QFileDialog
    from PyQt4.QtCore import Qt

    import os

    if startAt is None:
        startAt = os.getcwd()

    app = guidata.qapplication()
    if caption is not None:
        di=QFileDialog(directory=startAt, caption=caption)
    else:
        di=QFileDialog(directory=startAt)

    if extensions is not None:
        filter_ = "(%s)" % " ".join( "*."+e for e in extensions)
        di.setNameFilter(filter_)


    if onlyDirectories:
        di.setFileMode(QFileDialog.DirectoryOnly)
    elif multipleFiles:
        di.setFileMode(QFileDialog.ExistingFiles)
    elif anyFile:
        di.setFileMode(QFileDialog.AnyFile)
    else:
        di.setFileMode(QFileDialog.ExistingFile)

    di.setWindowFlags(Qt.Window)
    di.activateWindow()
    di.raise_()
    if di.exec_():
        files= di.selectedFiles()
        res = [ str(f.toLatin1()) for f in files]
        res = _normalize_network_paths(*res)
        return res
    return [None]


def askForDirectory(startAt=None):
    """
    asks for a single directory.

    you can provide a startup directory with parameter startAt.

    returns the path to the selected directory as a string,
    or None if the user aborts the dialog.
    """
    return __fileDialog(startAt, onlyDirectories=True)[0]

def askForSave(startAt=None, extensions=None):

    """
          asks for a single file, which needs not to exist.

          you can provide a startup directory with parameter startAt.
          you can restrict the files by providing a list of extensions.
          eg::

              askForSave(extensions=["csv"])

          or::

              askForSave(extensions=["mzXML", "mxData"])

          returns the path of the selected file as a string,
          or None if the user aborts the dialog.
    """
    return __fileDialog(startAt, anyFile=True, multipleFiles=False,
                                 extensions=extensions, caption="Save As")[0]

def askForSingleFile(startAt=None, extensions=None):

    """
          asks for a single file.

          you can provide a startup directory with parameter startAt.
          you can restrict the files to select by providing a list
          of extensions.
          eg::

             askForSingleFile(extensions=["csv"])

          or::

              askForSingleFile(extensions=["mzXML", "mxData"])

          returns the path of the selected file as a string,
          or None if the user aborts the dialog.
    """
    return __fileDialog(startAt, multipleFiles=False, extensions=extensions)[0]

def askForMultipleFiles(startAt=None, extensions=None):
    """
          asks for a single or multiple files.

          you can provide a startup directory with parameter startAt.
          you can restrict the files to select by providing a list
          of extensions.
          eg::

              askForSingleFile(extensions=["csv"])

          or::

              askForSingleFile(extensions=["mzXML", "mxData"])

          returns the paths of the selected files as a list of strings,
          or None if the user aborts the dialog.
    """
    return __fileDialog(startAt, multipleFiles=True, extensions=extensions)


def chooseConfig(configs, params):

    from libms.gui.ConfigChooseDialog import ConfigChooseDialog
    import guidata

    app = guidata.qapplication()
    dlg = ConfigChooseDialog(configs, params)
    dlg.activateWindow()
    dlg.raise_()
    dlg.exec_()

    return dlg.result

if __name__ == "__main__":

    print askForSave(extensions=["py", "pyc"])
