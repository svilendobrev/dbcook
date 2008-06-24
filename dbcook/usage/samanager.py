#yId: samanager.py 6 2007-07-18 18:29:49Z svilen_dobrev $
# -*- coding: cp1251 -*-

from dbcook import builder
import sqlalchemy
import sqlalchemy.orm

def _setup_state( x): pass
try:    #user_defined_state branch / v4xxx?
    from sqlalchemy.orm.session import _state_for_unsaved_instance
    from sqlalchemy.orm import session
    def _setup_state( x):
        try: session._state_for_unsaved_instance( x, entity_name=None)
        except session.sa_exc.InvalidRequestError: pass #already persistent
except ImportError:
    try:
        from sqlalchemy.orm.attributes import InstanceState    #>v3463
        def _setup_state( x):
            if not hasattr( x, '_state'):
                x._state = InstanceState(x)
                #sqlalchemy.attribute_manager.manage(obj) does above
    except ImportError: pass


from sa_engine_defs import Dengine

class Config( builder.config.Config):
    db   = ''               #'' or memory or sqlite or postgres or URL

    echo     = False        #same as log_sa=sql
    log_sa   = ''           #'sql all transact mapper'

    _help = '''
database options:
  db=       :: memory or sqlite (./) or postgres (localhost) or URI (default: memory via sqlite);
                URI is driver://[user:pass@host[:port]]/database
  no_echo_hack :: do not hack SA for nicer echo of selects
debug/output options:
  echo      :: echo SQL (same as log_sa=sql)        [default:no]
  log_sa=   :: SA-logging: sql,transact,mapper,connect,all  [default:no]
'''

config = Config( builder.config )

## nice echo of selects
import sys
try: sys.argv.remove( 'no_echo_hack')
except: import sa_hack4echo

############################


def _argdef( v, default):
    if v is None: v = default
    return v

