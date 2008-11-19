#$Id$
# -*- coding: cp1251 -*-
from dbcook.aboutrel import about_relation

def eq( me,o):
    for k in '_klas_attr has_many name klas attr'.split():
        my= getattr( me,k)
        other= getattr( o,k)
        if k == 'name': r = (my == other)
        else: r = (my is other)
        if not r: return False
    return True

def test( attr, other={}, about_relation= about_relation, **this):
    about_relation.__eq__ = eq
    a = about_relation( attr)
    print a
    if a.ownedside:
        if a.thisside.has_many:
            assert a.ownedside is a.otherside
            assert a.ownerside is a.thisside
        else:
            assert a.ownerside is a.otherside
            assert a.ownedside is a.thisside

    other.setdefault( 'has_many', not this['has_many'])
    for o,oexpect in [[a.thisside,this], [a.otherside,other]]:
        target = dict( (k,getattr(o,k)) for k in oexpect)
        assert target == oexpect, '%(o)s:\n result: %(target)r\n expect: %(oexpect)r' % locals()
    return a



from sqlalchemy.orm import clear_mappers, class_mapper
from sqlalchemy import MetaData, Integer, String
import unittest

class AboutRel( object):
    def tearDown( me):
        clear_mappers()

    BACKREF = False
    backref_kids = backref_club = backref_work = backref_friend = None
    def backrefs( me):
        BACKREF = me.BACKREF
        me.backref_kids2 = me.backref_kids = BACKREF and 'mama' or None
        me.backref_club = BACKREF and 'members' or None
        me.backref_work = BACKREF and 'employes' or None
        me.backref_papa = BACKREF and 'opap' or None

    def test_mama_kids_1_n( me):
        test( me.Mama.kids,
            name='kids', klas=me.Mama, has_many=True,
            other=dict( name=me.backref_kids, klas=me.Kid, anyname=me.backref_kids2)
        )
    def test_mama_work_n_1( me):
        test( me.Mama.work,
            name='work', klas=me.Mama, has_many=False,
            other=dict( name=me.backref_work, klas=me.Work)
        )
    def test_mama_club_n_n( me):
        a = test( me.Mama.club,
            name='club', klas=me.Mama, has_many=True,
            other=dict( name=me.backref_club, klas=me.Club, has_many=True)
        )
        assert a.midthis.klas is a.midother.klas
    def test_mama_friend_self_n_1( me):
        Mama = me.Mama
        test( Mama.friend,
            name='friend', klas=Mama, has_many=False,
            other=dict( name=None, klas=Mama)
        )
    def test_mama_papa_1_1( me):
        Mama = me.Mama
        test( Mama.papa,
            name='papa', klas=Mama, has_many=False,
            other=dict( name=me.backref_papa, klas=me.Papa, has_many=not me.backref_papa )
        )
    def test_wrongs( me):
        for a in me.Kid, me.Kid.name, 'alala':
            try:
                about_relation( a)
            except ValueError, e:
                if 'not a relation klas_attr' in e.message: continue
                raise

class AboutRel_backref( AboutRel):
    BACKREF = True
    def test_kid_mama_1_n_back( me):
        test( me.Kid.mama,
            name='mama', klas=me.Kid, has_many=False,
            other=dict( name='kids', klas=me.Mama)
        )
    def test_work_employes_n_1_back( me):
        test( me.Work.employes,
            name='employes', klas=me.Work, has_many=True,
            other=dict( name='work', klas=me.Mama)
        )
    def test_club_members_n_n_back( me):
        a=test( me.Club.members,
            name='members', klas=me.Club, has_many=True,
            other=dict( name='club', klas=me.Mama, has_many=True)
        )
        assert a.midthis.klas is a.midother.klas


