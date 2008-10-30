#$Id$

from sqlalchemy import *
from sqlalchemy.orm import *

#see baseobj.py
class Base( object):
    'with __init__(kwargs) and nice/non-recursive str()'
    def __init__( me, **kargs):
        for k,v in kargs.iteritems(): setattr( me, k, v)
    props = [ 'id' ]  #[...]
    props4ref = props + [ 'name' ]
    def __str__( obj, props =None):
        klas = obj.__class__
        r = klas.__name__ + '('
        for k in props or klas.props:
            v = getattr( obj, k, '<notset>')
            if isinstance( v, Base):
                v = '>' + v.__str__( klas.props4ref)
            r += ' '+k+'='+str(v)
        return r+' )'

class config:
    echo = False
    dump = False
    debug = False
    log_sa = False
    session_clear = True
    reuse_db = False
    leak = False
    gc = False
    memory = False
    db = 'sqlite:///:memory:'
    repeat = 1

#_mem = ''
def memusage():
    import os
    pid = os.getpid()
    m = ''
    for l in file( '/proc/%(pid)s/status' % locals() ):
        l = l.strip()
        for k in 'VmPeak VmRSS VmData'.split():
            if l.startswith(k):
                m += '; '+l
    if m: print m
#            global _mem
#            if _mem != m:
#                _mem = m
#                print m

import unittest
class Test_SA( unittest.TestCase):
    _db = None
    def setUp(me):
        if config.debug or config.echo:
            print '=====', me.id()

        if config.reuse_db and me._db:
            db = me._db
        else:
            db = create_engine( config.db)
            if config.reuse_db:
                me._db = db

        format ='* SA: %(levelname)s %(message)s'
        #plz no timestamps!
        if config.log_sa:
            import logging
            logging.basicConfig( level=logging.DEBUG, format=format, stream =logging.sys.stdout)
            logging.getLogger( 'sqlalchemy').setLevel( logging.DEBUG) #debug EVERYTHING!

        me.db = db
        db.echo = config.echo
        me.meta = MetaData( db)

    def tearDown(me):
        me.meta.drop_all()
        me.meta = None
        #destroy ALL caches
        clear_mappers()

        if not config.reuse_db:
            me.db.dispose()
        me.db = None
        if config.gc:
            import gc
            gc.set_debug( gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_SAVEALL | gc.DEBUG_INSTANCES | gc.DEBUG_STATS ) #OBJECTS
            gc.collect()
        if config.leak:
            from sqlalchemy.orm import mapperlib
            from sqlalchemy.orm.session import _sessions
            from sqlalchemy.util import ArgSingleton
            print "MAPPER REG:", len( dict( getattr( mapperlib, 'mapper_registry', getattr( mapperlib, '_mapper_registry', None)) ))
            print "SESION REG:", len( dict( _sessions) )
            print "CLASSKEYS:",  len( dict( ArgSingleton.instances) )
        if config.gc:
            i = 0
            for x in gc.get_objects():
                if isinstance(x, mapperlib.Mapper) or isinstance(x, MetaData):
                    i+=1
                    #print x
            print 'gc/SA objects:', i

    def dump( me, expects):
        if config.debug:
            print 'items:'
            for item in expects:
                print item['exp_single']
        if config.dump:
            print 'tables:'
            for item in expects:
                tbl = item['table']
                s = tbl.select()
                for x in s.execute():
                    print tbl, ':', ', '.join( '%s= %s' % kv for kv in zip( s.columns, x) )

    def query( me, session, expects, idname ='id'):
        me.dump( expects)
        for item in expects:
            me.query_by_id( session, idname=idname, **item)
            me.query_all( session, **item)
#            me.query_sub( session, **item)
#            me.query_base( session, **item)

    def check( me, q, exp, name):
        if not isinstance( exp, list): exp = [exp]
        exp.sort()
        q = sorted( str(x) for x in q)
        #assert q == exp
        me.assertEqual( q, exp, '''
%(name)s:
result= %(q)s
expect= %(exp)s''' % locals()
        )

    def query_by_id( me, session, klas, idname, oid, exp_single, **kargs_ignore):
        klasname = klas.__name__
        #single
        if config.session_clear: session.clear()
        name = '%(klasname)s .filter_by( %(idname)s=%(oid)s)' % locals()
        if config.debug: print name
        q = session.query( klas).filter_by( **{idname: oid})
        me.check( q, exp_single, name)

    def query_all( me, session, klas, exp_all, **kargs_ignore):
        klasname = klas.__name__
        #multiple
        if config.session_clear: session.clear()
        if config.debug: print klasname
        q = session.query( klas)
        me.check( q, exp_all, klasname )

    def query_sub( me, session, klas, sub, exp_sub, **kargs_ignore):
        #see dbcook/usage/samanager:query_SUB_instances
        klasname = klas.__name__
        if config.session_clear: session.clear()
        me.check( session.query( klas).from_statement( sub), exp_sub, klasname+'/sub-from_stmt')
        me.check( session.query( klas).select_from( sub), exp_sub, klasname+'/sub-select_from')

    def query_base( me, session, klas, mapr, exp_base, **kargs_ignore):
        #see dbcook/usage/samanager:query_BASE_instances
        klasname = klas.__name__
        if config.session_clear: session.clear()
        me.check( session.query( mapr), exp_base, klasname+'/base')

    def run( self, *a, **k):
        for i in range( config.repeat):
            unittest.TestCase.run( self, *a,**k)
            if config.memory: memusage()

help = 'echo dump debug log_sa no_session_clear reuse_db leak gc memory'
def setup():
    import sys
#    sys.setrecursionlimit( 600)
    for h in ['help', '-h', '--help']:
        if h in sys.argv:
            print 'options:', help

    for k in help.split():
        v = k in sys.argv
        if v: sys.argv.remove(k)
        if k.startswith('no_'):
            k = k[3:]
            v = not v
        setattr( config, k, v)

    for a in sys.argv[1:]:
        kv = a.split('=')
        if len(kv)==2:
            k,v = kv
            if k=='db':
                config.db = v
            elif k=='repeat':
                config.repeat = int(v)
            else: continue
            sys.argv.remove(a)

    print 'config:', ', '.join( '%s=%s' % (k,v) for k,v in config.__dict__.iteritems() if not k.startswith('__') )
# vim:ts=4:sw=4:expandtab
