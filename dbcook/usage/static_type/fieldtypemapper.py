#$Id$
# -*- coding: cp1251 -*-

from static_type.types.base import StaticType

class FieldTypeMapper:
    def __init__(me, typemap_upper ={}, typemap_lower ={}):
        me.typemap_upper = typemap_upper
        me.typemap_lower = typemap_lower

    def __call__( me, typ):
        '''опит за (йерархично) съответсвие  тип-поле -> тип-колона.

първо се търси на ниво StaticType, пряко и обхождане по йерархията на класовете.
(филтър в typemap по isinstance не може да направи правилен ред на обхождане)

после, се търси на ниво тип-на-стойността, пряко и филтър в typemap по isinstance

съответно, StaticType-огъвки с разни тип-на-стойността (като Number) не трябва да
се слагат като StaticType в typemap_upper, а в typemap_lower !
'''
    #    print '--', typ#, typemap_upper
    #    for k,v in me.typemap_upper.iteritems(): print k, id(k), v
        assert isinstance( typ, StaticType)

        t = typ.__class__
        while t is not StaticType:
    #        print t,'?', id(t)
            try:
                return me.typemap_upper[ t]
            except KeyError: pass
            for t in t.__bases__:
                if issubclass( t, StaticType):
                    break

        ttyp = typ.typ
        try:
            return me.typemap_lower[ ttyp]
        except KeyError, e:
            for k,v in me.typemap_lower.iteritems():
                if isinstance( ttyp, k): return v
            raise


if __name__ == '__main__':

    from static_type.types.atomary import Text, Bool, AKeyFromDict, Number
    import datetime

    import sqlalchemy

    #field mapping
    typemap_upper = {
        Text:   dict( type= sqlalchemy.String, ),
        Bool  : dict( type= sqlalchemy.Boolean), #Integer ?
     #    Number: dict( type= sqlalchemy.Integer), - dont! rely on typ.typ/lower-level
        AKeyFromDict: dict( type= sqlalchemy.String),
     #    Date: dict( type= sqlalchemy.Date ),
    }
    typemap_lower= {
        str:    dict( type= sqlalchemy.String ),
        float:  dict( type= sqlalchemy.Float ),
        int:    dict( type= sqlalchemy.Integer),
        datetime.datetime:  dict( type= sqlalchemy.DateTime ),
        datetime.date:  dict( type= sqlalchemy.Date ),
        datetime.time:  dict( type= sqlalchemy.Time ),
        datetime.timedelta:  dict( type= sqlalchemy.DateTime ),
    }

    fieldtype_mapper = FieldTypeMapper( typemap_upper, typemap_lower)

    from dbcook.usage.samanager import SAdb
    from sa2static import Builder, value_of_AKeyFromDict, Base

    def test_types():
        class A( Base):
            name = Text()
            name2 = Text()
            a_int  = Number(int)
            a_int2 = Number(int)
            a_bool = Bool()
            a_bool2= Bool()
            enum   = AKeyFromDict( dict( a=1, b=12, c=444) )
            enum2  = AKeyFromDict( dict( a=1, b=12, c=444) )

        def populate():
            a = A()
            a.name = 'pesho'
            try:
                a.enum = 'aaaaaaa'
            except ValueError: pass
            else: raise ValueError, 'A.enum  allows random values'
            a.enum = 'c'
            a.a_int = 344
            a.a_bool = True
            return locals()

        return locals()

    namespace = test_types()

    sa = SAdb()
    sa.open()
    sa.bind( namespace, fieldtype_mapper, builder=Builder, base_klas= Base, )

    A = namespace[ 'A']
    populate = namespace.get( 'populate', None)
    if populate:
        populate_namespace = populate()
    session = sa.session()
    sa.saveall( session, populate_namespace)
    session.flush()

    session = sa.session()
    query = session.query( A)
    print '\n'.join( str(r) for r in query )
    r = session.query( A).first()
    print 'enum->value:', r.enum, value_of_AKeyFromDict( r, 'enum')

# vim:ts=4:sw=4:expandtab
