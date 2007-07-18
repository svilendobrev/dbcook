#$Id$
# -*- coding: cp1251 -*-

from dbcook import builder
import sqlalchemy

import util.config
class Config( util.config.Config):
    db   = ''               #'' or memory or sqlite or postgres or URL

    echo     = False
    log_sa   = ''           #'sql all transact mapper'

    _help = '''
database options:
  db=       :: memory or sqlite (./) or postgres (localhost) or URL (default: memory via sqlite);
                URL is driver://[user:pass@host[:port]]/database
debug/output options:
  echo      :: echo SQL (same as log_sa=sql)        [default:no]
  log_sa=   :: SA-logging: sql,transact,mapper,connect,all  [default:no]
'''

config = Config( builder.config )

## nice echo of select etc
import sys
try: sys.argv.remove( 'no_echo_hack')
except: import sa_hack4echo



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
    def bind( me, namespace, fieldtypemap =None, builder =None, **kargs):
        print_srcgenerator = kargs.pop( 'print_srcgenerator', True)
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
        metadata = sqlalchemy.BoundMetaData( me.db)
        if me.echo or 'sql' in me.log_sa:
            metadata.engine.echo = True
        me.metadata = metadata
        return metadata

    def open( me, recreate =True, debug =False, **kargs):
        db_type = me.db_type
        if debug or 'open' in config.debug:  #XXX move ?????
            print 'open db:', db_type, recreate and 'recreate' or 'must-exist'

        if not db_type: db_type = 'memory'

        default_url = me._default_url.get( db_type, None)
        if not default_url:
            url = db_type
            if recreate:
                print 'cannot recreate by url, DIY'

            echo_pool= ('connect' in me.log_sa) or ('all' in me.log_sa)
            #to be replaced by kargs-per-enginetype, like default_url above
            if 'postgres' in db_type:
                kargs.update( echo_pool= echo_pool, max_overflow= -1)
        else:
            recreator = default_url[ 'recreate']
            url = default_url[ 'url']
            if recreate and callable( recreator):
                recreator( me)

        db = sqlalchemy.create_engine( url, **kargs)
        me.db = db

        return db

    def _recreate_sqlite( me):
        import os
        try: os.remove( 'proba1.db')
        except OSError: pass

    def _recreate_postgres( me):
        import os
        try:
            r = os.system( 'dropdb proba')
            r = os.system( 'createdb proba')
        except OSError: pass

    _default_url = dict(
        memory  = dict( url='sqlite:///:memory:' , recreate= None),
        sqlite  = dict( url='sqlite:///proba1.db', recreate= _recreate_sqlite),
        postgres= dict( url='postgres:///proba'  , recreate= _recreate_postgres),
    )
    ###### eo open stuff

    def destroy( me, full =True):
        #my caches
        for a in 'mappers tables klas_only_selectables'.split():
            try: getattr( me, a).clear()
            except AttributeError: pass

        #SA caches/data
        sqlalchemy.clear_mappers()

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

    def detach_instances( me, namespace_or_iterable):
        detach_instances( namespace_or_iterable, idname= builder.column4ID.name)


    def echo_sql( me, x):       #show SQL statements
        old = me.metadata.engine.echo
        me.metadata.engine.echo = x
        return old

    def iterklasi( me): return me.klasi.itervalues()

    def session( me):
        return sqlalchemy.create_session( echo_uow= 'transact' in me.log_sa)

    def saveall( me, session, *args):
        ''' usages:
                saveall( session, obj1,...)
                saveall( session, somedict) #or_namespace
                saveall( session, *iterable)
            do session.save over all proper objects in args/namespace_or_iterable,
            i.e. those which are mapped and has_instances.
            calls obj.pre_save() if available (just before session.save)
        '''
        if not args: return
        itervalues = args
        if len(args)==1:
            try: itervalues = args[0].itervalues()        #if dict-like
            except AttributeError: pass #itervalues = namespace_or_iterable   #or iterable
        for x in itervalues:
            if isinstance( x, me.mapcontext.base_klas) and me.mapcontext.has_instances( x.__class__):
                try: pre = x.pre_save
                except AttributeError: pass
                else: pre()
                session.save( x)

    def pipequery( me, session, mapper, selectable):
        return session.query( mapper).select( selectable)
        #return session.query( mapper).filter( selectable)  #raw


    ####### querys
    def query_all_tables( sadb, **kargs_ignore):
        print '=== whole database:'
        for k,t in sadb.tables.iteritems():
            print k,':',[r for r in t.select().execute()]
    def query_table( sadb, klas, **kargs_ignore ):
        table = sadb.tables[ klas]
        return table.select().execute()

    ####### klasifier querys

    def query_BASE_instances_raw( sadb, session, klas ):
        m = sadb.mappers[ klas]
        if m.plain is None: return ()
        return session.query( m.plain )

    def query_ALL_instances_raw( sadb, session, klas ):
        return session.query( klas) #must be equivalent ??
        return session.query( sadb.mappers[ klas].polymorphic_all )


    def query_BASE_instances( sadb, session, klas ):
        r = sadb.query_BASE_instances_raw( session, klas )
        if r: r = r.select()
        return r
    def query_ALL_instances( sadb, session, klas ):
        return sadb.query_ALL_instances_raw( session, klas).select()

    def query_SUB_instances( sadb, session, klas ):
        m = sadb.mappers[ klas]
        if m.polymorphic_sub_only is None: return ()
        return sadb.pipequery( session, m.polymorphic_all, m.polymorphic_sub_only )


