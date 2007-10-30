#$Id$
# -*- coding: cp1251 -*-
from tests.util.context import *
if USE_STATIC_TYPE:
    Base.auto_set = False
orm = Builder
from dbcook.builder import relation
class Base( orm.Base):
    __init__ = relation.setkargs

SAdb.config.getopt()
print 'config:', SAdb.config

class PeroVKlon( Base):
    name = Text()

class BudgetRow( Base):
    perokloni  = orm.Collection( PeroVKlon)
    silikoni   = orm.Collection( PeroVKlon)

sa = SAdb()
sa.open( recreate=True)
types = locals()
sa.bind( types, base_klas= Base )

s= sa.session()

br1 = BudgetRow()
for i in range(3):
    p = PeroVKlon( name= 'a'+str(i) )
    br1.perokloni.append( p)
    if 10:
        p = PeroVKlon( name= 'b'+str(i) )
        br1.silikoni.append( p)

op = ['a'+str(i) for i in range(3) ]
os = ['b'+str(i) for i in range(3) ]

sa.saveall( s, br1)
s.flush()
assert [ k.name for k in br1.perokloni ] == op
assert [ k.name for k in br1.silikoni  ] == os

s.clear()
br1 = s.query( BudgetRow).first()
assert [ k.name for k in br1.perokloni ] == op
assert [ k.name for k in br1.silikoni  ] == os

print 'br1 PK:', br1.perokloni
print 'br1 sK:', br1.silikoni

# vim:ts=4:sw=4:expandtab
