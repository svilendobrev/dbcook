#$Id$

from tests.util.context import *
from dbcook import walkklas
import sys
walkklas._debug = sys.argv.count( '-v') > 1

import walktest2
from walktest2 import C

class A0( Base):
    a = Int()
    p2A = Collection( 'A')  #test plain forward decl
    p2C = Collection( C  )  #test plain decl

class A( C):
    a = Int()
    p2B = Reference( 'B')   #test plain forward decl

class B( walktest2.D):
    b = Int()
    q2C = Reference( 'C')   #test walking C and pulling E
    #r2B = Collection( C)    #XXX fails test walking C and pulling E
#    r = Reference( walktest2.C)

AA = A      #test multiple aliases
CcCc = C

namespace = locals()


if 0:
    cmodname = C.__module__
    print cmodname
    cmod = sys.modules[ cmodname]
    print cmod.__dict__['D']

import unittest
class T( unittest.TestCase):
    expect = dict(
        A = A,
        C = walktest2.C,
        B = B,
        E = walktest2.E,
        D = walktest2.D,
        A0= A0,
        Base = Base
    )
    def test_namespace_partial( me, namespace =namespace, expect =None):
        expect = expect or me.expect
        from dbcook.util.attr import issubclass
        print 'in:', ' '.join( k+':'+v.__name__ for k,v in namespace.items() if issubclass( v,Base) )
        r = walkklas.walker( namespace, Builder.reflector, Base )
        if walkklas._debug:
            print
            print '\n   '.join( ['result:'] + [str(a) for a in r.iteritems() ] )

        if r != expect:
            q = dict( res=r,exp=expect)
            for k in q:
                q[k] = '\n'.join( sorted( '\t%s:%s' % kv for kv in q[k].items()))
            #print
            for a,b in q.items(): print a,b
            me.assertEquals( *q.values())
    def ztest_one_pulls_all_1ref( me):
        exp = me.expect.copy()
        del exp['A0']
        me.test_namespace_partial( dict( A=A), exp )
    def ztest_one_pulls_all_ncoll( me):
        me.test_namespace_partial( dict( A0=A0))

#SAdb.config.getopt()
unittest.main()

# vim:ts=4:sw=4:expandtab
