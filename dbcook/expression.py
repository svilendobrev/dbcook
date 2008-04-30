#$Id$
# -*- coding: cp1251 -*-
import sqlalchemy
import sqlalchemy.orm

_debug = 0
_v03 = hasattr( sqlalchemy, 'mapper')
if _v03:
    def base_mapper(m): return m.base_mapper()
    def equivs( parent):
        return parent._get_inherited_column_equivalents()
    def joincopy( c): return c.copy_container()
else:
    def base_mapper(m): return m.base_mapper
    if hasattr( sqlalchemy.orm.Mapper, '_equivalent_columns'):
        def equivs( parent): return parent._equivalent_columns
    elif hasattr( sqlalchemy.orm.Mapper, '_get_equivalent_columns'):
        def equivs( parent): return parent._get_equivalent_columns()
    else:
        def equivs( parent): return getattr( parent, '_Mapper__get_equivalent_columns')()
    def joincopy( c): return c._clone()


from dbcook.util.attr import find_valid_fullname_import

ClauseAdapter = find_valid_fullname_import( '''
    sqlalchemy.sql_util.ClauseAdapter
    sqlalchemy.sql.util.ClauseAdapter
''',1 )

_COMPOUNDexpr = find_valid_fullname_import( '''
    sqlalchemy.sql.expression.ClauseList
    sqlalchemy.sql.ClauseList
    sqlalchemy.sql._CompoundClause
''',1 )

_BinaryExpression = find_valid_fullname_import( '''
    sqlalchemy.sql.expression._BinaryExpression
    sqlalchemy.sql._BinaryExpression
''',1 )

if hasattr( sqlalchemy.sql.expression, '_corresponding_column_or_error'):
    def corresponding_column( tbl, col): return tbl.corresponding_column( col)
else:
    def corresponding_column( tbl, col): return tbl.corresponding_column( col, raiseerr=False)

def prop_get_join( self, parent, primary=True, secondary=True):
    ''' from PropertyLoader.get_join(), no cache, no polymorphic joins '''
    from sqlalchemy.orm import sync

    parent_equivalents = equivs( parent)
    primaryjoin = joincopy( self.primaryjoin)

    if self.secondaryjoin is not None:
        secondaryjoin = joincopy( self.secondaryjoin)
    else:
        secondaryjoin = None

    if 0:   #if this IS needed, it must happen only on first of a self.manager.manager.manager chain
        adapt = None
        if self.direction is sync.ONETOMANY:
            adapt = dict( exclude=self.foreign_keys)
        elif self.direction is sync.MANYTOONE:
            adapt = dict( include=self.foreign_keys)
        elif self.secondaryjoin:
            adapt = dict( exclude=self.foreign_keys)
        if adapt:
            primaryjoin=ClauseAdapter( parent.select_table, equivalents=parent_equivalents,
                            **adapt ).traverse( primaryjoin)

    if secondaryjoin is not None:
        if secondary and not primary:
            j = secondaryjoin
        elif primary and secondary:
            j = primaryjoin & secondaryjoin
        elif primary and not secondary:
            j = primaryjoin
    else:
        j = primaryjoin
    return j


class _OnDemand:
    def __init__( me, self_table):
        me.self_table = self_table
        me.use = 0
    def corresponding_column( me, *a, **k):
        r = me.self_table.corresponding_column( *a, **k)
        me.use += (r is not None)
        return r

