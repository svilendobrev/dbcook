#$Id$

import sqlalchemy
sql = sqlalchemy.sql

def polymorphic_union( table_map, typecolname, aliasname ='pu',
            allow_empty_typecolname =True,
            dont_alias_selects  =False,
        ):
    '''create a UNION ALL statement used by a polymorphic mapper.
    typecolname is used only if not present in some (concrete) table:
        - not used for "all only joined_table" - all have own typecolnames
        - always used for "all only concrete-table" - all have no typecolnames
        - in mixed cases, used for the concrete-tables only
    !!! assumes all typecolnames are same and equal to typecolname; no way to check...
        - pre v0.3.4: needs correlate=False for non-join() cases (tables/selects)
    '''
    if not allow_empty_typecolname:
        assert typecolname

    colnames = sqlalchemy.util.Set()
    colnamemaps = {}
    types = {}
    for key in table_map.keys():
        table = table_map[key]

        # mysql doesnt like selecting from a select; make it an alias of the select
        if isinstance(table, sql.Select):
            if not dont_alias_selects: table = table.alias()
            table_map[key] = table
        m = {}
        for c in table.c:
            colnames.add(c.name)
            m[c.name] = c       #for primary-key of joined-inhs in v0.4, this can be replaced with root one???
            types[c.name] = c.type
        colnamemaps[table] = m

    result = []
    for ctype, table in table_map.iteritems():
        sel = []
        typecol_as = typecolname and sql.literal_column("'%s'" % ctype).label( typecolname)
        for name in colnames:
            try:
                c = colnamemaps[ table ][ name]
            except KeyError:
                if name == typecolname:
                    c = typecol_as  #on same (proper) place - order DOES matter; don't append below
                else:
                    c = sql.cast( sql.null(), types[ name] ).label( name)
            sel.append( c)

        if typecolname: #else assume ALL are joined_table!
            if typecolname not in colnames:
                #assert typecolname  #if typecolname is not None and typecolname not in colnamemaps[ table]:
                sel.append( typecol_as )
#        r = sql.select( sel, from_obj=[table])
#$        print 'zzz', ctype, table, r
        result.append( sql.select( sel, from_obj=[table]))
#    print 'aaaaaaaa', ',\n'.join( str(s) for s in result)
    return sql.union_all(*result).alias(aliasname)

# vim:ts=4:sw=4:expandtab
