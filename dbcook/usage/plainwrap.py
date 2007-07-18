#$Id$
# -*- coding: cp1251 -*-

''' simple O3RM builder:
 - attribute types are only used for DB columns
 - DB-related objects should inherit Base / Association
 - no other (python) restrictions are imposed on objects

Either use the new Builder here, or staticaly
modify the base original: setup( builder.Builder).
Then use the Base, Association, Type4SubStruct, either
via Builder.xxxx, or directly from here.
'''


from dbcook import builder
import sys

class Type( object): pass
class Type4SubStruct( Type):
    def __init__( me, klas, lazy ='default', as_value =False):
        assert not as_value
        me.itemklas = klas
        me.lazy = lazy
        me.as_value = False
    @staticmethod
    def resolve_forward1( typ, *namespaces):
        assert isinstance( typ, Type4SubStruct)
        assert isinstance( typ.itemklas, str)
        for namespace in namespaces:
            try:
                r = typ.itemklas = namespace[ typ.itemklas]
                return r
            except KeyError: pass
        raise KeyError, typ.itemklas
    @staticmethod
    def resolve_forwards( namespace, klas_attrvalue_iterator, namespace2 ={}):
        for typ in klas_attrvalue_iterator:
            if isinstance( typ, Type4SubStruct):
                if isinstance( typ.itemklas, str):
                    Type4SubStruct.resolve_forward1( typ, namespace, namespace2)
    def __str__( me):
        return me.__class__.__name__ + '/'+repr(me.itemklas)

class Reflector4sa( builder.Reflector):
    def __init__( me):
        me.klas2attrtypes = {}
    def _get_attrtype_all( me, klas):     #can be stored also as some klas' attribute
        try:
            attrs = me.klas2attrtypes[ klas]
        except KeyError, e:
            attrs = {}
            for k in dir( klas):
                v = getattr( klas,k)
                if isinstance( v, Type):
                    attrs[k] = v
            me.klas2attrtypes[ klas] = attrs
        return attrs
    def iter_attrtype_all( me, klas):
        return me._get_attrtype_all( klas).iteritems()
    def owns_attr( me, klas, attr):
        return attr in me._get_attrtype_all( klas)

    def type_is_substruct( me, typ):
        if not isinstance( typ, Type4SubStruct):
            return None
        klas = typ.itemklas
        return dict( klas=typ.itemklas, lazy=typ.lazy, as_value=typ.as_value)

    def type_is_collection( me, typ): return False

    def _resolve_forward_references( me, namespace, base_klas):
        for klas in namespace.itervalues():
            if not builder.issubclass( klas, base_klas): continue
            Type4SubStruct.resolve_forwards( namespace, me._get_attrtype_all( klas ).itervalues(),
                    sys.modules[ klas.__module__].__dict__ )
        #this can also remove all Type4SubStruct's from klas
    def _resolve_forward_reference1( me, klas, namespace):
        return Type4SubStruct.resolve_forward1( klas, namespace)



reflector = Reflector4sa()

class Base( object):
    def __str__( me): return reflector.obj2str( me, Base, builder.column4ID.name)
    __repr__ = __str__

class Association( builder.relation.Association):
    Type4SubStruct = Type4SubStruct

def setup( s):
    s.reflector = reflector
    s.Type4SubStruct = Type4SubStruct
    s.Base = Base
    s.Association = Association

class Builder( builder.Builder): pass
setup( Builder)

#############################################

#XXX TODO one common example

if __name__ == '__main__':
    import sqlalchemy
    class Text( Type): pass
    fieldtypemap = {
        Text: dict( type= sqlalchemy.String, ),
    }

    class A( Base):
        name = Text()
        DB_HAS_INSTANCES =True
    class B( A):
        alias = Text()
    class C( Base):
        color = Text()
        blink = Type4SubStruct( B)

    from samanager import SAdb
    SAdb.Builder = Builder
    SAdb.config.getopt()
    sadb = SAdb()

    sadb.open( recreate=True)
    sadb.bind( locals(), fieldtypemap, )#, debug='mapper')

     #create some instances
    a = A()
    a.name = 'ala'

    b = B()
    b.name = 'bala'
    b.alias = 'ba'

    c = C()
    c.color = 'red'
    c.blink = b

     #save them
    populate_namespace = locals()
    session = sadb.session()
    sadb.saveall( session, populate_namespace )
    session.flush()
    session.close()

    for klas in [ A,B,C]:
        print '==', klas
        for qy in [ sadb.query_ALL_instances, sadb.query_BASE_instances, sadb.query_SUB_instances ]:
            print ' --', qy.__name__
            r = qy( session, klas)
            for a in r: print a

    sadb.destroy()

# vim:ts=4:sw=4:expandtab
