from string cimport *
from libcpp.vector cimport *
from InstrumentSettings cimport *
from Precursor cimport *
from Peak1D cimport *

cdef extern from "<OpenMS/KERNEL/MSSpectrum.h>" namespace "OpenMS":

    cdef cppclass MSSpectrum[PeakT]:
        MSSpectrum()
        MSSpectrum(MSSpectrum)
        double getRT()
        void   setRT(double)
        unsigned int getMSLevel()
        void setMSLevel(unsigned int)

        string getName()
        void setName(string)

        int size()
        PeakT operator[](int)

        void updateRanges()

    
        InstrumentSettings getInstrumentSettings()
        int findNearest(double) except+
        vector[Precursor] getPrecursors()
        void setPrecursors(vector[Precursor])

        void assign(vector[Peak1D].iterator, vector[Peak1D].iterator)

        string getNativeID()
        void   setNativeID(string)

        

