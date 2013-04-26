#encoding: utf-8

from libms.DataStructures.Table import Table

def toTable(colName, iterable,  fmt="", type_=None, title="", meta=None):
    return Table.toTable(colName, iterable, fmt, type_, title, meta)

toTable.__doc__ = Table.toTable.__doc__


def _topo_sort_with_in_order(orderings):

    for ordering in orderings:
        assert isinstance(ordering, (list, tuple, str, unicode))

    # give nodes some rank according to first appearance
    # in orderings:
    rank = dict()
    for i, n in enumerate(orderings):
        for ni in n:
            if ni not in rank: # first occurance ?
                rank[ni]=i

    # build graph. each node has follower list, sinks have
    # empty follower list
    nodes = set(ni for n in orderings for ni in n)
    graph = dict()
    for node in nodes:
        graph[node] = set()

    for ordering in orderings:
        for n0, n1 in zip(ordering[:-1], ordering[1:]):
            graph[n0].add(n1)

    # topological sort is easy: remove sinks until graph is empty
    topo_ordering = []

    sinks_to_process = set(n for n in graph if not graph[n])
    while sinks_to_process:
        # here comes special modification: remove sink which appears
        # last in input args of this function:
        current_sink = max(sinks_to_process, key = lambda n: rank[n])

        # remove current sink from todo list
        sinks_to_process.remove(current_sink)
        # update topo_ordering
        topo_ordering.insert(0, current_sink)

        # remove current sink from graph
        del graph[current_sink]
        for followers in graph.values():
            if current_sink in followers:
                followers.remove(current_sink)

        # as we removed sink, maybe new sinks appeared, so
        # update sinks_to_process:
        for n in graph:
            if not graph[n]:
                sinks_to_process.add(n)

    if len(topo_ordering) != len(nodes):
        return None # failed
    return topo_ordering


def _build_starttable(tables, force_merge):
    colname_orders = []
    for table in tables:
        colname_orders.append(table._colNames)

    colum_names = _topo_sort_with_in_order(colname_orders)
    if colum_names is None:
        raise Exception("could not combine all column names to a "\
                "consistent order. you have to provide a reference table")

    types = dict()
    for table in tables:
        for name in table._colNames:
            type_ = table.getType(name)
            if types.get(name, type_) != type_:
                if not force_merge:
                    raise Exception("type conflictfor column %s" % name)
                print "type conflict:",name, types.get(name, type_), type_
            types[name] = type_

    formats = dict()
    for table in tables:
        for name in table._colNames:
            format_ = table.getFormat(name)
            if formats.get(name, format_) != format_:
                if not force_merge:
                    raise Exception("format conflict for column %s" % name)
                print "format conflict:", name, formats.get(name, format_), format_
            formats[name] = format_


    final_types = [types.get(n) for n in colum_names]
    final_formats = [formats.get(n) for n in colum_names]

    prototype = Table(colum_names, final_types, final_formats,
                                                      circumventNameCheck=True)
    return prototype, colum_names

def mergeTables(tables, reference_table=None, force_merge=False):
    """ merges tables. Eg:

        .. pycon::
           t1 = ms.toTable("a",[1])
           t2 = t1.copy()
           t1.addColumn("b", 3)
           t2.addColumn("c", 5)

           t1.print_()
           t2.print_()
           t3 = ms.mergeTables([t1, t2])
           t3.print_()

        in case of conflicting names, name orders, types or formats
        you can try ``force_merge=True`` or provide a reference
        table. This reference table just serves information about
        wanted column names, types and formats and  is merged to the result
        only if it appers in  ``tables``.

    """
    if reference_table is not None:
        final_colnames = reference_table._colNames
        start_with = reference_table.buildEmptyClone()
    else:
        start_with, final_colnames  = _build_starttable(tables, force_merge)

    extended_tables = []
    for table in tables:
        missing_names = [c for c in final_colnames if c not in table._colNames]
        for name in missing_names:
            type_ = start_with.getType(name)
            format_ = start_with.getFormat(name)
            table.addColumn(name, None, type_, format_)
        table = table.extractColumns(*final_colnames)
        extended_tables.append(table)

    result = extended_tables[0]
    result.append(extended_tables[1:])
    return result


def openInBrowser(urlPath):
    """
    opens *urlPath* in browser, eg:

    .. pycon::
        ms.openInBrowser("http://emzed.biol.ethz.ch") !noexec

    """
    from PyQt4.QtGui import QDesktopServices
    from PyQt4.QtCore import QUrl
    import os.path

    url = QUrl(urlPath)
    scheme = url.scheme()
    if scheme not in ["http", "ftp", "mailto"]:
        # C:/ or something simiar:
        if os.path.splitdrive(urlPath)[0] != "":
            url = QUrl("file:///"+urlPath)
    ok = QDesktopServices.openUrl(url)
    if not ok:
        raise Exception("could not open '%s'" % url.toString())


def _recalculateMzPeakFor(postfix):
    def calculator(table, row, name, postfix=postfix):

        mzmin = table.get(row, "mzmin"+postfix)
        mzmax = table.get(row, "mzmax"+postfix)
        rtmin = table.get(row, "rtmin"+postfix)
        rtmax = table.get(row, "rtmax"+postfix)
        pm    = table.get(row, "peakmap"+postfix)
        mz = pm.representingMzPeak(mzmin, mzmax, rtmin, rtmax)
        return mz if mz is not None else (mzmin+mzmax)/2.0
    return calculator

def _hasRangeColumns(table, postfix):
    return all([table.hasColumn(n + postfix) for n in ["rtmin", "rtmax",
                                                 "mzmin", "mzmax", "peakmap"]])

def recalculateMzPeaks(table):
    #TODO: tests !
    """Adds mz value for peaks not detected with centwaves algorithm based on
       rt and mz window: needed are columns mzmin, mzmax, rtmin, rtmax and
       peakmap mz, postfixes are automaticaly taken into account"""
    postfixes = [ "" ] + [ "__%d" % i for i in range(len(table._colNames))]
    for postfix in postfixes:
        if _hasRangeColumns(table, postfix):
            mz_col = "mz" + postfix
            if table.hasColumn(mz_col):
                table.replaceColumn(mz_col, _recalculateMzPeakFor(postfix),
                                    format="%.5f", type_=float)
            else:
                table.addColumn(mz_col, _recalculateMzPeakFor(postfix),
                                format="%.5f", type_=float)