def join_via( keys, mapper, must_alias =None):
    '''from Query.join_via, input root mapper, return last mapper/table
        alias and link properly recursive /self-referential joins
    cases:
      - table vs inher-join (parent/child)
      - plain vs polymunion (parent/child)
    '''
    #XXX TODO: add inheritance-joins

    clause = None
    c = None
    self_table = None

    #must be also aliased if explicitly required, e.g. x1.in == x2.out (and x1,x2 both are instances of some X)
    if must_alias:
        self_table = must_alias.table
        if not self_table:
            self_table = base_mapper(mapper).mapped_table.alias()   #? local_table ? select_table?
            must_alias.table = self_table
    else:
        self_table = mapper.select_table

    self_colequivalents = None
    xmappers = set([mapper])        #mapper === parent
    ymappers = set([base_mapper(mapper) ])
    for key in keys:
        prop = mapper.get_property(key)

        c = prop_get_join( prop, mapper)

        forkey = prop.foreign_keys

        parent_table = self_table
        self_table = prop.target
        parent_colequivalents = self_colequivalents
        self_colequivalents = equivs( prop.mapper)

        if _debug:
            print '--prop:', key
            print '  primaryjoin:', prop.primaryjoin
            print '  foreignkeys:', ', '.join( str(s) for s in forkey )
            print '  remote_side:', ', '.join( str(s) for s in prop.remote_side )
            print '>', c

        if prop.mapper in xmappers or base_mapper(prop.mapper) in ymappers:
            self_table = self_table.alias()
            if _debug: print '>>', self_table.name, self_table.oid_column, 'equivs={', '; '.join( str(k)+':'+','.join(str(av) for av in v) for k,v in self_colequivalents.iteritems() )
            o_self_table = _OnDemand( self_table)
            if _debug: print '>>1', c, 'remote_side'
            c= ClauseAdapter(
                o_self_table, include=prop.remote_side, equivalents= self_colequivalents
            ).traverse(c)
            if _debug: print '>>2', c
            if not o_self_table.use:
                if _debug: print '>> foreignkey'
                c= ClauseAdapter(
                    o_self_table, include=forkey, equivalents= self_colequivalents
                ).traverse(c)

            xmappers.add( prop.mapper)
            ymappers.add( base_mapper(prop.mapper) )
        if _debug: print '>>>', c
        if mapper in xmappers or base_mapper(mapper) in ymappers:
            if parent_table:
                c= ClauseAdapter(
                    parent_table, include=forkey, equivalents= parent_colequivalents
                ).traverse(c)
        if _debug: print '>>>>', c

        #XXX stefanb
        inh_onclause = getattr( self_table, 'onclause', None)
        if inh_onclause:  #if SA Join must add onclause (i.e. inheritance-join happen)
            c &= inh_onclause

        if clause is None:
            clause = c
        else:
            clause &= c

        mapper = prop.mapper

    return clause, mapper, self_table

'''
C.boza= Alabala.Instance()
C.koza= Alabala.Instance()

a where a.b.c.boza_id=id1 AND a.b.c.koza_id=id2         #алиас=a.b.c; a.b.c.koza.алиас()==id1
    трябва от c надясно
a where a.b.c.boza_id=id1 AND a2.b.c.koza_id=id2        #алиас=автоматично
    A->B->C->Alabala          A2->B->C->Alabala
    трябва от b надясно (т.е. от a което е явно поискано)
a where a.boza_id=id1 OR  a.koza_id=id2     не трябва но не пречи
a where a.b.c.boza_id=id1 AND a.b.c.boza_id=id2
    йок??! трябва да не прави нищо (и съответно да връща нищо)
    ако направи нещо, ще се получи кво???? не се знае, я 2 реда я нищо
    а може би трябва да е WARNING?! уффф абе нека да настъпват...
'''

def get_column_and_joins( name, context4root, must_alias4root ={} ):
    '''name = multilevel a.b.c.d.e
    returns (clause-value, join_clause, is_plain)
    e.g.    (rootvalue,  None, True)            #1 level: x
            (lastcolumn, None, True)            #2 level: x.y
            (lastcolumn, join_clause, False)    #>2 level x.y.z
'''

    path = name.split('.')
    root_name = path[0]
    root_value = context4root[ root_name]

    if len( path)<2:
#       if isinstance( root_value, klas ot mapnatite):
#           return root_value.db_id
        return root_value, None, True
        #eventualy return a bindparam( name=name, type=??...), store the expr and
        #and then use select(expr, params={name=value})
        #see way -f in explanation at bottom

