#encoding: utf-8



def integrate(ftable, integratorid="std", msLevel=1, showProgress = True):
    """ integrates features  in ftable.
        returns processed table. ``ftable`` is not changed inplace.

        The peak integrator corresponding to the integratorId is
        defined in ``configs.py`` or ``local_configs.py``

    """
    from configs import peakIntegrators
    from libms.DataStructures.Table import Table
    from libms.DataStructures.MSTypes import PeakMap
    import sys
    import time
    import copy

    assert isinstance(ftable, Table)

    neededColumns = ["mzmin", "mzmax", "rtmin", "rtmax", "peakmap"]
    supportedPostfixes = ftable.supportedPostfixes(neededColumns)
    if not supportedPostfixes:
        raise Exception("is no feature table")

    started = time.time()
    integrator = dict(peakIntegrators).get(integratorid)
    if integrator is None:
        raise Exception("unknown integrator '%s'" % integratorid)

    resultTable = ftable.copy()

    lastcent = -1
    for postfix in supportedPostfixes:
        areas = []
        rmses = []
        paramss =[]
        for i, row in enumerate(ftable.rows):
            if showProgress:
                # integer div here !
                cent = ((i+1)*20)/len(ftable)/len(supportedPostfixes)
                if cent != lastcent:
                    print cent*5,
                    sys.stdout.flush()
                    lastcent = cent
            rtmin = ftable.get(row, "rtmin"+postfix)
            rtmax = ftable.get(row, "rtmax"+postfix)
            mzmin = ftable.get(row, "mzmin"+postfix)
            mzmax = ftable.get(row, "mzmax"+postfix)
            peakmap = ftable.get(row, "peakmap"+postfix)
            if rtmin is None or rtmax is None or mzmin is None or mzmax is None\
                     or peakmap is None:
                area, rmse, params = (None, )* 3
            else:
                # this is a hack ! ms level n handling should first be
                # improved and gerenalized in MSTypes.py
                integrator.setPeakMap(peakmap)
                result = integrator.integrate(mzmin, mzmax, rtmin, rtmax,
                                             msLevel)
                # take existing values which are not integration realated:
                area, rmse, params = result["area"], result["rmse"],\
                                     result["params"]

            areas.append(area)
            rmses.append(rmse)
            paramss.append(params)

        resultTable.updateColumn("method"+postfix, integratorid, str, "%s",\
                                  insertBefore="peakmap"+postfix)
        resultTable.updateColumn("area"+postfix, areas, float, "%.2e",\
                                  insertBefore="peakmap"+postfix)
        resultTable.updateColumn("rmse"+postfix, rmses, float, "%.2e",\
                                  insertBefore="peakmap"+postfix)
        resultTable.updateColumn("params"+postfix, paramss, object, None,\
                                  insertBefore="peakmap"+postfix)


    resultTable.meta["integrated"]=True
    resultTable.title = "integrated: "+ (resultTable.title or "")
    needed = time.time() - started
    minutes = int(needed)/60
    seconds = needed - minutes * 60
    print
    if minutes:
        print "needed %d minutes and %.1f seconds" % (minutes, seconds)
    else:
        print "needed %.1f seconds" % seconds
    resultTable.resetInternals()
    return resultTable
