#$Id$
# -*- coding: cp1251 -*-

class table_inheritance_types:      #db-layout
    JOINED    = 'joined_table'      #it's own (extra-base) fields only + join(base)
    CONCRETE  = 'concrete_table'    #each is complete and separate, stand-alone
    SINGLE    = 'single_table'      #all-in-one: all fields go in base's table - no own representation
    DEFAULT = CONCRETE
    #TODO:  особен случай за оптимизация: при JOINED наследяване без нови полета (=смяна на типа)
    #       може да мине без собствена (празна) таблица - като single_table
    #       special case for optimisation: JOINED inheritance without new fields (=change of type)
    #       can do without own (empty)             table - like single_table
    _all = dict( (v,v) for k,v in locals().iteritems() if not k.startswith('__') )
    _all.update( (v.split('_table',1)[0],v) for v in _all.keys() )

class _Base( object):   #use as example/template
    '''постоянстващ обект, т.е. persistent;
    има си (собствена или споделена/сглобена) колекция/таблица;
    атрибут (на някого) от такъв тип винаги става връзка към тази "таблица".
    Йерархията (дървото) от постоянстващите обекти/класове е подмножество
    на пълната йерархия от класове, т.е. има възли които не са постоянстващи.
  $ persistent object;
    it has (own or shared/assembled) collection/table;
    an attribute (of someone) of this type always becomes a link to this "table".
    Hierarchy (tree) of persistent objects/classes is a subset of the full hierarchy of classes,
    i.e. there can be nodes which are not persisting.

  настройки:
$ settings:
    DBCOOK_inheritance = <table_inheritance_type> (default =table_inheritance_types.DEFAULT)
        table_inheritance_type: едно от 'joined_table' , 'concrete_table' , 'single_table';
        тази настройка се наследява / разпространява / вижда от подкласовете.
      $ this setting is inherited / distributed / seen in the subclasses.

    DBCOOK_inheritance_local = <table_inheritance_type>
        за улесняване на специфични случаи.
        важи само локално за класа (не се разпространява в подкласовете),
        И има приоритет над горната обща DBCOOK_inheritance:
            пример: А: inh=1
                    B(A): inh_local=2
                    C(B): pass
                -> inhtype(A) == 1; inhtype(B) == 2; inhtype(C) == 1 (остава от А)
      $ to ease some special cases.
        Applies only locally for the class (is not inherited / seen in sublasses),
        AND has priority over the above general DBCOOK_inheritance.

    DBCOOK_no_mapping = boolean (default =False)
        този клас няма БД-съответствие (междинен, "пълнител", невалиден).
        Всичкото му съдържание се "изсипва" / разпространява във всичките му (реални) наследници.
        Важи само локално за класа в който е обявено.
        Използвай внимателно - атрибутите на такъв клас се "появяват" във всички наследници (!)
      $ this class has no DB-mapping (intermediate, "filling").
        All of its contents goes into all of its (real) subclasses.
        Applies only locally for the class.
        Use carefully - attributes of such class appear in all of its heirs/subclasses (!)

    DBCOOK_has_instances = boolean  (default =is_leaf)
        този клас има екземпляри, т.е. не е само междинно ниво,
        и всички полиморфни заявки през него трябва да го включват.
        Листата в йерархията винаги имат екземпляри.
        Важи само локално за класа.
      $ this class has instances, i.e. is not just an intermediate level,
        and all polymorphic requests through it must include it.
        Leafs in a hierarchy always have instances.
        Applies only locally.

    DBCOOK_needs_id = boolean   (default =False, i.e. has_no_primary_key or is_joined_table-inheritance)
        този клас трябва да има db_id независимо от наличието на друг уникален ключ
        (виж DBCOOK_unique_keys), например защото други класове го сочат направо.
        се добавя db_id, не да се премхва.
        Важи само локално за класа.
      $ this class must have db_id regardless of availability of other unique keys
        (see DBCOOK_unique_keys), for example because other classes are pointing it directly.
        Applies only locally.

    DBCOOK_dbname = име-на-БД-таблицата или classmethod който го прави
        Важи само локално за класа
      $ name-of-DB-table or classmethod to make it
        Applies only locally

    DBCOOK_unique_keys = списък от списъци от (имена на полета или полета (търси се .name) )
                          или classmethod който връща такъв
                          default = ()
        Важи само локално за класа, или в наследените ако класът няма БД-съответствие
      $ list of lists of (field-names or fields (.name wanted) )
                          or classmethod which returns such
        Applies only locally, or in subclases if class is non-mappable (a-la mixin).

    DBCOOK_indexes = списък от имена на полета, или classmethod който връща такъв
                        $ list of field-names, or classmethod returning such
                          default = () #nothing
        Важи само локално за класа, или в наследените ако класът няма БД-съответствие
      $ Applies only locally, or in subclases if class is non-mappable (a-la mixin).

    DBCOOK_defaults = речник от (име на поле: стойност-или-функция ), или classmethod който връща такъв
                        $ dict of (field-names: value-or-func), or classmethod returning such
                          default = {} #nothing
        стойности / функции даващи стойност по подразбиране за сътветното поле при запис на нов обект
        Важи само локално за класа, или в наследените ако класът няма БД-съответствие
      $ values / functions returning values to use as default of the field on insert
        Applies only locally, or in subclases if class is non-mappable (a-la mixin).

    DBCOOK_defaults_on_update =
        същото като DBCOOK_defaults но за on_update - при запис на промяна на обекта
      $ same as DBCOOK_defaults but for on_update

    '''
    #__slots__ = [ column4ID.name ]     #db_id is automatic
    #DBCOOK_inheritance = 'concrete_table'  #default
    #DBCOOK_no_mapping = True    #default; klas-local only
    #DBCOOK_has_instances = False   #default; klas-local only

