from collections import defaultdict as  _defaultdict
from scipy.stats import f_oneway as _f_oneway, kruskal as _kruskal
import numpy as _numpy

from ..DataStructures.Table import Table


def _getSamples(factorColumn, dependentColumn, minsize=1):
    factors, _, _ = factorColumn._eval(None)
    dependents, _, _ = dependentColumn._eval(None)
    groups = _defaultdict(list)
    for factor, depenent in zip(factors, dependents):
        groups[factor].append(depenent)
    samples = groups.values()
    if any(len(s) < minsize for s in samples):
        print "WARNING: sample has less than %d subjects" % minsize
    return map(_numpy.array, samples)


def oneWayAnova(factorColumn, dependentColumn):
    F, p = _f_oneway(*_getSamples(factorColumn, dependentColumn))
    return F, p


def kruskalWallis(factorColumn, dependentColumn):
    H, p = _kruskal(*_getSamples(factorColumn, dependentColumn, 5))
    return H, p


def _runStatistcsOnTables(tableSet1, tableSet2, idColumn, valueColumn,
                          pCalculator):
    ids = set()
    for t in tableSet1:
        ids.update(t.getColumn(idColumn).values)
    for t in tableSet2:
        ids.update(t.getColumn(idColumn).values)

    result = Table(["id", "n1", "n2",
                    "avg1_" + valueColumn, "std1_" + valueColumn,
                    "avg2_" + valueColumn, "std2_" + valueColumn,
                    "p_value"],
                   [str, int, int] + 5 * [float],
                   ["%s", "%d", "%d"] + 5 * ["%.2e"])

    for id_ in ids:
        samples1 = []
        for t in tableSet1:
            subt = t.filter(t.getColumn(idColumn) == id_)
            samples1.extend(subt.getColumn(valueColumn).values)
        samples2 = []
        for t in tableSet2:
            subt = t.filter(t.getColumn(idColumn) == id_)
            samples2.extend(subt.getColumn(valueColumn).values)

        samples1 = _numpy.array([s for s in samples1 if s is not None])
        samples2 = _numpy.array([s for s in samples2 if s is not None])

        p = pCalculator(samples1, samples2)

        new_row = [ id_,
                      len(samples1), len(samples2), ]
        for v in [ _numpy.mean(samples1), _numpy.std(samples1),
                   _numpy.mean(samples2), _numpy.std(samples2),
                   p]:
            if _numpy.isnan(v):
                v = None
            else:
                v = float(v)
            new_row.append(v)

        result.addRow(new_row)

    return result


def oneWayAnovaOnTables(tableSet1, tableSet2, idColumn, valueColumn):
    """
    Compares two sets of tables. Each set is a list of tables, with
    common columns ``idColumn`` and ``valueColumn``. The first one
    is a factor which used to build groups, the latter is the dependent
    numerical value.

    Eg you have to lists with tables, where each table has factor column
    ``compound`` and dependent value column ``foldChange``.  Then you get
    a result table which looks like:

    .. pycon::
       :invisible:

       t = ms.toTable("id", ["ATP", "ADP"])
       t.addColumn("n1", [4,5])
       t.addColumn("n2", [6,6])
       t.addColumn("avg1_foldChange", [1.4, 1.6])
       t.addColumn("std1_foldChange", [0.4, 0.13])
       t.addColumn("avg2_foldChange", [0.4, 1.5])
       t.addColumn("std2_foldChange", [0.3, 0.08])
       t.addColumn("p_value", [0.9, 0.23])
       tresult=t


    .. pycon::
       tresult = ms.oneWayAnovaOnTables(tables1, tables2, idColumn="compound", valueColumn="foldChange") !noexec
       tresult.print_()

    """
    result = _runStatistcsOnTables(tableSet1, tableSet2, idColumn, valueColumn,
             lambda s1, s2: _f_oneway(s1, s2)[1])
    result.title = "ANOVA ANALYSIS"
    return result


def kruskalWallisOnTables(tableSet1, tableSet2, idColumn, valueColumn):
    """
       Works as :py:meth:`~ms.oneWayAnovaOnTables` above, but uses non parametric kruskal wallis test.
    """
    result = _runStatistcsOnTables(tableSet1, tableSet2, idColumn, valueColumn,
             lambda s1, s2: _kruskal(s1, s2)[1])
    result.title = "KRUSKAL WALLIS ANALYSIS"
    return result
