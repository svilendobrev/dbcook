#$Id$
# uses sa0.4 MetaData.reflect; no indexes there!

import sqlalchemy

########################################
def plain( name): return name.encode( 'utf-8')

class AutoLoader:
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

    #coltypes_sa2db = {}  #sa2db
    coltypes_db2sa = {}   #db2sa - extra to the reverse of above
    def metadata( me, engine =None):
        coltypes = dict( (v,k) for k,v in me.coltypes_sa2db.iteritems() )
        coltypes.update( me.coltypes_db2sa)
        engine = engine or me.engine
        me.metadata = metadata = sqlalchemy.MetaData( engine, reflect=True)
        for table in metadata.table_iterator():
            table.name = plain( table.name)
            #print `table`

            #convert types back to abstract
            for c in table.columns:
                # try engine.dialect.type_descriptor( type) - no
                #     sqlalchemy.types.adapt_type( c.type, coltypes ) - no
                c.type = c.type.adapt( coltypes[ c.type.__class__] )
                c.name = plain( c.name)

            for c in table.constraints:
                if c.name: c.name = plain( c.name)

            table.indexes = me.indexes( table)
        return metadata

#######
from sqlalchemy import types as sqltypes

from sqlalchemy.databases import postgres
class AutoLoader4postgress( AutoLoader):
    coltypes_sa2db = postgres.colspecs
        #XXX schema-name???
    sql4indexes = sqlalchemy.text( "SELECT indexname, tablename, indexdef FROM pg_indexes" )
    def __init__( me, engine):
        me.engine = engine
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
    coltypes_sa2db = mssql.MSSQLDialect.colspecs
    coltypes_db2sa = {
                    mssql.MSTinyInteger: sqltypes.Smallinteger,
                    mssql.MSBigInteger:  sqltypes.Integer,
                }
    def __init__( me, engine):
        me.engine = engine

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

    if hasattr( sqlite, 'pragma_names') and 'BOOLEAN' not in sqlite.pragma_names:    #pre 0.4beta
        sqlite.pragma_names[ 'BOOLEAN' ] = sqlite.SLBoolean

    coltypes_sa2db = sqlite.colspecs
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
        if (getattr( self, '_primary_key', None) or
            getattr( self, 'primary_key', None)
            ):   kwarg.append( 'primary_key')
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

    try:
        _TextClause = sqlalchemy.sql.expression._TextClause
    except AttributeError:
        _TextClause = sqlalchemy.sql._TextClause
    _TextClause.__repr__ = textclause_repr
    sqlalchemy.schema.Table.__repr__ = table_repr
    sqlalchemy.schema.Column.__repr__ = column_repr
    sqlalchemy.schema.ForeignKeyConstraint.__repr__ = foreignkeyconstraint_repr

    ########################################

    import sys
    try: dburl = sys.argv[1]
    except IndexError:
        raise SystemExit, 'usage: '+sys.argv[0]+ ' dburl'

    engine = sqlalchemy.create_engine( dburl)
    try:
        AutoLoader = engine.dialect.__class__.AutoLoader
    except AttributeError:
        assert 0, 'unsupported engine.dialect:'+str( engine.dialect)

    autoloader = AutoLoader( engine)

    print '''\
from sqlalchemy import *
metadata = MetaData()
'''

    metadata = autoloader.metadata()
    for table in metadata.table_iterator():
        tvarname = tablenamer( table.name)
        print tvarname, '=', repr(table)

        pindexes = '\n'.join( repr_index( index, tvarname) for index in table.indexes )
        if pindexes: print pindexes
        print

    print '''
if __name__ == '__main__':
    import sys
    try: dburl = sys.argv[1]
    except IndexError:
        raise SystemExit, 'usage: '+sys.argv[0]+ ' dburl'

    metadata.bind = create_engine( dburl)
    metadata.create_all()
'''
# vim:ts=4:sw=4:expandtab
