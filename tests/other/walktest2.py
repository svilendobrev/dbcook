#$Id$
# -*- coding: cp1251 -*-
from tests.util.context import *

class C( Base):
    c = Int()
    t2D = Type4Reference( 'D')

class D( Base):
    d = Int()
    s2E = Type4Reference( 'E')

class E( Base):
    e = Int()
    y2C = Type4Reference( 'C')

# vim:ts=4:sw=4:expandtab
