from libms.RConnect import CentwaveFeatureDetector as _Centwave
from libms.RConnect import MatchedFilterFeatureDetector as _MatchedFilters


def runCentwave(pm, **kws):
    det = _Centwave(**kws)
    return det.process(pm)

def runMatchedFilters(pm, **kws):
    det = _MatchedFilters(**kws)
    return det.process(pm)