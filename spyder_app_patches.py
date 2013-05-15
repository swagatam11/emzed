# encoding: utf-8

from patch_utils import replace, add
import os

def patch_spyder():

    # patches default config values for first startup
    # including path to startup.py for "normal" python console:    
    patch_userconfig()
    
    # patches python path, so that external IPython shell loads patched
    # startup.py
    patch_baseconfig()

    # the following patch must appear before patching Externalshell, as the
    # corresponding import of ExternalConsole implies import of baseshell. So
    # patching baseshell will not work, as it is registered in sys.modules in
    # unpatched version !
  
    # patches python path, so that external IPython shell loads patched
    # sitecustomize.py
     
    patch_baseshell()
    
    # patch dialogs for emzed specific types:
    patch_RemoteDictEditorTableView()
    patch_NamespaceBrowser()


def patch_RemoteDictEditorTableView():

    from  spyderlib.widgets.dicteditor import (RemoteDictEditorTableView,
                                               BaseTableView)

    @replace(RemoteDictEditorTableView.edit_item, verbose=True)
    def patch(self):
        if self.remote_editing_enabled:
            index = self.currentIndex()
            if not index.isValid():
                return
            key = self.model.get_key(index)
            if (self.is_list(key) or self.is_dict(key) 
                or self.is_array(key) or self.is_image(key)):
                # If this is a remote dict editor, the following avoid 
                # transfering large amount of data through the socket
                self.oedit(key)
            # START MOD EMZED
            elif self.is_peakmap(key) or self.is_table(key) or\
                 self.is_tablelist(key):
                self.oedit(key)
            # END MOD EMZED
            else:
                BaseTableView.edit_item(self)
        else:
            BaseTableView.edit_item(self)


def patch_NamespaceBrowser():
    
    from spyderlib.widgets.externalshell.monitor import communicate
    from spyderlib.widgets.externalshell.namespacebrowser\
                                                 import NamespaceBrowser

    @add(NamespaceBrowser, verbose=True)
    def is_peakmap(self, name):
        """Return True if variable is a PeakMap"""
        return communicate(self._get_sock(),
           "isinstance(globals()['%s'], (libms.DataStructures.PeakMap))" % name)

    @add(NamespaceBrowser, verbose=True)
    def is_table(self, name):
        """Return True if variable is a PeakMap"""
        return communicate(self._get_sock(),
             "isinstance(globals()['%s'], (libms.DataStructures.Table))" % name)

    @add(NamespaceBrowser, verbose=True)
    def is_tablelist(self, name):
        """Return True if variable is a PeakMap"""
        return communicate(self._get_sock(),
            "isinstance(globals()['%s'], list) "\
            "and all(isinstance(li, libms.DataStructures.Table)"\
            "        for li in globals()['%s'])" %(name, name))

    @replace(NamespaceBrowser.setup, verbose=True)
    def setup(self, *a, **kw):
        NamespaceBrowser._orig_setup(self, *a, **kw)
        self.editor.is_peakmap = self.is_peakmap
        self.editor.is_table = self.is_table
        self.editor.is_tablelist = self.is_tablelist

    @replace(NamespaceBrowser.import_data, verbose=True)
    def import_data(self, filenames=None):
        NamespaceBrowser._orig_import_data(self, filenames)
        self.save_button.setEnabled(self.filename is not None)


    @add(NamespaceBrowser, verbose=True)
    def get_remote_view_settings(self):
        """Return dict editor view settings for the remote process,
        but return None if this namespace browser is not visible (no need
        to refresh an invisible widget...)"""
        if self.is_visible and self.isVisible():
            return self.get_view_settings()



