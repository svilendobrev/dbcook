#$Id$
# -*- coding: cp1251 -*-

from sqlalchemy import schema
from dbcook.util.attr import find_valid_fullname_import
sql_util = find_valid_fullname_import( '''
    sqlalchemy.sql_util
    sqlalchemy.sql.util
''')#this order!
print sql_util
def fix_table_circular_deps( tablelist, dbg =0, **kargs):
    if dbg: print 'fix_table_circular_dependencies...'

    def traverse( visitor, obj):
        try: f = visitor.traverse
        except: return obj.accept_schema_visitor( visitor)
        else: return f( obj)

    alltbl = sql_util.TableCollection( tablelist)
    tuples = []
    fkeys = {}
    inheritances = set()
    class TVisitor( schema.SchemaVisitor):
        def visit_foreign_key( _self, fkey):
            if fkey.use_alter:
                return
            #the fk is in the child; child points/references to parent;
            parent_table = fkey.column.table
            if parent_table in alltbl:
                child_table = fkey.parent.table
                #pointed, pointing
                tt = ( parent_table, child_table )
                tuples.append( tt)
                fkeys.setdefault( tt,[]).append( fkey)
                if fkey.column.primary_key and fkey.parent.primary_key:
                    inheritances.add( tt)
            else:
                import warnings
                warnings.warn( 'foreign_key.column.table (parent) "%(parent_table)s" not in all_tables' % locals() )

    vis = TVisitor()
    for table in alltbl.tables:
        traverse( vis, table)

    if dbg>1: print ' graph:', [ '%s:%s' % t for t in tuples]
    if dbg>1: print ' inheritances(uncuttable):', [ '%s:%s' % s for s in inheritances]

    result_fkeys = []

    from kjmincut import Amin
    a = Amin( tuples,
            uncutables=inheritances,
            **kargs)
    if not a.cut:
        if dbg>1: print ' cut: no need'
    else:
        if dbg>1: print ' cut:', [ '%s:%s' % t for t in a.cut ], a.cost
        for tt in a.cut:
            for fkey in fkeys[ tt]:
                fkey.use_alter = True
                fkey.name = fkey.parent.name + '_fk'
                con = fkey.constraint
                if con:
                    con.use_alter = True
                    con.name = fkey.name

                if dbg: print '  use_alter on table', fkey.parent.table.name, fkey.name, '=', fkey
                result_fkeys.append( fkey)
    return result_fkeys

# vim:ts=4:sw=4:expandtab
