#$Id$
# -*- coding: cp1251 -*-

def mapper_of_query( query):
    #m = getattr( query, 'mapper', None)     #0.4
    #if m is not None: return m
    return query._mapper_zero()  #0.5

def exact_count( query):
    'usable before sa0.5rc4'
    from sqlalchemy.sql import func
    m = mapper_of_query( query)
    #see Query.count()
    return query._col_aggregate( m.primary_key[0],
                lambda x: func.count( func.distinct(x)) )

from sqlalchemy.orm.properties import PropertyLoader
_RelComparator = PropertyLoader.Comparator
class RelComparator( _RelComparator):
    '''this make .contains serve as .eq for *2many vs single arg; i.e. these are all valid:
    q.filter( A.x == 5).filter( A.ptrB == B1 ).filter( A.collectionB == B1) (last one uses contains)
    q.filter_by( x = 5).filter_by( ptrB = B1 ).filter_by( collectionB = B1) (last one uses contains)
    q.filter_by( x = 5, ptrB = B1, collectionB = B1) (last one uses contains)
    '''
    def __eq__( me, other):
        if other is not None and me.prop.uselist and not hasattr( other, '__iter__'):
            if me.prop.secondary:   #many2many only!
                return me.contains( other)
        return _RelComparator.__eq__( me, other)
    def __ne__( me, other):
        if other is not None and me.prop.uselist and not hasattr( other, '__iter__'):
            if me.prop.secondary:   #many2many only!
                return ~me.contains( other)
        return _RelComparator.__ne__( me, other)
    def has( me, *a,**k):
        if me.prop.uselist:
            if me.prop.secondary:   #many2many only!
                return me.any( *a,**k)
        return _RelComparator.has( me, *a,**k)

    @classmethod
    def setup_rel2many_is2contains_has2any( klas):
        PropertyLoader.Comparator = klas


from sqlalchemy.orm.query import Query as _saQuery
class QueryX( _saQuery):
    count = exact_count
    class config:
        func2expr = True
    def _filterX( me, *a,**k): return _saQuery.filter( me, *a,**k)
    def filter( me, *args):
        '''and() all args as expressions - like filter_by: q.filter( A.x >= 5, A.ptrB == B1)'''
        return expr2filter( me, filter_method_name= '_filterX',
                func2expr= me.config.func2expr, *args)

    def filter_by_subattr( me, _subattr, **kargs):
        ''' A.query().filter( A.b.has( cod= b1.cod)).filter( A.c.has( cod= c1.cod))
         == A.query().join( A.b).filter_by( cod= b1.cod).join( A.c).filter_by( cod= c1.cod))
         -> A.query().filter_by_subattr( 'cod', b=b1, c=c1)
        used for hiding .obj_id, similar to .dbid being hidden in A.ptrB == b1, e.g.
           Pozicia.query( lambda self: self.firma.obj_id == f1.obj_id)
        -> Pozicia.query().filter_by_obj_id( firma = f1)
        '''
        r = me
        for k,v in kargs.iteritems():
            r = r.join( k.split('.'))
            r = _saQuery.filter_by( r, **{ _subattr: getattr(v,_subattr) })
        return r

    def filter_by( me, **kargs):
        ''' A.query().filter_by( x=4, **{'b.c.d':5, ...}) '''
        r = me
        for k,v in kargs.iteritems():
            attrs = k.split('.')
            if attrs[:-1]:
                r = r.join( attrs[:-1])
            r = _saQuery.filter_by( r, **{ attrs[-1]:v})
        return r

    @classmethod
    def setup_kargs4session( klas,
            count2exact_distinct =True,         #usable before sa0.5rc4
            filter_by2multilevel_join =True,
            func2expr   =True,      # lambda self: (self.a.b.c >= 5) | (self.x == 3)
            filter_ands_args =True,
        ):
        QueryX = klas
        if not count2exact_distinct: del QueryX.count
        if not filter_by2multilevel_join: del QueryX.filter_by
        if not filter_ands_args: del QueryX.filter
        QueryX.config.func2expr= func2expr
        kargs = dict( query_cls = QueryX )
        return kargs


################### dbcook-dependent:
####expression2clause:
def prepare_expr( klas, clause):
    'prepare appropriate expression for the clause and bind it with the klas'
    from dbcook import expression
    e = expression.func2expr( clause)
    sae,_klas = expression.expr2clause2( e, klas=klas)       #TODO ПАРАМЕТРИ !!??
    return sae
