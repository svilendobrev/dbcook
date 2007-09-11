#$Id$
# -*- coding: cp1251 -*-

''' O3RM builder for mapping of statictype-d objects:
 - attribute types are enforced in python, not only for DB columns
 - DB-related objects should inherit Base / Association
 - no additional attributes (post-definition) attributes allowed

Either use the new Builder here, or staticaly
modify the base original: setup( builder.Builder).
Then use the Base, Association, Type4Reference, either
via Builder.xxxx, or directly from here.
'''


class _static_type:
    from static_type.types.base import StaticStruct, SubStruct, StaticType, config
    from static_type.types.sequence import Sequence
    from static_type.types.forward import ForwardSubStruct

from dbcook import builder
table_inheritance_types = builder.table_inheritance_types

class Reflector4StaticType( builder.Reflector):
    def iter_attrtype_all( me, klas): return klas.StaticType.itertypes()  #name,type
    def owns_attr( me, klas, attr):   return attr in klas.StaticType
    def type_is_collection( me, typ): return isinstance( typ, _static_type.Sequence)

    #checker4substruct_as_value = None
    def type_is_substruct(  me, typ):
        if not isinstance( typ, _static_type.SubStruct):
            return None
        klas = typ.typ
        lazy = getattr( klas, 'DB_must_be_reference', False) or getattr( typ, 'lazy', False)
        return dict( klas=klas, lazy=lazy, as_value=False)
        #as_value = callable( me.checker4substruct_as_value) and me.checker4substruct_as_value( klas)

    def _resolve_forward_references( me, namespace, base_klas):
        _static_type.ForwardSubStruct.resolve( namespace )


class _Base( _static_type.StaticStruct):
    __slots__ = [ builder.column4ID.name ]  #db_id автоматично, не-StaticType
    #DBCOOK_inheritance = 'concrete_table'    #default
    #DBCOOK_no_mapping = True       #default; klas-local only
    #DBCOOK_has_instances = True    #default: only for leafs; klas-local only

    if 'needs _str_ with id':
        @staticmethod
        def _order_maker( klas):
            r = _static_type.StaticStruct._order_maker( klas)
            for k in _Base.__slots__:
                try: r.remove(k)
                except ValueError: pass
            return list( _Base.__slots__) + r
        @staticmethod
        def _order_Statics_gettype( klas, k):
            if k in _Base.__slots__: return None
            return _static_type.StaticStruct._order_Statics_gettype( klas,k)



###########################
'адаптиране на StaticStruct за пред sqlAlchemy'

from dbcook.config import _v03
if _v03: #'AVOID having privately-named __sa_attr_state':      #not needed for v04?
    from sqlalchemy.orm import mapperlib
    mapperlib.attribute_manager.init_attr = lambda me: None

_static_type.config.notSetYet = None
_debug = 0*'dict'

class dict_via_attr( object):
    '''this to avoid having __dict__ - SA uses __dict__ directly,
    for both normal and for additionaly mapped attributes, e.g. a_id;
    use as  __dict__ = property( dict_via_attr)
    '''
    __slots__ = [ 'src' ]
    def __init__( me, src): me.src = src
    def has_key( me, k):
        try: me[k]
        except KeyError: return False
        return True
    __contains__ = has_key
    def __getitem__( me,k):
        src = me.src
        dbg = 'dict' in _debug
        if dbg: print 'dict get', me.src.__class__, k
        try:
            r = src.StaticType[ k].__get__( src)    #, #no_defaults=True)
            if 0*dbg: print '  got', repr(r)
            return r
        except AttributeError,e:    #attribute declared but not set
            if dbg: print ' not found, KeyError'
            raise KeyError,k
        except KeyError,e:  #extra attribute
            try: d = src._my_sa_stuff
            except AttributeError: d = src._my_sa_stuff = dict()
            if dbg: print ' _my_sa_stuff get', k, d.get( k, '<missing>')
            #raise KeyError, a.args
            return d[k]
    def __setitem__( me, k,v, delete =False):
        src = me.src
        dbg = 'dict' in _debug
        SET = delete and 'DEL' or 'SET'
        if dbg: print 'dict', SET, me.src.__class__, k, repr(v)
        vv = v
        try: return src.StaticType[ k].__set__( src, vv)
#        except AttributeError,e:    #attribute declared but readonly
#            raise KeyError,k
        except KeyError,e:  #extra attribute
            try: d = src._my_sa_stuff
            except AttributeError: d = src._my_sa_stuff = dict()
            if dbg: print ' _my_sa_stuff', SET, k, repr(v)
            if delete: return d.__delitem__( k)
            return d.__setitem__( k,v)
    def __delitem__( me, k):
        return me.__setitem__( k, None, True)

######################

