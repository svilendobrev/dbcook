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
        = явна
+           class myAssocAB( Association):
                DBCOOK_hidden=False
+               a = Link( неименован) - трябва да има съотв. Relation в обекта
+               b = Link( именован) - може да нямат съотв. Relation в обекта, ще се създаде
            class A:
+               x = Association.Relation( myAssocAB) - трябва да има съответна Link в асоциацията
-           * възможно служебно име_в_асоциацията
-       = неявна, обявена
+           обявява се както явната, но като скрита (без междинен обект: DBCOOK_hidden=True)
            не може да има повече от 2 връзки
                class myAssocAB( Association):
                    DBCOOK_hidden=True
+       = неявна, необявена
            обявява се само в единия край; останалото става служебно
            става скрита (DBCOOK_hidden) - не може да има повече от 2 връзки
            class A:
                x = Association.Hidden( B, име_отсреща )
                    име_отсреща е на асоциацията от другата страна (B)
-           * възможно служебно име_отсреща


+       * 2-посочна
-       * еднопосочна

'''

import sqlalchemy
import sqlalchemy.orm
import warnings
from config import config

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
    DBCOOK_hidden = False
    #DBCOOK_needs_id= True    #XXX db_id is a must only if table is referred

    #DBCOOK_unique_keys= [lists] or classmethod     #may override - all links by default
    @classmethod
    def DBCOOK_unique_keys( klas):
        return [ klas._DBCOOK_references.keys() ]
        return [ [ k for k,kklas in klas.walk_links() ] ]
        '''
