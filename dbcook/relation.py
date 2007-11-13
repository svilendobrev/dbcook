#$Id$
# -*- coding: cp1251 -*-

'''
TODO:

връзки:
      * към 1:
        x = Reference( struct) = has_one(struct) = SubStruct(struct) = struct.Instance()
+       * самостоятелна (1-посочна)
-?      * 2-посочна 1към1: Reference( struct, backref =име_отсреща, singular=True)
-       * 2-посочна с 1-към-много: Reference( struct, backref =име_отсреща, singular=False)
            име_отсреща става колекция ??

+     1 към много:
        x = Collection( struct, backref =име_отсреща) = has_many
        * име_отсреща може да липсва, т.е. неявно/служебно; става указател( Reference)
        * Collection в 2временно Entity трябва да става автоматично Association
+       * 2-посочна с много-към-1: backref е указано

      много към много:
-       = неявна
+           обявява се съвсем явно, но като скрита (без междинен обект) (DBCOOK_hidden=True)
                class myAssocAB( Association):
                    DBCOOK_hidden=True
                    ... .Links
                x = Association.Relation( myAssocAB, име_в_асоциацията='')
-           трябва да може да се обявява съвсем служебно:
                x = Association.Hidden( otherstruct, име_отсреща ='')
                    име_отсреща е на асоциацията от другата страна
                    с възможно служебно име_отсреща

        = явна
+           class myAssocAB( Association):
                DBCOOK_hidden=False
                ... .Links
            x = Association.Relation( myAssocAB, име_в_асоциацията='')
                име_в_асоциацията е на Reference/Association.Link
-           * възможно служебно име_в_асоциацията
+       * 2-посочна
-       * еднопосочна

'''

import sqlalchemy
import sqlalchemy.orm
import warnings
from config import config, _v03

def _associate( klas, attrklas, assoc_details, column):
    dbg = 'relation' in config.debug
    if not assoc_details.primary_key: return
    if dbg:
        print 'relate parent:', attrklas, 'to child:', klas
        print '  attrname:', assoc_details.relation_attr, 'column:', column

    try: foreign_keys = klas.foreign_keys
    except AttributeError: foreign_keys = klas.foreign_keys = {}

    kk = foreign_keys.setdefault( attrklas, {} )
    key = assoc_details.relation_attr

    if key is not None:
        assert key not in kk, '''duplicate/ambigious association to %(attrklas)s in %(klas)s; specify attr=<assoc_relation_attr> explicitly''' % locals()
    else:
        if key in kk:
            warnings.warn( '''duplicate/ambigious/empty association to %(attrklas)s in %(klas)s; specify attr=>assoc_relation_attr> explicitly''' % locals() )
    kk[ key ] = column

class Association( object):
    ''' serve as description of the association table and
    storage of association arguments - names and klases -
    which are to be processed/interpreted later.
    It is a mix-in only, to allow attaching to different bases -
    the resulting subclasses may or may not be mixable.
    Keep namespace clean - do not pollute with non-dependent stuff
    '''
    __slots__ = ()
    DBCOOK_no_mapping = True
    #DB_NO_ID = True    #XXX db_id is a must only if table is referred
    #DBCOOK_unique_keys= ...  #primary key consist of which fields; all by default
    DBCOOK_hidden = False

    Type4Reference = None
    @classmethod
    def Link( klas, target_klas, attr =None, primary_key =True, nullable =False):
        '''declaration of link to target_klas, aware of being part of association'''
        typ = klas.Type4Reference( target_klas)
        typ.assoc = _AssocDetails( primary_key= primary_key, nullable= nullable, relation_attr= attr )
        #the klas is typ.typ (or will be after forward-decl-resolving)
        print 'Link', klas, target_klas, attr, primary_key
        return typ

    @classmethod
    def _is_valid( klas):
        for k in dir( klas):
            if not k.startswith( '__') and hasattr( getattr( klas, k), 'assoc'):
                return True     #has at least 1 Link
        return False

    @classmethod
    def Relation( klas, intermediate_klas= None):       #XXX kargs?
        '''storage (declaration) of association arguments for
        intermediate_klas for the end-obj-klas where this is declared'''

        if intermediate_klas: klas = intermediate_klas
        assert klas
        if not isinstance( klas, str):
            assert issubclass( klas, Association)
            assert klas._is_valid(), '''empty Association %(klas)r - specify .Relation argument, or add .Links of this''' % locals()
        return _Relation( klas)

    @classmethod
    def _CollectionFactory( klas):
        m = _AssocDetails.MyCollection()
        m.factory = klas
        return m


