
from MSExperiment  cimport *
from ChromatogramPeak cimport *
from Peak1D cimport *
from string cimport *

cdef extern from "<OpenMS/FORMAT/MzMLFile.h>" namespace "OpenMS":

    cdef cppclass MzMLFile:
        MzMLFile()
        # hier muss leider spezialisert werden:
        void load(string, MSExperiment[Peak1D, ChromatogramPeak]) except+
        void store(string, MSExperiment[Peak1D, ChromatogramPeak]) except+
