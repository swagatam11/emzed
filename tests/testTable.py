#encoding: utf-8

from libms.DataStructures.Table import Table
import ms
import numpy as np
import pickle, os, re

def testRunnerTable():

    with ExceptionTester():
        Table(["a"],[np.float32],["%f"],[[32.0]])

    #build table
    names="int long float str object array".split()
    types = [int, long, float, str, object, np.ndarray,]
    formats = [ "%3d", "%d", "%.3f", "%s", "%r", "'array(%r)' % (o.shape,)" ]

    row1 = [ 1, 12323L, 1.0, "hi", { 1: 1 },  np.array((1,2,3)) ]
    row2 = [ 2, 22323L, 2.0, "hi2", [2,3,], np.array(((2,3,4),(1,2,3))) ]
    row3 = [ 3, 32323L, 3.0, "hi3", (3,) , np.array(((3,3,4,5),(1,2,3,4))) ]

    rows = [row1, row2, row3]
    t=Table(names, types, formats, rows, "testtabelle", meta=dict(why=42))


    run(t, names, [row1, row2, row3])
    # test pickle
    dat = pickle.dumps(t)
    t = pickle.loads(dat)
    run(t, names, [row1, row2, row3])
    ms.storeTable(t, u"temp_output/test.table")
    try:
        ms.storeTable(t, "temp_output/test.table")
        assert False, "no exception thrown althoug file should exist!"
    except:
        pass
    ms.storeTable(t, "temp_output/test.table", True)
    t = ms.loadTable("temp_output/test.table")
    run(t, names, [row1, row2, row3])