def is_association_reference( klas, attrtyp, attrklas):
    'used in table-maker'
    column_kargs = {}
    column_func = None
    if issubclass( klas, Association):
        assoc_details = getattr( attrtyp, 'assoc', None)
        if assoc_details and assoc_details.primary_key:
            column_kargs = dict( primary_key= True, nullable= assoc_details.nullable )
            column_func = lambda column: _associate( klas, attrklas, assoc_details, column)
    return column_kargs, column_func


class _Unspecified: pass

def setkargs( me, **kargs):
    for k,v in kargs.iteritems():
        setattr( me, k,v)

class _Relation( object):
    __slots__ = [ 'rel_kargs', 'assoc_klas', 'backref' ]
    def __init__( me, assoc_klas, backref =None, rel_kargs ={}):
        me.assoc_klas = assoc_klas
        me.rel_kargs = rel_kargs
        me.backref = backref
    def __str__( me):
        return me.__class__.__name__+'/'+str(me.assoc_klas)
    def make( me, builder, klas, name ):
        'return relation_klas, actual_relation_klas, relation_kargs'
        dbg = 'relation' in config.debug
        assoc_klas = me.assoc_klas
        #print '?', name, assoc_klas
        if isinstance( assoc_klas, str):
            try: assoc_klas = builder.klasi[ assoc_klas]
            except KeyError: assert 0, '''undefined relation/association class %(assoc_klas)r in %(klas)s.%(name)s''' % locals()

        foreign_keys = assoc_klas.foreign_keys

        try: fks = foreign_keys[ klas ]
        except KeyError: assert 0, '''missing declaration of link in association %(klas)s.%(name)s <- %(assoc_klas)s''' % locals()

        for key in (name, None):
            try:
                fk = fks[ key]
                break
            except KeyError: pass
        else:
            assert 0, '''missing/wrong relation for association %(klas)s.%(name)s <- %(assoc_klas)s
attrname: %(name)s;
available: %(fks)s;
all foreign_keys: %(foreign_keys)s.
Check for double-declaration with different names''' % locals()


        rel_kargs = dict(
                lazy    = True,
    #           cascade = 'all, delete-orphan',    #DB_hidden-relation does FlushError with this
                uselist = True,
                collection_class = getattr( assoc_klas, '_CollectionFactory', None),      #needed if InstrumentedList.append is replaced
            )
        rel_kargs.update( me.rel_kargs)

        colid = builder.column4ID( klas )

        if getattr( assoc_klas, 'DBCOOK_hidden', None):
            if len(fks)==2:     #2 diff links to same klas
                #print 'same klas x2'
                assert len(foreign_keys) == 1
                for k in fks:
                    if k != key: break
                else:
                    assert 0, 'internal error, wrong .foreign_keys[%(klas)s] on %(assoc_klas)s' % locals()
                othername = k
                otherfk = fks[k]
                otherklas = klas
            else:   #2 diff klasi
                #print '2diff', foreign_keys
                assert len(foreign_keys) == 2, 'internal error, wrong .foreign_keys on %(assoc_klas)s' % locals()
                for otherklas in foreign_keys:
                    if otherklas is not klas: break
                #else:  cannot happen because of above assert
                otherfks = foreign_keys[ otherklas]
                assert len(otherfks) == 1
                othername, otherfk = otherfks.items()[0]
                #assert othername

            assoc_klas_actual = otherklas
            rel_kargs.update(
                    secondary   = builder.tables[ assoc_klas],
                    primaryjoin = (fk == colid),
                    secondaryjoin = (otherfk == builder.column4ID( otherklas)),
                )
        else:
            assoc_klas_actual = assoc_klas
            rel_kargs.update(
                    primaryjoin = (fk == colid),
                    remote_side = fk,
                )
        if dbg: print me, 'make:', assoc_klas, assoc_klas_actual, rel_kargs
        return assoc_klas, assoc_klas_actual, rel_kargs


