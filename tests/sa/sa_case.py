#$Id$
# -*- coding: cp1251 -*-

from tests.util import sa_gentestbase
import sqlalchemy.orm

class SACase( sa_gentestbase.Test_SA):
    clear_session = True

    def make_tables( me): pass

    def populate( me): pass #save + return iter-over-objects

    def setUp( me):
        sa_gentestbase.Test_SA.setUp( me)
        me.make_tables()

        me.session = sqlalchemy.orm.create_session()
        expect = me.populate()
        me.session.flush()

        d = me.expect_typid = {}
        for x in expect:
            d.setdefault( x.__class__, set() ).add( (x.id,str(x)) )

        if me.clear_session: me.session.clear()

    def test( me ):
        for typ,items in me.expect_typid.items():
            #single
            for (id,expect) in items:
                s = me.session.query( typ).filter_by( id=id).first()
                result = str(s)
                me.assertEqual( result, expect)
            #all
            s = me.session.query( typ).all()
            result = set( str(z) for z in s )
            me.assertEqual( len(result), len(items) )
            expect = set( exp for (id,exp) in items )
            me.assertEqual( result, expect)

Base = sa_gentestbase.Base

class A( Base): pass

class B( Base): pass
class BA( A): pass

class C( Base): pass
class CA( A): pass

#if __name__ == '__main__':
#    import sys
#    sys.setrecursionlimit(140)
#    from ref_A_A   import Case_A_A
#    from ref_A_B_A import Case_A_B_A
#    from ref_A_B_C_A import Case_A_B_C_A
#    from ref_A_B_C_A_X_Y import Case_A_B_C_A_X_Y

#    del SACase
#    import unittest
#    unittest.main()

# vim:ts=4:sw=4:expandtab
