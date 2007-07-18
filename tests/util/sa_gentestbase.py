#$Id$

from sqlalchemy import *

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
            logging.getLogger('sqlalchemy').setLevel( logging.DEBUG) #debug EVERYTHING!

        me.db = db
        me.meta = BoundMetaData( db)
        me.meta.engine.echo = config.echo

    def tearDown(me):
        me.meta.drop_all()
        me.meta = None
        #destroy ALL caches
        clear_mappers()

        if not config.reuse_db:
            me.db.dispose()
        me.db = None
        if config.leak:
            import gc, sqlalchemy
            gc.set_debug( gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_SAVEALL | gc.DEBUG_INSTANCES | gc.DEBUG_STATS ) #OBJECTS
            gc.collect()
            #print "MAPPER REG:", dict(sqlalchemy.orm.mapperlib.mapper_registry)
            #print "SESION REG:", dict(sqlalchemy.orm.session._sessions)
            #print "CLASSKEYS:", dict(sqlalchemy.util.ArgSingleton.instances)
            i = 0
            for x in gc.get_objects():
                if isinstance(x, sqlalchemy.orm.Mapper) or isinstance(x, sqlalchemy.BoundMetaData):
                    i+=1
                    #print x
            print 'gc/sqlalc', i

    def query( me, session, expects, idname ='id'):
        if config.debug:
            print 'items:'
            for item in expects:
                print item['exp_single']
        if config.dump:
            print 'tables:'
            for item in expects:
                for x in item['table'].select().execute():
                    print item['table'], ':', x
        for item in expects:
            me.query1( session, idname=idname, **item)

    def query1( me, session, idname, klas, table, oid, exp_single, exp_multi):
        if config.session_clear: session.clear()
        #single
        q = session.query( klas).get_by( **{idname: oid})
        me.assertEqual( exp_single, str(q),
                klas.__name__+'.getby_'+idname+'():\n result= %(q)s\n expect= %(exp_single)s' % locals()
            )

        if config.session_clear: session.clear()
        #multiple
        q = session.query( klas).select()
        x = [ str(z) for z in q ]
        x.sort()
        exp_multi.sort()
        me.assertEqual( exp_multi, x,
                klas.__name__+'.select():\n result= %(x)s\n expect= %(exp_multi)s' % locals()
            )

    def run( self, *a, **k):
        for i in range( config.repeat):
            unittest.TestCase.run( self, *a,**k)
            if config.memory: memusage()

help = 'echo dump debug log_sa no_session_clear reuse_db leak memory'
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
