#$Id$
# -*- coding: cp1251 -*-

class Reflector:
    '''трябва да извлича нужните за O3RM атрибути и типовете им, както
    и други свързани запитвания и операции - оправяне на предварително обявени
    (символични) указатели (forward declared references)'''

    def attrtypes_hasattr( me, klas, attr):
        raise NotImplementedError
        return 'bool( attr belongs to klas+bases)'
    def attrtypes_iteritems( me, klas):
        raise NotImplementedError
        return 'iter_over_ all (attr_name, attr_type) of klas+bases'
#    def iter_attrtype_local( me, klas):
#        raise NotImplementedError
#        return 'iter_over_ (attr_name, attr_type) of klas only (no bases!)'
    def type_is_collection( me, typ):
        raise NotImplementedError
        return bool
    def type_is_substruct( me, typ):
        raise NotImplementedError
        return None or dict( klas=typ.itemklas, lazy=bool or None or 'default', as_value=bool)
    def _resolve_forward_references( me, namespace, base_klas):
        raise NotImplementedError

    def obj2str( me, obj, base_klas, idname, refname ='name'):
        from baseobj import obj2str
        '''nice str(obj), cuts recursion. Uses obj.refname for references (if available)'''
        return obj2str( obj, base_klas,
                    attrname_iterator= lambda o: (k for k,typ in me.attrtypes_iteritems( o.__class__)) ,
                    idname = idname,
                    refname= refname,
                )

# vim:ts=4:sw=4:expandtab
