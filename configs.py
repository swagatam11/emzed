#encoding: utf-8


from libms.RConnect.XCMSConnector import CentwaveFeatureDetector, MatchedFilterFeatureDetector

cwfstd = CentwaveFeatureDetector.standardConfig
centwaveConfig = [   ("std", "standard config orbitrap", cwfstd) ]

tourConfig = cwfstd.copy()
tourConfig.update(dict(ppm=10,\
                       peakwidth=(15, 60),\
                       prefilter=(5, 10000),\
                       snthresh = 0.1,\
                       mzdiff = 0.001)
                 )


centwaveConfig += [ ("tour", "config for example in tour", tourConfig)]

mfstd = MatchedFilterFeatureDetector.standardConfig
matchedFilterConfig = [  ( "std", "standard config" , mfstd ) ]


from libms.PeakPicking import PeakPickerHiRes

peakPickerHiResConfig = [ ("std", "orbitrap standard", PeakPickerHiRes.standardConfig) ]


from libms.PeakIntegration import *
# key "std" must exist !
peakIntegrators = [ ( "std",  SGIntegrator(window_size=11, order=2) ) ,
                    ( "asym_gauss", AsymmetricGaussIntegrator() ) ,
                    ( "trapez", TrapezIntegrator() ) ,
                    ( "emg_exact", SimplifiedEMGIntegrator() ) ,
                    ( "no_integration", NoIntegration() ) ,
                   ]

metaboff_defaults = dict(epdet_width_filtering="auto")

std_config = metaboff_defaults.copy()
std_config.update({"common_chrom_fwhm": 25.0,
                    "mtd_min_trace_length" : 3.0,
                    "ffm_local_mz_range" : 15.0,
                    "ffm_disable_isotope_filtering" : "true"
                   })

_fast_for_test = metaboff_defaults.copy()
_fast_for_test.update({"common_noise_threshold_int": 10000.0,
                        "common_chrom_peak_snr": 10000.0,
                   })

metaboFFConfigs = [ (None, "no params set", metaboff_defaults),
                    ("std", "std params",  std_config),
                    ("_test", "params for fast test",  _fast_for_test),
                    ]



import os.path

from string import Template

# modules are searched in this order, search ends at first hit
# configs are read in this order, so local configs overrun global configs

import userConfig
exchangeFolder = userConfig.getScriptsExchangeFolder()
repositoryPathes = []
if exchangeFolder is not None:
    if not os.path.exists(exchangeFolder):
        os.makedirs(exchangeFolder)
    repositoryPathes.append(exchangeFolder)
repositoryPathes.extend([ userConfig.getDataHome() ])


for p in repositoryPathes:
    pp = os.path.join(Template(p).substitute(os.environ), "local_configs.py")
    if os.path.exists(pp):
        print "RUN FILE", pp
        dd = locals()
        dd["is_exec"]=True
        execfile(pp, globals(), dd)

assert "std" in set(k for k, i in peakIntegrators), "integratorid 'std' missing"
