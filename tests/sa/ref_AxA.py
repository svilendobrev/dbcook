#$Id$
# -*- coding: cp1251 -*-

import sa_case
from sa_case import A,B,C
from sqlalchemy import *
from sqlalchemy.orm import *

class Case_A_A_self( sa_case.SACase):
    def make_tables( me):
        t1 = Table('table1', me.meta,
                Column('name', String, ),
                Column('id', Integer, primary_key=True),
                Column('t_id', Integer,
                            ForeignKey('table1.id',
                                #use_alter=True, name='zt1id_fk'
                            )
                    ),
            )

        me.meta.create_all()
        mapper( A, t1, properties={
                'link': relation( A,
                        primaryjoin= t1.c.t_id==t1.c.id,
                        post_update=True,
                        uselist=False,
                        lazy=True,
                        ),
                    }
            )

    def populate( me):
        p = A( name='a1' )

        p.link = p

        me.session.save( p)
        return [p]



class Case_A_A1( Case_A_A_self):
    def populate( me):
        p = A( name='a1' )
        q = A( name='a2' )

        p.link = q
        q.link = p

        me.session.save( p)
        return p,q


class Case_A_B_A( sa_case.SACase):
    def make_tables( me):
        t1 = Table('table1', me.meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('t2_id', Integer,
                            ForeignKey('table2.id',)
                    )
            )

        t2 = Table('table2', me.meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('t1_id', Integer,
                            ForeignKey('table1.id',
                                use_alter=True,
                                name='zt2id_fk'
                            )
                    )
            )

        me.meta.create_all()
        mapper( A, t1, properties={
            'link': relation( B,
                        primaryjoin= t1.c.t2_id==t2.c.id,
                        )
        })

        mapper( B, t2, properties={
            'link': relation( A,
                        primaryjoin= t2.c.t1_id==t1.c.id,
                        post_update=True
                        )
        })

    def populate( me):
        p = A( name='a1' )
        q = B( name='b1' )

        p.link = q
        q.link = p

        me.session.save( p)
        return p,q


class Case_A_B_C_A( sa_case.SACase):
    def make_tables( me):
        t1 = Table('table1', me.meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('t2_id', Integer,
                            ForeignKey('table2.id',)
                    )
            )

        t2 = Table('table2', me.meta,
               Column('name', Integer, ),
               Column('id', Integer, primary_key=True),
               Column('t3_id', Integer,
                            ForeignKey('table3.id',)
                    )
            )

        t3 = Table('table3', me.meta,
               Column('name', Integer, ),
               Column('id', Integer, primary_key=True),
               Column('t1_id', Integer,
                            ForeignKey('table1.id',
                                use_alter=True,
                                name='zt3id_fk'
                            )
                    )
            )

        me.meta.create_all()

        mapper( A, t1, properties={
            'link': relation( B,
                    primaryjoin= t1.c.t2_id==t2.c.id,
                )
        })

        mapper( B, t2, properties={
            'link': relation( C,
                    primaryjoin= t2.c.t3_id==t3.c.id,
                )
        })

        mapper( C, t3, properties={
            'link': relation( A,
                    primaryjoin= t3.c.t1_id==t1.c.id,
                    post_update=True
                )
        })

    def populate( me):
        p = A( name='a1' )
        q = B( name='b1' )
        r = C( name='c1' )

        p.link = q
        q.link = r
        r.link = p

        me.session.save( r)
        return p,q,r


from dbcook.table_circular_deps import fix_table_circular_deps

class Case_A_B_C_A_X_Y_mincut( Case_A_B_C_A):
    def make_tables( me):
        t11 = Table('table11', me.meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('t12_id', Integer,
                            ForeignKey('table12.id',)
                    )
            )

        t12 = Table('table12', me.meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('t11_id', Integer,
                            ForeignKey('table11.id',)
                    ),
                Column('t1_id', Integer,
                            ForeignKey('table1.id',)
                    )
            )

        t1 = Table('table1', me.meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('t2_id', Integer,
                            ForeignKey('table2.id',)
                    )
            )

        t2 = Table('table2', me.meta,
               Column('name', Integer, ),
               Column('id', Integer, primary_key=True),
               Column('t3_id', Integer,
                            ForeignKey('table3.id',)
                    ),
               Column('t11_id', Integer,
                            ForeignKey('table11.id',)
                    ),
            )

        t3 = Table('table3', me.meta,
               Column('name', Integer, ),
               Column('id', Integer, primary_key=True),
               Column('t1_id', Integer,
                            ForeignKey('table1.id',)
                    )
            )

        alltbl = me.meta.tables.values() #[t1,t2,t3, t11,t12]
        print '----'
        r = fix_table_circular_deps( alltbl, dbg=1)
        print '===='
        me.meta.create_all()

        mapper( A, t1, properties={
            'link': relation( B,
                    primaryjoin= t1.c.t2_id==t2.c.id,
                )
        })

        mapper( B, t2, properties={
            'link': relation( C,
                    primaryjoin= t2.c.t3_id==t3.c.id,
                )
        })

        mapper( C, t3, properties={
            'link': relation( A,
                    primaryjoin= t3.c.t1_id==t1.c.id,
                    post_update=True
                )
        })

if __name__ == '__main__':
#    import sys
#    sys.setrecursionlimit(100)
    import unittest
    unittest.main()

# vim:ts=4:sw=4:expandtab