def patch_baseshell():

    # modifies assembly of PYTHONPATH before starting the external
    # shell in spyderlib\widgets\externalshell\pythonshell.py
    # so the sitecustomize will be loaded from patched_modules\
    # and not from spyderlib\widgets\externalshell\


    import spyderlib.widgets.externalshell.baseshell as baseshell
    import os.path
    @replace(baseshell.add_pathlist_to_PYTHONPATH, verbose=True)
    def patched(env, pathlist):
        for i, p in enumerate(pathlist):
            # replace path to ../externalshell/ (which contains
            # sitecustomize.py) with path to patched_modules/
            if p.rstrip("/").endswith("externalshell"):
                startupdir = os.environ["EMZED_HOME"]
                pathlist[i] = os.path.join(startupdir, "patched_modules")
        return baseshell._orig_add_pathlist_to_PYTHONPATH(env, pathlist)

def patch_userconfig():

    # patching the default settings for the first start is not easy,
    # as defaults are set in spyderlib.config during the first import
    # and the constructor of spyderlib.userconfig.UserConfig saves
    # them immediately. 

    # this works:
    import spyderlib.userconfig
    @replace(spyderlib.userconfig.get_home_dir)
    def patched():
        """
        Return user home directory
        """
        import os.path as osp
        from spyderlib.utils import encoding
        for env_var in ('APPDATA', 'USERPROFILE', 'TMP'):
            # os.environ.get() returns a raw byte string which needs to be
            # decoded with the codec that the OS is using to represent environment
            # variables.
            path = encoding.to_unicode_from_fs(os.environ.get(env_var, ''))
            if osp.isdir(path):
                break
        if path:
            return path
        try:
            # expanduser() returns a raw byte string which needs to be
            # decoded with the codec that the OS is using to represent file paths.
            path = encoding.to_unicode_from_fs(osp.expanduser('~'))
        except:
            raise RuntimeError('Please define environment variable $HOME')


    from spyderlib.userconfig import UserConfig

    here = os.path.abspath(os.path.dirname(__file__))
    path_to_emzed_startup = os.path.join(here, "patched_modules/startup.py")

    class MyConfig(UserConfig):

        # save this, else we get a recursion below
        __orig_base_class = UserConfig

        def __init__(self, name, defaults, *a, **kw):
            __my_defaults = {
                "console": 
                            { "pythonstartup/default" : False,
                              "pythonstartup/custom"  : True,
                              "pythonstartup" : path_to_emzed_startup,
                              "open_ipython_at_startup"  : True,
                               "object_inspector": False,
                              "open_python_at_startup"  : False, 
                            }
                 ,
                 "inspector":
                             { "automatic_import" : False,  # faster !
                             }
                 ,
                 "variable_explorer":
                             { "remote_editing" : True, 
                             }
                 ,
                 "editor":
                             # paranthesis closing is annoying
                             { "close_parentheses" : False, 
                               "outline_explorer": True,
                               "object_inspector": True,
                             }
                 ,
                 #"startup":  # not needed, we set workingdir for first startup in emzed.pyw
                             #{ "use_fixed_directory" : True, 
                               #"fixed_directory" : path_to_emzed_home,
                             #}
                 #,
            }
            for section, settings in defaults:
                override = __my_defaults.get(section)
                if override:
                    settings.update(override)
            
            # using UserConfig.__init__ would recurse here as we set UserConfig = MyConfig below !
            MyConfig.__orig_base_class.__init__(self, name, defaults, *a, **kw)


    import spyderlib.userconfig
    spyderlib.userconfig.UserConfig = MyConfig 

    return


def patch_baseconfig():
    from spyderlib import baseconfig

    # Opening an IPYTHON shell does not use the configures startup.py
    # which we see in spyder.ini, but locate starup.py inside the
    # the directory where spyderlib.widgets.externalshell resides.
    # So we fool ExternalPythonShell in widgets/externalshell/pythonshell.py
    # by patching baseconfig.get_module_source_path:

    @replace(baseconfig.get_module_source_path, verbose=True)
    def patch(modname, basename=None):
        if modname == "spyderlib.widgets.externalshell"\
            and basename=="startup.py":
            import os
            return os.path.join(os.environ.get("EMZED_HOME"),
                                "patched_modules",
                                "startup.py")
        return baseconfig._orig_get_module_source_path(modname, basename)

