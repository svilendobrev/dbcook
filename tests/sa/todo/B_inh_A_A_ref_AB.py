#$Id$

from sqlalchemy import *
from sqlalchemy.orm import *

_debug = 'echo'
def mmapper( *args,**kargs):
    func = mapper
    if 'call' in _debug:
        print func,'(\n ', args, '\n  '+ '\n  '.join( '%s=%s' % kv for kv in kargs.iteritems()), '\n)'
    return func( *args, **kargs)

from sa_case import SACase, Base
class A( Base):
    props = [ 'id', 'data1', 'link1', ]
    props4ref = [ 'id', 'data1', ]
class B( A ):
    props = A.props + [ 'data2', ]
    props4ref = [ 'id', 'data2', ]

clear = False
Alink = 'B'
if 0 and __name__ == '__main__':
    import sys
    kargs = dict( kv.split('=') for kv in sys.argv[1:])
    clear = kargs.get('clear', clear)
    Alink = kargs.get('Alink', Alink)

class Case_B_inh_A_A_ref_AB( SACase):
    clear_session = clear
    Alink = Alink

    def make_tables( me):
        #concrete=False, Blink=''
        #inh=True, polymorphic=True,

        class tables: pass

        tables.A = Table('A', me.meta,
                Column('id', Integer, primary_key=True),
                Column('data1', String, ),
                Column('atype', String),
            )
        if me.Alink:
            tables.A.append_column( Column('link1_id', Integer,
                            ForeignKey( me.Alink+'.id',
                               use_alter=True, name='zt1id_fk'
                            )
                    )
            )
        tables.B = Table('B', me.meta,
                Column('data2', String, ),
                Column('id', Integer,
                            ForeignKey( 'A.id'),
                            primary_key=True,
                    ),
        )
        me.meta.create_all()

        class mappers: pass
        ajoin = {
            'A': tables.A.select( tables.A.c.atype == 'A'),
            'B': join( tables.A, tables.B, tables.B.c.id ==tables.A.c.id),
        }
        Ajoin = polymorphic_union( ajoin, None )
        mappers.A = mmapper( A, tables.A,
            select_table=Ajoin, polymorphic_on=Ajoin.c.atype,
            polymorphic_identity='A'
        )

        if me.Alink:
            mappers.A.add_property( 'link1',
                    relation( me.Alink == 'A' and A or B,
                        primaryjoin= tables.A.c.link1_id==(me.Alink=='A' and tables.A or tables.B).c.id,
                        lazy=True,
                        uselist=False,
                        post_update=True
                    )
            )
        mappers.B = mmapper( B, tables.B,
                polymorphic_identity='B',
                inherits = mappers.A,
                inherit_condition = (tables.A.c.id == tables.B.c.id),
        )

    def populate( me):
        me.a = A()
        me.a.data1 = 'aa'
        me.b = B()
        if 'data1' in B.props:
            b.data1 = 'ba'
        me.b.data2 = 'bb'

        if me.Alink:
            me.a.link1 = (me.Alink == 'A' and me.a or me.b)

        me.session.save( me.a)
        me.session.save( me.b)

    def test_inh_ref( me):
        print a      #does not work after session.clear() #XXX
        print b      #does not work after session.clear() #XXX
        expected = [
            dict( klas=A, id=a.id, str= str(a)),
            dict( klas=B, id=b.id, str= str(b)),
        ]

        print list( tables.A.select().execute() )
        print list( tables.B.select().execute() )

        for single in [1,0]:
            for item in expected:
                klas = item['klas']
                aid  = item['id']
                astr = item['str']
                if single:
                    s = me.session.query( klas).get_by( id=aid)
                    x = str(s)
                    r = 'assert single %(x)s ; expect: %(astr)s' % locals()
                    print '>>>>>', r
                    me.assertEqual( x, astr, r)
                else:
                    s = me.session.query( klas).select()
                    x = '; '.join( str(z) for z in s )
                    r = 'assert multiple %(x)s ; expect: %(astr)s' % locals()
                    me.failUnless( len(s) >= 1, 'size? '+ r)
                    me.assertEqual( str(s[0]), astr, r)


if __name__ == '__main__':
    import sys
    sys.setrecursionlimit(70)
    import unittest
    unittest.main()

####################################################
if 0:
    def case( clear =False, Alink='B', ):
        #concrete=False, Blink=''
        #inh=True, polymorphic=True,

        class A( Base):
            props = [ 'id', 'data1', 'link1', ]
            data = property( lambda me: me.data1)
            pass
        class B( A ):
            props = A.props + [ 'data2', ]
            data = property( lambda me: me.data2)
            pass

        meta = MetaData( 'sqlite:///')
        meta.bind.echo=ECHO

        class tables: pass

        tables.A = Table('A', meta,
                Column('id', Integer, primary_key=True),
                Column('data1', String, ),
                Column('atype', String),
            )
        if Alink:
            tables.A.append_column( Column('link1_id', Integer,
                            ForeignKey( Alink+'.id',
                               use_alter=True, name='zt1id_fk'
                            )
                    )
            )


        tables.B = Table('B', meta,
                Column('data2', String, ),
                Column('id', Integer,
                            ForeignKey( 'A.id'),
                            primary_key=True,
                    ),
        )
        meta.create_all()


        class mappers: pass

        ajoin = {
            'A': tables.A.select( tables.A.c.atype == 'A'),
            'B': join( tables.A, tables.B, tables.B.c.id ==tables.A.c.id),
        }
        Ajoin = polymorphic_union( ajoin, None )
        mappers.A = mmapper( A, tables.A,
            select_table=Ajoin, polymorphic_on=Ajoin.c.atype,
            polymorphic_identity='A'
        )

        if Alink:
            mappers.A.add_property( 'link1',
                    relation( Alink == 'A' and A or B,
                        primaryjoin= tables.A.c.link1_id==(Alink=='A' and tables.A or tables.B).c.id,
                        lazy=True,
                        uselist=False,
                        post_update=True
                    )
            )

        mappers.B = mmapper( B, tables.B,
                polymorphic_identity='B',
                inherits = mappers.A,
                inherit_condition = (tables.A.c.id == tables.B.c.id),
        )


        #populate
        session = create_session()

        a = A()
        a.data1 = 'aa'
        b = B()
        if 'data1' in B.props:
            b.data1 = 'ba'
        b.data2 = 'bb'

        if Alink:
            a.link1 = (Alink == 'A' and a or b)

        session.save(a)
        session.save(b)

        session.flush()

        print a      #does not work after session.clear() #XXX session-clear?
        print b      #does not work after session.clear() #XXX session-clear?
        expected = [
            dict( klas=A, id=a.id, str= str(a)),
            dict( klas=B, id=b.id, str= str(b)),
        ]

        if clear: session.clear()

        print list( tables.A.select().execute() )
        print list( tables.B.select().execute() )

        test( session, expected )


    def test( session, items):
        for single in [1,0]:
            for item in items:
                klas = item['klas']
                aid  = item['id']
                astr = item['str']
                if single:
                    s = session.query( klas).get_by( id=aid)
                    x = str(s)
                    r = 'assert single %(x)s ; expect: %(astr)s' % locals()
                    print '>>>>>', r
                    assert x == astr, r
                else:
                    s = session.query( klas).all()
                    x = '; '.join( str(z) for z in s )
                    r = 'assert multiple %(x)s ; expect: %(astr)s' % locals()
                    assert len(s) >= 1, 'size? '+ r
                    assert str(s[0]) == astr, r


# vim:ts=4:sw=4:expandtab
