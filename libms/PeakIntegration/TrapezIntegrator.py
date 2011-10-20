from PeakIntegrator import PeakIntegrator

class TrapezIntegrator(PeakIntegrator):

    def __str__(self):
        return "TrapezIntegrator()"

    def integrator(self, allrts, fullchromatogram, rts, chromatogram):

        if len(rts) == 2:
             ix = allrts.index(rts[0])
             area = 0.5 * (chromatogram[0]+chromatogram[1])*(rts[1]-rts[0])
             return area, 0.0, (rts, chromatogram)

        if len(rts) == 1:
            return 0, 0.0, (rts, chromatogram)

        area = self.trapez(rts, chromatogram)
        return area, 0.0, (rts, chromatogram)

    def getSmoothed(self, rtvalues, params):
        return params
