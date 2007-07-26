#$Id$
#sdobrev

import sqlalchemy

########################################
def plain( name): return name.encode( 'utf-8')

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
    def indexes( me, table):
        raise NotImplementedError
        return indexes-of-the-table

    def metadata( me, engine =None):
        engine = engine or me.engine
        metadata = sqlalchemy.BoundMetaData( engine)
        for tname,schema in me.table_names:
            tname = plain( tname)
            table = sqlalchemy.Table( tname, metadata, schema= schema, autoload= True)
            table.name = tname  #this gets screwed up again - autoload?

            #convert types back to abstract
            for c in table.columns:
                # try engine.dialect.type_descriptor( type) - no
                #     sqlalchemy.types.adapt_type( c.type, me.coltypes ) - no
                c.type = c.type.adapt( me.coltypes[ c.type.__class__] )
                c.name = plain( c.name)

            for c in table.constraints:
                if c.name: c.name = plain( c.name)

            table.indexes = me.indexes( table)
        return metadata

#######

from sqlalchemy.databases import postgres
class AutoLoader4postgress( AutoLoader):
    coltypes = dict( (v,k) for k,v in postgres.pg2_colspecs.iteritems() )
        #XXX schema-name???
    sql4tables  = sqlalchemy.text( "SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    sql4indexes = sqlalchemy.text( "SELECT indexname, tablename, indexdef FROM pg_indexes" )
    def __init__( me, engine):
        me.engine = engine
        me.table_names = [ (name,None) for (name,) in engine.execute( me.sql4tables) ]
        me._indexes = ix = {}
        for name,tbl_name,sqltext in engine.execute( me.sql4indexes):
            ix.setdefault( tbl_name, [] ).append( (name,sqltext) )

    def _index_from_def( me, name, sqltext, table):
        #CREATE UNIQUE INDEX name ON "tablename" USING btree (columnslist)
        unique = ' UNIQUE ' in sqltext
        cols = sqltext.split(' (')[1].split(')')[0].split(',')
        cols = [ table.columns[ cname.strip() ] for cname in cols]
        name = plain( name)
        return sqlalchemy.Index( name, unique=unique, *cols )

    def indexes( me, table):
        return [ me._index_from_def( name, sqltext, table)
                    for name,sqltext in me._indexes.get( table.name, () )
                ]
postgres.PGDialect.AutoLoader = AutoLoader4postgress

#######

from sqlalchemy.databases import mssql
class AutoLoader4mssql( AutoLoader):
    coltypes = dict( (v,k) for k,v in mssql.MSSQLDialect.colspecs.iteritems() )
    def __init__( me, engine):
        me.engine = engine
        schema = engine.dialect
        #XXX or engine.url? or dialect.descriptor['name']? was dburl.database

        from sqlalchemy.databases import information_schema
        itables = information_schema.tables
        sqltext = select(
                [itables.c.table_name, itables.c.table_schema],
                itables.c.table_schema == schema
            )
        me.table_names = engine.execute( sqltext)

    def indexes( me, table): return table.indexes
mssql.MSSQLDialect.AutoLoader = AutoLoader4mssql

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
    sql4tables  = sqlalchemy.text( "SELECT name FROM sqlite_master WHERE type='table'")
    sql4indexes = sqlalchemy.text( "SELECT name,tbl_name,sql FROM sqlite_master WHERE type='index'" )
sqlite.SQLiteDialect.AutoLoader = AutoLoader4sqlite

#######
# TODO
'''
    Column.default -> reverse to abstract SQLAlchemy
    Column.type    -> reverse to abstract SQLAlchemy - ~done
    Constraints    -> convert string _colspecs to actual columns ?is it needed?
'''

if __name__ == '__main__':

    # yet another autocode.py
    # http://www.sqlalchemy.org/trac/wiki/UsageRecipes/AutoCode

    ########################################
    #some nice-printing stuff

    def tablenamer( tablename): return 'tbl_'+tablename

    tab = 4*' '

    def textclause_repr( self):
        return 'text( %r)' % self.text

    def table_repr( self):
        return 'Table( ' + (',\n'+tab).join( [ '%r, metadata' % self.name ]
                    +[ repr(x) for x in self.columns]
                    +[ repr(x) for x in self.constraints
                                if not isinstance( x, sqlalchemy.PrimaryKeyConstraint)]
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

    if 0:
        def get_colspec( col):
            return '.'.join( [ tablenamer( col.table.name), 'c', col.name ])

        def get_fk_colspec( col):
            '''like Column._get_colspec - actualy,
                this is dialect.reflecttable job, it must not leave strings !!!''' #XXX
            colspec = col._colspec

            if isinstance( colspec, basestring):
                x = colspec.split( '.' )
                if len(x) == 3:
                    schema, tablename, colname = x
                    #ignore schema...
                elif len(x) == 2:
                    tablename, colname = x
                else:
                    raise NotImplementedError, s
            else:
                tablename = colspec.table.name
                colname = colspec.key

            return '.'.join( [ tablenamer( tablename), 'c', colname ])

    def foreignkeyconstraint_repr( self):
        return 'ForeignKeyConstraint( ' + ', '.join( [
#                    '[ '+ ', '.join( get_colspec( x.parent)  for x in self.elements ) + ' ]',
#                    '[ '+ ', '.join( get_fk_colspec(x) for x in self.elements ) + ' ]',
#                    '[ '+ ', '.join( repr( x.parent.name)  for x in self.elements ) + ' ]',
#                    '[ '+ ', '.join( repr(plain(x._get_colspec())) for x in self.elements ) + ' ]',
                    repr( [ x.parent.name for x in self.elements ]),
                    repr( [ plain( x._get_colspec()) for x in self.elements ]),
                    'name= ' + repr(self.name)
                ]) + ' )'

    def repr_index( index, tvarname):
        name = index.name
        return 'Index( ' + ', '.join( [ repr( index.name) ]
            +[ '%s.c.%s' % (tvarname, c.name) for c in index.columns]
            +[ 'unique= ' + repr(index.unique)]
        ) + ' )'


    sqlalchemy.sql._TextClause.__repr__ = textclause_repr
    sqlalchemy.schema.Table.__repr__ = table_repr
    sqlalchemy.schema.Column.__repr__ = column_repr
    sqlalchemy.schema.ForeignKeyConstraint.__repr__ = foreignkeyconstraint_repr

    ########################################

    import sys
    try: dburl = sys.argv[1]
    except IndexError:
        raise SystemExit, 'usage: '+sys.argv[0]+ ' dburl'

#   dburl = sqlalchemy.engine.url.make_url( dburl)
    engine = sqlalchemy.create_engine( dburl)
    try:
        AutoLoader = engine.dialect.__class__.AutoLoader
    except AttributeError:
        assert 0, 'unsupported engine.dialect:'+str( engine.dialect)

    autoloader = AutoLoader( engine)
    #print '\n'.join( str(s) for s in autoloader.table_names )

    print '''\
from sqlalchemy import *
metadata = MetaData()
'''

    metadata = autoloader.metadata()
    for tname,table in metadata.tables.iteritems():
        tvarname = tablenamer( tname)
        print tvarname, '=', repr(table)

        pindexes = '\n'.join( repr_index( index, tvarname) for index in table.indexes )
        if pindexes: print pindexes
        print

    print '''
import sys
try: dburl = sys.argv[1]
except IndexError:
    raise SystemExit, 'usage: '+sys.argv[0]+ ' dburl'

metadata.bind = create_engine( dburl)
metadata.create_all()
'''
# vim:ts=4:sw=4:expandtab