mssql refused to have unique constraints other than the primary key
>Here's the TSQL for a unique index:
> CREATE UNIQUE NONCLUSTERED INDEX IX_UQ_Sample ON Sample (
> first ASC, other ASC, something ASC)
>
>I defined Sample as:
> CREATE TABLE Sample( first int NOT NULL, something int NULL, other bit NULL)
theres a ddl() construct used for this. http://www.sqlalchemy.org/docs/04/sqlalchemy_schema.html#docstrings_sqlalchemy.schema_DDL
        '''

    @classmethod
    def Link( klas, parent_klas, attr =None, **kargs4type):
        '''(in some assoc_klas) declaration of link to parent_klas'''
        typ = klas.Type4Reference( parent_klas, **kargs4type)
        typ.assoc = _AssocDetails( relation_attr= attr, relation_klas=parent_klas )
        #print 'Link', klas, parent_klas, attr
        return typ

    @classmethod
    def Relation( klas, assoc_klas =None, **kargs):
        '''(in some parent_klas) denotes explicit association to klas/assoc_klas'''
        if not assoc_klas: assoc_klas = klas
        if not isinstance( assoc_klas, str):
            assert issubclass( assoc_klas, Association)
            #assert assoc_klas._is_valid(), 'empty explicit association %(assoc_klas)r' % locals()
        return Collection( assoc_klas, **kargs)

    @classmethod
    def Hidden( klas, other_side_klas, other_side_attr ='', backref ='', **kargs):
        #print 'Hidden Assoc', other_side_klas, '.'+ other_side_attr
        return _AssocAutomatic( other_side_klas, backref= backref or other_side_attr,
                    assoc_base= klas, **kargs )
    HIDDEN_NAME_PREFIX = '_Assoc'
    '''if any of above methods has to be overloaded, it has to be renamed as say _Hidden,
        become @staticmethod and be overloaded as such, while keeping the
        @classmethod just as
        def Hidden( klas, *a,**k): return klas._Hidden( klas, *a,**k)
    '''

    @classmethod
    def get_link_info( klas, attr):
        #sees parent_klas after forward-decl-resolving
        if isinstance( attr, str):
            attr = getattr( klas, attr)
        rel_info = klas.reflector.is_relation_type( attr)
        assert rel_info.is_reference
        return rel_info.klas, attr.assoc.relation_attr

    @classmethod
    def walk_links( klas, with_typ =False ):
        if not klas.DBCOOK_hidden:      #explicit
            #only works after mapping - i.e. not at table level
            from sqlalchemy.orm import class_mapper
            from sqlalchemy.orm.properties import PropertyLoader
            for prop in class_mapper( klas).iterate_properties:
                if not isinstance( prop, PropertyLoader): continue
                key = prop.key
                r = key, prop.mapper.class_
                if with_typ:
                    typ = klas.reflector.attrtypes( klas).get( key, None)   #not getattr, it gives SA-stuff
                    r = r + (typ,)
                yield r
        else:
            #sees parent_klasi after forward-decl-resolving
            #does not see implied links, e.g. by A.asoc = Assoc.Relation( backref='a_ptr')
            for attr,typ in klas.reflector.attrtypes( klas, plains=False).iteritems():
                rel_info = klas.reflector.is_relation_type( typ)
                assert rel_info.is_reference
                assoc_details = getattr( typ, 'assoc', None)
                if assoc_details:
                    r = attr, rel_info.klas
                    if with_typ: r = r + (typ,)
                    yield r

    @classmethod
    def find_links( klas, parent_klas):  #, parent_name):
        for l_attr,l_klas in klas.walk_links():
            if l_klas is parent_klas: #... and l_attr
                yield l_attr


    ######## these must be setup by reflector types
    Type4Reference = None
    reflector = None

    _used = False       #for hidden m2m: set on first found side, to avoid duplication

    ######## internal interface
    @classmethod
    def _is_valid( klas):
        n=0
        for whatever in klas.walk_links():
            n+=1
        return n>=1 #has at least 1 Link
        #for k in dir( klas):
        #    if not k.startswith( '__') and hasattr( getattr( klas, k), 'assoc'):
        #        return True     #has at least 1 Link

    @staticmethod
    def _CollectionFactory_any( cklas):
        m = _AssocDetails.MyCollection()
        m.factory = cklas
        #m.assoc_attr           #assoc side
        #m.owner, m.owner_attr  #owner side
        return m
    @classmethod
    def _CollectionFactory( klas):
        return klas._CollectionFactory_any( klas)


from config import table_namer
def resolve_assoc_hidden( builder, klasi):
    dbg = 'assoc' in config.debug or 'relation' in config.debug
    mapcontext = builder.mapcontext
    news = {}
    for k,klas in klasi.iteritems():
        for attr, rel_typ, nonmappable_origin in sorted( mapcontext.iter_attr( klas,
                                                    collections=True, plains=False, references=False,
                                                    attr_base_klas= _AssocAutomatic,
                                                    local= True,
                                                    denote_nonmappable_origin= True,
                                                    dbg=dbg ),
                                                key= lambda (a,rel_typ,nmo): (rel_typ.variant_of,nmo,a) ):
            rel_typ.name = attr
            other_side_klas = rel_typ.assoc_klas
            Assoc = rel_typ.assoc_base
            other_side_attr = rel_typ.backrefname
            if dbg:
                print 'assoc_hidden: ', klas, '.'+attr, '<->', rel_typ,
                if rel_typ.synonym_by: print 'synonym_by:'+rel_typ.synonym_by,
                if rel_typ.variant_of: print 'variant_of:'+rel_typ.variant_of,
                print

            mapbase = mapcontext.base_klas
            if not issubclass( Assoc, mapbase):
                metabase = getattr( Assoc, '__metaclass__', None)
                if not metabase: metabase = getattr( mapbase, '__metaclass__', None)
                if not metabase: metabase = type
                class meta( metabase):
                    def __new__( meta, name, bases, adict):
                        bases = (mapbase,) + bases
                        return metabase.__new__( meta, name, bases, adict)
            else: meta = None

            class AssocHidden( Assoc):
                DBCOOK_automatic = True
                if meta: __metaclass__ = meta
                DBCOOK_hidden = rel_typ.hidden
                if rel_typ.indexes:
                    DBCOOK_indexes = list(Assoc.DBCOOK_indexes) + 'left right'.split()
                left  = Assoc.Link( klas, attr= attr, nullable=False)
                right = Assoc.Link( other_side_klas, attr= other_side_attr, nullable=False)
                if rel_typ.variant_of:
                    _DBCOOK_variant_of = getattr( klas, rel_typ.variant_of)     #ok for cloned because of nonmappable_origin
                if rel_typ.dbname:
                    DBCOOK_dbname = rel_typ.dbname % dict( klas_name= klas.__name__)
                else:
                    @classmethod
                    def DBCOOK_dbname( klas):
                        #this sees forward-resolved
                        this_side_klas,  this_side_attr  = klas.get_link_info( 'left')
                        other_side_klas, other_side_attr = klas.get_link_info( 'right')
                        r = '_'.join( x for x in (
                                klas.HIDDEN_NAME_PREFIX,
                                table_namer( this_side_klas ), this_side_attr,
                                '2',
                                table_namer( other_side_klas), other_side_attr
                            ) if x)
                        return r
            #TODO test

            if nonmappable_origin:
                if dbg: print ' inherited from nonmappable base, clone'
                rel_typ = rel_typ.copy()
                setattr( klas, attr, rel_typ)
            rel_typ.assoc_klas = assoc_klas = AssocHidden

            #change __name__ - see __name__DYNAMIC
            klasname = '_'.join( x for x in (
                Assoc.HIDDEN_NAME_PREFIX,
                table_namer( klas), attr,
                '2',
                isinstance( other_side_klas, str) and other_side_klas or table_namer( other_side_klas),
                other_side_attr ) if x)
            assoc_klas.__name__ = klasname

            #self-add to mappable klasi
            news[ klasname ] = assoc_klas
    klasi.update( news)

def is_association_reference( klas, attrtyp, attrklas):
    'used in table-maker'
    column_kargs = {}
    column_func = None
    if issubclass( klas, Association):
        assoc_details = getattr( attrtyp, 'assoc', None)
        if assoc_details:
            #column_kargs = dict( nullable= assoc_details.nullable )
            column_func = lambda column, cacher: relate( klas, attrklas, assoc_details.relation_attr,
                                                            column, cacher=cacher)
    return column_kargs, column_func

def relate( klas, parent_klas, parent_attr, column, cacher ):
    dbg = 'relation' in config.debug
    if dbg:
        print 'relate parent:', parent_klas, 'to child:', klas
        print '  parent.attr:', parent_attr, 'child.column:', column

    ### collect parent_attr to be created by make_relation() if not already done explicitly
    lcache = cacher.assoc_links = getattr( cacher, 'assoc_links', {})
    links = lcache.setdefault( parent_klas, set() )
    link = (klas, parent_attr)
    link_already_there = link in links
    if link_already_there:
        warnings.warn( '''duplicate definition
            of assoc_link %(klas)s <- %(parent_klas)s.%(parent_attr)s''' % locals() )
    links.add( link )

    ### collect foreign_keys
    #parent_klas.parent_attr is pointed by klas.column
    #dict( klas: dict( parent_klas: dict( parent_attr:column)))
    fcache = cacher.foreign_keys = getattr( cacher, 'foreign_keys', {})
    foreign_keys = fcache.setdefault( klas, {})
    kk = foreign_keys.setdefault( parent_klas, {} )
    key = parent_attr

    if key is not None:
        if key in kk:
            if link_already_there: return
            assert 0, '''duplicate/ambigious association %(parent_klas)s.%(key)s -> %(klas)s;
                specify attr=<assoc_relation_attr> explicitly
                kk=%(kk)s''' % locals()
    else:
        if key in kk:
            warnings.warn( '''duplicate/ambigious/empty association %(parent_klas)s.%(key)s -> %(klas)s;
                specify attr=<assoc_relation_attr> explicitly ''' % locals() )
    kk[ key ] = column
    if dbg:
        print '  fkeys:', kk


class _Unspecified: pass

class _Relation( object):
    class frozendict( dict):
        def _block( *a,**k):
            raise AttributeError, 'cannot modify frozendict'
        __delitem__ = __setitem__ = clear = pop = popitem = setdefault = update = _block
    DICT = frozendict

    _meta_kargs = ()    #allowed meta-kargs
    def __init__( me, assoc_klas, backref =None, synonym_by =None, variant_of =None, **rel_kargs):
        me.assoc_klas = assoc_klas
        me.__dict__.update( (k,rel_kargs.pop(k)) for k in me._meta_kargs if k in rel_kargs )
        me.rel_kargs = me.DICT( rel_kargs)
        if backref and not isinstance( backref, dict):
            backref = dict( name= backref)
        me.backref = backref
        me.synonym_by = synonym_by
        me.variant_of = variant_of
    def __str__( me):
        return me.__class__.__name__ +'/' + str(me.assoc_klas) +'.' + (me.backref and str(me.backref) or 'nobackref')

    def copy( me):
        from copy import copy
        return copy( me)

    def resolve( me, builder):
        'needed separately before make()'
        assoc_klas = me.assoc_klas
        if isinstance( assoc_klas, str):
            try: assoc_klas = me.assoc_klas = builder.klasi[ assoc_klas]
            except KeyError: assert 0, '''\
