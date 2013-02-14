#encoding: utf-8
from RExecutor import RExecutor
from ..DataStructures import PeakMap, XCMSFeatureParser

import os, sys

from ..intern_utils import TemporaryDirectoryWithBackup
from pyOpenMS import FileHandler

from userConfig import getExchangeFolder, getRLibsFolder

exchangeFolderAvailable = getExchangeFolder() is not None


def install_xmcs_if_needed_statements():
    r_libs = getRLibsFolder().replace("\\", "\\\\")

    script = """
                if (require("xcms") == FALSE)
                {
                    source("http://bioconductor.org/biocLite.R")
                    biocLite("xcms", dep=T, lib="%s", destdir="%s")
                }
            """ % (r_libs, r_libs)

    return script


def installXcmsIfNeeded():

    if not exchangeFolderAvailable:
# all installled libs will get to local folder
        print "no xcms install as exchange folder is not available"
        return

    RExecutor().run_command(install_xmcs_if_needed_statements())


def lookForXcmsUpgrades():

    if not exchangeFolderAvailable:
        print "no xcms upgrade check as exchange folder is not available"
        return

    script = """
                 source("http://bioconductor.org/biocLite.R")
                 todo <- old.packages(repos=biocinstallRepos(), lib="%s")
                 q(status=length(todo))
             """ % getRLibsFolder().replace("\\", "\\\\")

    num = RExecutor().run_command(script)
    if not num:
        print "No update needed"
    else:
        print num, "updates found"


def doXcmsUpgrade():

    if not exchangeFolderAvailable:
        print "no xcms upgrade as exchange folder is not available"
        return

    r_libs = getRLibsFolder().replace("\\", "\\\\")

    script = """
     source("http://bioconductor.org/biocLite.R")
     todo <- update.packages(repos=biocinstallRepos(), ask=FALSE, checkBuilt=TRUE, lib="%s", destdir="%s")
     q(status=length(todo))
    """ % (r_libs, r_libs)

    return RExecutor().run_command(script)


def _get_temp_peakmap(msLevel, peakMap):
    if msLevel is None:
        msLevels = peakMap.getMsLevels()
        if len(msLevels) > 1:
            raise Exception("multiple msLevels in peakmap "\
                            "please specify msLevel in config")
        msLevel = msLevels[0]

    temp_peakmap =  peakMap.extract(mslevelmin=msLevel, mslevelmax=msLevel)
    temp_peakmap.spectra.sort(key = lambda s: s.rt)
    return temp_peakmap


class CentwaveFeatureDetector(object):

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "centwave.txt")

    __doc__ = """ CentwaveFeatureDetector

    usage:

           print CentwaveFeatureDetector.standardConfig

           detector = CentwaveFeatureDetector(param1=val1, ....)
           detector.process(peakmap)


    Docs from XCMS library:

    """

    __doc__ += "".join(file(path).readlines())
    __doc__ = unicode(__doc__, "utf-8")

    standardConfig = dict(   ppm=25,
                             peakwidth=(20,50),
                             prefilter=(3,100),
                             snthresh = 10,
                             integrate = 1,
                             mzdiff=-0.001,
                             noise=0,
                             mzCenterFun="wMean",
                             fitgauss=False,
                             msLevel=None,
                             verbose_columns = False )

    def __init__(self, **kw):

        #installXcmsIfNeeded()

        self.config = self.standardConfig.copy()
        self.config.update(kw)

    def process(self, peakMap):
        assert isinstance(peakMap, PeakMap)
        if len(peakMap) == 0:
            raise Exception("empty peakmap")

        temp_peakmap = _get_temp_peakmap(self.config.get("msLevel"), peakMap)

        with TemporaryDirectoryWithBackup() as td:

            temp_input = os.path.join(td, "input.mzData")
            temp_output = os.path.join(td, "output.csv")

            # needed for network shares:
            if sys.platform == "win32":
                temp_input = temp_input.replace("/","\\")

            FileHandler().storeExperiment(temp_input, temp_peakmap.toMSExperiment())

            dd = self.config.copy()
            dd["temp_input"] = temp_input
            dd["temp_output"] = temp_output
            dd["fitgauss"] = str(dd["fitgauss"]).upper()
            dd["verbose_columns"] = str(dd["verbose_columns"]).upper()


            script = install_xmcs_if_needed_statements() + """
                        library(xcms)
                        xs <- xcmsSet(%(temp_input)r, method="centWave",
                                          ppm=%(ppm)d,
                                          peakwidth=c%(peakwidth)r,
                                          prefilter=c%(prefilter)r,
                                          snthresh = %(snthresh)f,
                                          integrate= %(integrate)d,
                                          mzdiff   = %(mzdiff)f,
                                          noise    = %(noise)f,
                                          fitgauss = %(fitgauss)s,
                                          verbose.columns = %(verbose_columns)s,
                                          mzCenterFun = %(mzCenterFun)r
                                     )
                        write.table(xs@peaks, file=%(temp_output)r)
                        q(status=123)
                     """ % dd

            del dd["temp_input"]
            del dd["temp_output"]

            if RExecutor().run_command(script, td) != 123:
                raise Exception("R operation failed")

            # parse csv and shift rt related values to undo rt modifiaction
            # as described above
            table = XCMSFeatureParser.parse(file(temp_output).readlines())
            table.addConstantColumn("centwave_config", dd, dict, None)
            table.meta["generator"] = "xcms.centwave"
            decorate(table, temp_peakmap)
            return table

