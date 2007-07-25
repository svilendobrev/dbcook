#$Id$
# another autocode.py
# (http://www.sqlalchemy.org/trac/wiki/UsageRecipes/AutoCode)

from sqlalchemy import *


########################################

class AutoLoader:
#    registry = {}

    '''metadata stuff from:
http://sqlzoo.cn/howto/source/z.dir/tip137084/i12meta.xml

sqlite: SELECT * FROM sqlite_master WHERE type='table'
    tables and indexes
pg: SELECT tablename FROM pg_tables WHERE tableowner = current_user
mysql: show tables
    ????????????
ms? SQLserver: SELECT * FROM sysobjects WHERE xtype='U'
    see also sp_table and table sysobjects
access: SELECT Name FROM MSysObjects WHERE Type=1 AND Flags=0
oracle: SELECT * FROM cat
    see also user_tables and user_catalog
sybase: SELECT * FROM sysobjects WHERE type='U'
mimer:  SELECT * FROM information_schema.tables WHERE table_type='BASE TABLE'
db2: SELECT * FROM syscat.tables WHERE tabschema = '<schemaname>'

'''
#######

from sqlalchemy.databases import postgres
class AutoLoader4postgress( AutoLoader):
    coltypes = dict( (v,k) for k,v in postgres.pg2_colspecs.iteritems() )
        #XXX schema-name???
    sql4tables = text( "SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    sql4indexes = text( "SELECT indexname, tablename, indexdef FROM pg_indexes" )
    def __init__( me, db):
        me.table_names = [ (name,None) for (name,) in db.execute( me.sql4tables) ]
        me._indexes = ix = {}
        for name,tbl_name,sqltext in db.execute( me.sql4indexes):
            ix.setdefault( tbl_name, [] ).append( (name,sqltext) )

    def _index_from_def( me, name, sqltext, table):
        #CREATE UNIQUE INDEX name ON "tablename" USING btree (columnslist)
        unique = ' UNIQUE ' in sqltext
        cols = sqltext.split(' (')[1].split(')')[0].split(',')
        cols = [ table.columns[ cname.strip() ] for cname in cols]
        name = name.encode( 'utf-8')
        return Index( name, unique=unique, *cols )

    def indexes( me, table):
        return [ me._index_from_def( name, sqltext, table)
                    for name,sqltext in me._indexes.get( table.name, () )
                ]
postgres.PGDialect.autoloader = AutoLoader4postgress

#######

from sqlalchemy.databases import mssql
class AutoLoader4mssql( AutoLoader):
    coltypes = dict( (v,k) for k,v in mssql.MSSQLDialect.colspecs.iteritems() )
    def __init__( me, db):
        from sqlalchemy.databases import information_schema
        itables = information_schema.tables
        sqltext = select(
                [itables.c.table_name, itables.c.table_schema],
                itables.c.table_schema==dburl.database
            )
        me.table_names = db.execute( sqltext)

    def indexes( me, table): return table.indexes
mssql.MSSQLDialect.autoloader = AutoLoader4mssql

#######

from sqlalchemy.databases import sqlite
class AutoLoader4sqlite( AutoLoader4postgress):
    sqlite_master = '''\
CREATE TABLE sqlite_master (
  type TEXT,
  name TEXT,
  tbl_name TEXT,
  rootpage INTEGER,
  sql TEXT
);'''

    coltypes = dict( (v,k) for k,v in sqlite.colspecs.iteritems() )
    sql4tables  = text( "SELECT name FROM sqlite_master WHERE type='table'")
    sql4indexes = text( "SELECT name,tbl_name,sql FROM sqlite_master WHERE type='index'" )
    #CREATE UNIQUE INDEX name ON "tablename" USING btree (columnslist)

sqlite.SQLiteDialect.autoloader = AutoLoader4sqlite

##################################
#some nice-printing stuff

tab = 4*' '

def textclause_repr( self):
    return 'text( %r)' % self.text

def table_repr( self):
    return 'Table( ' + (',\n'+tab).join( [ '%r, metadata' % self.name ]
                +[ repr(x) for x in self.columns]
                +[ repr(x) for x in self.constraints if not isinstance( x, PrimaryKeyConstraint)]
            ) + '\n)'

def column_repr( self):
    kwarg = []
    if self.key != self.name: kwarg.append( 'key')
    if self._primary_key:   kwarg.append( 'primary_key')
    if not self.nullable:   kwarg.append( 'nullable')
    kwarg2 = []
    if self.onupdate:       kwarg2.append( 'onupdate')
    if self.default:        kwarg2.append( 'default')
    name = self.name
    type = self.type
    lines  = [ 'Column( %(name)r, %(type)r' % locals() ]
    lines += [ repr(x) for x in self.constraints ]
    ks = ', '.join( '%s= %r' % (k, getattr(self, k)) for k in kwarg )
    if ks: lines.append( ks)
    ks = ', '.join( '%s= %r' % (k, getattr(self, k)) for k in kwarg2 )
    if ks: lines.append( ks)
    return (',\n'+2*tab).join( lines) + ' )'

def foreignkeyconstraint_repr( self):
    return 'ForeignKeyConstraint( ' + ', '.join( [
                repr( [x.parent.name for x in self.elements] ),
                repr( [x._get_colspec() for x in self.elements] ),
                'name= ' + repr(self.name)
            ]) + ' )'

def repr_index( index, tvarname):
    name = index.name
    return 'Index( ' + ', '.join( [ repr( index.name) ]
        +[ '%s.c.%s' % (tvarname, c.name) for c in index.columns]
        +[ 'unique= ' + repr(index.unique)]
    ) + ' )'


sql._TextClause.__repr__ = textclause_repr
schema.Table.__repr__ = table_repr
schema.Column.__repr__ = column_repr
schema.ForeignKeyConstraint.__repr__ = foreignkeyconstraint_repr

#########

import sys
try: dburl = sys.argv[1]
except IndexError:
    raise SystemExit, 'usage: '+sys.argv[0]+ ' dburl'

dburl = engine.url.make_url( dburl)
db = create_engine( dburl)
try:
    autoloader = db.dialect.__class__.autoloader
except AttributeError:
    assert 0, 'unsupported db.dialect:'+str( db.dialect)

autoloader = autoloader( db)
#print '\n'.join( str(s) for s in autoloader.table_names )

print '''\
from sqlalchemy import *
metadata = MetaData()
'''

metadata = BoundMetaData( db)
for tname,schema in autoloader.table_names:
    tname = tname.encode( 'utf-8')
    table = Table( tname, metadata, schema=schema, autoload=True)
    for c in table.columns:
        c.type = autoloader.coltypes[ c.type.__class__ ]()

    print tname, '=', repr(table)

    pindexes = '\n'.join( repr_index( index, tname)
                        for index in autoloader.indexes( table) )
    if pindexes: print pindexes
    print

# vim:ts=4:sw=4:expandtab
