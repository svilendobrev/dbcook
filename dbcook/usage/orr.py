#$Id$


import sqlalchemy
def or2union( qbase, filters4subqueries, extra_filter_per_query =None):
    uu = []
    for a in filters4subqueries:
        if isinstance( a, tuple): a=a[0]    #HACK for (expr,name)
        ra = qbase.filter( a)
        if extra_filter_per_query is not None:
            ra = ra.filter( extra_filter_per_query )
        if len(filters4subqueries)<=1:
            return ra
        s = ra._compile_context().statement
        s.use_labels = True
        uu.append( s)
    filt = sqlalchemy.union( *uu)
    return qbase.select_from( filt)

# vim:ts=4:sw=4:expandtab