#    if root_value ne e klas ot mapnatite:


    attr_name = path[-1]
    via_names = path[1:-1]
    if 0:
        from sqlalchemy.orm.query import Query
        q = Query( root_value)
        q = q.join( via_names, aliased= must_alias4root.get( root_name,None) )
        print 'AAA', q._joinpoint, q._criterion, q._from_obj

        #needs the query's mapper; for now assume primary
    mapper0 = sqlalchemy.orm.class_mapper( root_value)
    clause, mapper, lasttable = join_via( via_names, mapper0, must_alias= must_alias4root.get( root_name,None) )
#    prop = mapper.props[ attr_name]
    prop = mapper.get_property( attr_name)
    if _debug: print 'cols/joins:', mapper, prop, 'lasttable:', lasttable, 'clause:', clause

        #hope for the first if many...
    if isinstance( prop, sqlalchemy.orm.properties.ColumnProperty):
        lastcol = prop.columns[0]

    elif isinstance( prop, sqlalchemy.orm.properties.PropertyLoader):
        for c in prop.foreign_keys:
            lastcol = c
            break
    else:
        raise NotImplementedError, prop

    if lasttable:   #self-ref   #now always because of must_aliases
        if _debug: print '>>>>?', lastcol, getattr( lasttable,'original',lasttable)#.__class__

        if 0:
            lastcol = lasttable.corresponding_column( lastcol)
        else:   #see PropertyLoader._create_polymorphic_joins in orm/properies.py
            self_colequivalents = equivs( mapper)
            for col in [lastcol] + list( self_colequivalents.get( lastcol, [])):
                #print col, lasttable.__class__
                lc = corresponding_column( lasttable, col)
                #print '*******', col, lc
                if lc:
                    lastcol = lc
                    break
            else:
                assert 0, str(self) + ": Could not find corresponding column for " + str(c) + " in selectable "  + str(self.mapper.select_table)

        if _debug: print '>>>>>', lastcol

    if 0: print 'BBB', lastcol, clause
    return lastcol, clause, False


from dbcook.util import expr
from sqlalchemy import sql

class Translator( expr.Expr.Visitor):
    class SAVisitor( sql.ClauseVisitor):
        def __init__( me, join_clauses):
            me.join_clauses = join_clauses
            me.joins = []

        def gather_joins( me, *clauses):
            for i in clauses:
