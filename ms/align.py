#encoding:utf-8

def rtAlign(tables, refTable = None, destination = None, nPeaks=-1,
            numBreakpoints=5, maxRtDifference = 100, maxMzDifference = 0.3,
            maxMzDifferencePairfinder = 0.5, forceAlign=False):

    """ aligns feature tables in respect to retention times.
        the algorithm produces new tables with aligned data.
        **input tables including the assiciatoted peakmap(s) are not modified**.

        Parameters:

            - *nPeaks*: max number of peaks matched by superimposer, -1
              means: all peaks

            - *maxRtDifference*: max allowed difference in rt values for
              searching matching features.

            - *maxMzDifference*: max allowed difference in mz values for
              super imposer.

            - *maxMzDifferencePairfinder*: max allowed difference in mz values
              for pair finding.

            - *numBreakpoints*: number of break points of fitted spline.
              default:5, more points result in splines with higher variation.

            - *forceAlign*: has to be *True* to align already rt aligned tables.

            - *refTable*: extra reference table, if *None* the table
              with most features among *tables* is taken.
    """

    import os.path
    import pyopenms
    import copy
    from  libms.DataStructures.Table import toOpenMSFeatureMap, Table
    import custom_dialogs

    assert refTable is None or isinstance(refTable, Table)
    assert destination is None or isinstance(destination, basestring)

    for table in tables:
        # collect all maps
        maps = set(table.peakmap.values)
        assert len(maps) == 1, "can only align features from one single peakmap"
        map = maps.pop()
        assert map != None, "None value for peakmaps not allowed"
        if forceAlign:
            map.meta["rt_aligned"]=False
        else:
            if map.meta.get("rt_aligned"):
                message = "there are already rt_aligned peakmaps in the "\
                          "tables.\nyou have to provide the forceAlign "\
                          "parameter of this function\nto align all tables"
                raise Exception(message)
        assert isinstance(table, Table), "non table object in tables"
        table.requireColumn("mz"), "need mz column for alignment"
        table.requireColumn("rt"), "need rt column for alignment"

    if destination is None:
        destination = custom_dialogs.askForDirectory()
        if destination is None:
            print "aborted"
            return

    if refTable is not None:
        maps = set(refTable.peakmap.values)
        assert len(maps) == 1, "can only align features from one single peakmap"
        map = maps.pop()
        assert map != None, "None value for peakmaps not allowed"
        refTable.requireColumn("mz"), "need mz column in reftable"
        refTable.requireColumn("rt"), "need rt column in reftable"

    assert os.path.isdir(os.path.abspath(destination)), "target is no directory"

    # setup algorithm
    algo = pyopenms.MapAlignmentAlgorithmPoseClustering()
    algo.setLogType(pyopenms.LogType.CMD)

    algo_params = algo.getDefaults()
    algo_params["max_num_peaks_considered"] = nPeaks
    algo_params["superimposer:num_used_points"] = nPeaks
    algo_params["superimposer:mz_pair_max_distance"] = float(maxMzDifferencePairfinder)
    algo_params["pairfinder:distance_RT:max_difference"] = float(maxRtDifference)
    algo_params["pairfinder:distance_MZ:max_difference"] = float(maxMzDifference)
    algo_params["pairfinder:distance_MZ:unit"] = "Da"
    algo.setParameters(algo_params)


    # convert to pyOpenMS types and find map with max num features which
    # is taken as refamp:
    fms = [ (toOpenMSFeatureMap(table), table) for table in tables]
    if refTable is None:
        refMap, refTable = max(fms, key=lambda (fm, t): fm.size())
        print
        print "REFMAP IS",
        print os.path.basename(refTable.meta.get("source","<noname>"))
    else:
        if refTable in tables:
            refMap = fms[tables.index(refTable)][0]
        else:
            refMap = toOpenMSFeatureMap(refTable)
    results = []
    for fm, table in fms:
        # we do not modify existing table inkl. peakmaps: (rt-values
        # might change below in _transformTable) !
        table = copy.deepcopy(table)
        if fm is refMap:
            results.append(table)
            continue
        sources = set(table.source.values)
        assert len(sources)==1, "multiple sources in table"
        source = sources.pop()
        filename = os.path.basename(source)
        print
        print "ALIGN FEATURES FROM ", filename
        print
        transformation = _computeTransformation(algo, refMap, fm, numBreakpoints)
        _plot_and_save(transformation, filename, destination)
        _transformTable(table, transformation)
        results.append(table)
    for t in results:
        t.meta["rt_aligned"] = True
    return results

def _computeTransformation(algo, refMap, fm, numBreakpoints):
    # be careful: alignFeatureMaps modifies second arg,
    # so you MUST NOT put the arg as [] into this
    # function ! in this case you have no access to the calculated
    # transformations.
    import pyopenms
    #ts = []
    # index is 1-based, so 1 refers to refMap when calling
    # alignFeatureMaps below:
    algo.setReference(refMap)
    trafo = pyopenms.TransformationDescription()
    if (refMap == fm):
        trafo.fitModel("identity")
    else:
        algo.align(fm, trafo)
        model_params = pyopenms.Param()
        pyopenms.TransformationModelBSpline.getDefaultParameters(model_params)

        model_params.setValue("num_breakpoints", numBreakpoints, "", [])
        trafo.fitModel("b_spline", model_params)
        trafo.getModelParameters(model_params)

    return trafo

def _plot_and_save(transformation, filename, destination):
    import numpy as np
    import matplotlib
    matplotlib.use("Qt4Agg")
    import pylab
    import os.path
    dtp = transformation.getDataPoints()
    print len(dtp), "matching data points"
    if len(dtp) == 0:
        raise Exception("no matches found.")

    x,y = zip(*dtp)
    x = np.array(x)
    y = np.array(y)
    pylab.clf()
    pylab.plot(x, y-x, ".")
    x.sort()
    yn = [ transformation.apply(xi) for xi in x]
    pylab.plot(x, yn-x)
    filename = os.path.splitext(filename)[0]+"_aligned.png"
    target_path = os.path.join(destination, filename)
    print
    print "SAVE", os.path.abspath(target_path)
    print
    pylab.savefig(target_path)

def _transformTable(table, transformation):

    transfun = lambda x: transformation.apply(x)

    table.replaceColumn("rt", table.rt.apply(transfun))
    table.replaceColumn("rtmin", table.rtmin.apply(transfun))
    table.replaceColumn("rtmax", table.rtmax.apply(transfun))

    # we know that there is only one peakmap in the table
    peakmap = table.peakmap.values[0]
    peakmap.meta["rt_aligned"] = True
    table.meta["rt_aligned"] = True
    for spec in peakmap.spectra:
        spec.rt = transformation.apply(spec.rt)
    table.replaceColumn("peakmap", peakmap)

