#$Id$

def copy( metadata, src_engine, dst_engine, echo =0 ):
    for tbl in metadata.table_iterator( reverse= False):
        if echo: print tbl
        data = [ dict( (col.key, x[ col.name]) for col in tbl.c)
                    for x in src_engine.execute( tbl.select()) ]
        if echo>1:
            for a in data: print a
        if data:
            dst_engine.execute( tbl.insert(), data)

if __name__ == '__main__':
    import sys, sqlalchemy
    arg_model = sys.argv[1]
    model = __import__( arg_model )
    copy( model.metadata,
            src_engine= sqlalchemy.create_engine( sys.argv[2]),
            dst_engine= sqlalchemy.create_engine( sys.argv[3]),
        )

# vim:ts=4:sw=4:expandtab