#                print '>>>>', i
                try:
                    p = me.join_clauses.pop(i)
                except KeyError: pass
                else: me.joins.append( p )
        def visit_binary( me, binary): me.gather_joins( binary.left, binary.right)
        def visit_compound( me, compound): me.gather_joins( *compound.clauses)

    def __init__( me, context, must_alias ={} ):
        me.context = context
        me.must_alias = must_alias
        me.join_clauses = {}

    def var( me, name):
        if _debug: print '?var', name
        lastcol, clause, is_plain= get_column_and_joins( name, me.context, me.must_alias)
            #if is_plain:
            # eventualy return a bindparam( name=name, type=??...), store the expr and
            # and then use select(expr, params={name=value})
            #see way -f in explanation at bottom
        if clause is not None:
            me.join_clauses[ lastcol] = clause
        return lastcol

    def const( me, value):
        if _debug: print '?const', value
        if value is None: return sql.null()
        #XXX TODO must be redone; db_id may not be valid; needs primarykey( value)
        from sqlalchemy.orm import mapperlib
        try:
            mapperlib.object_mapper( value)
        except: pass
        else:
            return value.db_id
        if isinstance( value, (list, tuple)): return value
        return sql.literal( value)

    _ops = {
               'gt'  : '__gt__'     ,
               'lt'  : '__lt__'     ,
               'ge'  : '__ge__'     ,
               'le'  : '__le__'     ,
               'eq'  : '__eq__'     ,
               'ne'  : '__ne__'     ,
               'and' : '__and__'    ,
               'or'  : '__or__'     ,
               'not' : '__invert__' ,
               '+'   : '__add__'    ,
               '-'   : '__sub__'    ,
               '*'   : '__mul__'    ,
               '/'   : '__div__'    ,
               '%'   : '__mod__'    ,
             }

    aggregates = [ 'max', 'min', 'avg', 'sum', 'count' ]

        #? maybe also DESC,ASC,DISTINCT -> now UnaryExpr

    def __call__( me, level, op, *args, **kargs):
        op = me._ops.get( op,op)
        args = list(args)
        obj = args.pop(0)

        if op.startswith( 'M-'):
            op = op[2:]
        elif op.startswith( 'F-') :
            op = op[2:]
            op = op.split('.',1)[1]     #XXX ignoring rootname ???

        #try as method first
        operator = getattr(obj, op, None)
        if operator:
            e = operator(*args, **kargs)
        else:
            #wrap as func
            operator = getattr( sql.func, op)
            if op in me.aggregates:
                raise NotImplementedError, 'aggregate funcs not implemented: '+op
                #not really meaningful - get the rows that have max/min/avg/sum value..
                e = (sql.select( [ operator(obj) ] ) )# == obj)      # label/alias
            else:
                e = operator( obj, *args, **kargs)

        gather_joins = False
        if not level or isinstance(e, _COMPOUNDexpr):
            gather_joins = True
        else:
            if isinstance(e, _BinaryExpression) and e.op in 'AND,OR,NOT,BETWEEN,IS,IS NOT'.split(','):     #maybe also EXISTS -> now Unary...?
                gather_joins=True
        if gather_joins:
            e = me.gather_joins( e)
        if not level: assert not me.join_clauses        #nothing should have left
        return e

    def gather_joins( me, e):
        visitor = me.SAVisitor( me.join_clauses)
        visitor.traverse(e)
        for i in visitor.joins:
            e &= i
        return e


##################

def func2expr( func):
    e = expr.makeExpresion( func)
    return e

class Aliaser( object):
    def __init__(me): me.table = None
    @staticmethod
    def must_alias( context, args):
        #x1=myklas, x2=myklas -> x2 must be x1.alias()
        aliases = {}
        counts = {}
        for k in args:
            try: v = context[k]
            except KeyError: continue
            if v in counts: aliases[k] = Aliaser()
            counts[v] = 1
        return aliases

def expr2clause( e, context_in ={}, binders =[], **kargs4Translator):
    context = e.arg_defaults.copy()
    for binder in binders:
        if callable( binder): binder = binder( e)
        context.update( binder )
    context.update( context_in)
    func=e
    if _debug: print 'context for %(func)s: %(context)s' % locals()
    args = e.arg_names
    missing_args = [a for a in args if a not in context]
    assert not missing_args, '%(func)s(): missing_args %(missing_args)s' % locals()

    extra_args = [a for a in context if a not in args]
    if extra_args: print '%(func)s(): extra_args %(extra_args)s' % locals()

    #x1=myklas, x2=myklas -> x2 must be x1.alias()
    aliases = Aliaser.must_alias( context, args)

    ev = Translator( context, must_alias=aliases, **kargs4Translator)
    sae = e.walk( ev)
    return sae


def context_binder_self2klas( e, klas =None):
    '''replace all args named self* with klas '''
    context4klasi = dict( (k,e.arg_defaults.get( k,klas))
                            for k in e.arg_names if k.startswith( 'self'))
    return context4klasi

class classdecl:
    def __init__( me, klas =None): me.klas = klas

def context_binder_classdecl( e, namespace4klasi ={}):
    '''replace/ resolve classdecl(X)/ classdecl('X') with X '''
    context4klasi = {}
    for k,v in e.arg_defaults.iteritems():
        if isinstance( v, classdecl):
            klas = v.klas
            if isinstance( klas, str): klas = namespace4klasi[ klas]
            context4klasi[ k] = klas
    return context4klasi

