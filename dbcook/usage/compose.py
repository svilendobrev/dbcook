#$Id$
# -*- coding: cp1251 -*-

class composer( object):
    class proxy( object):
        __slots__ = 'obj name'.split()
        @staticmethod
        def compose_name( name, subname):
            return name + '_' + subname
        def __init__( me, obj, name):
            me.obj = obj
            me.name = name
        def __getattr__( me, key):
            return getattr( me.obj, me.compose_name( me.name, key))
        def __setattr__( me, key, value):
            if key in me.__slots__:
                return object.__setattr__( me, key, value)
            return setattr( me.obj, me.compose_name( me.name, key), value )

    def __init__( me, factory, name):
        me.factory = factory
        me.name = name
    def __get__( me, obj, klas ):
        return me.proxy( obj or klas, me.name)

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
        a = composer( None, 'a')
        b_x = Text()
        b_y = Int()
        b = composer( None, 'b')

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
    #anything off Base, go to db
    for a in locals().values():
        if isinstance( a, Base): session.save( a)
    session.flush()
    session.clear()

    def prn(q):
        for x in q: print ' ', x
        print

    print '       --- xxxxxxxxxxxxxx'
    prn( session.query( Engineer).filter( Engineer.a.x < 6 ).all() )
#    prn( session.query( Engineer).filter( Engineer.a == ( 6,4) ).all() )
    prn( expression.query1( lambda self: self.a.y > 5, klas=Engineer, session=session) )

# vim:ts=4:sw=4:expandtab