class SAdb:
    config  = config

    def __init__( me,
                db_type =None,      #memory, sqlite, postgres, url ==config.db
                echo = None,        #same as log_sa=sql
                log_sa = None,      #same as config.log_sa
                log2stream =False,
            ):
        me.db_type  = _argdef( db_type, config.db)
        me.echo     = _argdef( echo, config.echo)
        me.log_sa   = _argdef( log_sa, config.log_sa)
        if log2stream:
            import StringIO
            log2stream = StringIO.StringIO()
        me.log2stream = log2stream

        setup_logging( me.log_sa, log2stream)

    Builder = builder.Builder           #do override
    fieldtypemap = None                 #do override
    def bind( me, namespace, fieldtypemap =None, builder =None, print_srcgenerator =True, **kargs):
        '''make and run a builder, and keep some important stuff locally:
            mapcontext: context of work - baseklas, subclasses-tree, meta-info
            klasi:   dict(name:klas) of ALL classes
            tables:  dict(klas:table) of ALL classes
            mappers: dict(klas:mapper/mapper) of ALL ORMapped classes (less Hidden Association-classes);
        '''
        if builder is None: builder = me.Builder
        if fieldtypemap is None: fieldtypemap = me.fieldtypemap

        assert builder
        assert fieldtypemap
        b = builder( me.make_metadata(), namespace, fieldtype_mapper=fieldtypemap, **kargs)

        for a in 'mapcontext klasi mappers   tables'.split():
            setattr( me, a, getattr( b, a))

        if print_srcgenerator and b.generator:
            print '========= generated SA set-up'
            print b.generator.out
            print '========= eo generated SA set-up'
        return b

    def make_metadata( me):
        metadata = sqlalchemy.MetaData( me.db)
        me.metadata = metadata
        return metadata


    def _open( me, url, echo =None, **kargs):
        if 'open' in config.debug:  print '_open db:', url
        if echo is None:
            echo = me.echo or 'sql' in me.log_sa
        echo_pool= ('connect' in me.log_sa) or ('all' in me.log_sa)
    #    dict( echo_pool= echo_pool, max_overflow= -1)
        db = me.db = sqlalchemy.create_engine( url, echo_pool=echo_pool, echo=echo, **kargs)
        return db

    def open( me, recreate =False, **engine_kargs):
        'uses default urls, and can recreate'
        db_type = me.db_type or 'memory'
        if 'open' in config.debug: print 'open db:', db_type, recreate and 'recreate' or ''

        url,kargs = Dengine.setup( db_type, recreate, **engine_kargs)
        return me._open( url, **kargs)

    def destroy( me, full =True):
        if 'open' in config.debug: print 'destroy:', full and 'full' or ''
        #my caches
        for a in 'mappers tables'.split(): #klas_only_selectables
            try: getattr( me, a).clear()
            except AttributeError: pass

        #SA caches/data
        sqlalchemy.orm.clear_mappers()

        try: me.metadata.drop_all()
        except AttributeError: pass
        me.metadata = None
        if full:
            try: me.db.dispose()
            except AttributeError: pass
            me.db = None

        #from sqlalchemy.orm import mapperlib
        #mapperlib.global_extensions[:] = []
        #more?

    #these may be used between make_metadata()/bind() and destroy()
    def destroy_tables( me):
        me.metadata.drop_all()
    def create_tables( me):
        me.metadata.create_all()

    @staticmethod
    def detach_instances( namespace_or_iterable, **kargs):
        detach_instances( namespace_or_iterable, idname= builder.column4ID.name, **kargs)


    def iterklasi( me): return me.klasi.itervalues()

    def rootTable( me, klas):
        mostBaseMappableKlas = me.mapcontext.root( klas)
        return me.tables[ mostBaseMappableKlas]

    def session( me):
        return sqlalchemy.orm.create_session( echo_uow= 'transact' in me.log_sa)

    def saveall( me, session, *args, **kargs):
        ''' kargs:
            pre_save= methodname to call on all objects before session.save;
                        empty disables it;
                        a list of names will try for alternatives;
                        defaults to "pre_save"
        usages:
            saveall( session, obj1,...)
            saveall( session, somedict) #or_namespace
            saveall( session, *iterable)
        do session.save over all proper objects in args/namespace_or_iterable,
        i.e. those which are mapped and has_instances.
        calls obj.pre_save() if available (just before session.save)
        kargs: pre_save
        '''
        if not args: return
        itervalues = args
        if len(args)==1:
            try: itervalues = args[0].itervalues()        #if dict-like
            except AttributeError: pass #itervalues = namespace_or_iterable   #or iterable
        mapcontext = me.mapcontext
        base_klas = mapcontext.base_klas
        pre_save_names = kargs.get( 'pre_save', 'pre_save' )
        if not isinstance( pre_save_names, (list,tuple)): pre_save_names = [ pre_save_names ]
        for x in itervalues:
            if isinstance( x, base_klas) and mapcontext.has_instances( x.__class__):
                for fname in pre_save_names:
                    pre = getattr( x, fname, None)
                    if pre:
                        #_setup_state(x)    #XXX not needed?
                        #print 'pre_save', object.__repr__( x)
                        pre()

                session.save_or_update( x)

    ####### querys
    def query_all_tables( sadb, *classes, **kargs_ignore):
        yield '=== whole database:'
        for k,t in sadb.tables.iteritems():
            if not classes or k in classes:
                yield k, '\n'.join(
                        ' '.join( '%s=%s' % kv for kv in r.items())
                        for r in t.select().execute() )

    ####### klasifier querys
    def query_BASE_instances( sadb, session, klas ):
        m = sadb.mappers[ klas]
        if m.plain is None: return ()
        return session.query( m.plain )

    def query_ALL_instances( sadb, session, klas ):
        return session.query( klas)

    def query_SUB_instances( sadb, session, klas ):
        m = sadb.mappers[ klas]
        f = m.polymorphic_sub_only
        if f is None: return ()
        q = session.query( m.polymorphic_all )
        if isinstance( f, sqlalchemy.sql.Selectable):
            return q.from_statement( f)
        else:
            return q.filter( f)


