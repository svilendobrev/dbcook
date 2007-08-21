#$Id$

import autoload, copydata

import sys, sqlalchemy
dbsrc = sys.argv[1]
dbdst = sys.argv[2]

src_engine = sqlalchemy.create_engine( dbsrc)
try:
    AutoLoader = src_engine.dialect.__class__.AutoLoader
except AttributeError:
    assert 0, 'unsupported engine.dialect:'+str( src_engine.dialect)

autoloader = AutoLoader( src_engine)
#print '\n'.join( str(s) for s in autoloader.table_names )

metadata = autoloader.metadata()

dst_engine= sqlalchemy.create_engine( dbdst)
metadata.bind = dst_engine
metadata.create_all()
copydata.copy( metadata,
        src_engine= src_engine,
        dst_engine= dst_engine, #sqlalchemy.create_engine( dbdst)
    )

# vim:ts=4:sw=4:expandtab
