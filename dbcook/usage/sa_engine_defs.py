#$Id$
# -*- coding: cp1251 -*-
'''descriptions of various db-drivers/engines:
    - db recreation,
    - default driver-kargs/ connect_args,
    - default url - may come via environment as $DB_<DRIVERNAME>, omit the drivername:// prefix
      e.g. export DB_SQLITE=/myfile
'''

import sqlalchemy
from os import environ

class Dengine:
    url = None          #override
    engine_kargs = {}   #override
    connect_args = {}   #override
    recreate = None     #override as method

    @staticmethod
    def setup( db_type_or_dburl =None, recreate =False, **kargs):
        '''if engine-type given, get its Dengine and default url;
            else get Dengine for engine-type from dburl;
            do recreate if requested;
            merge kargs with default engine_kargs/connect_args;
            will not complain in any case
        '''
        url = db_type_or_dburl or 'memory'
        dengine = engines.get( url, None)
        if not dengine:
            ourl = sqlalchemy.engine.url.make_url( url)
            dengine = engines.get( ourl.drivername, None)
        else:
            url = dengine.url
            ourl = sqlalchemy.engine.url.make_url( url)

        recreator = getattr( dengine, 'recreate', None)
        if recreate and callable( recreator):
            recreator( ourl)

        if dengine:
            mkargs = dengine.engine_kargs.copy()
            mkargs.update( kargs)

            kk = dengine.connect_args
            if kk:
                kk.update( mkargs.get( 'connect_args', () ))
                mkargs[ 'connect_args'] = kk
        return url, mkargs

class Dsqlite( Dengine):
    url= 'sqlite://'  +environ.get( 'DB_SQLITE',   '/proba1.db')
    def recreate( me, ourl):
        filename = ourl.database
        if filename and filename != ':memory:':
            import os
            try: os.remove( filename)
            except OSError: pass

class Dpostgres( Dengine):
    url= 'postgres://'+environ.get( 'DB_POSTGRES', '/proba')
    engine_kargs = dict( max_overflow= -1)  #echo_pool= echo_pool,
    def recreate( me, ourl):
        if ourl.host and ourl.host != 'localhost':
            print 'cannot recreate via url, DIY'
        else:
            import os
            try:
                r = os.system( 'dropdb '   + ourl.database)
                r = os.system( 'createdb ' + ourl.database)
            except OSError: pass

class Dmemory( Dengine):
    url= 'sqlite:///'
    recreate = None

class Dmssql( Dengine):
    url= 'mssql://' +environ.get( 'DB_MSSQL', 'usr:psw@host:port/dbname?text_as_varchar=1')
    connect_args= dict( text_as_varchar=1)
    #engine_kargs = dict( connect_args= dict( text_as_varchar=1) )
    def recreate( me, ourl):
        dbname = ourl.database
        host = ourl.host
        port = ourl.port
        user = ourl.username
        pasw = ourl.password
        if 0*'pyodbc & lunix': # not recomended in this combination
            another_db_used_to_kill_others = 'probacfg'
            cmd = 'isql %(another_db_used_to_kill_others)s %(user)s (%pasw)s' % locals()
                #XXX user/pasw above maybe different than dbname's!!!
            stdin = '''\
drop database %(dbname)s;
create database %(dbname)s;
''' % locals()
            try:
                if 'subprocess':
                    from subprocess import Popen, PIPE
                    p = Popen( cmd.split(), stdin= PIPE, stdout= PIPE )
                    output = p.communicate( stdin)[0]
                else:
                    import os
                    r = os.system( 'echo -e "'+stdin.replace('\n','\\n')+ '" | %(cmd)s' % locals() )
            except OSError: pass
        else:
            import pymssql, _mssql  #recomended for lunix
            con = _mssql.connect( '%(host)s:%(port)s' % locals(), user, pasw)
            #print 'cfg DB selected: ', con.select_db( 'probacfg')
            cur = pymssql.pymssqlCursor( con)
            try: cur.execute( 'drop database %(dbname)s;' % locals())
            except pymssql.DatabaseError: pass
            cur.execute( 'create database %(dbname)s;' % locals())
            con.close()

engines = dict(
    memory  = Dmemory(),
    sqlite  = Dsqlite(),
    postgres= Dpostgres(),
    mssql   = Dmssql(),
)

# vim:ts=4:sw=4:expandtab
