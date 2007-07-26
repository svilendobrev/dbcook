#$Id$
# -*- coding: cp1251 -*-

from tests.util.context import *
from dbcook import walkklas
import sys
walkklas._debug = sys.argv.count( '-v') > 1

import walktest2
from walktest2 import C

class A( C):
    a = Int()
    p2B = Type4Reference( 'B')

class B( walktest2.D):
    b = Int()
    q2C = Type4Reference( 'C')
#    r = Type4Reference( walktest2.C)

AA = A
BDDD = C

namespace = locals()


if 0:
    cmodname = C.__module__
    print cmodname
    cmod = sys.modules[ cmodname]
    print cmod.__dict__['D']

import unittest
class T( unittest.TestCase):
    def test_walker( me):
        r = walkklas.walker( namespace, Builder.reflector, Base )
        if walkklas._debug:
            print
            print '\n   '.join( ['result:'] + [str(a) for a in r.iteritems() ] )

        expect = {
         'A': A,
         'C': walktest2.C,
         'B': B,
         'E': walktest2.E,
         'D': walktest2.D,
         'Base': Base
        }
        me.assertEquals( r, expect)

SAdb.config.getopt()
unittest.main()
# vim:ts=4:sw=4:expandtab
