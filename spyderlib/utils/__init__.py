# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
spyderlib.utils
===============

Spyder's utilities
"""

from __future__ import with_statement
import os, os.path as osp, shutil, sys, StringIO, traceback, time
STDERR = sys.stderr


def __remove_pyc_pyo(fname):
    if osp.splitext(fname)[1] == '.py':
        for ending in ('c', 'o'):
            if osp.exists(fname+ending):
                os.remove(fname+ending)

def rename_file(source, dest):
    """
    Rename file from *source* to *dest*
    If file is a Python script, also rename .pyc and .pyo files if any
    """
    os.rename(source, dest)
    __remove_pyc_pyo(source)

def remove_file(fname):
    """
    Remove file *fname*
    If file is a Python script, also rename .pyc and .pyo files if any
    """
    os.remove(fname)
    __remove_pyc_pyo(fname)

def move_file(source, dest):
    """
    Move file from *source* to *dest*
    If file is a Python script, also rename .pyc and .pyo files if any
    """
    shutil.copy(source, dest)
    remove_file(source)


def select_port(default_port=20128):
    """Find and return a non used port"""
    import socket
    while True:
        try:
            sock = socket.socket(socket.AF_INET,
                                 socket.SOCK_STREAM,
                                 socket.IPPROTO_TCP)
#            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind( ("127.0.0.1", default_port) )
        except socket.error, _msg:
            default_port += 1
        else:
            break
        finally:
            sock.close()
            sock = None
    return default_port


def count_lines(path, extensions=None, excluded_dirnames=None):
    """Return number of source code lines for all filenames in subdirectories
    of *path* with names ending with *extensions*
    Directory names *excluded_dirnames* will be ignored"""
    if extensions is None:
        extensions = ['.py', '.pyw', '.ipy', '.c', '.h', '.cpp', '.hpp', '.inc',
                      '.cl', '.f', '.for', '.f90', '.f77']
    if excluded_dirnames is None:
        excluded_dirnames = ['build', 'dist', '.hg', '.svn']
    def get_filelines(path):
        dfiles, dlines = 0, 0
        if osp.splitext(path)[1] in extensions:
            dfiles = 1
            with open(path, 'rb') as textfile:
                dlines = len(textfile.read().strip().splitlines())
        return dfiles, dlines
    lines = 0
    files = 0
    if osp.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for d in dirnames[:]:
                if d in excluded_dirnames:
                    dirnames.remove(d)
            if excluded_dirnames is None or \
               osp.dirname(dirpath) not in excluded_dirnames:
                for fname in filenames:
                    dfiles, dlines = get_filelines(osp.join(dirpath, fname))
                    files += dfiles
                    lines += dlines
    else:
        dfiles, dlines = get_filelines(path)
        files += dfiles
        lines += dlines
    return files, lines


def is_builtin(text):
    import __builtin__
    return text in [str(name) for name in dir(__builtin__)
                    if not name.startswith('_')]

def is_keyword(text):
    import keyword
    return text in keyword.kwlist


def fix_reference_name(name, blacklist=None):
    """Return a syntax-valid reference name from an arbitrary name"""
    import re
    name = "".join(re.split(r'[^0-9a-zA-Z_]', name))
    while name and not re.match(r'([a-zA-Z]+[0-9a-zA-Z_]*)$', name):
        if not re.match(r'[a-zA-Z]', name[0]):
            name = name[1:]
            continue
    name = str(name.lower())
    if not name:
        name = "data"
    if blacklist is not None and name in blacklist:
        get_new_name = lambda index: name+('%03d' % index)
        index = 0
        while get_new_name(index) in blacklist:
            index += 1
        name = get_new_name(index)
    return name


def remove_trailing_single_backslash(text):
    """
    Remove trailing single backslash in *text*
    
    This is especially useful when formatting path strings on 
    Windows platforms for which folder paths may end with such 
    a character
    """
    if text.endswith('\\') and not text.endswith('\\\\'):
        text = text[:-1]
    return text


def get_error_match(text):
    """Return error match"""
    import re
    return re.match(r'  File "(.*)", line (\d*)', text)

def log_time(fd):
    timestr = "Logging time: %s" % time.ctime(time.time())
    print >>fd, "="*len(timestr)
    print >>fd, timestr
    print >>fd, "="*len(timestr)
    print >>fd, ""

def log_last_error(fname, context=None):
    """Log last error in filename *fname* -- *context*: string (optional)"""
    out = StringIO.StringIO()
    traceback.print_exc(file=out)
    fd = open(fname, 'a')
    log_time(fd)
    if context:
        print >>fd, "Context"
        print >>fd, "-------"
        print >>fd, ""
        print >>fd, context
        print >>fd, ""
        print >>fd, "Traceback"
        print >>fd, "---------"
        print >>fd, ""
    traceback.print_exc(file=fd)
    print >>fd, ""
    print >>fd, ""

def log_dt(fname, context, t0):
    fd = open(fname, 'a')
    log_time(fd)
    print >>fd, "%s: %d ms" % (context, 10*round(1e2*(time.time()-t0)))
    print >>fd, ""
    print >>fd, ""
