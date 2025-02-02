import ms
import glob

def testMzAlign():
    tab = ms.loadTable("data/ftab_for_mzalign.table")
    pm = tab.peakmap.values[0]
    s0 = pm.spectra[0].peaks[:,0]
    import os
    print os.getcwd()
    print os.listdir("temp_output")
    tab_aligned = ms.mzAlign(tab, interactive=False, minPoints=4, tol=14*MMU,
                      destination="temp_output")
    after = tab_aligned.mz.values
    pm = tab_aligned.peakmap.values[0]
    s0 = pm.spectra[0].peaks[:,0]
    assert abs(s0[0]-202.121231079) < 1e-5, float(s0[0])
    assert abs(after[0]-272.199238673) < 1e-5, float(after[0])

    assert len(glob.glob("temp_output/2011-10-06_054_PKTB*"))==4

    # former errror: transformation resulted in numpy.float64 values
    assert tab_aligned.get(tab_aligned.colTypes, "mz") == float
    assert tab_aligned.get(tab_aligned.colTypes, "mzmin") == float
    assert tab_aligned.get(tab_aligned.colTypes, "mzmax") == float
