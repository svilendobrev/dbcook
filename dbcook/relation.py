#$Id$
# -*- coding: cp1251 -*-

'''
TODO:

връзки:
      * към 1:
        x = Reference( struct) = has_one(struct) = SubStruct(struct) = struct.Instance()
+       * самостоятелна
-       * или с backref: Reference( struct, backrefCollection =име_отсреща)
            име_отсреща e колекция

-     1 към много:
        x = Collection( struct, име_отсреща ='') = has_many( struct, име_отсреща ='')
            име_отсреща e указател( Reference)
        * име_отсреща миже да липсва, т.е. неявно/служебно
        * Collection в Entity трябва да става автоматично Association

      много към много:
-       = неявна
+           сега се обявява съвсем явно, но като неявна (без междинен обект) (DB_HIDDEN=True)
                class myAssocAB( Association):
                    DB_HIDDEN=True
                    ... .Links
                x = Association.Relation( myAssocAB, име_в_асоциацията='')
-           трябва да може да се обявява съвсем служебно:
                x = Association.Hidden( otherstruct, име_отсреща ='')
                    име_отсреща е на асоциацията от другата страна
                с възможно служебно име_отсреща

    = явна
+       class myAssocAB( Association):
            DB_HIDDEN=False
            ... .Links
        x = Association.Relation( myAssocAB, име_в_асоциацията='')
            име_в_асоциацията е на Reference/Association.Link
-       * възможно служебно име_в_асоциацията

'''

import sqlalchemy
import warnings

class _Relation: pass

def setkargs( me, **kargs):
    for k,v in kargs.iteritems():
        setattr( me, k,v)

class Association:
    ''' serve as description of the assoc.table and
    storage of association arguments - names/klases,
    which are to be processed/interpreted later.
    It is a mix-in only to allow attaching to different bases -
    the resulting subclasses may or may not be mixable.
    '''
    DB_NO_MAPPING = True
    #DB_NO_ID = True    #XXX db_id is a must only if table is referred
    #DB_UNIQ_KEYS= ...  #primary key consist of which fields; all by default
    DB_HIDDEN = False

    class _AssocDetails:
        __init__ = setkargs

    Type4Reference = None
    @classmethod
    def Link( klas, target_klas, attr =None, primary_key =True, nullable =False):
        '''declaration of link to target_klas, aware of being part of association'''
        typ = klas.Type4Reference( target_klas)
        typ.assoc = Association._AssocDetails( primary_key= primary_key, nullable= nullable, relation_attr= attr )
        #the klas is typ.typ (or will be after forward-decl-resolving)
        print 'Link', klas, target_klas, attr, primary_key
        return typ

    @classmethod
    def Relation( klas, intermediate_klas= None):
        '''storage (declaration) of association arguments for
        intermediate_klas for the end-obj-klas where this is declared'''
#        print klas, Association
        if intermediate_klas: klas = intermediate_klas
        assert klas
        if not isinstance( klas, str):
            assert issubclass( klas, Association)
            for k in dir( klas):
                if not k.startswith( '__') and hasattr( getattr( klas, k), 'assoc'):
                    break
            else:
                assert 0, 'empty Association %(klas)r - either specify proper .Relation argument, or add .Links of this' % locals()

        r = _Relation()
        r.assoc_klas = klas
        return r

    class MyCollection( list):
        factory = None
        def append( me, obj =_Relation, **kargs):
            if obj is _Relation:    #marker for notset
                obj = me.factory( **kargs)
            list.append( me, obj)
            return obj

    @classmethod
    def myCollectionFactory( klas):
        m = Association.MyCollection()
        m.factory = klas
#        print 'made', m, m.factory
        return m

#########

_empty_dict = {}
class Associator:       #used in mapper-builder
    def associate( me, klas, attrklas, assoc, column):
        if not assoc.primary_key: return

        try: foreign_keys = klas.foreign_keys
        except AttributeError: foreign_keys = klas.foreign_keys = {}

        kk = foreign_keys.setdefault( attrklas, {} )
        key = assoc.relation_attr
