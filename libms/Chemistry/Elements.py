import pdb
import os
import pyopenms

from ..DataStructures import Table

class NestedBunchDict(dict):

   def __missing__(self, k):
       self[k] = NestedBunchDict()
       return self[k]

   def __getattr__(self, k):
       return self[k]


class Elements(Table):

    __we_are_all_one = dict() # borg pattern, data is only loaded once

    def __init__(self):
        self.__dict__ = Elements.__we_are_all_one  # shared state

        if not hasattr(self, "rows"):
            path = os.path.dirname(os.path.abspath(__file__))
            param = pyopenms.Param()
            ph = pyopenms.ParamXMLFile()
            ph.load(os.path.join(path, "Elements.xml"), param)

            getters = {
                    pyopenms.DataType.STRING_VALUE: "toString",
                    pyopenms.DataType.INT_VALUE: "toInt",
                    pyopenms.DataType.DOUBLE_VALUE: "toDouble",
            }


            data = NestedBunchDict()
            for k, value in param.asDict().items():
                fields = k.split(":")
                element = fields[1]
                kind = fields[2]
                if kind in ["Name", "Symbol", "AtomicNumber"]:
                    #entry = param.getValue(pyopenms.String(k))
                    #value = getattr(entry, getters[entry.valueType()])()
                    data[element][kind] =  value
                if kind == "Isotopes":
                    massnumber = int(fields[3])
                    kind = fields[4]
                    #if kind in ["RelativeAbundance", "AtomicMass"]:
                        #entry = param.getValue(pyopenms.String(k))
                        #value = getattr(entry, getters[entry.valueType()])()
                    data[element]["Isotopes"][massnumber][kind]=value

            colNames = ["number", "symbol", "name", "massnumber", "mass", "abundance"]
            colTypes = [int, str, str, int, float, float]
            colFormats = ["%d", "%s", "%s", "%d", "%.10f", "%.3f" ]

            rows = []
            for props in data.values():
                row0 = [props.AtomicNumber, props.Symbol, props.Name]
                for k, isoprop in props.Isotopes.items():
                    row = row0 + [ k, isoprop.AtomicMass, isoprop.RelativeAbundance / 100.0 ]
                    rows.append(row)

            super(Elements, self).__init__(colNames, colTypes, colFormats, rows,
                                           title="Elements")
            self.sortBy("number")

            self.massDict = dict()
            for row in self.rows:
                sym = self.getValue(row, "symbol")
                massnum = self.getValue(row, "massnumber")
                mass = self.getValue(row, "mass")
                self.massDict[sym, massnum] = mass
            syms = set(s for s, _ in self.massDict.keys())
            for sym in syms:
                minmass = min(mass for (s, mass) in self.massDict.keys() if s == sym)
                self.massDict[sym, None] = self.massDict[sym, minmass]

        # borg pattern is sh*t for columns which hold a reference to the
        # table which might change, but the columns stay the same !!!
        self.resetInternals()

    def getMass(self, symbol, massnumber):
        return self.massDict.get((symbol, massnumber))


class MonoIsotopicElements(Table):

    # borg pattern
    __we_are_all_one = dict()

    def __init__(self):
        self.__dict__ = MonoIsotopicElements.__we_are_all_one

        if not hasattr(self, "rows"): # empty on first run
            elements = Elements()
            self.rows = []
            # find monoisotopic data for each element
            for s in set(elements.symbol.values): # unique symbols
                tsub = elements.filter(elements.symbol == s)
                massnumber = tsub.massnumber.values
                t0   = tsub.filter(tsub.massnumber == min(massnumber))
                self.rows.append(t0.rows[0][:])

            self._colNames = elements.getColNames()
            self._colTypes = elements.getColTypes()
            self._colFormats = elements.getColFormats()
            self.title = "Monoisotopic Elements"
            self.meta  = dict()

            self.resetInternals()
            self.renameColumns(mass="m0")
            self.dropColumns("abundance")
            self.sortBy("number")
            self.massDict = dict()
            for row in self.rows:
                sym = self.getValue(row, "symbol")
                mass = self.getValue(row, "m0")
                self.massDict[sym] = mass

        # borg pattern is sh*t for columns which hold a reference to the
        # table which might change, but the columns stay the same !!!
        self.resetInternals()


    def getMass(self, symbol):
        return self.massDict.get(symbol)


    def buildSymbolIndex(self):
        symbols = self.symbol.values
        self.symbolIndex = dict( (s,i) for (i,s) in enumerate(symbols))

    def sortBy(self, *a, **kw):
        super(MonoIsotopicElements, self).sortBy(*a, **kw)
        self.buildSymbolIndex()

    def getProperty(self, symbol, name):
        if not symbol in self.symbolIndex:
            return None
        row = self.rows[self.symbolIndex.get(symbol)]
        return self.getValue(row, name)



if __name__ == "__main__":
    print Elements().symbol.values



