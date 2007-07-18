#$Id$
# -*- coding: cp1251 -*-
from tests.util.context import *

class C( Base):
    c = Int()
    t2D = Type4SubStruct( 'D')

class D( Base):
    d = Int()
    s2E = Type4SubStruct( 'E')

class E( Base):
    e = Int()
    y2C = Type4SubStruct( 'C')

# vim:ts=4:sw=4:expandtab
