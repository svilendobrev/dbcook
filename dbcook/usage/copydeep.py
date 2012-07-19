#$Id$


dbg = 0
from util_all.dbg import Level
_level = Level( '    ', initial=0)

class _NOTFOUND: pass


class Copier( object):
    'abstract base for all copiers and similars (e.g. pickle)'

    def walk_singulars( me, obj):
        '''return iter( names_of_all_singular_attributes( obj )) - anything not any2many'''
        for k in me.walk_plain_attrs( obj): yield k
        for k in me.walk_references( obj): yield k

    def walk_plain_attrs( me, obj):
        raise NotImplementedError
        return iter( names_of_plain_attributes( obj ))
    def walk_references( me, obj):
        raise NotImplementedError
        return iter( names_of_singular_references( obj ))    #any2one
    def walk_collections( me, obj):
        raise NotImplementedError
        return name_klas_tuples( collections_any2many( obj ))

    def copy_factory( me, obj):
        return obj.__class__()

    def dont_copy_these( me, obj):
        return ()
        return list( names_of_attributes_to_not_copy )
    def dont_copy_deep( me, obj, name, value):
        return False
        return bool( whether_to_copy_deep_or_shallow_the_item )
        #examples:
        return getattr( value, 'dont_copy_me', False)       #the item knows
        return name in getattr( obj, 'dont_copy_deep', ())  #the owner knows
        return or_combination-of-above

    def make_copy( me, valueobj):
        vcopy = getattr( valueobj, 'copy', None)
        if callable( vcopy):
            if dbg: print l, ' copy-deep', name, '=', r(item)
            item = vcopy()

    def is_explicit_association( me, obj, attr, child_klas):
        raise NotImplementedError
        return bool( obj.attr-of-type-child_klas is explicit_assoc_object )
    def is_implicit_association( me, obj, attr, child_klas):
        raise NotImplementedError
        return bool( obj.attr-of-type-child_klas is implicit_assoc )

    def repr( me, obj):     #debug
        return object.__repr__( obj)

    # TODO may need a real full copy, whci will need a way to ignore dont_copy/dont_copy_me?

    def copy( me, obj, dont_copy_now =() ):
        ''' basicaly, logic is to copy all plain attributes and references
        then walk all relations and copy those, with the special case of
        explicit associations, where the backlink of the copy of each member should
        be explicitly set to the new owner.
        Each item (plain or relation-member) is checked if it has to be depth-copied or not.
        '''

        if dbg:
            r = me.repr
            l = _level()
            print l, 'copying', r(obj)

        new = me.copy_factory( obj)
        dont_copy_these = me.dont_copy_these( obj)
        dont_copy_deep = me.dont_copy_deep

        done = set()
        for name in me.walk_singulars( obj ):
            if name in done: continue
            done.add( name)
            if name in dont_copy_now or name in dont_copy_these:
                if dbg: print l, ' ignore', name
                continue

            item = getattr( obj, name, _NOTFOUND)
            if item is _NOTFOUND: #nothing to copy
                if dbg: print l, ' ignore/novalue', name
                continue

            i0 = item
            if not dont_copy_deep( obj, name, item):

                #DO TUKA #XXX me.make_copy( ? )

                vcopy = getattr( item, 'copy', None)
                if callable( vcopy):
                    if dbg: print l, ' copy-deep', name, '=', r(item)
                    item = vcopy()
            if dbg:
                if i0 is item: print l, ' copy-ref', name
                print l, '   copied', name, '=', r(item)
            setattr( new, name, item)


        for name,child_klas in walk_collections( obj):
            if name in dont_copy_now or name in dont_copy_these:
                if dbg: print l, ' ignore', name
                continue

            #make deep-copy of the set = set of copies of each item

            if dbg: print l, ' copy-relation', name, ':', child_klas
            children = getattr( obj, name)     #XXX this can load all!!
            new_children = getattr( new, name)
            #if dbg: print l, '   <', [ r(a) for a in children ]
            #if dbg: print l, '   >', [ r(a) for a in new_children]

            #def copy_relation( obj, name, child_klas, children, new_children, dbg,l ):
            explicit_assoc = me.is_explicit_association( obj, name, child_klas)
                #walk the cases separately???
                #3 cases: non-assoc (nocopy), assoc.hidden (nocopy),
                #         assoc.explicit:copy
            if not explicit_assoc:
                for a in children:
                    if dbg: print l, '  copied-over-ref', r( a)
                    new_children.append( a )
            else:
                ab = about_relation( obj.__class__, name)
                attr = ab.otherside.name
                for a in children:
                    if dbg: print l, '  copy-deep-assoc', r( a)
                    assert getattr( a, attr) is obj
                    a = me.copy( a, dont_copy_now= [attr] )
                    if ab.no_backref:
                        if dbg: print l, '   replace', attr, r(new)
                        setattr( a, attr, new)
                    if dbg: print l, '  copied-over', r( a)
                    new_children.append( a )
            if dbg: print l, ' copied-relation', name, ':', [ r(a) for a in new_children ]
        return new


