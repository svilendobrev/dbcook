#$Id$

'''
regression test: inheritances are not cuttable deps, all else are.
'''

from tests.util.context import *
#if USE_STATIC_TYPE:
Base.auto_set = False

from tests.util.case2unittest import Case

class Employee( Base):
    DBCOOK_inheritance = JOINED
    DBCOOK_has_instances = True
    boss  = Type4Reference( 'Manager')   #put a big weight on this relation
    boss2 = Type4Reference( 'Manager')
    boss3 = Type4Reference( 'Manager')
    name = Text()
    dept = Type4Reference( 'Dept')          #without this session.topology will not cycle

class Manager( Employee):
    extras = Text()

class Dept( Base):
    boss = Type4Reference( Manager)
    name = Text()

'''
graph: ['Dept:Employee',
    'Manager:Employee', 'Manager:Employee', 'Manager:Employee',     #3x
    'Manager:Dept',
    'Employee:Manager'      #inheritance
]
cutting just 1 Employee:Manager would solve it - but it is not cuttable - it is inheritance.
Hence a more costly cut must be searched - cut: ['Dept:Employee', 'Manager:Employee'] 4
'''

types = locals()


class TestMinCut( Case):
    def setUp( me):
        me.db = SAdb()
        me.db.open( recreate=True)
        me.db.bind( types, debug='graph' )

        #populate
        a = Employee()
        a.name = 'empo'

        m = Manager()
        m.name = 'mummy'
        m.extras= 'big'

        a.boss = m

        dept = Dept()
        dept.name = 'cubics'
        a.dept = dept
        m.dept = dept
        dept.boss = m

        session = me.db.session()
        me.db.saveall( session, locals() )
        session.flush()
        session.clear()

    def test_cuttable_deps( me):
        import sys
        db = me.db
        session = db.session()
        q2 = db.query_all_tables()
        for kl in [Employee, Manager][0:]:
            print '== query_BASE', kl.__name__
            q2 = db.query_BASE_instances(session, klas=kl)
            print  '\n'.join( '  '+str(x) for x in q2)
            sys.stdout.flush()
            print '== query_ALL', kl.__name__
            q1 = db.query_ALL_instances( session, klas=kl)
            print  '\n'.join( '  '+str(x) for x in q1)
            sys.stdout.flush()
            print '== query_SUB', kl.__name__
            q3 = db.query_SUB_instances( session, klas=kl)
            print  '\n'.join( '  '+str(x) for x in q3)
            sys.stdout.flush()

if __name__ == '__main__':
    import sys
    sys.setrecursionlimit( 50)
    SAdb.config.getopt()
    import unittest
    unittest.main()

# vim:ts=4:sw=4:expandtab
