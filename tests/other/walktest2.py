#$Id$
# -*- coding: cp1251 -*-
from tests.util.context import *

class C( Base):
    c = Int()
    t2D = Reference( 'D')

class D( Base):
    d = Int()
    s2E = Reference( 'E')

class E( Base):
    e = Int()
    y2C = Reference( 'C')

# vim:ts=4:sw=4:expandtab
