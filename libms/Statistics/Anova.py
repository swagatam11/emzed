from collections import defaultdict
from scipy.stats import f_oneway, kruskal
import numpy

def _getSamples(factorColumn, dependentColumn, minsize=1):
    factors, _ = factorColumn._eval(None)
    dependents, _ = dependentColumn._eval(None)
    groups = defaultdict(list)
    for factor, depenent in zip(factors, dependents):
        groups[factor].append(depenent)
    samples = groups.values()
    if any(len(s) < minsize for s in samples):
        print "WARNING: sample has less than %d subjects" % minsize
    return map(numpy.array, samples)

def oneWayAnova(factorColumn, dependentColumn):
    F, p = f_oneway(*_getSamples(factorColumn, dependentColumn))
    return F, p

def kruskalWallis(factorColumn, dependentColumn):
    H, p = kruskal(*_getSamples(factorColumn, dependentColumn, 5))
    return H, p

