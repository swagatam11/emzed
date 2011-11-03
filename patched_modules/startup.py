# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""modified msworkbench Startup file used by ExternalPythonShell"""

print "patched startup"

import sys
import os

def __run_pythonstartup_script(namespace):
    filename = os.environ.get('PYTHONSTARTUP')
    if filename and os.path.isfile(filename):
        print "exec", filename
        execfile(filename, namespace)

def __run_init_commands():
    return os.environ.get('PYTHONINITCOMMANDS')

def __is_ipython_shell():
    return os.environ.get('IPYTHON', False)

def __is_ipython_kernel():
    return os.environ.get('IPYTHON_KERNEL', False)

def __create_banner():
    """Create shell banner"""
    print 'Python %s on %s\nType "copyright", "credits" or "license" ' \
          'for more information.'  % (sys.version, sys.platform)

def __remove_sys_argv__():
    """Remove arguments from sys.argv"""
    sys.argv = ['']
    
def __remove_from_syspath__():
    """Remove this module's path from sys.path"""
    import os.path as osp
    try:
        sys.path.remove(osp.dirname(__file__))
    except ValueError:
        pass


class UserModuleDeleter(object):
    """
    User Module Deleter (UMD) aims at deleting user modules 
    to force Python to deeply reload them during import
    
    pathlist [list]: blacklist in terms of module path
    namelist [list]: blacklist in terms of module name
    """
    def __init__(self, namelist=None, pathlist=None):
        if namelist is None:
            namelist = []
        self.namelist = namelist+['sitecustomize', 'spyderlib', 'spyderplugins']
        if pathlist is None:
            pathlist = []
        self.pathlist = pathlist
        self.previous_modules = sys.modules.keys()

    def is_module_blacklisted(self, modname, modpath):
        for path in [sys.prefix]+self.pathlist:
            if modpath.startswith(path):
                return True
        else:
            return set(modname.split('.')) & set(self.namelist)
        
    def run(self, verbose=False):
        """
        Del user modules to force Python to deeply reload them
        
        Do not del modules which are considered as system modules, i.e. 
        modules installed in subdirectories of Python interpreter's binary
        Do not del C modules
        """
        log = []
        for modname, module in sys.modules.items():
            if modname not in self.previous_modules:
                modpath = getattr(module, '__file__', None)
                if modpath is None:
                    # *module* is a C module that is statically linked into the 
                    # interpreter. There is no way to know its path, so we 
                    # choose to ignore it.
                    continue
                if not self.is_module_blacklisted(modname, modpath):
                    log.append(modname)
                    del sys.modules[modname]
        if verbose and log:
            print "\x1b[4;33m%s\x1b[24m%s\x1b[0m" % ("UMD has deleted",
                                                     ": "+", ".join(log))

__umd__ = None

def runfile(filename, args=None, wdir=None):
    """
    Run filename
    args: command line arguments (string)
    wdir: working directory
    """
    global __umd__
    if os.environ.get("UMD_ENABLED", "").lower() == "true":
        if __umd__ is None:
            namelist = os.environ.get("UMD_NAMELIST", None)
            if namelist is not None:
                namelist = namelist.split(',')
            __umd__ = UserModuleDeleter(namelist=namelist)
        else:
            verbose = os.environ.get("UMD_VERBOSE", "").lower() == "true"
            __umd__.run(verbose=verbose)
    if args is not None and not isinstance(args, basestring):
        raise TypeError("expected a character buffer object")
    glbs = globals()
    shell = glbs.get('__ipythonshell__')
    if shell is not None:
        if hasattr(shell, 'user_ns'):
            # IPython >=v0.11
            glbs = shell.user_ns
        else:
            # IPython v0.10
            glbs = shell.IP.user_ns
    glbs['__file__'] = filename
    sys.argv = [filename]
    if args is not None:
        for arg in args.split():
            sys.argv.append(arg)
    if wdir is not None:
        os.chdir(wdir)
    execfile(filename, glbs)
    sys.argv = ['']
    glbs.pop('__file__')
    

def debugfile(filename, args=None, wdir=None):
    """
    Debug filename
    args: command line arguments (string)
    wdir: working directory
    """
    import pdb
    debugger = pdb.Pdb()
    filename = debugger.canonic(filename)
    debugger._wait_for_mainpyfile = 1
    debugger.mainpyfile = filename
    debugger._user_requested_quit = 0
    debugger.run("runfile(%r, args=%r, wdir=%r)" % (filename, args, wdir))


def evalsc(command):
    """Evaluate special commands
    (analog to IPython's magic commands but far less powerful/complete)"""
    assert command.startswith(('%', '!'))
    system_command = command.startswith('!')
    command = command[1:].strip()
    if system_command:
        # System command
        if command.startswith('cd '):
            evalsc('%'+command)
        else:
            from subprocess import Popen, PIPE
            Popen(command, shell=True, stdin=PIPE)
            print '\n'
    else:
        # General command
        import re
        clear_match = re.match(r"^clear ([a-zA-Z0-9_, ]+)", command)
        cd_match = re.match(r"^cd \"?\'?([a-zA-Z0-9_ \.]+)", command)
        if cd_match:
            os.chdir(eval('r"%s"' % cd_match.groups()[0].strip()))
        elif clear_match:
            varnames = clear_match.groups()[0].replace(' ', '').split(',')
            for varname in varnames:
                try:
                    globals().pop(varname)
                except KeyError:
                    pass
        elif command in ('cd', 'pwd'):
            print os.getcwdu()
        elif command == 'ls':
            if os.name == 'nt':
                evalsc('!dir')
            else:
                evalsc('!ls')
        elif command == 'scientific':
            from spyderlib import baseconfig
            execfile(baseconfig.SCIENTIFIC_STARTUP, globals())
        else:
            raise NotImplementedError, "Unsupported command: '%s'" % command


