from libms.DataStructures.MSTypes import *
from pyOpenMS import *
import numpy as np
import os.path
def exceptionwrapper(fun):
    e0 = None
    try:
        fun()
    except Exception, e:
        e0 = e
    assert e0 is not None


class TestMSTypes(object):

    def test001(self):
        exp = MSExperiment()
        basename = "SHORT_MS2_FILE.mzData"
        FileHandler().loadExperiment(os.path.join("data", basename), exp)
        assert exp.size()>0

        pc = Precursor()
        pc.setMZ(1.0)
        pc.setIntensity(100)
        s0 = exp[0]
        s0.setPrecursors([pc])
        spec = Spectrum.fromMSSpectrum(s0)
        settings = InstrumentSettings()
        settings.setPolarity(Polarity.POSITIVE)
        s0.setInstrumentSettings(settings)

        self.compare_specs(spec, s0)

        specneu = Spectrum.fromMSSpectrum(spec.toMSSpectrum())

        self.compare_specs(specneu, s0)

        pm = PeakMap.fromMSExperiment(exp)
        assert os.path.basename(pm.meta["source"]) ==  basename

        rtmin, rtmax = pm.rtRange()
        ms1s = pm.ms1Peaks(rtmin, rtmax)
        assert ms1s.shape == (1797, 2), ms1s.shape

        ms1s2 = pm.ms1Peaks(rtmax=rtmax)
        assert np.all(ms1s == ms1s2)

        ms1s3 = pm.ms1Peaks(rtmin=0)
        assert np.all(ms1s == ms1s3)

        spec = pm.spectra[0]
        assert len(list(spec)) == len(spec) # calls iter


        allrts = pm.allRts()
        assert (allrts[0], allrts[-1]) == pm.rtRange()
        assert len(allrts) == 41, len(allrts)

        level1 = pm.levelNSpecs(1, 1)
        level2 = pm.levelNSpecs(2, 2)
        level12 = pm.levelNSpecs(1, 2)
        assert len(level1) > 0
        assert len(level2) > 0
        assert len(level1) + len(level2) == len(level12) == len(pm)
        assert level1[0].msLevel == 1
        assert level2[0].msLevel == 2

        lone = pm.levelOneRts()
        assert len(lone) == len(level1)

        self.compare_exp(pm, exp, basename)
        pm2 = PeakMap.fromMSExperiment(pm.toMSExperiment())
        self.compare_exp(pm2, exp, basename)

        pm2 = pm.extract(rtmin = rtmin+.000001)
        assert len(pm2) == len(pm)-1
        pm2 = pm2.extract(rtmax = rtmax-0.000001)
        assert len(pm2) == len(pm)-2

        mzmin, mzmax = pm.mzRange()

        assert mzmin < 250
        assert mzmax > 1049

        pm2 = pm.extract(rtmin+0.00001, mzmin=300)

        mzmin2, mzmax2 = pm2.mzRange()
        assert mzmin2 >= 300
        assert mzmax2 == mzmax

        pm2 = pm.extract(rtmin = rtmin+0.000001, mzmin=300, mzmax=1000)
        mzmin2, mzmax2 = pm2.mzRange()
        assert mzmin2 >= 300
        assert mzmax2 <= 1000

        exceptionwrapper(lambda: pm.spectra[0].peaksInRange())

        pp1 = pm.spectra[0].peaksInRange(mzmax = 10000)
        pp2 = pm.spectra[0].peaksInRange(mzmin = 0)
        assert np.all(pp1 == pp2)

        specs0 = pm.spectra[:]
        specs1 = pm.specsInRange(0, 99999)
        specs2 = pm.specsInRange(0, specs0[0].rt)
        specs3 = pm.specsInRange(specs0[-1].rt, 999999)



        assert specs0 == specs1
        assert specs2 == [ specs0[0] ]
        assert specs3 == [ specs0[-1] ]



        pm.spectra[0].polarity = "+"
        pm.spectra[1].polarity = "-"

        PeakMap(pm.spectra) 


    def testEmptyPeakMap(self):
        pm = PeakMap([])
        assert pm.extract(0, 9999, 0, 10000).spectra == []
        assert pm.filter(lambda t: True).spectra == []
        assert pm.specsInRange(0, 10e6) == []
        assert pm.levelOneSpecsInRange(0, 10e6) == []
        assert pm.chromatogram(0, 10e6, 0, 10e6) == ([], [])
        assert pm.chromatogram(0, 10e6) == ([], [])
        assert pm.ms1Peaks(0, 10e6).tolist() == []
        assert pm.allRts() == []
        assert pm.levelOneRts() == []
        assert pm.levelNSpecs(1,2) == []

    def compare_exp(self, pm, exp, basename):

        assert len(pm) == exp.size()

        assert (pm.spectra[0].rt-exp[0].getRT())/exp[0].getRT() < 1e-7
        assert pm.spectra[0].msLevel == exp[0].getMSLevel()
        assert pm.spectra[0].peaks.shape == (exp[0].size(), 2)

    def compare_specs(self, spec, s0):

        assert (spec.rt-s0.getRT())/s0.getRT() < 1e-7
        assert spec.msLevel == s0.getMSLevel()
        assert spec.peaks.shape == (s0.size(), 2)
        assert spec.precursors == [ (1.0, 100) ], spec.precursors
        assert spec.polarity == "+"

        assert len(spec) == s0.size() 


    def testIntensityInRange(self):
        data = np.array([ 0.0, 1.0, 2.0, 3.0, 4.0, 5.0 ]).reshape(-1,1)
        ones = np.ones_like(data)
        peaks = np.hstack((data, ones))
        assert peaks.shape == (6,2)
        spec = Spectrum(peaks, 0.0, 1, "0")
        assert spec.intensityInRange(0.0, 5.0) == 6.0
        assert spec.intensityInRange(0.1, 5.0) == 5.0
        assert spec.intensityInRange(0.0, 4.5) == 5.0
        assert spec.intensityInRange(0.5, 4.5) == 4.0
        assert spec.intensityInRange(2.0, 2.0) == 1.0
        assert spec.intensityInRange(2.1, 2.0) == 0.0