def run(t, colnames, rows):
    t = t.copy()
    ixs = set()
    for i, name in enumerate(colnames):
        ixs.add(t.getIndex(name))
    assert not None in ixs
    assert len(ixs) == len(colnames)

    # test iteration
    content = []
    for row in t.rows:
        for (cell, formatter) in zip(row, t.colFormatters):
            content.append( formatter(cell))
        break

    # test formatting
    assert content[0] == "  1"
    assert content[1] == "12323"
    assert content[2] == "1.000"
    assert content[3] == "hi"
    assert content[4] == repr({1:1})
    assert content[5] in ("array((3,))", "array((3L,))"), content[5]

    assert set(t.getVisibleCols()) == { 'int', 'long', 'float', 'str',
                                        'object', 'array' }


    expr = t.str.contains("hi")
    tn = t.filter(expr)
    assert len(tn) == 3
    tn = t.filter(~ t.str.contains("hi"))
    assert len(tn) == 0

    tn = t.filter(t.str.contains("2"))
    assert len(tn) == 1



    # test requireColumn
    for name in colnames:
        t.requireColumn(name)

    ex = None
    try:
        t.requireColumn("asdfkl�dsflkjaldfkja�sdlfjal�djf")
    except Exception, e:
        ex = e
    assert ex is not None

    # test other fields
    assert t.meta["why"] == 42
    assert t.title == "testtabelle"

    t.sortBy("int", ascending=False)

    # restrct cols
    tn = t.extractColumns("int", "long")
    assert len(tn.getColNames()) == 2, len(t.getColNames())
    assert len(tn.getColTypes()) == 2
    assert len(tn.getColFormats()) == 2

    assert len(tn) == len(t)

    assert tn.meta["why"] == 42
    assert tn.title == "testtabelle"

    tn.addEnumeration()
    assert set(tn.getVisibleCols()) == { 'int', 'long', 'id' }
    assert tn.getColNames()[0]=="id"
    assert list(tn.id) == range(len(t))

    tn.renameColumns(int='iii')
    assert set(tn.getVisibleCols()) == { 'iii', 'long', 'id' }

    tn.addColumn('x', 'hi', str, '%s')
    assert set(tn.getVisibleCols()) == { 'iii', 'long', 'id', 'x' }
    assert tn.getColNames()[-1]=="x"

    assert list(tn.x) == ["hi"]*len(tn)

    before = set(os.listdir("temp_output"))
    tn.storeCSV(u"temp_output/x.csv")

    tnre  = ms.loadCSV("temp_output/x.csv")
    assert len(tnre) == len(tn)
    assert tnre.getColNames() == tn.getColNames()
    assert tnre.id.values == tn.id.values
    assert tnre.iii.values == tn.iii.values
    assert tnre.long.values == tn.long.values
    assert tnre.x.values == tn.x.values



    tn.storeCSV("temp_output/x.csv", onlyVisibleColumns=False)
    after = set(os.listdir("temp_output"))
    # file written twice !
    assert len(after-before) == 2
    for n in after-before:
        # maybe we have some x.csv.? from previous run of this
        #function so we can not assume that we find x.csv and
        #x.csv.1
        assert re.match("x.csv(.\d+)?", n)

    ex = None
    try:
        # wrong file extension
        tn.storeCSV("temp_output/x.dat")
    except Exception, e:
        ex = e

    assert ex != None

    # computed by exrpression
    tn.print_()
    tn.addColumn("computed", tn.long / (tn.iii + 1))
    # computed by callback:
    tn.addColumn("squared", lambda t,r,n: t.getValue(r, "iii")**2)


    assert list(tn.getColumn("computed").values ) == [8080, 7441, 6161], tn.computed.values
    assert list(tn.getColumn("squared").values ) == [9, 4, 1]


    tn.replaceColumn("squared", tn.squared+1)
    assert list(tn.getColumn("squared").values ) == [10, 5, 2]
    assert len(tn.getColNames())  == 6

    tx  = tn.copy()
    tx.dropColumns("squared", "computed")
    assert tx.getColNames() == ["id", "iii", "long", "x"]
    assert len(tx) == 3

    tn.dropColumns("computed", "squared")
    assert tn.getColNames() == ["id", "iii", "long", "x"]
    assert len(tn) == 3

    tn.dropColumns("id", "x")
    t2 = tn.copy()
    res = tn.leftJoin(t2, tn.iii == tn.long)
    assert len(res) == len(t2)
    res = tn.leftJoin(t2, tn.iii == tn.iii)
    assert len(res) == len(t2)**2
    res = tn.leftJoin(t2, (tn.iii == tn.iii) & (t2.long==32323))
    assert len(res) == len(t2)

    res = tn.join(t2, tn.iii == tn.long)
    assert len(res) == 0
    res = tn.join(t2, tn.long == tn.iii)
    assert len(res) == 0
    res = tn.join(t2, tn.iii == tn.iii)
    assert len(res) == len(t2)**2, len(res)
    res = tn.join(t2, (tn.iii == tn.iii) & (t2.long==32323))
    assert len(res) == len(t2), len(res)

    tx = tn.filter(tn.iii.isIn([1,4]))
    tx._print()
    assert len(tx) == 1
    assert tx.iii.values == [1]

    tn.addColumn("li", [1,2,3])
    assert len(tn) == 3
    assert len(tn.getColNames()) == 3
    assert "li" in tn.getColNames()

    tn.addRow([1, 1, 1])
    assert len(tn) == 4

    ex = None
    try:
        tn.addRow([1,2,3,2])
    except Exception, e:
        ex = e
    assert ex is not None

    ex = None
    try:
        tn.addRow(["a",1,2])
    except Exception, e:
        ex = e
    assert ex is not None


def testSomePredicates():
    #build table
    names="int long float str object array".split()
    types = [int, long, float, str, object, np.ndarray,]
    formats = [ "%3d", "%d", "%.3f", "%s", "%r", "'array%r' % (o.shape,)" ]

    row1 = [ 1, 12323L, 1.0, "hi", { 1: 1 },  np.array((1,2,3)) ]
    row2 = [ 2, 22323L, 2.0, "hi2", [2,3,], np.array(((2,3,4),(1,2,3))) ]
    row3 = [ 3, 32323L, 3.0, "hi3", (3,) , np.array(((3,3,4,5),(1,2,3,4))) ]

    rows = [row1, row2, row3]
    t=Table(names, types, formats, rows, "testtabelle", meta=dict(why=42))

    tn = t.filter((t.int+t.float).inRange(-1, 2))
    assert len(tn) == 1
    assert tn.getValue(tn.rows[0], "int") == 1
    tn = t.filter((t.float+t.int).inRange(-1, 2))
    assert len(tn) == 1
    assert tn.getValue(tn.rows[0], "int") == 1

    tn = t.filter(t.float.approxEqual(1.0, t.int/10))
    tn._print()
    assert len(tn) == 1, len(tn)
    assert tn.getValue(tn.rows[0], "int") == 1