# XXX assert not( DBCOOK_no_mapping and DBCOOK_has_instances) ???

from dbcook.util.attr import getattr_local_instance_only, issubclass
class _NOTFOUND: pass

class MappingContext:
    def __init__( me,
        base_klas = None,  #_Base or something else
        reflector = None,  #some Reflector()
    ):
        me.base_klas = base_klas
        me.reflector = reflector

    def mappable( me, klas):
        if klas and issubclass( klas, me.base_klas) and klas is not me.base_klas:
            DBCOOK_no_mapping = getattr_local_instance_only( klas, 'DBCOOK_no_mapping', None)
            if not DBCOOK_no_mapping: return True
        return False

    def has_instances( me, klas):
        #if not me.mappable( klas): return False
        if len( me.subklasi[ klas]) == 1: return True      #leaf
        DBCOOK_has_instances = getattr_local_instance_only( klas, 'DBCOOK_has_instances', None)
        return bool( DBCOOK_has_instances)

    def __getattr_local_or_nonmappable_base( me, klas, attr, *default):
            # allow non-mapped classes to declare certain DBCOOK_xxxxxxx for their children
            # TODO see below iter_attr_local
        klas0 = klas
        for klas in klas.__mro__:
            r = getattr_local_instance_only( klas, attr, _NOTFOUND)
            if r is not _NOTFOUND:
                if klas is not klas0 and me.mappable( klas):
                    break   #not found
                #XXX tricky: klas.__dict__['xyz'] is not klas.xyz, esp. classmethods/descriptors
                #this is the only place so far, it is safe to getattr
                return getattr( klas0, attr)
        if default: return default[0]
        raise AttributeError, 'no attr %(attr)s in %(klas)s' % locals()

    @staticmethod
    def needs_id( klas):
        return getattr_local_instance_only( klas, 'DBCOOK_needs_id', None)

    @staticmethod
    def dbname( klas):
        import config   #XXX ~hack
        return config.table_namer( klas)

    def _getattr_local_or_nonmappable_base_list( me, klas, name, default =()):
        #association must see attrs belonging to base non-mappable classes
        r = me.__getattr_local_or_nonmappable_base( klas, name, default)
        if callable( r): r = r()
        return r

    def uniques( me, klas):
        'list of lists of (column-names or columns  (having .name) )'
        return me._getattr_local_or_nonmappable_base_list( klas, 'DBCOOK_unique_keys' )

    def indexes( me, klas):
        'list of column-names'
        r = me._getattr_local_or_nonmappable_base_list( klas, 'DBCOOK_indexes' )
        for a in r: assert isinstance( a, str)  #composites not implemented
        return r

    def defaults( me, klas):
        'dict of column-name:func'
        return me._getattr_local_or_nonmappable_base_list( klas, 'DBCOOK_defaults', default= {} )

    def defaults_on_update( me, klas):
        'dict of column-name:func'
        return me._getattr_local_or_nonmappable_base_list( klas, 'DBCOOK_defaults_on_update', default= {} )

    def nonnullables( me, klas):
        'list of column-names'
        return me._getattr_local_or_nonmappable_base_list( klas, 'DBCOOK_nonnullables' )

    def base( me, klas):
        '''дава (първия) базов валиден клас, None ако няма такъв. т.е. на или отвъд валидния корен
         $ get (first) base that is mappable, None if no such, i.e. at or under root-mappable'''
        #TODO optimize via __mro__
        assert klas
        base_klas = me.base_klas
        while klas is not base_klas:
            for base in klas.__bases__:
                if issubclass( base, base_klas): break
            else:
                assert 0, '%(klas)s does not inherit baseklas %(base_klas)s' % locals()
            if me.mappable( base): return base
            # allow non-mapped classes to declare props -> added to _all_ their children
            klas = base
        return None

    def base4table_inheritance( me, klas):
        base = me.base( klas)
        inheritype = table_inheritance_types.DEFAULT
        if base:
            inheritype = getattr( klas, 'DBCOOK_inheritance', None)
            #local:
            inheritype = getattr_local_instance_only( klas, 'DBCOOK_inheritance_local', inheritype) or table_inheritance_types.DEFAULT
            try: inheritype = table_inheritance_types._all[ inheritype]
            except KeyError, e:
                assert 0, '%(klas)s: unknown DBCOOK_inheritance=%(inheritype)r' % locals()
        return base, inheritype

    def iter_attr( me, klas, attr_base_klas =None,
                local =False, denote_nonmappable_origin =False, dbg =False,
                **kargs4attrtypes ):
        'sorted'
        base_klas, inheritype = me.base4table_inheritance( klas)
        is_joined_table = (inheritype == table_inheritance_types.JOINED)
        dir_base_klas = is_joined_table and dir( base_klas) or ()
            #joined_table: subclass' tables consist of extra attributes -> joins
        for k,typ in sorted( me.reflector.attrtypes( klas, **kargs4attrtypes ).iteritems()):
            if attr_base_klas and not isinstance( typ, attr_base_klas): continue
            if local and k in dir_base_klas:
                if dbg: print '  inherited:', k
                continue
            if denote_nonmappable_origin:
                nonmappable_origin = getattr_local_instance_only( klas, k, _NOTFOUND) is _NOTFOUND
                yield k,typ, nonmappable_origin
            else:
                yield k,typ

    def is_direct_inherited_non_concrete( me, klas):
        for sk in me.subklasi[ klas].direct:
            _base_klas, sk_inheritype = me.base4table_inheritance( sk)
            if sk_inheritype != table_inheritance_types.CONCRETE:
                return True
        return False

    def root( me, klas):
        '''намира базовия валиден клас най-близко до корена на йерархията; връща входа ако е корен
         $ get the mappable base class nearest to real root; input klas if at root'''
        assert klas
        while klas:
            root = klas
            klas = me.base( root)
        return root

    def need_typcolumn( me, klas):
        '''ако klas e _пряко_ наследен от някого с не-concrete_table,
            И наследява с (т.е. е) concrete_table
         $ if klas is directly inherited by someone with non-concrete_table,
            AND inherits with (is) concrete_table
        '''
        _base_klas, inheritype = me.base4table_inheritance( klas)
        if inheritype != table_inheritance_types.CONCRETE: return False

        return me.is_direct_inherited_non_concrete( klas)

    SET = set
    DICT = dict