class MatchedFilterFeatureDetector(object):

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "matchedFilter.txt")

    __doc__ = """ MatchedFilterFeatureDetector

    usage:

           print MatchedFilterFeatureDetector.standardConfig

           detector = MatchedFilterFeatureDetector(param1=val1, ....)
           detector.process(peakmap)


    Docs from XCMS library:

    """

    __doc__ += "".join(file(path).readlines())
    __doc__ = unicode(__doc__, "utf-8")

    standardConfig = dict(   fwhm = 30,
                             sigma = 30/2.3548,
                             max_ = 5,
                             snthresh = 10,
                             step = 0.1,
                             steps = 2,
                             mzdiff = 0.8 - 2*2,
                             msLevel = None,
                             index = False )

    def __init__(self, **kw):
        #installXcmsIfNeeded()
        self.config = self.standardConfig.copy()
        self.config.update(kw)

    def process(self, peakMap):
        assert isinstance(peakMap, PeakMap)
        if len(peakMap) == 0:
            raise Exception("empty peakmap")

        temp_peakmap = _get_temp_peakmap(self.config.get("msLevel"), peakMap)
        minRt = peakMap.spectra[0].rt
        # xcms does not like rt <= 0, so we shift that rt starts with 1.0:
        # we have to undo this shift later when parsing the output of xcms
        shift = minRt-1.0
        peakMap.shiftRt(-shift)

        with TemporaryDirectoryWithBackup() as td:

            temp_input = os.path.join(td, "input.mzData")
            temp_output = os.path.join(td, "output.csv")

            # needed for network shares:
            if sys.platform == "win32":
                temp_input = temp_input.replace("/","\\")

            FileHandler().storeExperiment(temp_input, peakMap.toMSExperiment())

            dd = self.config.copy()
            dd["temp_input"] = temp_input
            dd["temp_output"] = temp_output
            dd["index"] = str(dd["index"]).upper()

            script = install_xmcs_if_needed_statements() + """
                        library(xcms)
                        xs <- xcmsSet(%(temp_input)r, method="matchedFilter",
                                       fwhm = %(fwhm)f, sigma = %(sigma)f,
                                       max = %(max_)d,
                                       snthresh = %(snthresh)f,
                                       step = %(step)f, steps=%(steps)d,
                                       mzdiff = %(mzdiff)f,
                                       index = %(index)s,
                                       sleep=0
                                     )
                        write.table(xs@peaks, file=%(temp_output)r)
                        q(status=123)
                     """ % dd

            del dd["temp_input"]
            del dd["temp_output"]

            if RExecutor().run_command(script, td) != 123:
                raise Exception("R opreation failed")

            # parse csv and
            table = XCMSFeatureParser.parse(file(temp_output).readlines())
            table.addConstantColumn("matchedfilter_config", dd, dict, None)
            table.meta["generator"] = "xcms.matchedfilter"
            decorate(table, temp_peakmap)
            return table

def decorate(table, peakMap):
    table.addConstantColumn("peakmap", peakMap, object, None)
    src = peakMap.meta.get("source","")
    table.addConstantColumn("source", src, str, None)
    table.addConstantColumn("polarity", peakMap.polarity, str, None)
    table.addEnumeration()
    table.title = os.path.basename(src)