##        print 'pas 1:', klas, attrklas, key, ' >>', column

        if key is not None:
            assert key not in kk, 'duplicate/ambigious association to %(attrklas)s in %(klas)s; specify attr=assoc_relation_attr explicitly' % locals()
        else:
            if key in kk:
                warnings.warn( 'duplicate/ambigious/empty association to %(attrklas)s in %(klas)s; specify attr=assoc_relation_attr explicitly' % locals() )
        kk[ key ] = column
#        me.primary_key.add( column)

#        try: links_klasi = klas.links_klasi
#        except AttributeError: links_klasi = klas.links_klasi = []
#        links_klasi.append( attrklas)


    def is_assoc_attr( me, klas, attrtyp, attrklas):
        column_kargs = _empty_dict
        column_func = None
        assoc = issubclass( klas, Association) and getattr( attrtyp, 'assoc', None)
#        print 'isassoc', assoc, attrtyp, klas
        if assoc and assoc.primary_key:
            column_kargs = dict( primary_key= True, nullable= assoc.nullable )
            column_func = lambda c: me.associate( klas, attrklas, assoc, c)
        return column_kargs, column_func


def make_relations( builder):
    ##XXX in builder._make_mapper_polymorphic() ???

    if 'needed for assoc-object case':
        def append( self, *args, **kwargs):
            item = self._data_appender( *args,**kwargs)
            self._InstrumentedList__setrecord( item)    #private __setrecord; was _before_ _data_appender
        sqlalchemy.orm.attributes.InstrumentedList.append = append

##    print '\n pas 2'
    for m in builder.itermapi( primary_only =True):
##        print m
        klas = m.class_
        if issubclass( klas, Association):
            primary_key = m.local_table.primary_key.columns
            m.allow_null_pks = bool( primary_key and [c for c in primary_key if c.nullable] )
            print ' allow_null_pks:', m.allow_null_pks
            continue

        relations = {}
        for name in dir( klas):
            typ = getattr( klas, name)
            if not isinstance( typ, _Relation): continue

            assoc_klas = typ.assoc_klas
            print '?', name, assoc_klas
            if isinstance( assoc_klas, str):
                try:
                    assoc_klas = builder.klasi[ assoc_klas]
                except KeyError:
                    raise KeyError, 'undefined association class %(assoc_klas)r in %(klas)s.%(name)s' % locals()

            try:
                fks = assoc_klas.foreign_keys[ klas ]
            except KeyError:
                raise KeyError, 'missing declaration of link in association %(klas)s.%(name)s <- %(assoc_klas)s' % locals()

            for key in [name, None]:
                try:
                    fk = fks[ key]
                    break
                except KeyError: pass
            else:
                print assoc_klas, name, assoc_klas.foreign_keys
                raise KeyError, 'missing/wrong relation for association %(klas)s.%(name)s <- %(assoc_klas)s, available: %(fks)s. Check for double-declaration with different names' % locals()


            rel_kargs = dict(
                    lazy    =   True, #False,
#                    cascade = 'all, delete-orphan',    #DB_hidden-relation does FlushError with this
                    uselist = True,
                    collection_class = assoc_klas.myCollectionFactory,      #needed if InstrumentedList.append is replaced
                )

            colid = builder.column4ID( klas )

            if assoc_klas.DB_HIDDEN:
                if len(fks)==2:     #2 diff links to same klas
                    print 'same klas x2'
                    assert len(assoc_klas.foreign_keys) == 1
                    for k in fks:
                        if k != key: break
                    othername = k
                    otherfk = fks[k]
                    otherklas = klas
                else:   #2 diff klasi
                    print '2diff', assoc_klas.foreign_keys
                    assert len(assoc_klas.foreign_keys) == 2
                    for otherklas in assoc_klas.foreign_keys:
                        if otherklas is not klas: break
                    otherfks = assoc_klas.foreign_keys[ otherklas]
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
            print ' property', name, 'on', klas, 'via', assoc_klas, ':', assoc_klas_actual, ', '.join( '%s=%s' % kv for kv in rel_kargs.iteritems() )
            m.add_property( name, sqlalchemy.relation( assoc_klas_actual, **rel_kargs) )
            relations[ name ] = assoc_klas

        if relations:       #винаги ли е нужно? май трябва само при изрично поискване
            klas.DB_relations = relations



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