def setup_logging( log_sa, log2stream =None):
    import logging
    #plz no timestamps!
    format ='* SA: %(levelname)s %(message)s'
    logging.basicConfig( format= format, stream= log2stream or logging.sys.stdout)  #level= logging.DEBUG,
    if log_sa == 'all':
        logging.getLogger( 'sqlalchemy').setLevel( logging.DEBUG) #debug EVERYTHING!
    else:
        from dbcook.util.attr import find_valid_fullname_import
        salog = find_valid_fullname_import( '''
            sqlalchemy.log
            sqlalchemy.logging
            ''', 0)
        salog.default_enabled= True    #else, default_logging() will setFormatter...

        if 'mapper' in log_sa:
            from sqlalchemy.orm import mapperlib
            mapperlib.Mapper.logger.setLevel( logging.DEBUG)
        if 'orm' in log_sa:
            logging.getLogger( 'sqlalchemy.orm').setLevel( logging.DEBUG)

def detach_instances( namespace_or_iterable, idname, resetup =False ):
    debug = 'open' in config.debug
    if debug: print 'detach_instances:', resetup and 'resetup' or ''
    try: itervalues = namespace_or_iterable.itervalues()        #if dict-like
    except AttributeError: itervalues = namespace_or_iterable   #or iterable
    assert idname
    for e in itervalues:
        for k in '_instance_key _state'.split():
            try: delattr( e, k)
            except AttributeError: pass
        setattr( e, idname, None)       #or delattr ??
        if resetup:
            if debug: print 'resetup', e.__class__, id(e)
            _setup_state( e)

if 0*'inline_inside_table/embedded_struct':
    _level_delimiter4embedded_name = '_' #( parent,child): return '_'.join( (parent,child) )

    pfx = k+_level_delimiter4embedded_name
    inside_columns = make_table_columns( typ.typ,
                        mapcontext,
                        name_prefix= pfx,
                    )
    columns += inside_columns


    #... ����������: a.b.c = a.b_c
    #... ��������� ��� �� �������� a.b.c.d? -> a.b_c_d -> a.b.c_d -> a.b.c.d ??
    if 0:
        for c in inside_columns:
            assert c.name.startswith( pfx)
            subattr = c.name[ len(pfx): ]
            if dbg: print '    aliasing', pfx, subattr, getattr( klas, pfx+subattr)

        ''' ���� �� ����� ������. SA �� ������� ���� �������� ���
        InstrumentedAttribute/��������, ������� setattr - ����� ���� �� �� �����.
        T����� setattr( a.b.c) �� �� ��������/������ �� setattr( a_b_c)...
        ���� ��������� ������ � a.b = B() - ���� ������ �� ������ �������� ���-��������... �����.
        set( a.b.c.d) -> a.set( b_c_d) =SA> a.dict[ b_c_d] - � �� ������ �� ���� �� dict!
        set( a.b_c_d) =SA> a.dict[ b_c_d] -> a.set( b.c.d)
        get( a.b_c_d) =SA> a.dict[ b_c_d] -> a.get( b.c.d)
        get( a.b.c.d) -> SA? lazy-get?

        class ASValue( StaticStruct):
            __slots__ = ['_parent_', '_name_']
            def _setattr_props( me, name, value, type):
                me._parent_._setattr_props( me.name + _level_delimiter4embedded_name + name, value, type)
        class SubStruct4ASValue( SubStruct4):
            def __init__( me, typ, **kargs): ...

        ��� �� ����� �� �� ������� �� ���� StaticType_ValueContainer - ��� ��� parent???
        ��� ����� ASValue.SubStruct �� � _������_ �������� ���� �� SubStruct ... - �� �����,
        � �������- ���������� proxy...
        ������ - ������ ����...

        �������:
         1/ ������/������� ASValue
         2/ ������ ORM � ������ ������ � ������� �� ���� ������������� � deepcopy Obj<->SAObj
            - ���� ������ � �������� � ���������������� ��������� / dirtyness
         ������ 1/... ������ ��?
        '''

# vim:ts=4:sw=4:expandtab