import sys
try: sys.argv.remove('debug'); debug=True
except: debug=False

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
            backref_work = me.backref_work
            backref_papa = me.backref_papa and dict( name=me.backref_papa, uselist=False)
            backref = me.BACKREF

            class Work( o2r.Base):
                name = Text()
                if backref_work:
                    assert backref_work == 'employes'
                    employes = o2r.Collection( 'Mama', backref='work')
            class Club( o2r.Base):
                name = Text()
                if 0:#*backref_club:
                    assert backref_club == 'members'
                    members = o2r.Collection( 'Mama', backref='club')
            class Kid( o2r.Base):
                name = Text()
            class Mama( o2r.Base):
                name = Text()
                if not backref_work:
                    work = o2r.Reference( Work)
                if 1:#not backref_club:
                    club = o2r.Association.Hidden( Club, backref_club and 'members' or '')
                kids = o2r.Collection( Kid, backref=backref_kids)
                friend = o2r.Reference( 'Mama')
                papa   = o2r.Reference( 'Papa', backref=backref_papa)
                if 1: #not yet without this
                    skills = o2r.Association.Relation( 'SkillMap', backref='mama')
            class Papa( o2r.Base):
                name = Text()
            class Skill( o2r.Base):
                name = Text()
                if backref:
                    actors = o2r.Association.Relation( 'SkillMap', backref='skill')
            class SkillMap( o2r.Association, o2r.Base):
                #cannot be helped if no Mama.skills...
                #mama = o2r.Association.Link( Mama, 'skills') #not yet just this
                if not backref:
                    skill = o2r.Association.Link( Skill)
                level = Text()
            namespace = locals().copy()
            mkids = Mama.kids
            meta = MetaData()
            o2r.Builder( meta, namespace, fieldtype_mapper= fieldtype_mapper,
                    only_declarations =True,
                    debug= debug and 'mapper,relation.table' or ''
                )

            from dbcook import config
            me.backref_kids2 = backref_kids or config.column4ID.ref_make_name( mkids.backrefname)
            me.Mama = Mama
            me.Kid = Kid
            me.Club = Club
            me.Work = Work
            me.Papa = Papa
            me.Skill = Skill
            me.SkillMap = SkillMap

        def test_skills_n_n_explicit( me):
            from dbcook.aboutrel import about_relation_assoc_explicit
            a=test( me.Mama.skills,
                about_relation = lambda *a,**k: about_relation_assoc_explicit( about_relation( *a,**k)),
                name='skills', klas=me.Mama, has_many=True,
                other=dict( name=me.BACKREF and 'actors' or None, klas=me.Skill, has_many=True)
            )
            assert a.midthis.klas is a.midother.klas
            assert a.midthis.klas is me.SkillMap
            assert a.midthis.name == 'mama'
            assert a.midother.name == 'skill'

    class t3_dbcook_nobackref( dbcook_setup, AboutRel, unittest.TestCase ):
        pass
    class t4_dbcook_backref( dbcook_setup, AboutRel_backref, unittest.TestCase ):
        pass

class sa_setup( object):
    def table( me, klas):
        return class_mapper( klas).local_table.c
    def setUp( me):
        me.backrefs()
        from sqlalchemy.orm import mapper, relation, compile_mappers, backref
        from sqlalchemy import Table, Column, ForeignKey
        meta = MetaData( 'sqlite:///')
        #meta.bind.echo=True

        twork = Table('work', meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
            )
        tclub = Table('club', meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
            )
        tpapa = Table('papa', meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('mama_id', Integer, ForeignKey('mama.id'))
            )
        tmama = Table('mama', meta,
                Column('name', Integer, ),
                Column('id', Integer, primary_key=True),
                Column('work_id', Integer, ForeignKey('work.id',)),
                Column('friend_id', Integer, ForeignKey('mama.id', use_alter=True, name='ma2ma')),
                Column('papa_id', Integer, ForeignKey('papa.id', use_alter=True, name='ma2pa')),
            )
        tclubmama = Table('clubmama', meta,
                Column('club_id', Integer, ForeignKey('club.id',)),
                Column('mama_id', Integer, ForeignKey('mama.id',)),
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
        class Papa( Base):pass
        class Work( Base):pass
        class Mama( Base): pass
        class Kid( Base): pass

        mapper( Mama, tmama, properties={
                'kids': relation( Kid,  backref= me.backref_kids,),
                'club': relation( Club, backref= me.backref_club, secondary=tclubmama),
                'work': relation( Work, backref= me.backref_work,),
                'friend': relation( Mama,
                            post_update=True,
                            uselist=False,
                            lazy=True,
                        ),
                'papa': relation( Papa,
                            uselist=False,
                            primaryjoin= tmama.c.papa_id == tpapa.c.id,
                            backref= me.backref_papa and backref(
                                me.backref_papa,
                                primaryjoin= tpapa.c.mama_id == tmama.c.id,
                                uselist=False,
                            ),
                        ),

            })
        mapper( Kid, tkid)
        mapper( Club, tclub)
        mapper( Work, twork)
        pa=mapper( Papa, tpapa)
        if not me.backref_papa:
            pa.add_property(  'mama', relation( Mama,
                            primaryjoin= tpapa.c.mama_id == tmama.c.id,
                            uselist=False,
                        ))
        compile_mappers()   #or populate()

        me.backref_kids2 = me.backref_kids or 'mama_id'
        me.Mama = Mama
        me.Kid = Kid
        me.Club = Club
        me.Work = Work
        me.Papa = Papa

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
