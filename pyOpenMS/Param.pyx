from libcpp.vector cimport *
from DataValue cimport *
from DataValue cimport *
from Param cimport *

cdef paramToDict(Param p):
    cdef list[string] keys = getKeys(p)
    cdef list[string].iterator it = keys.begin()
    cdef dict rv = dict()
    cdef string skey
    cdef DataValue val
    while it != keys.end():
        skey = deref(it)
        val = p.getValue(skey)
        if val.valueType() == STRING_VALUE:
            rv[skey.c_str()] =  val.toChar()
        elif val.valueType() == INT_VALUE:
            rv[skey.c_str()] = <int> val
        elif val.valueType() == DOUBLE_VALUE:
            rv[skey.c_str()] = <double> val
        else:
            raise "not implemented !"
        it = next(it)
        
    return rv
        
    
   

cdef Param dictToParam(dict dd):
    cdef Param p
    cdef DataValue * dv
    cdef string * temps
    for key, value in dd.items():
        if isinstance(value, int) or isinstance(value, long):
            dv = new DataValue(<long>(value))
        if isinstance(value, float) :
            dv = new DataValue(<double>(value))
        if isinstance(value, str) :
            dv = new DataValue(<char *>value)
        temps = new string(key)
        p.setValue(deref(temps), deref(dv))
        del temps
    return p