###############


def query1( func, **kargs):
    e = func2expr( func)
    return query2( e, **kargs)

def expr2clause2( e, context_in ={}, klas =None, namespace4klasi =None, **kargs ):
    binders = []
    if klas:
        binders.append( context_binder_self2klas( e, klas) )

    if namespace4klasi:
        context4klasi = context_binder_classdecl( e, namespace4klasi )
        if not klas:    #pick first classdecl for a klas
            for a in e.arg_names:
                try:
                    klas = context4klasi[ a]
                    break
                except KeyError: pass
            assert klas
        binders.append( context4klasi )
    sae = expr2clause( e, context_in, binders)
    if _debug: print 'expr2clause:', sae
    return sae, klas

def query2( e, context_in ={}, klas =None, namespace4klasi =None, **kargs ):
    sae, klas = expr2clause2( e, context_in, klas, namespace4klasi, **kargs)
    return query3( sae, klas, **kargs)

def query3( sae, klas, session =None):
    return session.query( klas).filter( sae)

#from dbcook.util.expr import GluerAnd
#Gluer GlueAnd GlueOR

__all__ = '''
func2expr expr2clause2
query1 query2 query3
'''.split()


if 0:
    '''expr.translating:
    -a py-func -> makeExpresion -> expr
    -b expr -> walk( Translator( context) ) -> SA column expression
        context needs plain vars, and vars-classes/mappers
    -c context binding: classes / mappers
    -d context binding: plain vars
    -e apply column-expression as select over a query
    -f sql.bindparams

    way0: all everytime: a c, d,b,e,sql - no bindparams whatsoever
    way1: a c, store; then d,b,e,sql - no bindparams whatsoever
    way2: a b c, store; then d/bindparams, e,sql    #query.select() does execute! so this step is gone
    way3: a b c, e, store; then d/bindparams, sql
    way4: a b c, e, sql, store; then d/bindparams

    0# def func( xklas,a (default args/classes)): return x.y.z == a
    a# expr = makeExpresion( func)
    b# expr.classes = ...
    evaluator = Translator( context)
    c,d1# saexpr = expr.walk( evaluator)
    d2# saexpr.reeval( context/params)
    e# session.query( clas/mapper).select( saexpr)

    results = session.query( klas).select( expr.walk( Translator( context_Vars, context_classes
    '''



    class Query:
        def __init__( me, func):
            me.expr = expr.makeExpresion( func)
        def __call__( me, session, *args, **kargs4context):
            return query( me.expr, session, args, kargs4context)

    #class meta - _new_(meta,myname,dict,...) обикаля dict и за всяко query
    # замества classdecl() и classdecl(myname) в query.default_args със myclass,
    # т.е. получава се свързан метод

    #plain unboundable - no classes can be assumed
    def less_than( a, b): return b.num < a

    #"boundable" unbound method - self_x will be assumed (the) class of some smart-enough wrapper
    def less_than( a, self_x =classdecl()): return self_x.num < a

    class X:
        @Query #use the containing class, that is self_x=X
        def all_less_than1( a, self_x =classdecl()   ): return self_x.num < a
        @Query #use the specified default class, that is self_x=X
        def all_less_than2( a, self_x =classdecl('X')): return self_x.num < a
        @Query #reuse another method, eventualy changing defaults
        def all_less_than3( a, self_x =classdecl('X')): return less_than( a,self_x)
        #@query #reuse another method, only changing defaults
        all_less_than4 = redefault( less_than, self_x =classdecl('X'))
        @Query #use the specified default class, that is self_x=X
        def all_less_than5( a, self_x =classdecl('Y')): return self_x.num < a
        address = struct('Y')

    class Y:
        #x = relation1to1(X)
        @query  #multilevel references
        def all_x_odd( a, self_y =classdecl() ): return self_y.x.num % 1



# vim:ts=4:sw=4:expandtab
