#$Id$
# -*- coding: cp1251 -*-

class Reflector:
    '''трябва да извлича нужните за O3RM атрибути и типовете им, както
    и други свързани запитвания и операции - оправяне на предварително обявени
    (символични) указатели (forward declared references)'''

    def attrtypes( me, klas):
        raise NotImplementedError
        return dict-like-thing
    if 0:
        class dictLike:
            '(the attr belonging to klas+bases)'
            def __contains__(): return 'bool( attr belongs to klas+bases)'
            def iterkeys():     return 'yield attr_name '
            def iteritems():    return 'yield (attr_name, attr_type) '
            def itervalues():   return 'yield attr_type '
            #def iter_klasi():       return 'yield attr_type.klas '
            #def iter_attr_klas():   return 'yield (attr_name, attr_type.klas) '
            #def iter_attr_type_klas():  return 'yield (attr_name, attr_type, attr_type.klas) '
#    def iter_attrtype_local( me, klas):
#        raise NotImplementedError
#        return 'iter_over_ (attr_name, attr_type) of klas only (no bases!)'
#    def is_collection_type( me, typ):
#        raise NotImplementedError
#        return bool
    def cleanup( me, klas):
        'clean klas of any side-effects like caches'
        raise NotImplementedError
    def is_reference_type( me, typ):
        raise NotImplementedError
        return None or dict( klas= typ.itemklas, lazy= bool or None or 'default', as_value= bool)
    def _resolve_forward_references( me, namespace, base_klas):
        raise NotImplementedError

    def obj2str( me, obj, base_klas, idname, refname ='name'):
        from baseobj import obj2str
        '''nice str(obj), cuts recursion. Uses obj.refname for references (if available)'''
        return obj2str( obj, base_klas,
                    attrname_iterator= lambda o: me.attrtypes( o.__class__).iterkeys() ,
                    idname = idname,
                    refname= refname,
                )

# vim:ts=4:sw=4:expandtab
