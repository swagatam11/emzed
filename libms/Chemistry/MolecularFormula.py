#encoding: latin-1


import FormulaParser
import Elements

import collections


class MolecularFormula(object):

    def __init__(self, form):
        if isinstance(form, str):
            self.stringForm = form
            self.dictForm = FormulaParser.parseFormula(form)
        elif isinstance(form, dict):
            self.stringForm = FormulaParser.joinFormula(form)
            # cleanup zero counts:
            self.dictForm = dict( (e,c) for (e,c) in form.items() if c)

    def asDict(self):
        # maybe dictForm is a Counter, so in order to provide too much
        # surprise we convert to dict:
        return dict(self.dictForm)

    def __str__(self):
        return self.stringForm

    asString = __str__

    def __add__(self, mf):
        dd = self.asDict().copy()
        for elem, count in mf.asDict().items():
            dd[elem] = dd.get(elem, 0) + count
        return MolecularFormula(dd)

    def __sub__(self, mf):
        dd = self.asDict().copy()
        for elem, count in mf.asDict().items():
            dd[elem] = dd.get(elem, 0) - count
        assert all(c>=0 for c in dd.values()), "negative counts not allowed"
        return MolecularFormula(dd)

    def mass(self, **specialisations):
        """
        specialisations maps symbol to a dictionary d providing a mass
        by d["mass"], eg:

            specialisations = { 'C' : 12.0 }
            inst.mass(C=12.0)

        or if you use the mass module:

            inst.mass(C=mass.C12)

        or you use mass in connection with the elements module:

            inst.mass(C=elements.C12)
        """

        el = Elements.Elements()
        items = self.dictForm.items()
        def get_mass(sym, massnum):
            # if mass num is None, and there is a specialisation
            # provided, we take this specialisation. Else we use
            # data from el, where a massnumber None is mapped to the
            # monoisotopic element:
            if massnum is None:
                specialisation = specialisations.get(sym)
                if specialisation is not None:
                    if isinstance(specialisation, collections.Mapping):
                        return specialisation["mass"]
                    try:
                        return float(specialisation)
                    except:
                        raise Exception("specialisation %r for %s invalid"\
                                        % (specialisation, sym))

            return el.getMass(sym, massnum)
        masses = list(get_mass(sym, massnum) for (sym, massnum), _  in items)
        if None in masses:
            return None
        return sum(m * c for m, (_, c) in zip(masses, items) )
