#$Id$
# -*- coding: cp1251 -*-

def obj2str( obj, base_klas, attrname_iterator, idname, refname ='name'):
    '''nice str(obj), cuts recursion in references.
    Uses obj.idname, attrname_iterator(obj), and obj.refname (if available) for references
'''
    r = obj.__class__.__name__ +'/id='+ str( getattr( obj, idname)) + '('
    for k in attrname_iterator( obj):
        v = getattr( obj, k, '<notset>')
        if isinstance( v, base_klas):
            v = v.__class__.__name__ +'/id'+ str( getattr( v, idname)) + '/'+ str( getattr( v, refname,''))
        r += ' '+k+'='+str(v)
    return r+' )'


class Base( object):
    def __init__( me, **kargs):
        for k,v in kargs.iteritems(): setattr( me, k, v)

    idname = 'id'
    props = ()  #[...]
    refname = 'name'
    def __str__( me):
        return obj2str( me, Base,
                    attrname_iterator= lambda me: me.__class__.props,
                    idname = me.__class__.idname,
                    pretty_name = me.__class__.refname,
                )

# vim:ts=4:sw=4:expandtab
