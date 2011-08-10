# -*- coding: utf-8 -*-
#
# Copyright © 2011 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
qthelpers
---------

The ``guiqwt.qthelpers`` module provides helper functions for developing 
easily Qt-based graphical user interfaces with guiqwt.

Ready-to-use open/save dialogs:
    :py:data:`guiqwt.qthelpers.exec_image_save_dialog`
        Executes an image save dialog box (QFileDialog.getSaveFileName)
    :py:data:`guiqwt.qthelpers.exec_image_open_dialog`
        Executes an image open dialog box (QFileDialog.getOpenFileName)
    :py:data:`guiqwt.qthelpers.exec_images_open_dialog`
        Executes an image*s* open dialog box (QFileDialog.getOpenFileNames)   

Reference
~~~~~~~~~

.. autofunction:: exec_image_save_dialog
.. autofunction:: exec_image_open_dialog
.. autofunction:: exec_images_open_dialog
"""

import sys, os.path as osp
from guidata.qt.QtGui import QFileDialog, QMessageBox

# Local imports
from guiqwt.config import _
from guiqwt.io import (IMAGE_SAVE_FILTERS, IMAGE_LOAD_FILTERS,
                       array_to_imagefile, imagefile_to_array)


#===============================================================================
# Ready-to-use open/save dialogs
#===============================================================================
def exec_image_save_dialog(data, parent, basedir='', app_name=None):
    """
    Executes an image save dialog box (QFileDialog.getSaveFileName)
        * data: image pixel array data
        * parent: parent widget (None means no parent)
        * basedir: base directory ('' means current directory)
        * app_name (opt.): application name (used as a title for an eventual 
          error message box in case something goes wrong when saving image)
    
    Returns filename if dialog is accepted, None otherwise
    """
    saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
    sys.stdout = None
    filename = QFileDialog.getSaveFileName(parent, _("Save as"), 
                                           basedir, IMAGE_SAVE_FILTERS)
    sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
    if filename:
        filename = unicode(filename)
        try:
            array_to_imagefile(data, filename)
            return filename
        except Exception, msg:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(parent,
                 _('Error') if app_name is None else app_name,
                 (_(u"%s could not be written:") % osp.basename(filename))+\
                 "\n"+str(msg))
            return

def exec_image_open_dialog(parent, basedir='', app_name=None,
                           to_grayscale=True):
    """
    Executes an image open dialog box (QFileDialog.getOpenFileName)
        * parent: parent widget (None means no parent)
        * basedir: base directory ('' means current directory)
        * app_name (opt.): application name (used as a title for an eventual 
          error message box in case something goes wrong when saving image)
        * to_grayscale (default=True): convert image to grayscale
    
    Returns (filename, data) tuple if dialog is accepted, None otherwise
    """
    saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
    sys.stdout = None
    filename = QFileDialog.getOpenFileName(parent, _("Open"),
                                           basedir, IMAGE_LOAD_FILTERS)
    sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
    filename = unicode(filename)
    try:
        data = imagefile_to_array(filename, to_grayscale=to_grayscale)
    except Exception, msg:
        import traceback
        traceback.print_exc()
        QMessageBox.critical(parent,
             _('Error') if app_name is None else app_name,
             (_(u"%s could not be opened:") % osp.basename(filename))+\
             "\n"+str(msg))
        return
    return filename, data

def exec_images_open_dialog(parent, basedir='', app_name=None,
                            to_grayscale=True):
    """
    Executes an image*s* open dialog box (QFileDialog.getOpenFileNames)
        * parent: parent widget (None means no parent)
        * basedir: base directory ('' means current directory)
        * app_name (opt.): application name (used as a title for an eventual 
          error message box in case something goes wrong when saving image)
        * to_grayscale (default=True): convert image to grayscale
    
    Yields (filename, data) tuples if dialog is accepted, None otherwise
    """
    saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
    sys.stdout = None
    filenames = QFileDialog.getOpenFileNames(parent, _("Open"),
                                             basedir, IMAGE_LOAD_FILTERS)
    sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
    filenames = [unicode(fname) for fname in list(filenames)]
    for filename in filenames:
        try:
            data = imagefile_to_array(filename, to_grayscale=to_grayscale)
        except Exception, msg:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(parent,
                 _('Error') if app_name is None else app_name,
                 (_(u"%s could not be opened:") % osp.basename(filename))+\
                 "\n"+str(msg))
            return
        yield filename, data
    