if __name__ == "__main__":


    __remove_from_syspath__()
    
    if not __is_ipython_shell() and not __is_ipython_kernel():
        __remove_sys_argv__()
        __create_banner()

    if not __is_ipython_kernel():
        __commands__ = __run_init_commands()

        if __commands__:
            for command in __commands__.split(';'):
                print "exec ", command
                exec command

    if not __is_ipython_shell() and not __is_ipython_kernel():
        __run_pythonstartup_script(globals())

    for _name in ['__run_pythonstartup_script', '__run_init_commands',
                  '__create_banner', '__commands__', 'command', '__file__',
                  '__remove_sys_argv__']+['_name']:
        if _name in locals():
            locals().pop(_name)

    __doc__ = ''
    __name__ = '__main__'

    if __is_ipython_kernel():
        # IPython >=v0.11 Kernel
        from IPython.zmq.ipkernel import IPKernelApp
        __ipythonkernel__ = IPKernelApp()
        __ipythonkernel__.initialize(sys.argv[1:])
        __ipythonshell__ = __ipythonkernel__.shell
        __ipythonkernel__.start()
    elif __is_ipython_shell():

        import os
        if os.name == 'nt':
            # Windows platforms: monkey-patching *pyreadline* module
            # to make IPython work in a remote process
            from pyreadline import unicode_helper
            unicode_helper.pyreadline_codepage = "ascii"
            # For pyreadline >= v1.7:
            from pyreadline import rlmain
            class Readline(rlmain.Readline):
                def __init__(self):
                    super(Readline, self).__init__()
                    self.console = None
            rlmain.Readline = Readline
            # For pyreadline v1.5-1.6 only:
            import pyreadline
            pyreadline.GetOutputFile = lambda: None
        del __is_ipython_shell
        import libms
        import ms
        import batches
        import traceback
        user_ns = dict(runfile = runfile, debugfile=debugfile, libms=libms, b=batches, ms=ms)
        try:
            from configs import repository_pathes
            from string import Template

            for p in reversed(repository_pathes):
                sys.path.insert(0, Template(p).substitute(os.environ))

        except ImportError, e:
            traceback.print_exc(file=sys.stdout)

        try:
            # IPython >=v0.11
            # Support for these recent versions of IPython is limited:
            # command line options are not parsed yet since there are still
            # major issues to be fixed on Windows platforms regarding pylab
            # support.
            from IPython.frontend.terminal.embed import InteractiveShellEmbed
            banner2 = None
            if os.name == 'nt':
                # Patching IPython to avoid enabling readline:
                # we can't simply disable readline in IPython options because
                # it would also mean no text coloring support in terminal
                from IPython.core.interactiveshell import InteractiveShell, io
                def patched_init_io(self):
                    io.stdout = io.IOStream(sys.stdout)
                    io.stderr = io.IOStream(sys.stderr)
                InteractiveShell.init_io = patched_init_io
                banner2 = """Warning:
Spyder does not support GUI interactions with IPython >=v0.11
on Windows platforms (only IPython v0.10 is fully supported).
"""

            __ipythonshell__ = InteractiveShellEmbed(user_ns= user_ns,
                                                     banner2=banner2)#,
#                                                     display_banner=False)
#            __ipythonshell__.shell.show_banner()
#            __ipythonshell__.enable_pylab(gui='qt')
            #TODO: parse command line options using the two lines commented
            #      above (banner has to be shown afterwards)
            #FIXME: Windows platforms: pylab/GUI loop support is not working
            __ipythonshell__.stdin_encoding = os.environ['SPYDER_ENCODING']
        except ImportError:
            # IPython v0.10
            import IPython.Shell
            __ipythonshell__ = IPython.Shell.start(user_ns=user_ns)
            __ipythonshell__.IP.stdin_encoding = os.environ['SPYDER_ENCODING']
            __ipythonshell__.IP.autoindent = 0
        
        # Workaround #2 to make the HDF5 I/O variable explorer plugin work:
        # we import h5py only after initializing IPython in order to avoid 
        # a premature import of IPython *and* to enable the h5py/IPython 
        # completer (which wouldn't be enabled if we used the same approach 
        # as workaround #1)
        # (see sitecustomize.py for the Workaround #1)
        try:
            import h5py #@UnusedImport
        except ImportError:
            pass
        
        #ip = __ipythonshell__
        #import pdb
        #pdb.set_trace()
        ip = IPython.ipapi.get()
        if ip.options.pylab_import_all:
            ip.ex("del e")
            ip.ex("del pi")
            ip.IP.user_config_ns.update(ip.user_ns)
        __ipythonshell__.mainloop()
