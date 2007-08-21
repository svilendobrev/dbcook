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
    url_args = ''       #override
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

        recreator = dengine.recreate
        if recreate and callable( recreator):
            recreator( ourl)

        if dengine:
            mkargs = dengine.engine_kargs.copy()
            mkargs.update( kargs)

            kk = dengine.connect_args
            if kk:
                kk = kk.copy()
                kk.update( mkargs.get( 'connect_args', () ))
                mkargs[ 'connect_args'] = kk

            uu = dengine.url_args
            if uu:
                sep = ourl.query and '&' or '?'
                url += sep + uu

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
        parms = []
        for url_parm,parm in [ ('host','-h'), ('port','-p'), ('username','-U') ]:  #XXX does the order really matter?
            url_attr = getattr( ourl, url_parm, '')
            if not url_attr: continue
            if not isinstance( url_attr, basestring): url_attr = str(url_attr)
            parms += [ parm, url_attr ]
        parms.append( ourl.database )
        print '<', parms, '>'
        if 'subprocess':
            from subprocess import Popen, PIPE
            try:
                p = Popen( ['dropdb'] + parms, stdout= PIPE )
                output = p.communicate()[0]
            except OSError: pass
            p = Popen( ['createdb'] + parms, stdout= PIPE )
            output = p.communicate()[0]
        else:
            parms_str = ' '.join( parms)
            import os
            try:
                r = os.system( 'dropdb ' + parms_str)
            except OSError: pass
            r = os.system( 'createdb ' + parms_str)

class Dmemory( Dengine):
    url= 'sqlite:///'
    recreate = None

class Dmssql( Dengine):
    url= 'mssql://' +environ.get( 'DB_MSSQL', 'usr:psw@host:port/dbname?text_as_varchar=1')
    #connect_args= dict( text_as_varchar=1)
    #engine_kargs = dict( connect_args= dict( text_as_varchar=1) )
    url_args = 'text_as_varchar=1' #considered only if they are in url - see mssql.py create_connect_args
    def recreate( me, ourl):
        dbname = ourl.database
        host = ourl.host
        port = ourl.port
        user = ourl.username
        pasw = ourl.password
        if 10 * 'pymssql & lunix':
            import pymssql, _mssql  #recomended for lunix
            con = _mssql.connect( '%(host)s:%(port)s' % locals(), user, pasw)
            cur = pymssql.pymssqlCursor( con)
            db_err = pymssql.DatabaseError
        else:   # 'pyodbc & windoze'
            import pyodbc
            another_db_used_to_kill_others = '' # fill it
            #TODO: use MSSQLDialect_pyodbc.make_connect_string()
            con = pyodbc.connect('''\
DRIVER={SQL Server}
SERVER=%(host)s:%(port)s
DATABASE=%(another_db_used_to_kill_others)s
UID=%(user)s
PWD=%(pasw)s'''.replace( '\n',';') % locals())
            cur = con.cursor()
            db_err = pyodbc.DatabaseError
        #print 'cfg DB selected: ', con.select_db( 'probacfg')
        try: cur.execute( 'drop database %(dbname)s;' % locals())
        except db_err: pass
        cur.execute( 'create database %(dbname)s;' % locals())
        con.close()
        #obsolete
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

engines = dict(
    memory  = Dmemory(),
    sqlite  = Dsqlite(),
    postgres= Dpostgres(),
    mssql   = Dmssql(),
)

# vim:ts=4:sw=4:expandtab
