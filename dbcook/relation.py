#$Id$
# -*- coding: cp1251 -*-

'''
TODO:

������:
      * ��� 1:
        x = Reference( struct) = has_one(struct) = SubStruct(struct) = struct.Instance()
+       * ������������� (1-�������)
-       * 2-������� 1���1: Reference( struct, other_side =���_�������, singular=True)
-       * 2-������� � 1-���-�����: Reference( struct, other_side =���_�������, singular=False)
            ���_������� ����� �������� ??

-     1 ��� �����:
        x = Collection( struct, other_side =���_�������) = has_many
            ���_������� e ��������( Reference)
        * ���_������� ���� �� ������, �.�. ������/��������
        * Collection � 2�������� Entity ������ �� ����� ����������� Association
-       * 2-������� � �����-���-1:

      ����� ��� �����:
-       = ������
+           ������� �� ������ ����, �� ���� ������ (��� �������� �����) (DBCOOK_hidden=True)
                class myAssocAB( Association):
                    DBCOOK_hidden=True
                    ... .Links
                x = Association.Relation( myAssocAB, ���_�_�����������='')
-           ������ �� ���� �� �� ������� ������ ��������:
                x = Association.Hidden( otherstruct, ���_������� ='')
                    ���_������� � �� ����������� �� ������� ������
                    � �������� �������� ���_�������

        = ����
+           class myAssocAB( Association):
                DBCOOK_hidden=False
                ... .Links
            x = Association.Relation( myAssocAB, ���_�_�����������='')
                ���_�_����������� � �� Reference/Association.Link
-           * �������� �������� ���_�_�����������
+       * 2-�������
-       * �����������

'''

import sqlalchemy
import sqlalchemy.orm
import warnings

_v03 = hasattr( sqlalchemy, 'mapper')

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
        return _AssocDetails._Relation( klas)

    @classmethod
    def _CollectionFactory( klas):
        m = _AssocDetails.MyCollection()
        m.factory = klas
        return m

    @classmethod
    def _associate( klas, attrklas, assoc_details, column):
        if not assoc_details.primary_key: return

        try: foreign_keys = klas.foreign_keys
        except AttributeError: foreign_keys = klas.foreign_keys = {}

        kk = foreign_keys.setdefault( attrklas, {} )
        key = assoc_details.relation_attr
##        print 'pas 1:', klas, attrklas, key, ' >>', column

        if key is not None:
            assert key not in kk, '''duplicate/ambigious association to %(attrklas)s in %(klas)s; specify attr=<assoc_relation_attr> explicitly''' % locals()
        else:
            if key in kk:
                warnings.warn( '''duplicate/ambigious/empty association to %(attrklas)s in %(klas)s; specify attr=>assoc_relation_attr> explicitly''' % locals() )
        kk[ key ] = column

def is_association_reference( klas, attrtyp, attrklas):
    'used in table-maker'
    column_kargs = {}
    column_func = None
    assoc_details = issubclass( klas, Association) and getattr( attrtyp, 'assoc', None)
    if assoc_details and assoc_details.primary_key:
        column_kargs = dict( primary_key= True, nullable= assoc_details.nullable )
        column_func = lambda column: klas._associate( attrklas, assoc_details, column)
    return column_kargs, column_func


class _Unspecified: pass

def setkargs( me, **kargs):
    for k,v in kargs.iteritems():
        setattr( me, k,v)

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

    class _Relation( object):
        def __init__( me, assoc_klas):
            me.assoc_klas = assoc_klas

        def make( me, builder, klas, name ):
            'return relation_klas, actual_relation_klas, relation_kargs'

            assoc_klas = me.assoc_klas
            #print '?', name, assoc_klas
            if isinstance( assoc_klas, str):
                try: assoc_klas = builder.klasi[ assoc_klas]
                except KeyError: raise KeyError, '''undefined association class %(assoc_klas)r in %(klas)s.%(name)s''' % locals()

            foreign_keys = assoc_klas.foreign_keys

            try: fks = foreign_keys[ klas ]
            except KeyError: raise KeyError, '''missing declaration of link in association %(klas)s.%(name)s <- %(assoc_klas)s''' % locals()

            for key in (name, None):
                try:
                    fk = fks[ key]
                    break
                except KeyError: pass
            else:
                raise KeyError, '''missing/wrong relation for association
%(klas)s.%(name)s <- %(assoc_klas)s, available: %(fks)s;
(all foreign_keys: %(foreign_keys)s).
Check for double-declaration with different names''' % locals()


            rel_kargs = dict(
                    lazy    =   True,
        #           cascade = 'all, delete-orphan',    #DB_hidden-relation does FlushError with this
                    uselist = True,
                    collection_class = assoc_klas._CollectionFactory,      #needed if InstrumentedList.append is replaced
                )

            colid = builder.column4ID( klas )

            if assoc_klas.DBCOOK_hidden:
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
            return assoc_klas, assoc_klas_actual, rel_kargs


##############################

class Collection( object):
    'one2many'

    def __init__( me, klas, other_side =None, unique =False, **rel_kargs):   #order_by =None, etc
        me.rel_klas  = klas
        me.rel_kargs = rel_kargs
        me.other_side = other_side    #backref ? name or dict( **rel_kargs)
        me.unique = unique

    def make( me, builder, klas, name ):
        'return relation_klas, actual_relation_klas, relation_kargs'

        rel_klas = me.rel_klas
        #print '?', name, rel_klas
        if isinstance( rel_klas, str):
            try:
                rel_klas = builder.klasi[ rel_klas]
            except KeyError:
                raise KeyError, 'undefined relating class %(rel_klas)r in %(klas)s.%(name)s' % locals()

        raise NotImplementedError

        #foreign_key guessing?

        #whatever... TODO

        rel_kargs = me.rel_kargs.copy()

        other_side = me.other_side
        if other_side:
            if isinstance( other_side, dict):
                other_side = sqlalchemy.orm.backref( **other_side)
            rel_kargs[ 'backref'] = other_side

        return rel_klas, None, rel_kargs


def make_relations( builder):
    if _v03:
        def append( self, *args, **kwargs):
            item = self._data_appender( *args,**kwargs)
            self._InstrumentedList__setrecord( item)    #private __setrecord; was _before_ _data_appender
        sqlalchemy.orm.attributes.InstrumentedList.append = append

##    print '\n pas 2'
    for m in builder.itermapi( primary_only =True):
        klas = m.class_
        if issubclass( klas, Association):
            primary_key = m.local_table.primary_key.columns
            m.allow_null_pks = bool( primary_key and [c for c in primary_key if c.nullable] )
            #print ' allow_null_pks:', m.allow_null_pks
            continue

        relations = {}
        for name in dir( klas):
            typ = getattr( klas, name)
            if isinstance( typ, _AssocDetails._Relation):
                rel_klas, rel_klas_actual, rel_kargs = typ.make( builder, klas, name)    #many2many
            elif isinstance( typ, Collection):
                rel_klas, rel_klas_actual, rel_kargs = typ.make( builder, klas, name)    #one2many
            else:
                continue

            if not rel_klas_actual: rel_klas_actual = rel_klas
            #print ' property', name, 'on', klas, 'via', rel_klas, rel_klas is not rel_klas_actual and '/'+str(rel_klas_actual) or '',
            #print ', '.join( '%s=%s' % kv for kv in rel_kargs.iteritems() )
            m.add_property( name, sqlalchemy.orm.relation( rel_klas_actual, **rel_kargs) )
            relations[ name ] = rel_klas

        if relations:       #������ �� � �����? ��� ������ ���� ��� ������� ���������
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
