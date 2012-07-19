#$Id$


''' simple O3RM builder:
 - attribute types are only used for DB columns
 - DB-related objects should inherit Base / Association
 - no other (python) restrictions are imposed on objects

Either use the new Builder here, or staticaly
modify the base original: setup( builder.Builder).
Then use the Base, Association, Reference, either
via Builder.xxxx, or directly from here.
'''


from dbcook import builder
table_inheritance_types = builder.table_inheritance_types
NO_CLEANUP = False
#XXX TODO cleanup() below makes all repeating-over-same-clas plainwrap tests FAIL
# because mapper+clear_mappers() wipes the Type-definitions in the classes
# Needs restoration procedure ?? put all back from the cache before erasing it?
# for now, use NO_CLEANUP = True where needed

class Type( object): pass
class Type4Reference( Type):
    def __init__( me, klas, lazy ='default', nullable ='default', as_value =False, backref =None):
        assert not as_value
        me.itemklas = klas
        me.lazy = lazy
        me.nullable = nullable
        me.as_value = False
        me.backref = backref
    def __str__( me):
        return me.__class__.__name__ + '/'+repr(me.itemklas)

class Reflector4sa( builder.Reflector):
    '''reflector is static sigleton, hence the attrtypes stay on klas._attrtypes,
    and not in the reflector.somedict[klas] (or it may grow forever).
    The only reason for the Reflector to be static and not local to Builder
    is the Base's __str___/obj2str below...
    '''

    def _attrtypes( me, klas, plains =None, references =None, collections =None):
        for k in dir( klas):
            if k.startswith('__'): continue
            v = getattr( klas,k)
            if collections is not None and isinstance( v, builder.relation._Relation): d = collections
            elif references is not None and isinstance( v, Type4Reference): d = references
            elif plains is not None and isinstance( v, Type): d = plains
            else: continue
            d[k]=v

    def cleanup( me, klas):
        if NO_CLEANUP: return
        try: del klas._attrtypes
        except AttributeError: pass

    ##############
    def is_relation_type( me, typ):
        if isinstance( typ, Type4Reference):
            return me.relation_info(
                        item_klas= typ.itemklas,
                        multiple=False,
                        own     =False, #?
                        as_value= typ.as_value,
                        lazy= typ.lazy,
                        nullable= typ.nullable,
                        backref= typ.backref,
                    )
        elif isinstance( typ, builder.relation._Relation):
            return me.relation_info(
                        item_klas= typ.assoc_klas,
                        multiple= True,
                        own = isinstance( typ, builder.relation.Collection),
                        as_value= False,
                        #lazy= typ.lazy,            #? rel_kargs[lazy]?
                        #nullable= typ.nullable,    #?
                        backref= typ.backref,
                    )
        else: return None

    ##############
    def resolve_forward_references( me, namespace, base_klas):
        return _resolver.resolve( namespace, base_klas )
        #this can also remove all Type4Reference's from klas
    def resolve_forward_reference1( me, typ, namespace):
        return _resolver.resolve1( typ, namespace)


Reference = Type4Reference
reflector = Reflector4sa()

from svd_util.forward_resolver import Resolver
class Resolver( Resolver):
    def finisher( me, typ, resolved_klas):
        typ.itemklas = resolved_klas
    def klas_reftype_iterator( me, klas):
        for t in reflector.attrtypes( klas, references=True ).itervalues():
            assert isinstance( t, Type4Reference)
            yield t
    def is_forward_decl( me, typ):
        assert isinstance( typ, Type4Reference)
        return isinstance( typ.itemklas, str) and typ.itemklas
_resolver = Resolver()


class Base( object):
    vstr = str
    def __str__( me):
        return reflector.obj2str( me, Base, idname=builder.column4ID.name, vstr=me.__class__.vstr)
    __repr__ = __str__
    @classmethod
    def Reference( klas, **kargs): return Reference( klas, **kargs)

class Association( builder.relation.Association):
    __slots__ = ()
    Type4Reference = Type4Reference
    reflector = reflector
class Collection( builder.relation.Collection):
    __slots__ = ()
    reflector = reflector

class Builder( builder.Builder):
    reflector = reflector
    Base = Base
    Type4Reference = Type4Reference
    Association = Association
    Collection = Collection

#############################################

#XXX TODO one common example

if __name__ == '__main__':
    import sqlalchemy
    class Text( Type): pass
    fieldtypemap = {
        Text: dict( type= sqlalchemy.String(100), ),
    }

    class A( Base):
        name = Text()
        DBCOOK_has_instances =True
    class B( A):
        alias = Text()
    class C( Base):
        color = Text()
        blink = Reference( B)

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