def testDoubleColumnames():
    ex = None
    try:
        colnames = ["col0", "col0", "col1", "col1", "col2"]
        Table(colnames, []*5, []*5)
    except Exception, e:
        ex = e.message
    assert ex != None
    assert "multiple" in ex
    assert "col0" in ex
    assert "col1" in ex
    assert "col2" not in ex

def testDetectionOfUnallowdColumnNames():
    ex = None
    try:
        Table(["__init__"], [int],["%d"])
    except Exception, e:
        ex = e.message
    assert ex != None
    assert "not allowed" in ex


def testWithEmtpyTablesAndTestColnameGeneration():
    e = ms.toTable("x", [])
    f = ms.toTable("y", [])
    g = ms.toTable("z", [1])

    assert len(e.filter(e.x == 0)) == 0
    t1 = e.join(f, f.y == e.x)
    assert len(t1) == 0
    assert t1.getColNames() == ["x", "y__0"], t1.getColNames()
    t1 = e.join(f, e.x == f.y)
    assert len(t1) == 0
    assert t1.getColNames() == ["x", "y__0"], t1.getColNames()

    t1 = e.join(g, g.z == e.x)
    assert len(t1) == 0
    assert t1.getColNames() == ["x", "z__0"], t1.getColNames()
    t1 = e.join(g, e.x == g.z)
    assert len(t1) == 0
    assert t1.getColNames() == ["x", "z__0"], t1.getColNames()


    t1 = g.join(e, e.x == g.z)
    assert len(t1) == 0
    assert t1.getColNames() == ["z", "x__0"], t1.getColNames()
    t1 = g.join(e, g.z == e.x)
    assert len(t1) == 0
    assert t1.getColNames() == ["z", "x__0"], t1.getColNames()

    t1 = e.leftJoin(f, f.y == e.x)
    assert len(t1) == 0
    assert t1.getColNames() == ["x", "y__0"], t1.getColNames()
    t1 = e.leftJoin(g, g.z == e.x)
    assert len(t1) == 0
    assert t1.getColNames() == ["x", "z__0"], t1.getColNames()
    t1 = g.leftJoin(e, e.x == g.z)
    assert len(t1) == 1
    assert t1.getColNames() == ["z", "x__0"], t1.getColNames()
    assert t1.rows[0] ==  [1, None]

    t1.print_()
    f.print_()
    t2 = t1.leftJoin(f, f.y == t1.x__0)
    assert t2.getColNames() ==["z", "x__0", "y__1"], t2.getColNames()
    assert len(t2) == 1


class ExceptionTester(object):

    def __init__(self, *expected):
        self.expected = expected or [Exception]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        assert a[0] in self.expected
        return True # suppress exceptoin

def testUniqeNotNone():

    t = ms.toTable("a", [1,1,None])
    assert t.a.uniqueNotNone() == 1

    t = ms.toTable("a", [1,1,1])
    assert t.a.uniqueNotNone() == 1

    t.addColumn("b", None)
    t._print()
    with ExceptionTester():
        t.b.uniqueNotNone()
    t.addColumn("c", [None, 1,2 ])
    with ExceptionTester():
        t.c.uniqueNotNone()

    t.addColumn("d", [1,2, 2 ])
    with ExceptionTester():
        t.d.uniqueNotNone()

    with ExceptionTester():
        t.addColumn("d", [2,3,4])

    with ExceptionTester():
        t.addConstantColumn("d", 3)

    t2 = ms.toTable("x",[])
    with ExceptionTester():
        t.aggregate(t2.x.mean, "neu")

