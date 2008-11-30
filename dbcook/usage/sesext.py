#$Id$
# -*- coding: cp1251 -*-

from sqlalchemy.orm.session import SessionExtension
_debug = 1

class SesExt( SessionExtension):
    def __init__( me, allow_mod =True, allow_del =True, fixer =None):
        me.allow_mod = allow_mod
        me.allow_del = allow_del
        me.fixer = fixer

    def before_flush( me, session, flush_context, instances):
            #`instances` is an optional list of objects which were passed to the ``flush()``
            #flush_context is WHAT? UOWTransaction of ...?
        s = session

        allnew = s.new
        allmod = [ i for i in s.dirty if s.is_modified( i) ]
        alldel = s.deleted
        if _debug:
            print ':to-be-inserted'
            for i in allnew: print i

            print ':to-be-modified'
            for i in allmod: print i

            print ':to-be-deleted'
            for i in alldel: print i

        if not me.allow_del: assert not alldel
        if not me.allow_mod: assert not allmod

        fixer = me.fixer
        if fixer:
            if _debug: print ':fixing:'
            for i in allnew:
                r = fixer( i)
                if _debug and r: print i

if __name__ == '__main__':
    from dbcook.usage import plainwrap as o2r
    from dbcook.util.attr import setattr_kargs
    from dbcook.baseobj import Base
    Association = o2r.Association
    Collection  = o2r.Collection
    Reference = o2r.Reference
    Collection2 = Association.Hidden    #many2many дето изглежда като one2many
    Reference2 = Association.Hidden     #many2many дето изглежда като one2many
    Type = o2r.Type

    class Text( Type): pass
    class Int( Type): pass

    _timer = 0
    def timer():
        global _timer
        _timer+=1
        return _timer
    class Base( Base):
        #DBCOOK_no_mapping = True
        idname='db_id'
        def __repr__( me): return str(me)
        #@staticmethod
        time  = Int()
        def fixer( o):      #session-level
            if o.time is None:
                o.time = timer()

    from sqlalchemy.ext.associationproxy import association_proxy
    class A( Base):
        name = Text()
        children = Collection( 'B')
        features = Collection2( 'Feature', backref='owners')
        props = 'time name children features '.split()

    class Feature( Base):
        name = Text()
        opa  = Int()
        value = Text()
        props = 'time name value opa'.split()
        def __repr__( me):
            return str(me) + '/owners:' + ','.join( a.name for a in me.owners )
        DBCOOK_defaults = dict( opa= timer)     #table-column level
    class B( Base):
        name = Text()
        props = 'time name ffeas befeas'.split()
        ffeas = association_proxy( 'befeas', 'fea', creator= lambda value: B_Fea( fea=value) )

    class B_Fea( Association, Base):
        owner = Association.Link( B, attr='befeas')
        fea   = Association.Link( Feature)
        __init__ = setattr_kargs
        props = 'time owner fea'.split()

    #fixers = { B_Fea: B_Fea.fixer,  }
    def fixer( o):
        f = getattr( o, 'fixer', None)
        if callable(f):
            f()
            return True
    if 0:
        for klas,func in fixers.iteritems():
            if isinstance( o, klas):
                func(o)
                return True

    from dbcook.usage.samanager import SAdb, sqlalchemy
    SAdb.Builder = o2r.Builder
    SAdb.config.getopt()
    sadb = SAdb()

    fieldtypemap = {
        Text: dict( type= sqlalchemy.String(100), ),
        Int: dict( type= sqlalchemy.Integer, ),
    }
    sadb.open( recreate=True)
    sadb.bind( locals(), fieldtypemap, base_klas=Base )#, debug='mapper')

    def populate():
        a = A()
        a.name = 'ala'

        b1 = B()
        b1.name = 'bala'
        a.children.append( b1)
        a.children.append( B( name='oja', ) )

        a2 = A( name='uuk')
        f1 = Feature( name='hair', value='red')
        f2 = Feature( name='nose', value='long')
        f3 = Feature( name='size', value='tall')
        a.features.extend( [f1,f2, f3] )
        a2.features.append( f1)
        a2.features+= [f1, f2]

        bf1 = B_Fea( owner=b1, fea=f1)
        bf2 = B_Fea( owner=b1, fea=f2)
        b1.ffeas.append( f3)
        print 11111111111111, b1
        return locals()

    pops = populate()
    sext = SesExt( fixer=fixer)
    ses = sadb.session( extension=sext)
    sadb.saveall( ses, pops)
    ses.flush()
    ses.clear()
    print '============'
    for a in sadb.query_ALL_instances( ses, A):
        print a
    print '============'
    for a in sadb.query_ALL_instances( ses, B):
        print a
# vim:ts=4:sw=4:expandtab