class CopierSA( Copier):

    def walk_all_props( me, obj):
        return instance_mapper( obj).iterate_properties
    def walk_all_props_non_pk( me, obj):
        primary_key = set( c.key for c in instance_mapper( obj).primary_key )
        return ( p for p in me.walk_all_props() if p.key not in primary_key)

    def walk_singulars( me, obj):
        return ( p.key for p in me.walk_all_props_non_pk()
                    if (not isinstance( p, PropertyLoader)      #not a relation
                        or p.use_list == False )                #or a singular relation/reference
                        #how about SynonymProperty
                        #how about CompositeProperty
                        #or should that be just ColumnProperty + PropertyLoader.use_list=False
                )
    def walk_plain_attrs( me, obj):
        return ( p.key for p in me.walk_all_props_non_pk()
                    if not isinstance( p, PropertyLoader)   #not a relation
                        #how about SynonymProperty
                        #how about CompositeProperty
                        #just plain ColumnProperty
                )
    def walk_references( me, obj):
        return ( p.key for p in me.walk_all_props()
                    if not getattr( p, 'use_list', True)
                        # same as: isinstance( p, PropertyLoader) and not p.use_list
                        # non_pk is implied as pk cant be a relation
                )
    def walk_collections( me, obj):
        return ( (p.key, p._get_target_class()) for p in me.walk_all_props()
                    if getattr( p, 'use_list', False)
                        # same as: isinstance( p, PropertyLoader) and p.uselist
                        # non_pk is implied as pk cant be a relation
                )




if 0:
    class Copier4DBCOOK( Copier):
        def is_explicit_association( me, obj, attr, child_klas):
            return not getattr( child_klas, 'DBCOOK_hidden', True)  #there and empty; 123 is not explicit
        def is_implicit_association( me, obj, attr, child_klas):
            return getattr( child_klas, 'DBCOOK_hidden', False)     #not there or non-empty; 123 is implicit
        def walk_references( me, obj):
            return getattr( obj, 'DBCOOK_references', () )      #would these include inherited?
        def walk_collections( me, obj):
            return getattr( obj, 'DBCOOK_relations', () )       #XXX these DO NOT include inherited

    class Struct( ):
        dont_copy = []  # set of attr-names to ignore when copying;
                        #XXX when inheriting dont miss the base set
        dont_copy_me = False    #copy as reference, not in depth;
                                # the copy will refer same object

        @classmethod
        def _walk_attr( klas):
            raise NotImplementedError
            return iter( names_of_plain_attributes )
        def _walk_refs( klas):
            raise NotImplementedError
            return iter( names_of_singular_references)
        def _walk_collects( klas):
            raise NotImplementedError
            return iter( names_of_collections_any2many)
        class Copier( Copier):
            def walk_plain_attrs( me, obj): return obj._walk_attr()
            def walk_references(  me, obj): return obj._walk_refs()
            def walk_collections( me, obj): return obj._walk_collects()
            def dont_copy_these( me, obj):  return getattr( obj, 'dont_copy', ())
            def dont_copy_deep( me, obj):   return getattr( obj, 'dont_copy_me', False)
        copier = Copier()
        def copy( me, dont_copy_now =(), **kargs):
            return me.__class__.copier.copy( me, dont_copy_now= dont_copy_now, **kargs)

# vim:ts=4:sw=4:expandtab