#    def __init__( me): me.subklasi = {}
    def make_subklasi( me, iterklasi ):
        'subklasi = { klas: (subklas1,subklas2) }'
        SET = me.SET
        class Subklasi( SET):
            def __init__( me, klas):
                SET.__init__( me, (klas,) )
                me.direct = SET()
        subklasi = me.DICT()
        for klas in iterklasi:
            #issubclass klas, klas
            subklasi.setdefault( klas, Subklasi( klas) )
            base_klas = klas
            level = 0
            while True:
                base_klas = me.base( base_klas)
                if not base_klas: #me.mappable( base_klas):
                    break
                #issubclass klas, base_klas
                subs = subklasi.setdefault( base_klas, Subklasi( base_klas))
                subs.add( klas)
                if not level:
                    subs.direct.add( klas)
                level += 1
        me.subklasi = subklasi
        return subklasi

    def subklasi4any( me, klas):
        'return all mappable classes that are subclasses of klas, be it mappable or not'
        if me.mappable( klas):
            return klas, me.subklasi[ klas]
        klas_mappable = me.base( klas)
        subklasi_mappable = me.subklasi[ klas_mappable]
        subs = [ k for k in subklasi_mappable if issubclass( k, klas) ]
        return klas_mappable, subs


#not really here but...
from dbcook.util.attr import subclasses_in
def subclasses4db_in( klasi, *args,**kargs):   #klasi= locals() or list
    exclude_ = kargs.pop('exclude_',True)
    return [ c for c in subclasses_in( klasi, *args, **kargs)
             if not getattr_local_instance_only( c, 'DBCOOK_no_mapping', False)
             and not (exclude_ and c.__name__.startswith( '_'))
            ]

# vim:ts=4:sw=4:expandtab
