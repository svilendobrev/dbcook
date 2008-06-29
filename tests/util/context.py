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
    import dbcook.usage.static_type.sa2static as orm
    from static_type.types.atomary import Text
    from static_type.types.atomary import Number as Int
#    def qstr(q, **str_kargs): return q.__str__( **str_kargs)
else:
    import dbcook.usage.plainwrap as orm
    class Text( orm.Type): pass
    class Int(  orm.Type): pass
#    def qstr(q, **str_kargs): return str(q)
Builder = orm.Builder
Base = orm.Base
Reference = orm.Reference

from dbcook.usage.samanager import SAdb

import sqlalchemy
fieldtypemap = {
    Text: dict( type= sqlalchemy.String(200), ),
    Int : dict( type= sqlalchemy.Integer, ),
}

SAdb.Builder = Builder
SAdb.fieldtypemap = fieldtypemap


from dbcook.mapcontext import table_inheritance_types
JOINED    = table_inheritance_types.JOINED
CONCRETE  = table_inheritance_types.CONCRETE
SINGLE    = table_inheritance_types.SINGLE
DEFAULT   = table_inheritance_types.DEFAULT


# vim:ts=4:sw=4:expandtab
