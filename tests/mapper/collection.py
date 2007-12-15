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

class Kid( Base):
    name = Text()

def tsingle():
    class Parent( Base):
        things  = orm.Collection( Kid)
    return locals()

def t2collects():
    class Parent( Base):
        things  = orm.Collection( Kid)
        mings   = orm.Collection( Kid)
    return locals()

def t3inheritparent():
    class Parent( Base):
        things  = orm.Collection( Kid)
    class Parent2( Parent):
        DBCOOK_inheritance = 'joined'
        a = Text()
    return locals()

for namespacer in tsingle, t2collects, t3inheritparent:
    sa = SAdb()
    sa.open( recreate=True)
    print '---', namespacer.__name__
    types = namespacer()
    types.update( Kid=Kid)
    sa.bind( types, base_klas= Base )

    s= sa.session()

    parentklas = types.get( 'Parent2', types[ 'Parent'] )
    use_mings = 'mings' in dir( parentklas)

    parent = parentklas()
    for i in range(3):
        p = Kid( name= 'a'+str(i) )
        parent.things.append( p)
        if use_mings:
            p = Kid( name= 'b'+str(i) )
            parent.mings.append( p)

    op = ['a'+str(i) for i in range(3) ]
    os = ['b'+str(i) for i in range(3) ]

    sa.saveall( s, parent)
    s.flush()
    assert [ k.name for k in parent.things ] == op
    if use_mings:
        assert [ k.name for k in parent.mings  ] == os

    s.clear()
    print list( s.query( parentklas) )
    parent = s.query( parentklas).first()
    assert [ k.name for k in parent.things ] == op
    if use_mings: assert [ k.name for k in parent.mings  ] == os

    print ' collection:', parent.things
    if use_mings: print ' collect2:', parent.mings
    sa.destroy()

# vim:ts=4:sw=4:expandtab