undefined relation/association class %(assoc_klas)r -
maybe it does not inherit a mappable base?''' % locals()
        return assoc_klas

    def make( me, builder, klas, name ):
        'return relation_klas, actual_relation_klas, relation_kargs'
        dbg = 'relation' in config.debug
        assoc_klas = me.resolve( builder)
        if dbg: print ' ' , me, 'prop:', klas, '.', name or None
        original_rel = getattr( assoc_klas, '_DBCOOK_variant_of', None)
        if original_rel: name = original_rel.name
        foreign_keys = builder.foreign_keys[ original_rel and original_rel.assoc_klas or assoc_klas]
        if dbg: print ' ', me, 'assoc_fkeys:', foreign_keys

        try: fks = foreign_keys[ klas ]
        except KeyError: assert 0, '''missing declaration of link in association %(assoc_klas)s -> %(klas)s.%(name)s ''' % locals()

        assert name, 'relation/association %(assoc_klas)r relates to %(klas)r but no attrname specified anywhere' % locals()
        for key in (name, None):
            try:
                fk = fks[ key]
                break
            except KeyError: pass
        else:
            assert 0, '''missing/wrong relation for association
 %(klas)s.%(name)s <- %(assoc_klas)s
 attrname: %(name)s;
 available: %(fks)s;
 all foreign_keys: %(foreign_keys)s.
