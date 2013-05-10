import pdb


import _BatchRunner
class _FD(_BatchRunner.BatchRunner):

    def __init__(self, *a, **kw):
        #import libms.RConnect
        super(_FD, self).__init__(*a, **kw)

    def process(self, path):
        import ms

        try:
            print "read ", path
            ds = ms.loadPeakMap(path)
        except Exception, e:
            print e
            print "reading FAILED"
            return None

        table = self.det.process(ds)
        table.title = path

        print len(table), "features found"
        return table

    def write(self, result, destinationDir, path):
        import os.path
        basename, ext = os.path.splitext(os.path.basename(path))
        savePath = os.path.join(destinationDir, basename+".csv")
        print "save to ", savePath
        result.storeCSV(savePath)



def runCentwave(pattern=None, destination=None, configid="std", **params):

    """
         runs centwave algorithm from xcms in batch mode.
         input files are map files (mzXML, mxML, mzData),
         ouput files are csv files

         you can add modifications to the standard parameters, eg ppm,
         as named arguments.

         if you have multiple configs for centwave, you can give an
         configid as defined in configs.py, or you are asked to choose
         a config.

         if you have a single config this one is used automatically

         examples:

              runCentwave():
                     asks for source files and target directory
                     asks for config if multiple configs are defined

              runCentwave(configid="std", ppm=17)
                     uses config with id "std", overwrites ppm parameter
                     with ppm=17.

              runCentwave(ppm=13):
                     asks for source files and target directory
                     runs centwave with modified ppm=13 parameter.

              runCentwave(pattern):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file

              runCentwave(pattern, mzDiff=0.003):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file
                     runs centwave with modified mzDiff parameter

              runCentwave(pattern, destination):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory

              runCentwave(pattern, destination, ppm=17, peakwidth=(5,100) ):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory
                     runs centwave with modified ppm and peakwidth parameters.

    """

    import configs
    import libms.RConnect

    class P(_FD):

        def setup(self, config):
            self.det = libms.RConnect.CentwaveFeatureDetector(**config)

    return P(configs.centwaveConfig, True).run(pattern, destination, configid, **params)

import libms.RConnect as __libmsrconnect
runCentwave.__doc__ += __libmsrconnect.CentwaveFeatureDetector.__doc__

def runMatchedFilter(pattern=None, destination=None, configid="std", **params):

    """
         runs matched filters algorithm from xcms in batch mode.
         input files are map files (mzXML, mzML, mzData),
         output files are csv files

         you can add modifications to the standard parameters, eg ppm,
         as named arguments.

         if you have multiple configs for matched filter, you can give an
         configid as defined in configs.py, or you are asked to choose
         a config.

         if you have a single config this one is used automatically

         examples:

              runMatchedFilter():
                     asks for source files and target directory
                     asks for config if multiple configs are defined

              runMatchedFilter(configid="std", ppm=17)
                     uses config with id "std", overwrites ppm parameter
                     with ppm=17.

              runMatchedFilter(ppm=13):
                     asks for source files and target directory
                     runs matched filter with modified ppm=13 parameter.

              runMatchedFilter(pattern):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file

              runMatchedFilter(pattern, mzDiff=0.003):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file
                     runs matched filter with modified mzDiff parameter

              runMatchedFilter(pattern, destination):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory

              runMatchedFilter(pattern, destination, ppm=17, peakwidth=(5,100) ):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory
                     runs matched filter with modified ppm and peakwidth parameters.

    """

    import libms.RConnect
    import configs

    class P(_FD):

        def setup(self, config):
            self.det = libms.RConnect.MatchedFilterFeatureDetector(**config)

    return P(configs.matchedFilterConfig, True).run(pattern, destination, configid, **params)

runMatchedFilter.__doc__ += __libmsrconnect.MatchedFilterFeatureDetector.__doc__




def runMetaboFeatureFinder(pattern=None, destination=None, configid="std", **params):

    """
         runs matched filters algorithm from xcms in batch mode.
         input files are map files (mzXML, mzML, mzData),
         output files are csv files

         you can add modifications to the standard parameters, eg ppm,
         as named arguments.

         if you have multiple configs for matched filter, you can give an
         configid as defined in configs.py, or you are asked to choose
         a config.

         if you have a single config this one is used automatically

         examples:

              runMatchedFilter():
                     asks for source files and target directory
                     asks for config if multiple configs are defined

              runMatchedFilter(configid="std", ppm=17)
                     uses config with id "std", overwrites ppm parameter
                     with ppm=17.

              runMatchedFilter(ppm=13):
                     asks for source files and target directory
                     runs matched filter with modified ppm=13 parameter.

              runMatchedFilter(pattern):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file

              runMatchedFilter(pattern, mzDiff=0.003):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file
                     runs matched filter with modified mzDiff parameter

              runMatchedFilter(pattern, destination):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory

              runMatchedFilter(pattern, destination, ppm=17, peakwidth=(5,100) ):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory
                     runs matched filter with modified ppm and peakwidth parameters.

    """

    import configs

    class P(_FD):

        def __init__(self, *a, **kw):
            _BatchRunner.BatchRunner.__init__(self, *a, **kw)

        def process(self, path):
            import ms
            from ms._metabo import metaboFeatureFinder

            try:
                print "read ", path
                ds = ms.loadPeakMap(path)
            except Exception, e:
                print e
                print "reading FAILED"
                return None

            table = metaboFeatureFinder(ds, **self._ff_config)
            table.title = path

            print len(table), "features found"
            return table

        def setup(self, config):
            self._ff_config = config

    return P(configs.metaboFFConfigs, True).run(pattern, destination, configid, **params)

runMetaboFeatureFinder.__doc__ += __libmsrconnect.MatchedFilterFeatureDetector.__doc__
