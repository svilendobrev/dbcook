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


__all__ = '''QueryX RelComparator
            rel_is_or_contains rel_has_or_anyhas
        '''.split()

# vim:ts=4:sw=4:expandtab
