Please read the following instructions carefully, version numbers
and package names do matter ! Read the whole document before you start !


INSTALLING INSTRUCTIONS FOR A PLAIN WINDOWS 7 SYSTEM
----------------------------------------------------

You need :

  * 64 bit Python 2.7 from http://www.python.org/download/

  * numpy-MKL-1.7.X.win-amd64-py2.7.exe from
    http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy 

Run 'download.py' which is contained in this archive for downloading all
needed Python packages.

This creates a file "install.bat"

Run install.bat, we recomment to run it with administrator rights.



IF PYTHON 2.7 IS ALREADY INSTALLED
----------------------------------

1) IF YOU HAVE IPYTHON ON YOUR SYSTEM UNINSTALL THIS FIRST. 

   The downloader installs both IPython 0.10 and IPython 0.13.x.
   with easy_installs multi version mode ("-m" command line switch)

2) Have a look at urls.txt and install.bat to install missing packages
   manually.

3) Python packages can be installed locally or in a virtualenv.
