#$Id$
# -*- coding: cp1251 -*-
from dbcook.aboutrel import about_relation

def test( *args,**kargs):
    is_parent = bool( kargs.pop( 'is_parent', None))
    mname = kargs.pop( 'name',  None)
    oname = kargs.pop( 'oname', None)
    mklas = kargs.pop( 'klas',  None)
    oklas = kargs.pop( 'oklas', None)

    def eq( me,o):
        for k in '_klas_attr is_parent name klas attr'.split():
            my= getattr( me,k); other= getattr( o,k)
            if k == 'name': r = (my == other)
            else: r = (my is other)
            if not r: return False
        return True
    about_relation.__eq__ = eq
    a = about_relation( *args,**kargs)
    print a
    b = a.otherside
    print b
    assert b.otherside is a
    if a.is_parent:
        assert a.child  is a.otherside
        assert a.parent is a
    else:
        assert a.parent is a.otherside
        assert a.child  is a
    assert a.is_parent == (not b.is_parent)

    for target,expect,intype in [
            (a.is_parent, is_parent, 'is_parent=bool' ),
            (a.name, mname, 'name=str' ),
            (b.name, oname, 'oname=str'),
            (a.klas, mklas, 'klas='  ),
            (b.klas, oklas, 'oklas=' ),
        ]:
        if expect is None: print 'give', intype, 'to test it'
        else: assert target == expect, '%s: %r ?= %r' % (intype, target, expect)

    return a,b


from sqlalchemy.orm import clear_mappers
from sqlalchemy import MetaData, Integer, String
import unittest

class AboutRel( object):
    def tearDown( me):
        clear_mappers()

    BACKREF = False
    backref_kids = backref_club = None
    def backrefs( me):
        BACKREF = me.BACKREF
        me.backref_kids = BACKREF and 'mama' or None
        me.backref_club = BACKREF and 'members' or None

    def test_mama_kids( me):
        Mama = me.Mama
        test( Mama.kids, is_parent=True,
            name='kids', klas=Mama,
            oname=me.backref_kids,
            oklas=me.Kid
        )
    def test_mama_club( me):
        Mama = me.Mama
        test( Mama.club, is_parent=False,
            name='club', klas=Mama,
            oname=me.backref_club,
            oklas=me.Club
        )

    def test_mama_friend( me):
        Mama = me.Mama
        test( Mama.friend, is_parent=False,
            name='friend', klas=Mama,
            oname=None,
            oklas=Mama
        )

    def test_wrongs( me):
        for a in me.Kid, me.Kid.name, 'alala':
            try:
                about_relation( a)
            except AssertionError, e:
                if 'not a relation klas_attr' in e.message: continue
                raise

class AboutRel_backref( AboutRel):
    BACKREF = True
    def test_kid_mama( me):
        test( me.Kid.mama, is_parent=False,
            name='mama', klas=me.Kid,
            oname='kids',
            oklas=me.Mama
        )
    def test_club_members( me):
        test( me.Club.members, is_parent=True,
            name='members', klas=me.Club,
            oname='club',
            oklas=me.Mama
        )


import sys
if 'nodbcook' not in sys.argv:
    import dbcook.usage.plainwrap as o2r
    class Text( o2r.Type): pass
    class Int( o2r.Type): pass
    fieldtype_mapper = {
        Text:   dict( type=String(20) ),
        Int:    dict( type=Integer),
    }

    class dbcook_setup( object ):
        def setUp( me):
            me.backrefs()
            backref_kids = me.backref_kids
            backref_club = me.backref_club
            class Club( o2r.Base):
                place = Text()
                if backref_club:
                    assert backref_club == 'members'
                    members = o2r.Collection( 'Mama', backref='club')
            class Kid( o2r.Base):
                name = Text()
            class Mama( o2r.Base):
                name = Text()
                if not backref_club:
                    club = o2r.Reference( Club)
                kids = o2r.Collection( Kid, backref=backref_kids)
                friend = o2r.Reference( 'Mama')

            namespace = locals().copy()
            mkids = Mama.kids
            meta = MetaData()
            o2r.Builder( meta, namespace, fieldtype_mapper= fieldtype_mapper,
                    only_declarations =True,
                    #debug='mapper,relation.table'
                )

            from dbcook import config
            me.backref_kids = backref_kids or config.column4ID.ref_make_name( mkids.backrefname)
            me.backref_club = backref_club
            me.Mama = Mama
            me.Kid = Kid
            me.Club = Club

    class t3_dbcook_nobackref( dbcook_setup, AboutRel, unittest.TestCase ):
        pass
    class t4_dbcook_backref( dbcook_setup, AboutRel_backref, unittest.TestCase ):
        pass

class sa_setup( object):
    def setUp( me):
        me.backrefs()
        from sqlalchemy.orm import mapper, relation, compile_mappers
        from sqlalchemy import Table, Column, ForeignKey
        meta = MetaData( 'sqlite:///')
        #meta.bind.echo=True

        tclub = Table('club', meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
            )
        tmama = Table('mama', meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('club_id', Integer, ForeignKey('club.id',)),
                Column('friend_id', Integer, ForeignKey('mama.id', use_alter=True, name='zt2id_fk'))
            )
        tkid = Table('kid', meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('mama_id', Integer, ForeignKey('mama.id',)),
            )

    #    meta.create_all()
        class Base(object):
            def __init__( me, **kargs):
                for k,v in kargs.items(): setattr( me,k,v)
        class Club( Base):pass
        class Mama( Base): pass
        class Kid( Base): pass

        mapper( Mama, tmama, properties={
                'kids': relation( Kid,  backref= me.backref_kids,),
                'club': relation( Club, backref= me.backref_club,),
                'friend': relation( Mama,
                            post_update=True,
                            uselist=False,
                            lazy=True, )
            })
        mapper( Kid, tkid)
        mapper( Club, tclub)
        compile_mappers()   #or populate()

        me.backref_kids = me.backref_kids or 'mama_id'
        me.Mama = Mama
        me.Kid = Kid
        me.Club = Club

class t1_sa_nobackref( sa_setup, AboutRel, unittest.TestCase ):
    pass
class t2_sa_backref( sa_setup, AboutRel_backref, unittest.TestCase ):
    pass

def populate():
    c = Club( name='kef')
    p = Mama( name='Mam' )
    q = Kid( name='b1' )
    r = Kid( name='b2' )
    p.kids.append( q)
    p.kids.append( r)
    p.club = c

    s = create_session()
    s.save( p)
    s.flush()
    s.clear()

    for a in s.query( Mama):
        print a, a.kids, a.club
    print '-----------'

if __name__ == '__main__':
    unittest.main()

# vim:ts=4:sw=4:expandtab
