#$Id$
# -*- coding: utf-8 -*-

#TODO: put all them _DBCOOK_attrtypes _DBCOOK_relations _DBCOOK_references
#   under single._DBCOOK.attrtypes


class Reflector:
    '''трябва да извлича нужните за O3RM атрибути и типовете им, както
    и други свързани запитвания и операции - оправяне на предварително обявени
    (символични) указатели (forward declared references)'''

    class relation_info( object):
        #_cardinality = '1:1 1:n n:1 n:n'.split()
        def __init__( me, item_klas, **kargs):
            assert item_klas
            me.klas = item_klas
            #assert cardinality in me._cardinality
            #me.cardinality = cardinality
            from svd_util.attr import setattr_from_kargs
            setattr_from_kargs( me, kargs,
                as_value= False,    #bool,
                lazy    = 'default' or bool or None,
                nullable= 'default' or bool,
                backref = None,     #name or dict( kargs) or None,
                own     = None,     #bool or None
                multiple= False,    #bool
            )
            assert not kargs
            if me.as_value: assert me.own
        @property
        def is_reference( me):   return not me.multiple
        @property
        def is_association( me): return me.multiple and not me.own
        @property
        def is_collection( me):  return me.multiple and me.own
        @property
        def cardinality( me):
            return (me.own and '1' or 'n'),(me.multiple and 'n' or '1')

    if 0:
        class dictLike:
            'all {attr:type} belonging to klas+bases'
            def __contains__(): return 'bool( attr belongs to klas+bases)'
            def iterkeys():     return 'yield attr_name '
            def iteritems():    return 'yield (attr_name, attr_type) '
            def itervalues():   return 'yield attr_type '
            def get( key, default): return attr_type/default
            def __getitem__( key):  return attr_type/default

    DICT = dict
    _categories = 'plains references collections'.split()

    def attrtypes( me, klas, **kargs):  #references =True, collections =False, plains =True):
        'return dict-like-thing == {attr:type}'
        assert kargs
        try: all = klas.__dict__[ '_DBCOOK_attrtypes']
        except KeyError:
            klas._DBCOOK_attrtypes = all = {}

        dicts = {}
        dicts2fill = {}
        for k in me._categories:
            if not kargs.get( k): continue
            d = all.get( k)
            if d is None:
                d = me.DICT()
                if k == 'plains': all[k] = d    #cache immediately
                dicts2fill[k] = d
            dicts[k] = d

        assert dicts
        if dicts2fill:
            me._attrtypes( klas, **dicts2fill)

        r = me.DICT()
        for k in me._categories:
            p = dicts.get( k)
            if p: r.update( p)
        return r

    def _attrtypes( me, klas, plains =None, references =None, collections =None):   #dicts2fill or None
        'do not cache!'
        #reasons: AssocHidden-cloning
        # PolymorphicAssociation.cloning??
        raise NotImplementedError

    def cleanup( me, klas):
        'clean klas of any side-effects like caches'
        pass
    def before_mapping( me, klas):
        'called just before make_mapper( klas, ... )'
        #cache these... and so long
        #print 'before_mapping', klas
        references = klas._DBCOOK_attrtypes[ 'references' ] = me.DICT()
        collections= klas._DBCOOK_attrtypes[ 'collections'] = me.DICT()
        me._attrtypes( klas, references= references, collections= collections)

    def is_relation_type( me, typ):
        raise NotImplementedError
        return None or relation_info
    def resolve_forward_references( me, namespace, base_klas):
        raise NotImplementedError
    def resolve_forward_reference1( me, typ, namespace):
        raise NotImplementedError

    def obj2str( me, obj, base_klas, idname, refname ='name', **kargs):
        from baseobj import obj2str
        '''nice str(obj), cuts recursion. Uses v.idname and obj.refname for references (if available)'''
        return obj2str( obj, base_klas,
                    attrname_iterator= lambda o: list( me.attrtypes( o.__class__, plains=True, references=True, collections=True)
                                             ) + list( getattr( o.__class__, '_extra_attrs4str', [])),
                    idname = idname,
                    refname= refname,
                    **kargs
                )

# vim:ts=4:sw=4:expandtab