def testWithNoneValues():

    # simple int compare ###################################
    t = ms.toTable("a", [None, 2])
    t.print_()

    assert len(t.filter(t.a < 3)) == 1

    t2 = t.copy()
    assert len(t.join(t2, t.a==t2.a)) == 1
    t.leftJoin(t2, t.a==t2.a).print_()

    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    t.sortBy("a")

    assert len(t.join(t2, t.a==t2.a)) == 1
    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    t.sortBy("a", ascending=False)

    assert len(t.join(t2, t.a==t2.a)) == 1
    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    t = ms.toTable("a", [None, 2.0])
    t.print_()

    assert len(t.filter(t.a < 3)) == 1

    t2 = t.copy()
    assert len(t.join(t2, t.a==t2.a)) == 1
    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    # simple float compare ##################################
    t.print_()
    t2.print_()
    t.leftJoin(t2, t.a<t2.a).print_()
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    t.join(t2, t.a!=t2.a).print_()
    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    t.sortBy("a", ascending=True)

    assert len(t.join(t2, t.a==t2.a)) == 1
    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    t.join(t2, t.a!=t2.a).print_()
    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    t.sortBy("a", ascending=False)

    assert len(t.join(t2, t.a==t2.a)) == 1
    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    t.join(t2, t.a!=t2.a).print_()
    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    # simple str compare ###################################
    t = ms.toTable("a", [None, "2"])
    t.filter(t.a < "3").print_()

    assert len(t.filter(t.a < "3")) == 1

    t2 = t.copy()
    assert len(t.join(t2, t.a==t2.a)) == 1
    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    t.join(t2, t.a!=t2.a).print_()
    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    t.sortBy("a", ascending=True)
    assert len(t.join(t2, t.a==t2.a)) == 1
    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    t.join(t2, t.a!=t2.a).print_()
    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2

    t.sortBy("a", ascending=False)
    assert len(t.join(t2, t.a==t2.a)) == 1
    assert len(t.leftJoin(t2, t.a==t2.a)) == 2

    assert len(t.join(t2, t.a<=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a<t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    t.join(t2, t.a!=t2.a).print_()
    assert len(t.join(t2, t.a!=t2.a)) == 0
    assert len(t.leftJoin(t2, t.a!=t2.a)) == 2

    assert len(t.join(t2, t.a>=t2.a)) == 1
    assert len(t.leftJoin(t2, t.a<=t2.a)) == 2

    assert len(t.join(t2, t.a>t2.a)) == 0
    assert len(t.leftJoin(t2, t.a<t2.a)) == 2


    # simple float compare reversed #########################
    t = ms.toTable("a", [None, 2.0])
    t.print_()

    assert len(t.filter(3.0 > t.a)) == 1
    assert len(t.filter(3.0 >= t.a)) == 1
    assert len(t.filter(3.0 == t.a)) == 0
    assert len(t.filter(3.0 < t.a)) == 0
    assert len(t.filter(3.0 <= t.a)) == 0
    assert len(t.filter(3.0 != t.a)) == 1
    assert len(t.filter(3 > t.a)) == 1
    assert len(t.filter(3 >= t.a)) == 1
    assert len(t.filter(3 == t.a)) == 0
    assert len(t.filter(3 < t.a)) == 0
    assert len(t.filter(3 <= t.a)) == 0
    assert len(t.filter(3 != t.a)) == 1

    t.sortBy("a")
    t.print_()
    t.filter(3 > t.a).print_()
    assert len(t.filter(3 > t.a)) == 1
    assert len(t.filter(3 >= t.a)) == 1
    assert len(t.filter(3 == t.a)) == 0
    assert len(t.filter(3 < t.a)) == 0
    assert len(t.filter(3 <= t.a)) == 0
    assert len(t.filter(3 != t.a)) == 1
    assert len(t.filter(3.0 > t.a)) == 1
    assert len(t.filter(3.0 >= t.a)) == 1
    assert len(t.filter(3.0 == t.a)) == 0
    assert len(t.filter(3.0 < t.a)) == 0
    assert len(t.filter(3.0 <= t.a)) == 0
    assert len(t.filter(3.0 != t.a)) == 1

    t.sortBy("a", ascending=False)
    assert len(t.filter(3 > t.a)) == 1
    assert len(t.filter(3 >= t.a)) == 1
    assert len(t.filter(3 == t.a)) == 0
    assert len(t.filter(3 < t.a)) == 0
    assert len(t.filter(3 <= t.a)) == 0
    assert len(t.filter(3 != t.a)) == 1
    assert len(t.filter(3.0 > t.a)) == 1
    assert len(t.filter(3.0 >= t.a)) == 1
    assert len(t.filter(3.0 == t.a)) == 0
    assert len(t.filter(3.0 < t.a)) == 0
    assert len(t.filter(3.0 <= t.a)) == 0
    assert len(t.filter(3.0 != t.a)) == 1

    # simple int   compare reversed #########################
    t = ms.toTable("a", [None, 2])
    t.print_()

    assert len(t.filter(3 > t.a)) == 1
    assert len(t.filter(3 >= t.a)) == 1
    assert len(t.filter(3 == t.a)) == 0
    assert len(t.filter(3 < t.a)) == 0
    assert len(t.filter(3 <= t.a)) == 0
    assert len(t.filter(3 != t.a)) == 1

    assert len(t.filter(3.0 > t.a)) == 1
    assert len(t.filter(3.0 >= t.a)) == 1
    assert len(t.filter(3.0 == t.a)) == 0
    assert len(t.filter(3.0 < t.a)) == 0
    assert len(t.filter(3.0 <= t.a)) == 0
    assert len(t.filter(3.0 != t.a)) == 1

    t.sortBy("a")
    assert len(t.filter(3 > t.a)) == 1
    assert len(t.filter(3 >= t.a)) == 1
    assert len(t.filter(3 == t.a)) == 0
    assert len(t.filter(3 < t.a)) == 0
    assert len(t.filter(3 <= t.a)) == 0
    assert len(t.filter(3 != t.a)) == 1

    assert len(t.filter(3.0 > t.a)) == 1
    assert len(t.filter(3.0 >= t.a)) == 1
    assert len(t.filter(3.0 == t.a)) == 0
    assert len(t.filter(3.0 < t.a)) == 0
    assert len(t.filter(3.0 <= t.a)) == 0
    assert len(t.filter(3.0 != t.a)) == 1

    t.sortBy("a", ascending=False)
    assert len(t.filter(3 > t.a)) == 1
    assert len(t.filter(3 >= t.a)) == 1
    assert len(t.filter(3 == t.a)) == 0
    assert len(t.filter(3 < t.a)) == 0
    assert len(t.filter(3 <= t.a)) == 0
    assert len(t.filter(3 != t.a)) == 1

    assert len(t.filter(3.0 > t.a)) == 1
    assert len(t.filter(3.0 >= t.a)) == 1
    assert len(t.filter(3.0 == t.a)) == 0
    assert len(t.filter(3.0 < t.a)) == 0
    assert len(t.filter(3.0 <= t.a)) == 0
    assert len(t.filter(3.0 != t.a)) == 1

    # simple str   compare reversed #########################
    t = ms.toTable("a", [None, "2"])
    t.print_()

    assert len(t.filter("3" > t.a)) == 1
    assert len(t.filter("3" >= t.a)) == 1
    assert len(t.filter("3" == t.a)) == 0
    assert len(t.filter("3" < t.a)) == 0
    assert len(t.filter("3" <= t.a)) == 0
    assert len(t.filter("3" != t.a)) == 1

    t.sortBy("a")
    assert len(t.filter("3" > t.a)) == 1
    assert len(t.filter("3" >= t.a)) == 1
    assert len(t.filter("3" == t.a)) == 0
    assert len(t.filter("3" < t.a)) == 0
    assert len(t.filter("3" <= t.a)) == 0
    assert len(t.filter("3" != t.a)) == 1

    t.sortBy("a", ascending=False)
    assert len(t.filter("3" > t.a)) == 1
    assert len(t.filter("3" >= t.a)) == 1
    assert len(t.filter("3" == t.a)) == 0
    assert len(t.filter("3" < t.a)) == 0
    assert len(t.filter("3" <= t.a)) == 0
    assert len(t.filter("3" != t.a)) == 1

    ##########################################################

    t = ms.toTable("i", [1,2,None])
    assert len(t.filter(t.i.isNone())) == 1
    assert len(t.filter(t.i.isNotNone())) == 2

    t.addColumn("b", [2,3,None])
    assert t.getColNames() == ["i", "b"]
    t.replaceColumn("b", t.b+1)

    assert t.getColNames() == ["i", "b"]

    t.addRow([None, None])
    t.addRow([3, None])
    t.addRow([3, 3.0])
    assert t.b.values == [ 3, 4, None, None, None, 3]

    # check order
    t.replaceColumn("i", t.i)
    assert t.getColNames() == ["i", "b"]

    s = ms.toTable("b",[])
    x = t.join(s, t.b == s.b)
    assert len(x) == 0

    assert s.b.max() == None

def testSomeExpressions():
    t = ms.toTable("mf", ["Ag", "P", "Pb", "P3Pb", "PbP"])
    tn = t.filter(t.mf.containsElement("P"))
    assert len(tn) == 3
    tn = t.filter(t.mf.containsElement("Pb"))
    assert len(tn) == 3


def testIfThenElse():
    t = Table(["a", "b", "c"], [str, int, int], ["%s", "%d", "%d"],[])
    t.rows.append(["0", 1, 2])
    t.rows.append([None, 2, 1])
    t._print()
    t.addColumn("x", (t.a.isNotNone()).thenElse(t.b, t.c))
    assert t.getColNames()==["a", "b", "c", "x"]
    print
    t._print()
    t.addColumn("y", (t.a.isNotNone()).thenElse("ok", "not ok"))
    t._print()
    assert t.y.values == ["ok", "not ok"]


def testDynamicColumnAttributes():
    t = Table(["a", "b", "c"], [str, int, int], ["%s", "%d", "%d"],[])
    t.a
    t.b
    t.c
    assert len(t.a.values) == 0
    assert len(t.b.values) == 0
    assert len(t.c.values) == 0

    t.renameColumns(dict(a="aa"))
    assert "a" not in t.getColNames()
    assert "aa"  in t.getColNames()
    t.aa
    try:
        t.a
        raise Exception("t.a should be deteted")
    except:
        pass

    col = pickle.loads(pickle.dumps(t.aa))
    assert len(col.values) == 0

    t.dropColumns("aa")
    assert "aa" not in t.getColNames()
    try:
        t.aa
        raise Exception("t.aa should be deteted")
    except:
        pass

def testRename():
    t = ms.toTable("a", [1,1,3,4])
    t.addColumn("b", [1,1,3,3])
    t.addColumn("c", [1,2,1,4])
    with ExceptionTester():
        t.renameColumns(dict(d="e"))

    with ExceptionTester():
        t.renameColumns(a="b")

    with ExceptionTester():
        t.renameColumns(a="x", b="x")

    with ExceptionTester():
        t.renameColumns(dict(a="f"), a="d")

    t.renameColumns(dict(a="x"), dict(c="z"), b="y")
    assert tuple(t.getColNames()) == ("x", "y", "z")

def testSplitBy():
    t = ms.toTable("a", [1,1,3,4])
    t.addColumn("b", [1,1,3,3])
    t.addColumn("c", [1,2,1,4])
    t._print()
    subts = t.splitBy("a")
    assert len(subts) == 3
    res = ms.mergeTables(subts)
    assert len(res) == len(t)
    subts[0]._print()
    assert res.a.values == t.a.values
    assert res.b.values == t.b.values
    assert res.c.values == t.c.values

    # check if input tables are not altered
    for subt in subts:
        assert subt.getColNames() == [ "a", "b", "c"]

    subts = t.splitBy("a", "c")
    assert len(subts) == 4
    res = ms.mergeTables(subts)
    assert res.a.values == t.a.values
    assert res.b.values == t.b.values
    assert res.c.values == t.c.values

    # check if input tables are not altered
    for subt in subts:
        assert subt.getColNames() == [ "a", "b", "c"]

def testConstantColumn():
    t = ms.toTable("a",[1,2,3])
    t.addConstantColumn("b", dict())
    assert len(set(id(x) for x in t.b.values)) == 1

def testSlicing():
    t = ms.toTable("a", [1, 2, 3])
    assert t[0].a.values == [1]
    assert t[:1].a.values == [1]
    assert t[1:].a.values == [2, 3]
    assert t[:].a.values == [1, 2, 3]


def testMerge():
    t1 = ms.toTable("a", [1])
    t1.addColumn("b", [2])
    t1.addColumn("c", [3])

    t2 = ms.toTable("a", [1,2])
    t2.addColumn("c", [1,3])
    t2.addColumn("d", [1,4])

    tn = ms.mergeTables([t1, t2])

    assert tn.a.values == [1, 1, 2]
    assert tn.b.values == [2, None, None]
    assert tn.c.values == [3, 1, 3]
    assert tn.d.values == [None, 1, 4]

    # check if input tables are not altered
    assert t1.getColNames() == [ "a", "b", "c"]
    assert t2.getColNames() == [ "a", "c", "d"]


def testApply():

    t = ms.toTable("a", [0.01, 0.1, 0.1, 0.015, 0.2,1.0 ])

    t.addColumn("a_bin", t.a.apply(lambda v: int(v*100)))
    # this returned numpy-ints due to an fault in addColumn and so
    # we got 6 tables instead of 4:
    ts = t.splitBy("a_bin")
    assert len(ts) == 4


def testCompress():
    t = ms.toTable("a", [])
    from libms.DataStructures.Table import compressPeakMaps
    from libms.DataStructures.MSTypes import PeakMap, Spectrum
    import numpy
    compressPeakMaps(t)

    s = Spectrum(numpy.arange(12).reshape(-1,2), 1.0, 1, "+")
    pm = PeakMap([s])
    s = Spectrum(numpy.arange(12).reshape(-1,2), 1.0, 1, "+")
    pm2 = PeakMap([s])

    t = ms.toTable("pm", [pm, pm2])
    assert len(set(map(id, t.pm.values))) == 2
    compressPeakMaps(t)
    assert len(set(map(id, t.pm.values))) == 1


def testUpdateColumn():
    t = ms.toTable("a", [1, 2])
    t.updateColumn("a", t.a + 1)
    assert t.a.values == [2, 3]
    t.updateColumn("b", t.a + 1)
    assert t.b.values == [3, 4]


def test_all_comps():
    a = ms.toTable("a",[3,2,1])
    b = ms.toTable("b",[1,2,3]) # must be sorted for tests below !

    def _test(e, a=a, b=b):

        a.join(b, e).print_()

        t1 = a.join(b, a.a <= b.b).rows
        t2 = a.join(b, b.b >= a.a).rows
        t3 = b.join(a, a.a <= b.b).rows
        t4 = b.join(a, b.b >= a.a).rows

        b.sortBy("b")
        a.join(b, e).print_()
        s1 = a.join(b, a.a <= b.b).rows
        s2 = a.join(b, b.b >= a.a).rows
        s3 = b.join(a, a.a <= b.b).rows
        s4 = b.join(a, b.b >= a.a).rows

        assert t1 == t2
        assert t3 == t4
        assert t1 == s1
        assert t2 == s2
        assert t3 == s3
        assert t4 == s4

        b.join(a, e).print_()

        t1 = a.join(b, a.a <= b.b).rows
        t2 = a.join(b, b.b >= a.a).rows
        t3 = b.join(a, a.a <= b.b).rows
        t4 = b.join(a, b.b >= a.a).rows

        b.sortBy("b")
        b.join(a, e).print_()
        s1 = a.join(b, a.a <= b.b).rows
        s2 = a.join(b, b.b >= a.a).rows
        s3 = b.join(a, a.a <= b.b).rows
        s4 = b.join(a, b.b >= a.a).rows

        assert t1 == t2
        assert t3 == t4
        assert t1 == s1
        assert t2 == s2
        assert t3 == s3
        assert t4 == s4

    _test(a.a <= b.b)
    _test(a.a < b.b)
    _test(a.a >= b.b)
    _test(a.a > b.b)
    _test(a.a == b.b)
    _test(a.a != b.b)


def test_numpy_comparison():
    v = np.array((1,2,3))
    t = ms.toTable("a",[v])
    t2 = t.filter(t.a == t.a)
    assert len(t2) == len(t)
    t2 = t.filter(t.a <= t.a)
    assert len(t2) == len(t)
    t2 = t.filter(t.a >= t.a)
    assert len(t2) == len(t)
    t2 = t.filter(t.a != t.a)
    assert len(t2) == 0
    t2 = t.filter(t.a < t.a)
    assert len(t2) == 0
    t2 = t.filter(t.a > t.a)
    assert len(t2) == 0

    t2 = t.filter(t.a == 3)
    assert len(t2) == 0
    t2 = t.filter(t.a <= 3)
    assert len(t2) == 1
    t2 = t.filter(t.a >= 1)
    assert len(t2) == 1
    t2 = t.filter(t.a != 3)
    assert len(t2) == 0
    t2 = t.filter(t.a < 4)
    assert len(t2) == 1
    t2 = t.filter(t.a > 0)
    assert len(t2) == 1