class _Meta2check_dict( _Base.__metaclass__):
    @staticmethod
    def convert( mklas, name, bases, adict):
        for b in bases:
            for c in b.mro():
                d = c.__dict__.get( '__dict__', None)
                if d and not isinstance( d, property):
                    bb = b is not c and '(via %(b)s)' % locals() or ''
                    assert 0, '''cannot create class `%(name)s`, because
 a base class %(c)s %(bb)s
 contains/allows dynamic __dict__;
 setup __slots__ = () (or something) on that base class (and do not put "__dict__")''' % locals()
        _Base.__metaclass__.convert( mklas, name, bases, adict)

    def __delattr__( klas, attrname):
        'deleting attributes of the klas comes here - try restore the StaticType'
        try:
            st = klas.StaticType[ attrname]
        except KeyError:
            _Base.__metaclass__.__delattr__( klas, attrname)
        else:
            setattr( klas, attrname, st)

import sqlalchemy.orm.attributes
_noInstanceState = not hasattr( sqlalchemy.orm.attributes, 'InstanceState')    #>v3463

class Base( _Base):
    __metaclass__ = _Meta2check_dict
    __slots__ = [ '__weakref__',
            '_sa_session_id',
            '_sa_insert_order',
            '_instance_key',
            '_entity_name',

            _noInstanceState and '_my_state' or '_state',
            '_my_sa_stuff',
    ]
    if _noInstanceState:
        def _lazy_mystate( me):
            try: return me._my_state
            except AttributeError:
                m = me._my_state = {}
                return m
        _state = property( _lazy_mystate)
    __dict__ = property( dict_via_attr )

    __doc__ = '''
SA uses obj.__dict__ directly  - expects to be able to add any stuff to it!
NO __dict__ here - all is done to avoid it, as it shades the object
        and makes all the StaticTypeing meaningless.
SA-mapper-related attributes are hence split into these categories:
    system:     __sa_attr_state and others in the __slots__ above
    extra columns (foreign keys etc):      go in _my_sa_stuff
    plain attributes:   go where they should, in the object via get/set attr

this exercise would be a lot easier if:
    - _state didn't use another privately-named __sa_attr_state
    - plain attributes didn't access directly obj.__dict__, but have proper getattr/setattr
    - extra columns and extra system attributes went all into the above _state,
        or anywhere but in ONE place.
'''

def Type4Reference( klas, lazy =False, **kargs):
    if isinstance( klas, str):
        r = _static_type.ForwardSubStruct( klas, **kargs)
    else:
        r = klas.Instance( **kargs)
    r.lazy = lazy
    return r

class Association( builder.relation.Association):
    __slots__ = ()
    Type4Reference = staticmethod( Type4Reference)

Type = _static_type.StaticType
reflector = Reflector4StaticType()

def setup( s):
    s.reflector = reflector
    s.Type4Reference = staticmethod( Type4Reference)
    s.Base = Base
    s.Association = Association

class Builder( builder.Builder): pass
setup( Builder)

#######

def value_of_AKeyFromDict( obj, attrname):
    key = getattr( obj, attrname)
    value = obj.StaticType[ attrname ].dict[ key ]   #XXX ауу каква боза се получава...
    return value

#############################################

if __name__ == '__main__':

    from static_type.types.atomary import Text
    inh = 'joined_table'     #or 'concrete_table'

    class Employee( Base):
        auto_set = False    #StaticTypeing; else: maximum recursion depth at cascade_*
        DBCOOK_inheritance = inh
        DBCOOK_has_instances = True

        name = Text()
        dept = Type4Reference( 'Dept')

    class Engineer( Employee):
        helper = Type4Reference( 'Engineer')
        DBCOOK_has_instances = True

    class Manager( Employee):
        secretary = Type4Reference( Employee)

    class Hacker( Engineer):
        tools = Text()

    class Dept( Base):
        boss = Type4Reference( Manager)
        name = Text()

    def populate():
        anna = Employee( name='anna')
        dept = Dept( name='jollye' )
        boss = Manager(  name='boso')
        anna.dept = dept
        boss.dept = dept
        dept.boss = boss

        engo = Engineer( name='engo')
        engo.dept = dept
        haho = Hacker( name='haho', tools='fine' )
        engo.helper = haho

        return locals()


    fieldtypemap = {
        Text: dict( type= sqlalchemy.String, ),
    }

    def str1( me): return reflector.obj2str( me, Base, builder.column4ID.name)
    Base.__repr__ = Base.__str__ = str1
    from dbcook.util.attr import setattr_kargs
    Base.__init__ = setattr_kargs

    from dbcook.usage.samanager import SAdb
    SAdb.Builder = Builder
    SAdb.config.getopt()

    sa = SAdb()
    sa.open()
    sa.bind( locals(), fieldtypemap )

    population = populate()
    session = sa.session()
    sa.saveall( session, population)
    session.flush()
    session.close()

    for klas in [Employee, Engineer, Manager, Hacker, Dept]:
        for q in [ sa.query_ALL_instances, sa.query_BASE_instances, sa.query_SUB_instances]:
            print '====', klas, q.__name__
            r = list( q( session, klas ) )
            if not r: print r
            else:
                for a in r: print a

# vim:ts=4:sw=4:expandtab
