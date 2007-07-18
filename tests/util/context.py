#$Id$
# -*- coding: cp1251 -*-

USE_STATIC_TYPE= 0
import sys

try: sys.argv.remove( 'statictype')
except ValueError: pass
else: USE_STATIC_TYPE = 1

try: sys.argv.remove( 'static_type')
except ValueError: pass
else: USE_STATIC_TYPE = 1

if USE_STATIC_TYPE:
    from dbcook.usage.static_type.sa2static import Builder, Base, Type4SubStruct
        #Type4SubStruct (x,auto_set=False): x=string->context.ForwardSubStruct; x=class->DirectSubStruct
    from static_type.types.atomary import Text
    from static_type.types.atomary import Number as Int
#    def qstr(q, **str_kargs): return q.__str__( **str_kargs)
else:
    from dbcook.usage.plainwrap import Builder, Base, Type4SubStruct, Type
    class Text( Type): pass
    class Int(  Type): pass
#    def qstr(q, **str_kargs): return str(q)

Reference = SubStruct = Type4SubStruct

from dbcook.usage.samanager import SAdb

import sqlalchemy
fieldtypemap = {
    Text: dict( type= sqlalchemy.String, ),
    Int : dict( type= sqlalchemy.Integer, ),
}

SAdb.Builder = Builder
SAdb.fieldtypemap = fieldtypemap

# vim:ts=4:sw=4:expandtab