Check for double-declaration with different names''' % locals()

        collection_class = getattr( assoc_klas, '_CollectionFactory', None)
        #if collection_class:
        #    c = collection_class
        #    collection_class = lambda : c( owner=klas, owner_attr=name, assoc_attr= klas)) #klas
        rel_kargs = dict(
                lazy    = True,
    #           cascade = 'all, delete-orphan',    #DB_hidden-relation does FlushError with this
                uselist = True,
                collection_class = collection_class     #needed if InstrumentedList.append is replaced
            )
        rel_kargs.update( me.rel_kargs)
        #for k,v in me.rel_kargs.iteritems():
        #    if callable( v): v = v( klas, assoc_klas )
        #    rel_kargs[k] = v

        colid = builder.column4ID( klas )

        ERR_CANNOT_HIDE_ASSOC = '''association %(assoc_klas)s between more than 2 items
            cannot be DBCOOK_hidden (which one to give as other side?)'''

        if getattr( assoc_klas, 'DBCOOK_hidden', None):
            if assoc_klas._used:
                return None
            assoc_klas._used = True
            if len(fks)==2:     #2 diff links to same klas
                #print 'same klas x2'
                assert len(foreign_keys) == 1, ERR_CANNOT_HIDE_ASSOC % locals()
                for k in fks:
                    if k != key: break
                else:
                    assert 0, 'internal error, wrong .foreign_keys[%(klas)s] on %(assoc_klas)s' % locals()
                othername = k
                otherfk = fks[k]
                otherklas = klas
            else:   #2 diff klasi
                #print '2diff', foreign_keys
                assert len(foreign_keys) == 2, ERR_CANNOT_HIDE_ASSOC % locals()
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
#                    cascade = 'all',
                    collection_class = lambda: Association._CollectionFactory_any( otherklas),
                )
        else:
            assoc_klas_actual = assoc_klas
            rel_kargs.update(
                    primaryjoin = (fk == colid),
                    remote_side = fk,
                )
        for k,v in me.rel_kargs.iteritems():
            if callable( v):
                rel_kargs[k] = v( klas, assoc_klas_actual )
        if dbg: print ' ', me, 'made:', assoc_klas, assoc_klas_actual, rel_kargs
        return assoc_klas, assoc_klas_actual, rel_kargs

from dbcook.util.attr import setattr_kargs, setattr_from_kargs

class _AssocDetails:
    __init__ = setattr_kargs

    #do not pollute Association' namespace
    class MyCollection( list):
        #owner = None
        factory = None
        @sqlalchemy.orm.collections.collection.internally_instrumented
        def append( me, obj =_Unspecified, **kargs):
            msg = 'give premade %r obj, or only kargs to make one, or maybe use hidden assoc (DBCOOK_hidden=True)'
            if obj is _Unspecified:
                assert kargs, msg % me.factory
                obj = me.factory( **kargs)
            assert isinstance( obj, me.factory), msg % me.factory
            me._append( obj)
            return obj
        @sqlalchemy.orm.collections.collection.appender
        def _append( me, *a,**k): return list.append( me, *a, **k)

class _AssocAutomatic( _Relation):
    def __init__( me, assoc_klas, *args, **kargs ):
        setattr_from_kargs( me, kargs,
                assoc_base= Association, dbname =None, indexes =False, hidden =True,
            )
        _Relation.__init__( me, assoc_klas, *args, **kargs)
    @property
    def backrefname( me): return me.backref and me.backref['name'] or ''
    def __str__( me): return ','.join( [_Relation.__str__(me),
                            {True:'implicit', False: 'explicit'}.get( me.hidden, 'implicit='+str(me.hidden) )
                            ])
##############################

class Collection( _Relation):
    '''declare one2many relations - in the 'one' side of the relation'''
    def __init__( me, child_klas, *args, **kargs ):  #order_by =None, #backref= name or dict( rel_kargs), etc
                    #unique =False,  #   ??
        _Relation.__init__( me, child_klas, *args, **kargs)
        me._backrefname = None   #decided later
    @property
    def backrefname( me):
        b = me._backrefname
        return b
    def setup_backref( me, parent_klas, parent_attr):
        backrefname, me._backrefname = setup_backrefname( me.backref, parent_klas, parent_attr)
        return backrefname

def setup_backrefname( backref_dict, parent_klas, parent_attr):
    from config import column4ID
    if backref_dict and 'name' in backref_dict:
        backrefname = backref_dict[ 'name']
        #XXX save as functor to allow multiple-usage of same relation-def
        # in many inheriting classes - re-exec there
        #... is this obsolete because of Relation.copy() ?
        _backrefname = backrefname
        if callable( backrefname):
            backrefname = backrefname( parent_klas, parent_attr)
    else:
        #make once and save - no reexec
        backrefname = column4ID.backref_make_name( parent_klas, parent_attr)
        _backrefname = backrefname
    return backrefname, _backrefname

def make_relations( builder, sa_relation_factory, sa_backref_factory, FKeyExtractor ):
    dbg = 'relation' in config.debug

    #XXX TODO merge with make_mapper_props ??
    iter_attr = builder.mapcontext.iter_attr
    for m in builder.itermapi( primary_only =True):
        if dbg: print 'make_relations', m

        klas = m.class_
        fkeys = FKeyExtractor( klas, m.local_table, builder.mapcontext, builder.tables)
        assoc_links = getattr( builder, 'assoc_links', {}).get( klas, () )
        if assoc_links:
            #match assoc-links with real rels
            assoc_links_names = dict( (rel_attr, assoc_klas) for assoc_klas, rel_attr in assoc_links )
            for name,typ in iter_attr( klas, local= False):
                assert name not in assoc_links_names, '''%(klas)s.%(name)s specified both
                        as attribute and as link in association ''' % locals() + str( assoc_links_names[ name] )
            for name,typ in iter_attr( klas,
                                        collections=True, plains=False, references=False,
                                        local= False):
                typ.resolve( builder)
                if dbg: print '  try', name, typ
                try: assoc_links.remove( (typ.assoc_klas, name) )       #match real rel to named link
                except KeyError:
                    try: assoc_links.remove( (typ.assoc_klas, None))    #match real rel to unnamed link
                    except KeyError:
                        #print 'notfound'
                        pass
                    else:
                        if dbg: print '  found matching noname-assoc_link for', name
                        pass
                else:
                    if dbg: print '  found matching named-assoc_link and relation for', name
                    pass
                    #or error as duplicate??

            #only missing links left here in assoc_links... now combine with all other _Relation
            if dbg and assoc_links: print '  association-implied implicit relations:', assoc_links

        relations = {}

        #XXX this may invent wrong (backref) relation !
        assoc_implicit_rels = [ (rel_attr, _Relation( assoc_klas))
                                    for assoc_klas, rel_attr in assoc_links
                                    if rel_attr and not getattr( assoc_klas, 'DBCOOK_hidden', None)
                                        #if no name on this side: nothing here, all at other side
                                        #if DBCOOK_hidden: nothing here, all at other/explicit side
                                ]
        if dbg and assoc_links: print '  association-implied valid implicit relations:', assoc_implicit_rels

        iter_rels = sorted( builder.mapcontext.iter_attr( klas,
                                collections=True, plains=False, references=False,
                                local= True, dbg=dbg ),
                            key= lambda (nm,typ): (typ.variant_of,nm) )

        for name,typ in iter_rels + assoc_implicit_rels:
            rel_info = typ.make( builder, klas, name)    #any2many
            if not rel_info:
                if dbg: print '  DONE ON OTHERSIDE:', name
                assert 0, 'must not come here???'
                #continue
            rel_klas, rel_klas_actual, rel_kargs = rel_info
            #if not rel_klas_actual: rel_klas_actual = rel_klas

            #forward link
            r = fkeys.get_relation_kargs( name)
            if dbg: print '  FORWARD:', name, r, fkeys
            rel_kargs.update( r)

            #backward link 1:n
            backref = typ.backref
            if backref:
                backrefname = typ.backrefname
                if callable( backrefname): backrefname = backrefname( klas, name)
                r = fkeys.get_relation_kargs( backrefname)
                backref = backref.copy()
                backref['name'] = backrefname
                if dbg: print '  BACKREF:', backrefname, r, backref
                for p in 'post_update remote_side'.split():
                    try: backref[ p] = r[p]
                    except KeyError: pass
                #explicit - as SA does if backref is str
                pj = rel_kargs[ 'primaryjoin']
                sj = rel_kargs.get( 'secondaryjoin')
                if rel_kargs.get( 'secondary') and sj: pj,sj=sj,pj
                backref = sa_backref_factory(
                            #secondary = secondary,
                            primaryjoin  = pj,
                            secondaryjoin= sj,
                            ##XXX uselist= False, #??? goes wrong if selfref - both sides become lists
                            **backref)
                rel_kargs[ 'backref'] = backref
            if dbg:
                print ' add_property', klas,'.',name, 'via', rel_klas, rel_klas is not rel_klas_actual and '/'+str(rel_klas_actual) or '',
                print ', '.join( '%s=%s' % kv for kv in rel_kargs.iteritems() )
            m.add_property( name, sa_relation_factory( rel_klas_actual, **rel_kargs) )
            relations[ name ] = rel_klas
            synonym_by = typ.synonym_by
            if synonym_by:
                synattr = getattr( klas, synonym_by, None)
                if dbg:
                    print ' add_synonym', klas, '.', synonym_by, 'to', name, 'via', synattr
                m.add_property( synonym_by, sqlalchemy.orm.synonym( name, descriptor= synattr) )


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

from aboutrel import about_relation
def get_class_of_relation(*a,**k): return about_relation(*a,**k).otherside.klas

# vim:ts=4:sw=4:expandtab