class _AssocDetails:
    __init__ = setkargs

    #do not pollute Association' namespace
    class MyCollection( list):
        factory = None
        if _v03:
            def append( me, obj =_Unspecified, **kargs):
                if obj is _Unspecified: obj = me.factory( **kargs)
                list.append( me, obj)
                return obj
        else:
            @sqlalchemy.orm.collections.collection.internally_instrumented
            def append( me, obj =_Unspecified, **kargs):
                if obj is _Unspecified: obj = me.factory( **kargs)
                me._append( obj)
                return obj
            @sqlalchemy.orm.collections.collection.appender
            def _append( me, *a,**k): return list.append( me, *a, **k)


##############################

class Collection( _Relation):
    '''define one2many relations - in the 'one' side of the relation
    (parent-to-child/ren relations in terms of R-DBMS).
    '''
    __slots__ = [ 'backref', 'backrefname' ]

    def __init__( me, child_klas,
                    backref =None,   #backref name or dict( name, **rel_kargs)
                    #unique =False,  #   ??
                    **rel_kargs ):   #order_by =None, etc
        if backref and not isinstance( backref, dict):
            backref = dict( name= backref)
        _Relation.__init__( me, child_klas, backref, rel_kargs)
        me.backrefname = None   #decided later

def make_relations( builder, sa_relation_factory, sa_backref_factory, FKeyExtractor ):
    dbg = 'relation' in config.debug
    if dbg: print 'make_relations'

    if _v03:
        def append( self, *args, **kwargs):
            item = self._data_appender( *args,**kwargs)
            self._InstrumentedList__setrecord( item)    #private __setrecord; was _before_ _data_appender
        sqlalchemy.orm.attributes.InstrumentedList.append = append

    #XXX TODO move all this into make_mapper_props ??

    for m in builder.itermapi( primary_only =True):
        klas = m.class_
        if issubclass( klas, Association):
            primary_key = m.local_table.primary_key.columns
            m.allow_null_pks = bool( primary_key and [c for c in primary_key if c.nullable] )
            if dbg: print ' allow_null_pks:', m, m.allow_null_pks   #XXX add to m.tstr???
            continue

        fkeys = FKeyExtractor( klas, m.local_table, builder.mapcontext, builder.tables)

        relations = {}
        for name,typ in builder.mapcontext.iter_attr_local( klas, attr_base_klas= _Relation, dbg=dbg ):
            rel_klas, rel_klas_actual, rel_kargs = typ.make( builder, klas, name)    #any2many
            if not rel_klas_actual: rel_klas_actual = rel_klas

            #forward link
            r = fkeys.get_relation_kargs( name)
            if dbg: print ' ', m, name, r, fkeys
            rel_kargs.update( r)

            #backward link
            backref = typ.backref
            if backref:
                r = fkeys.get_relation_kargs( typ.backrefname)
                if dbg: print ' BACKREF ', m, typ.backrefname, r
                if 0:
                    backref.update( r)
                else:
                    for p in 'post_update remote_side'.split():
                        try: backref[ p] = r[p]
                        except KeyError: pass
                backref = sa_backref_factory(
                            #explicit - as SA does if backref is str
                            primaryjoin= rel_kargs[ 'primaryjoin'],
                            uselist= False, #??? goes wrong if selfref - both sides become lists
                            **backref)
                rel_kargs[ 'backref'] = backref

            #print ' property', name, 'on', klas, 'via', rel_klas, rel_klas is not rel_klas_actual and '/'+str(rel_klas_actual) or '',
            #print ', '.join( '%s=%s' % kv for kv in rel_kargs.iteritems() )
            m.add_property( name, sa_relation_factory( rel_klas_actual, **rel_kargs) )
            relations[ name ] = rel_klas

        if relations:       #винаги ли е нужно? май трябва само при изрично поискване
            klas._DBCOOK_relations = relations



'''
1. declare intermediate association class as subclass of Association, and
    using attrname = Association.Link( klasname), any number of these.
    other attributes as required
2. End-object attr for relation is specified either in above Base4Association.Link( attr=relname),
    or explicit in the End-object:
        relname = IntermediateKlas.Relation()
     or relname = Base4Association.Relation( IntermediateKlas)
    if both specified, the last declared is taken (overrides).
    Having such relation-attr is not mandatory, some End-object may not need it.
'''

# vim:ts=4:sw=4:expandtab