def setup_logging( log_sa, log2stream =None):
    import logging
    #plz no timestamps!
    format ='* SA: %(levelname)s %(message)s'
    logging.basicConfig( format= format, stream= log2stream or logging.sys.stdout)  #level= logging.DEBUG,
    if log_sa == 'all':
        logging.getLogger('sqlalchemy').setLevel( logging.DEBUG) #debug EVERYTHING!
    else:
        sqlalchemy.logging.default_enabled= True    #else, default_logging() will setFormatter...

        if 'mapper' in log_sa:
            from sqlalchemy.orm import mapperlib
            mapperlib.Mapper.logger.setLevel( logging.DEBUG)
        if 'orm' in log_sa:
            logging.getLogger('sqlalchemy.orm').setLevel( logging.DEBUG)

def detach_instances( namespace_or_iterable, idname ):
    try: itervalues = namespace_or_iterable.itervalues()        #if dict-like
    except AttributeError: itervalues = namespace_or_iterable   #or iterable
    assert idname
    for e in itervalues:
        try: del e._instance_key
        except AttributeError: pass
        setattr( e, idname, None)       #or delattr ??


if 0*'inline_inside_table/embedded_struct':
    _level_delimiter4embedded_name = '_' #( parent,child): return '_'.join( (parent,child) )

    pfx = k+_level_delimiter4embedded_name
    inside_columns = make_table_columns( typ.typ,
                        mapcontext,
                        name_prefix= pfx,
                    )
    columns += inside_columns


    #... псевдоними: a.b.c = a.b_c
    #... интересно как ще изглежда a.b.c.d? -> a.b_c_d -> a.b.c_d -> a.b.c.d ??
    if 0:
        for c in inside_columns:
            assert c.name.startswith( pfx)
            subattr = c.name[ len(pfx): ]
            if dbg: print '    aliasing', pfx, subattr, getattr( klas, pfx+subattr)

        ''' това не върши работа. SA ще подмени тези атрибути със
        InstrumentedAttribute/слушател, очакващ setattr - което няма да се случи.
        Tрябва setattr( a.b.c) да се прихване/закара до setattr( a_b_c)...
        Също интересен случай е a.b = B() - това трябва да обходи всичките под-атрибути... смрад.
        set( a.b.c.d) -> a.set( b_c_d) =SA> a.dict[ b_c_d] - а не трябва да ходи до dict!
        set( a.b_c_d) =SA> a.dict[ b_c_d] -> a.set( b.c.d)
        get( a.b_c_d) =SA> a.dict[ b_c_d] -> a.get( b.c.d)
        get( a.b.c.d) -> SA? lazy-get?

        class ASValue( StaticStruct):
            __slots__ = ['_parent_', '_name_']
            def _setattr_props( me, name, value, type):
                me._parent_._setattr_props( me.name + _level_delimiter4embedded_name + name, value, type)
        class SubStruct4ASValue( SubStruct4):
            def __init__( me, typ, **kargs): ...

        или би могла да се направи на ниво StaticType_ValueContainer - там има parent???
        или требе ASValue.SubStruct да е _съвсем_ различно нещо от SubStruct ... - не обект,
        а обектно- изглеждащо proxy...
        ВЪОБЩЕ - голяма боза...

        решения:
         1/ зарежи/забрани ASValue
         2/ зарежи ORM в нашите обекти и правене на явно преобразуване с deepcopy Obj<->SAObj
            - това решава и проблема с транзакционнната семантика / dirtyness
         засега 1/... докога ли?
        '''

# vim:ts=4:sw=4:expandtab
