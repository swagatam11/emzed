
class Table(object):

    def __init__(self, colNames, colTypes, rows = None):
        assert len(colNames) == len(colTypes)
        if rows is not None:
            for row in rows:
                assert len(row) == len(colNames)
        self.colNames = colNames
        self.colTypes = colTypes
        self.rows     = rows

        self.colIndizes = dict( (n, i) for i, n in enumerate(colNames)) 


    def addColumn(self, name, type_, value=None):
        for row in self.rows:
            row.append(value)
        self.colNames.append(name)
        self.colTypes.append(type_)

    
    def evaluateMacros(self):
        pass

        # TODO: ColTypes: dataCell, evalCell. letztere mit ergebnistyp
        
            #if type_ == "@expr":
            #   dd = dict( (n, row[self.colIndizes[n]]) for n in self.colNames )
            #   row.append(eval(value, dd))
            #else:

    def extractColumns(self, *names):
        
        colNames = []
        colTypes = []
        rows     = []

        for name in names:
            if not name in self.colIndizes.keys():
                raise Exception("column %r does not exist in %r" % (name, self)) 
            colNames.append(name)
            colTypes.append(self.colIndizes[name])

        for row in self.rows:
            rows.append( [ row[self.colIndizes[name]] for name in names ])
            
        return Table(colNames, colTypes, rows)

    def __len__(self):
        return len(self.rows)
             
            
            
            
