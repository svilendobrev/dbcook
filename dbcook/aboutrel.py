#$Id$
# -*- coding: cp1251 -*-

class about_relation( object):
    '''usage:
        a = about_relation(x)
        print a.name, a.klas, a.attr, 'is_parent:', a.is_parent
        b = a.otherside
        print b.name, b.klas, b.attr, 'is_parent:', b.is_parent
        assert a.otherside.otherside is a
        if a.is_parent:
            assert a.child  is a.otherside
            assert a.parent is a
        else:
            assert a.parent is a.otherside
            assert a.child  is a
        '''

    __slots__ = ''' _klas_attr _is_thisside
    is_parent klas name attr
    no_backref otherside parent child
        '''.split()
    #@property
    #def thisside( me): return me

    def __str__( me):
        org = me._is_thisside and me or me.otherside
        return me.__class__.__name__+ '( %s.%s ) ' % ( org.klas.__name__, org.name) + ' / '.join(
                '%s is %s %s' % (
                    o._is_thisside and 'thisside' or 'otherside',
                    o.is_parent and 'parent' or 'child',
                    not o._is_thisside and '%s.%s' % (o.klas.__name__, o.name) or '',
                    #me._klas_attr,
                ) for o in (me, me.otherside) )

    def __init__( me, klas_attr_or_klas, attr_name =None, _other =None):
        if attr_name is None: klas_attr = klas_attr_or_klas
        else: klas_attr = getattr( klas_attr_or_klas, attr_name)
        me._klas_attr = klas_attr
        try:
            impl = klas_attr.impl
            prop = klas_attr.property
            mapper = prop.mapper
        except AttributeError, e:
            assert 0, 'not a relation klas_attr: '+ repr( klas_attr) + ' / ' + str( klas_attr)

        if _other is None:
            from sqlalchemy.orm.attributes import CollectionAttributeImpl
            me._is_thisside = True
            me.is_parent = prop.uselist #isinstance( impl, CollectionAttributeImpl)
            me.otherside = about_relation( klas_attr, _other=me)
        else:   #slave
            me._is_thisside = False
            me.otherside = _other
            me.is_parent = not _other.is_parent

        '''
m2m:
    containerthis: getattr( prop.parent.class_, prop.key)
     midthis: getattr( prop.secondary, prop.remote_side[0]) -> this: getattr( prop.parent.class_, prop.local_side[0])
     midother:getattr( prop.secondary, prop.remote_side[1]) -> other:getattr( prop.mapper.class_, prop.local_side[1])
    containerother: getattr( prop.mapper.class_, ??????)
1toN:
    containerthis: getattr( prop.parent.class_, prop.key)
     other:getattr( prop.mapper.class_, prop.remote_side[0]) -> this:getattr( prop.parent.class_, prop.local_side[0])
    other:getattr( prop.mapper.class_, ??????)
*to1:
    this: getattr( prop.parent.class_, prop.key) ->
     this:getattr( prop.parent.class_, prop.local_side[0]) -> other:getattr( prop.mapper.class_, prop.remote_side[0])
    other:getattr( prop.mapper.class_, ??????)
'''
        me.parent, me.child = me.is_parent and (me, me.otherside) or (me.otherside, me)
        #TODO: try on 1:1/backref and n:n
        if me._is_thisside:
            me.klas = impl.class_   #same as prop.parent.class_
            me.name = prop.key
            me.attr = klas_attr
            assert me.attr is getattr( me.klas, me.name)
        else:
            me.klas = mapper.class_
            revprop = prop._reverse_property
            if revprop is None:
                if 0:
                    print 'ZZZZZZZ', prop
                    for k in '''
target secondary _opposite_side remote_side local_side foreign_keys
'''.split():
                        a = getattr( prop, k)
                        if isinstance( a, set): a = ', '.join( str(s) for s in a)
                        print ' .'+ k, ' \t', a

                me.no_backref = True
                if not me.is_parent:
                        #ok on 1:m
                        #not ok on m:m - see local_side/_opposite_side but those are db_id
                    me.name = list( prop.remote_side )[0].key    #column-name! not attr-name
                    me.attr = getattr( me.klas, me.name)
                else:
                    me.name = me.attr = None
            else:
                me.no_backref = False
                me.name = revprop.key
                me.attr = getattr( me.klas, me.name)



if 0:
    #return parent_klas._DBCOOK_relations[ attr]   #needs flatening from all the inh-classes
    #klas_attr.impl.* thisside
    #print  prop._reverse_property - needs backref
    #print  prop._reverse_property.impl.key  - otherside name, needs backref
    #print  prop.backref.key  - otherside attrname, needs backref
    # prop.remote_side - otherside , set of columns
    try:    me.propeprty
    except AttributeError:
        assert 0, 'not a relation klas_attr: '+ repr( me._klas_attr)

# vim:ts=4:sw=4:expandtab