def expr2filter( query, *args, **kargs):
    filter_method_name = kargs.get('filter_method_name', 'filter')
    func2expr = kargs.get( 'func2expr', True)
    klas = mapper_of_query( query).class_
    res = query
    for expr in args:   #and() them all
        if expr is None: continue
        if func2expr and callable( expr):
            #TODO klas can be query.joinpoint.class
            expr = prepare_expr( klas, expr)
        res = getattr( res, filter_method_name)( expr)
    return res

####rel2many: is->contains; has->any
from dbcook.aboutrel import about_relation
def rel_is_or_contains( klas_attr_or_klas, value, attr_name =None,):
    '''може ли да се прави OR !??x
    може ли да отиде в expression.py вместо join-ite там?
    '''
    if attr_name is None: klas_attr = klas_attr_or_klas
    else: klas_attr = getattr( klas_attr_or_klas, attr_name)
    op = klasattr.__eq__
    try: ab = about_relation( klas_attr)
    except ValueError: pass     #non-rel
    else:
        if ab.thisside.has_many: op = klasattr.contains
    return op( value)
def rel_has_or_anyhas( klas_attr_or_klas, other_attr_name, value, attr_name =None):
    ab = about_relation( klas_attr_or_klas, attr_name)
    klasattr = ab.thisside.attr
    other_attr = getattr( ab.otherside.klas, other_attr_name)
    has = ab.thisside.has_many and klasattr.any or klasattr.has
    return has( other_attr == value)



#############
'''query over multilevel alternatives, i.e. query1 or (query2 and (query3 or query4 ))
3 approaches:
    * alternatives into a clause: query(X).filter( (X.a > 5) | (X.b < 3) & (X.bb.c == 5) )
        + simple, although needs multilevels (a.b.c > 5 i.e. joins) to be expressed as ANDs
        - all tables in the or'red s clauses come into the FROM, causing explosion of decart product
    * alternatives as union:  query(X).select_from( union( query1(X), query2(X) ))
        + each alternative can be of any complexity by itself
        - postgres fails to do count() over these
    * alternatives as python-sequence: x.all() for x in [query1,query2,...]
        + each alternative can be anything
        - global ordering,sorting,grouping etc has to be done

the last approach seems to be fastest in very complex cases,
applied over the 1st level of alternative-branches only (the rest in each branch being plain or()s),
esp. as each branch seemed to have slightly different meaning hence treatment.
union'ing (applied same way - 1st level) is comparable and comes next,
but probably will deteriorate when number of unioned branches grows.
the plain or() goes dead when number of tables exceeds certain threshold (server-dependent).
the number of levels also has some impact but not that bad as number of alternatives.

the challenge is a query over (deep) directed-graph/tree-like structure with alternative paths
across the tree, e.g. get params of all objects under root;
objects are all of a different kind but all having params:
  a
   .b       #ref 0..1
     .y     #ref
   .c       #ref 0..1
     .x
       .y
   .ds      #collection [0..n]
      .y    #ref
      .ds   #...recursive

 A.params
 A.b.params
 A.b.y.params
 A.c.params
 A.c.x.params
 A.c.x.y.params
 A.d*.params
 A.d*.y.params
 A.d*.d*.params
 A.d*.d*.y.params
 ...
add all links being m2m with time-filters for additional taste...
    doesnt change the structure much except that number of tables grows awfully
'''

def or2union( qbase, filters4subqueries, extra_filter_per_query =None):
    'via unioning'
    import sqlalchemy
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

class QueryMulti( object):
    'saQuery-like over py-sequence of queries'
    def __init__( me, queries):
        me.queries = list( queries)
    def count( me):
        if 10:
            return sum( q.count() for q,nm in me.queries)
        s=0
        for q,nm in me.queries:
            c = q.count()
            #print 88888888, nm,c
            s+=c
        return s
    def all( me):
        return list( me)
    def __iter__( me):
        for q,nm in me.queries:
            for o in q:
                yield o
    def __str__( me):
        return '\n'.join( ['QueryMulti:'] + [ '\n >> '+str(nm)+': '+str(q) for q,nm in me.queries ])

class gen_join( object):
    ''' walk the tree/graph and build expression-tree like or( or( and( or(...
        the first level can be left as list or or()red
    .....
    '''
    pass

#################

__all__ = '''QueryX RelComparator
            rel_is_or_contains rel_has_or_anyhas
        '''.split()

# vim:ts=4:sw=4:expandtab
