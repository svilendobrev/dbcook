#$Id$


#see also  sqlachemy/examples/derived_attributes/attributes.py
# for methods that can be used at both class and instance

import sqlalchemy.orm

class proxy( object):
    __slots__ = 'obj name'.split()
    def compose_name( me, subname):
        return me.name + '_' + subname
    def __init__( me, obj, name):
        me.obj = obj
        me.name = name
    def __getattr__( me, key):
        return getattr( me.obj, me.compose_name( key))

class proxy4inst( proxy):
    __slots__ = ()
    def __setattr__( me, key, value):
        if key in me.__slots__ or key in proxy.__slots__:
            return object.__setattr__( me, key, value)
        return setattr( me.obj, me.compose_name( key), value )

class proxy4klas( proxy, sqlalchemy.orm.interfaces.PropComparator):
    def __init__( me, obj, name, eq_keys =()):
        me.obj = obj
        me.name = name
        me.eq_keys = eq_keys
    def __eq__( me, other):
        assert me.eq_keys
        obj = me.obj
        if isinstance( other, (tuple,list)):
            def getother( k,ix): return other[ix]
        elif isinstance( other, dict):
            def getother( k,ix): return other[k]
        else:
            def getother( k,ix): return getattr( other, k)
        return sqlalchemy.and_( *[
                    getattr( obj, me.compose_name(k)) == getother( k,ix)
                    for ix,k in enumerate( me.eq_keys) ])

class composer( object):
    eq_keys = ()
    def __init__( me, factory, name, eq_keys =() ):
        me.factory = factory
        me.name = name
        if isinstance( eq_keys, basestring): eq_keys = eq_keys.split()
        if eq_keys: me.eq_keys = eq_keys
    def __get__( me, obj, klas ):
        if obj: return proxy4inst( obj, me.name)
        return proxy4klas( klas, me.name, me.eq_keys)


if __name__ == '__main__':
    import sys
    from dbcook.usage import sa_hack4echo   #nicer selects echoed PLEAZE
    import dbcook.usage.plainwrap as o2r
    from dbcook import expression
    class Text( o2r.Type): pass
    class Int(  o2r.Type): pass
    class Bool( o2r.Type): pass
    Base = o2r.Base

    class Engineer( Base):
        machine = Text()
        a_x = Text()
        a_y = Int()
        a = composer( None, 'a', eq_keys ='x y')
        b_x = Text()
        b_y = Int()
        b = composer( None, 'b')

    if 0*1:
        class Point( composer):
            eq_keys = 'x y'
        class Vertex( Base):
            a_x = Text()
            a_y = Int()
            a_name = Text()
            a = Point( 'a')
            b_x = Text()
            b_y = Int()
            b_name = Text()
            b = Point( 'b')

    if 0*2:
        class Point( composer):
            eq_keys = 'x y'
        class Vertex( Base):
            a_x = Text()
            a_y = Int()
            a = Point( 'a')
            b_x = Text()
            b_y = Int()
            b = Point( 'b')

    import sqlalchemy
    import sqlalchemy.orm
    meta = sqlalchemy.MetaData( sqlalchemy.create_engine('sqlite:///', echo= 'echo' in sys.argv ))

    # build the mapping
    mybuild = o2r.Builder( meta,
            locals(),       #just scan anything here that looks like subclass of Base
            fieldtype_mapper = { # map attr-types to sql-column-types
                Text: dict( type= sqlalchemy.String(100), ),
                Int : dict( type= sqlalchemy.Integer, ),
                Bool: dict( type= sqlalchemy.Boolean, ),
            },
            generator =True     #lets see how this would look in plain sqlalchemy
        )

    if mybuild.generator:   #see how this should look in plain SA calls
        print '========= generated SA set-up'
        print mybuild.generator.out
        print '========= eo generated SA set-up'

    #populate
    e2 = Engineer()
    e2.name = 'ena'
    e2.age = 30
    e2.machine = 'deep'

    print 22222222222
    e2.a.x = ax = 'ewq'
    e2.a_y = ay = 12
    e2.b.x = 'eet'
    e2.b.y = by = 123
    assert e2.a.x == e2.a_x == ax
    assert e2.b.y == e2.b_y == by

    session = sqlalchemy.orm.create_session()
    for a in locals().values(): #anything off Base, go to db
        if isinstance( a, Base): session.save( a)
    session.flush()
    session.clear()

    def prn(q):
        print q
        for x in q: print ' ', x
        print

    print '       --- xxxxxxxxxxxxxx'
    print Engineer.a.x
    prn( session.query( Engineer).filter( Engineer.a.x < 6 ) )
    prn( expression.query1( lambda self: self.a.y > 5, klas=Engineer, session=session) )
    prn( session.query( Engineer).filter( Engineer.a == sqlalchemy.orm.aliased(Engineer).b ) )
    prn( session.query( Engineer).filter( Engineer.a == ( 6,4) ) )
    prn( session.query( Engineer).filter( Engineer.a == dict( x= 6, y=4) ) )

# vim:ts=4:sw=4:expandtab
