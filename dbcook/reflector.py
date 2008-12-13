#$Id$
# -*- coding: cp1251 -*-

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
            from util.attr import setattr_from_kargs
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

    class multidict( object):
        def __init__( me, *dicts):
            me.dicts = [ d for d in dicts if d]
        def __getitem__( me, k):
            for d in me.dicts:
                if k in d: return d[k]
            raise KeyError, k
        def __contains__( me, k):
            for d in me.dicts:
                if k in d: return True
            return False
        def iterkeys( me):
            for d in me.dicts:
                for k in d: yield k
        def itervalues( me):
            for d in me.dicts:
                for x in d.itervalues(): yield x
        def iteritems( me):
            for d in me.dicts:
                for x in d.iteritems(): yield x
        def get( me, k, default =None):
            for d in me.dicts:
                if k in d: return d[k]
            return default
        def __len__( me):
            return sum( len(d) for d in me.dicts)
        def __iter__( me):
            return me.iterkeys()

    DICT = dict

    def attrtypes( me, klas, references =True, collections =False, plains =True):
        'return dict-like-thing == {attr:type}'
        try:
            dd = klas.__dict__[ '_attrtypes']
        except KeyError:
            klas._attrtypes = dd = me.DICT()
            me._attrtypes_plains( klas, dd )
        if references: references = me.DICT()
        else: references = None
        if collections: collections= me.DICT()
        else: collections = None
        if not (references is collections is None):
            me._attrtypes_rels( klas, references=references, collections=collections )
        return me.multidict( plains and dd, references, collections)
    def _attrtypes_rels( me, klas, references, collections):    #dicts2fill or None
        'do not cache!'
        raise NotImplementedError
    def _attrtypes_plains( me, klas, plains):   #dict2fill
        raise NotImplementedError

    if 0:
        class dictLike:
            'all {attr:type} belonging to klas+bases'
            def __contains__(): return 'bool( attr belongs to klas+bases)'
            def iterkeys():     return 'yield attr_name '
            def iteritems():    return 'yield (attr_name, attr_type) '
            def itervalues():   return 'yield attr_type '
            def get( key, default): return attr_type/default
            def __getitem__( key):  return attr_type/default
#    def iter_attrtype_local( me, klas):
#        raise NotImplementedError
#        return 'iter_over_ (attr_name, attr_type) of klas only (no bases!)'
    def cleanup( me, klas):
        'clean klas of any side-effects like caches'
        raise NotImplementedError
    def before_mapping( me, klas):
        'called just before make_mapper( klas, ... )'
        pass
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
                    attrname_iterator= lambda o: list( me.attrtypes( o.__class__, collections=True)
                                             ) + list( getattr( o.__class__, '_extra_attrs4str', [])),
                    idname = idname,
                    refname= refname,
                    **kargs
                )

# vim:ts=4:sw=4:expandtab
