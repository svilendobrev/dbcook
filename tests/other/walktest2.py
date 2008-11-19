#$Id$
from tests.util.context import Base,Reference,Collection,Int

class C( Base):
    c = Int()
    t2D = Reference( 'D')

class D( Base):
    d = Int()
    s2E = Reference( 'E')
    #s2E = Collection( 'E') #XXX fails

class E( Base):
    e = Int()
    y2C = Reference( 'C')

# vim:ts=4:sw=4:expandtab
