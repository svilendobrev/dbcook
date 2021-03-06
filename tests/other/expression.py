#$Id$
# -*- coding: utf8 -*-

import dbcook.config
dbcook.config.table_namer = lambda klas: klas.__name__.lower()

from tests.util.context import *

if USE_STATIC_TYPE:
    Base.auto_set = False
    from dbcook import builder
    def _str( me): return Builder.reflector.obj2str( me, Base, builder.column4ID.name)
    if 'one-line-str':
        Base.__str__ = Base.__repr__ = _str

ONLY1 = False

#############

##############  model-definition
from svd_util.attr import get_attrib

def model(  address_inh ='', #'','c','j'
            person_inh  ='',
            person_ref_person =True, #elif inheriting, refs human
        ):

    class Home( Base):
        num = Int()

    class Addr0( Base):
        DBCOOK_no_mapping = not address_inh
        @property
        def name( me):
            home = str( get_attrib( me, 'home.num', 'none'))
            return str( getattr( me, 'street','none')) +'#'+ home
        street = Text()
        home = Reference( Home)

    class Adres( Addr0):
        if address_inh: DBCOOK_inheritance = address_inh
        kvartal = Text()
        owner = Reference( 'Person')
    class Adres2( Addr0):
        if address_inh: DBCOOK_inheritance = address_inh
        dupka = Int()

    class Human( Base):
        DBCOOK_no_mapping = person_inh != 'j'
        DBCOOK_has_instances = 1
        name    = Text()
        age     = Int()
        friend  = Reference( (person_ref_person or DBCOOK_no_mapping) and 'Person' or 'Human')

    class Person( Human):
        if person_inh: DBCOOK_inheritance = person_inh
        alias   = Text()
        adr = Reference( Adres)
        adr2= Reference( Adres2)

        def __eq__( me, other):     #for person.friend == otherperson
            if other is None: return False
            if isinstance( other, Base): return me.db_id == other.db_id
            if isinstance( other, int):  return me.db_id == other
            raise NotImplementedError, `other`

    def populate():
        pen4os = [
            ('pesho',  12, 'str.1',        11),
            ('mesho',  34, 'str.unnamed',  22),
            ('gosho',  56, 'str.22',       33),
            ('mosho',  78, 'str.34',       44),
            ('pencho', 87, 'str.foo',      55),
            ('mencho', 65, 'mencho.bza',   66),
            ('dencho', 66, None,      66),
        ]

        r = {}
        nn=0
        for i in pen4os:
            person = Person()
            person.name, person.age, street, homenum = i
            if street:
                person.adr          = Adres()
                person.adr.street   = street
                person.adr.kvartal  = street.replace('str', 'kv')
                person.adr.home     = Home()
                person.adr.home.num = homenum
                person.adr.owner = r.get( 'pesho')
                if person.name == 'pesho':
                    person.adr2     = Adres2()
                    person.adr2.dupka  = 1
                    person.adr2.street = 'dupka'
            person.alias = (person.age % 2) and person.name + 'ali' or 'b-'+person.name
            aa = nn% 5
            if aa==0: person.friend = person            #self
            if aa==1: person.friend = r[ 'pesho' ]
            if aa==2: person.friend = r[ 'mesho' ]
            if aa==3: person.friend = r[ 'gosho' ]
    #           if aa !=2 and person.name.startswith('g'): person.friend.friend = r[ 'pesho' ]
            r[ person.name ] = person
            nn+=1
        return r
    return locals()

def tests( person_pesho, do_friend_adr =True):
    # XXX XXX XXX XXX
    # be careful with possible NULLs - anyop(NULL) is NUL except true | NUL, false & NUL; bool(NUL) is False;
    # http://firebird.sourceforge.net/manual/nullguide-dealing-with-nulls.html
    # XXX XXX XXX XXX

    do_plain  = 1
    do_nested = 1
    do_method = 1
    do_funcs  = 1
    do_recursive = 1
    do_rec_plain = 1
    do_rec_ideq  = 1

    plains = do_plain * [
    ####plain
    #1level
        lambda person: (person.name == 'pesho'),    #simple value eq
        lambda person: (person.name != 'pesho'),    #simple value neq
        lambda person: (person.name != ''),         #simple value neq/''
        lambda person: (person.name != None),       #simple value neq/NULL
        lambda person: ( (person.name == 'pencho') & (person.age == 33) ),  #and of 2 simple eq
        lambda person: ( (person.name == 'pencho') | (person.age == 34) ),  #or  of 2 simple eq
        lambda person: ( (person.age > 45) & (person.name != 'mencho') & (person.age < 80) ),   #and of 3 value comparisons
    #same klas/table multiple times, needs aliasing
        [ 0*'ONLY1', lambda person, person2: (person.name == 'pesho') & (person2.name == 'gosho'), ],
        #used as func( self1, self2) or func( p1=klas, p2=klas )
    #multilevel
        lambda person: (person.adr.street == 'str.22'), #value eq
        lambda person: (person.adr.street == None),     #value eq NULL
        lambda person: (person.adr.street != None),     #value neq NULL
        lambda person: (person.adr.home.num == 33),
        lambda person: (person.adr.kvartal == 'kv.22'), #value eq

        lambda person: (person.adr == None),        #the reference itself; property

        lambda person: (
               (  (person.adr.home.num > 20)
                & (person.adr.home.num < 70)
                | (person.adr.street != 'str.22')
               )
               & (person.adr.kvartal >='kv.17')
           ),

    #similar to same klas/table multiple times - different inh-joins via same table, needs internal aliasing
        #XXX TODO [0*'ONLY1', lambda person: (person.adr.street == 'str.1') & ( person.adr2.street == 'dupka'), ],

        #these must raise
        #[AttributeError,    lambda person: (alabala > 45) ],
        [sqlalchemy.exceptions.InvalidRequestError, lambda person: (person.alabala > 45) ],

    ] + do_nested* [
     #nested no joins
        lambda person: (person.name + 'o') == 'peshoo',
        lambda person: ('p' + person.name ) == 'ppesho',

     #nested with joins
        lambda person: ((person.adr.street + 'o') == 'str.1o'),
    ] + do_recursive *(
        do_rec_plain * [
     #multilevel self-referential/recursive
        lambda person: (person.friend != None),
        lambda person: (person.friend.age >35),
        lambda person: (person.friend.age >35),
        lambda person: (person.friend.name == 'pesho'),
        lambda person: (person.friend.friend.friend.name == 'pesho'),
    ] + do_friend_adr * [
        lambda person: (person.friend.adr.street == 'str.22'),
        lambda person: (person.friend.adr.owner.friend.name == 'pesho'),
    ] + do_rec_ideq * [
     #db_id comparison - precalculated ("const")
        lambda person : (person.friend.db_id == 2),         #ok
        lambda person : (person.friend.db_id == p2.db_id),  #ok
        lambda person : (person.friend == p2),              #means "is"; needs op.__eq @python-test
        lambda person : (person.friend == p2.db_id),        #same as above; fails @python
    ] )

    funcs = do_funcs * [
     #plain func
        lambda person, f: f.substr( person.name, 4,1) == 'h',
     #method-operator-func
        lambda person, f: f.like( person.name, '%sho'),
        lambda person, f: f.like( person.alias, person.name+'%'),
        lambda person, f: f.like( person.adr.street, person.name+'%'),
    ] + do_method *[ #needs fix/hack in SA
     #method-func
        lambda person, f: f.startswith( person.name, 'pe'),
        lambda person, f: f.endswith( person.name, 'sho'),
        lambda person, f: f.startswith( person.alias, person.name),
        lambda person, f: f.endswith( person.adr.street, 'o' ),

        lambda person, f: f.in_( person.name,  ['pesho', 'mencho'] ),
        lambda person, f: f.in_( person.alias, ['peshoali', 'b-'+person.name] ),
    ] + do_funcs * [
        lambda person, f: (f.between( person.age, 10, 45) & f.like( person.adr.street, 'str%')),
    ] + do_method * [
        lambda person: person.name.endswith( 'sho'),
    ] + do_nested * do_method * [
     #nested + method
        lambda person, f: f.endswith( person.name+ 'o', 'oo' ),
        lambda person, f: f.endswith( person.adr.street + 'o', 'oo' ),
     #method off nested
        #lambda person: (person.adr.street + 'o').endswith('oo'),   #does not work
    ]
    ''' missing cases:
        * filter on X where other table pointing to X
            db.query( Node, lambda self,e =Link: return ( e.node_o == self.db_id ) & (e.node_i == node) )
            -> use Node's selectable ONCE - polymorphic or not - proper corresponding_column

        * filter needing multiple levels of X (aliases):
            def qy( e =Link, e1 =Link, e2 =Link):
                return (
                  ( e.node_i == node_i) & (
                         (e.node_o ==   node_o)                  # o-u
                      | ((e.node_o == e1.node_i) & (e1.node_o ==   node_o))  # o-*-u
                      | ((e.node_o == e1.node_i) & (e1.node_o == e2.node_i) & (e2.node_o ==   node_o))  # o-*-*-u
                    ) )
            return DB.query( Link, qy)
    '''

    aggregates = [  #no way, forget about these - any joins should go in the FROM?
        lambda person, faggr: faggr.max( person.age),                   #?? the max value itself
        lambda person, faggr: faggr.max( person.age) == person.age,     #?? rows of max value
        lambda person, faggr: faggr.max( person.age-9) == person.age,   #?? what this means
        lambda person, faggr: faggr.max( person.age)-9 == person.age,   #?? what this means
        lambda person, faggr: faggr.max( person.adr.home.num) == person.age,   #??
    ]
    orders = [  #similar thing - any joins should go in the FROM?
        lambda person, forder: forder.asc( person.age),                 #no joins!
        lambda person, forder: forder.asc( person.adr.home.num),    #no joins!
    ]

    allfuncs = plains + funcs #+ 0*aggregates
    return allfuncs


#helper namespace for the plain eval()
class metaFuncs2static( type):
    def __new__( meta, name, bases, adict):
        for k,v in adict.iteritems():
            if callable(v):
                adict[k] = staticmethod(v)
        return type.__new__( meta, name, bases, adict)

class Funcs:
    __metaclass__ = metaFuncs2static
    def endswith( a,b):   return a.endswith( b)
    def startswith( a,b): return a.startswith( b)

    def like( a,b):
        c = b.count('%')
        if not c: return a==b
        if c==1:
            if b.endswith('%'): return a.startswith( b[:-1])
            if b.startswith('%'): return a.endswith( b[1:])
        raise NotImplementedError, 'like '+b

    def between( a,b,c): return b<=a<=c

    def substr( a, start, sz):
        start-=1
        return a[start:start+sz]

    def sin( a):
        import math
        return math.sin(a)

    #def in_(*args, **kargs): return args[0] in args[1:]
    def in_(*args, **kargs):
        #print 'iiiiiin', args, args[0] in set(args[1])
        return args[0] in set(args[1])  #x in list  does x==element for each element..

    def asc(*args, **kargs):
        return 'asc/'+str(args)



if 0:
    class Maxer:    #this is only for the testing...
        def __init__( me, func):
            me.all = []
            me.func = func
            me.value = None
        def __call__( me, v):
            value = me.value
            if value is None: me.all.append(v)    #aggrmode
            else: return value
        def calc( me):
            value = me.value = me.func( me.all)
            assert value is not None
            return value
    Funcs.max = Maxer( max)

class AttrWrapError( AttributeError): pass
class AttrWrap:
    def __init__( me, o): me.o = o
    def __getitem__( me, k):
        try:
            return me.o.__dict__[k]
        except KeyError:
            #this to return None ONLY on last .attr; else it's a null
            # inbetween -> error to catch and ignore the whole thing
            kk = k.split('.')
            if len(kk)>1:
                try:
                    g = get_attrib( me.o, '.'.join( kk[:-1]))
                except AttributeError:
                    raise AttrWrapError, k
                if g is None:
                    raise AttrWrapError, k
            else:
                g = me.o
            return getattr( g, kk[-1], None)


######## use model

import sys
#sys.setrecursionlimit( 100)
DBCOOK_inheritance = 'joined' in sys.argv and JOINED or CONCRETE

SAdb.config.getopt()
inhs = ['', CONCRETE, JOINED ]

def combinator():   #no polymorphic
    for person_ref_person in [True, False]:
        for address_inh in inhs:
            for person_inh in inhs:
                if not person_ref_person and not person_inh: continue
                yield dict(
                        person_inh= person_inh,
                        person_ref_person= person_ref_person,
                        address_inh= address_inh
                    )


def strres( q, title):
    sres = [ str(p) for p in q]
    sres.sort()
    sres1 = ('\n'+2*' ').join( [title+':']+sres)
    return sres,sres1

from svd_util.struct import Struct
from dbcook import expression
expression._debug = 'dbg' in sys.argv
dbg = 'what' in sys.argv or expression._debug
one_error = 'one' in sys.argv
expr = expression.expr

x=0
errors = []
for combina in combinator():
    err = []
    print '===', combina
    namespace = model( **combina)
    sa = SAdb()
    sa.open( recreate=True)
    b= sa.bind( namespace, base_klas= Base, print_srcgenerator= 0)
    populate = namespace[ 'populate']
    popu= populate()
    session = sa.session()
    sa.saveall( session, popu)
    session.flush()
    printer = b.generator
    if printer:
        x+=1
        fname = '_t'+str(x)+'.py'
        header =''
        p = printer.testcase( 'test1' )#me.config.funcname + me.str_params( parameters), error ))
        p+= '''
        session = create_session()
        session.save( Person( name= 'pesho') )
        session.flush()
        session.clear()
        p2 = session.query( Person).filter_by( name= 'pesho').first()

        #combina = %(combina)r

    import sys
    sys.setrecursionlimit(100)

''' % locals()
        file( fname, 'w').write( printer._head + header + printer.classdef + p + printer.tail )

    #print ' ----objects:'
    objects = '\n'.join( str(p) for p in popu.itervalues() )
    session.clear()

    #print '-----tables:'
    #sa.query_all_tables()
#    print '======\n'

    Person = namespace['Person']
    Human  = namespace['Human']
    p2 = session.query( Person).filter_by( name= 'pesho').first()
    #print p2
    #session.clear()

    allfuncs = tests( p2,
        do_friend_adr = (combina['person_ref_person'] or not combina['person_inh'] )
    )

    try:
        n = 0
        for func in allfuncs:
            #print '\n---------'
            expected_err = None
            if isinstance( func, (tuple,list)):
                expected_err, func = func
            if ONLY1 and expected_err != 'ONLY1': continue
            if expected_err == 'ONLY1': expected_err = None
            n+=1
            e = expr.makeExpresion( func)
            #print e
            etxt = e.walk( expr.as_expr)
            if dbg: print 'expr:', etxt

            if expected_err:
                expected = None
            elif 'faggr' in e.arg_names: # func in Translator.aggregates:
                for p in popu.itervalues():
                    e.walk( expr.Eval( AttrWrap( Struct( person=p, faggr=Funcs))))
                #print Funcs.max.all, Funcs.max.calc()
                print 'expr:', etxt
                print NotImplementedError
                continue

            else:   #filter population by func
                expected = []
                for p in popu.itervalues():
                    p = session.merge(p)
                    ##real python eval
                    import inspect
                    args,vargs,kwargs,defaults = inspect.getargspec( func)
                    #print args, vargs, kwargs
                    f_kargs = {}
                    f_args  = []
                    #print p2.db_id, p.db_id
                    if 'p2' in args: f_kargs['p2'] = p2
                    if 'f'  in args: f_kargs['f'] = Funcs
                    if 'person2' in args:       #decart x product
                        rr = []
                        r = []
                        for pp in popu.itervalues():
                            f_kargs['person2'] = pp
                            #print f_args, f_kargs
                            try:
                                res = bool( func( p, *f_args, **f_kargs))
                            except AttributeError: res = None
                            rr.append( res)
                            ##simulated python eval
                            try:
                                res = bool( e.walk( expr.Eval( AttrWrap(
                                            Struct( person=p, **f_kargs)))) )
                            except AttrWrapError: res = None
                            r.append( res)

                            if res: expected.append(p)
                        #print 'ZZZZZZZ',r
                        assert rr == r, 'pyexec:%(rr)s != pysimeval:%(r)s' % locals()

                    else:
                        #print f_args, f_kargs, p.name
                        #print 'pyexec'
                        try:
                            rr = bool( func( p, *f_args, **f_kargs))
                        except AttributeError: rr = None
                        ##simulated python eval
                        #print 'pysimeval'
                        try:
                            r = bool( e.walk( expr.Eval( AttrWrap(
                                        Struct( person=p, f=Funcs, p2= p2, person2=p2 )))) )
                        except AttrWrapError: r = None

                        assert rr is r, 'pyexec:%(rr)s != pysimeval:%(r)s' % locals()

                        if r: expected.append(p)
            if dbg: print 'expected:', expected
            context = AttrWrap( Struct( person=Person, f=None, p2= p2, person2=Person ))
            eval = expression.Translator( context,
                    must_alias= expression.Aliaser.must_alias( context,
                                'person person2'.split()    #XXX order! same as above for p/for pp loops
                            ) )
            try:
                try:
                    sae = e.walk( eval)
                except expected_err:
                    #print '  got', expected_err
                    continue        #OK

                #print 'querying:', sae

                q = session.query( Human.DBCOOK_no_mapping and Person or Human)

                q = q.filter(sae)
                #print 111111111111111, q
                q = q.all()

                sres,sres1 = strres( q, 'result')
                sexp,sexp1 = strres( expected, 'expect')
                #print sres1
                assert sres==sexp, '\n%(sres1)s \n !=\n%(sexp1)s' % locals()
            except Exception, e:
                print 'expr:', etxt
                import traceback
                exc = traceback.format_exc()# ''.join( traceback.format_exception(inf[0], inf[1], None))
                print '### ERR:', e.__class__, exc
                err.append( (combina, etxt, exc) )
                #TODO: use MultiTester or mix.myTestCase4Function
                if one_error: break
        if not err: print 'OK:', n
        else:
            print 'ERRORS:', len(err), '/', n
            print ' ----objects:\n', objects
        errors += err
    finally:
        sa.destroy()
        pass
    if errors and one_error: break

for e in errors:
    print 40*'=' + '\n' + '\n'.join( str(s) for s in e)


'''
TODO: polymorphic Person / Adres(?)

errors: 27.07.2007
1. address_inh = joined
        -> Addr0.items not visible in Adres, e.g.
    expr: ( var:person.adr.street == 'str.22' ) -> ERR
        трябва да е mapper(adr).prop('street').table, а не mapper(adr).table
    expr: ( var:person.adr.kvartal== 'kv.22' ) -> OK

2
=== {'person_inh': 'concrete_table', 'address_inh': '', 'person_ref_person': False}
=== {'person_inh': 'concrete_table', 'address_inh': 'concrete_table', 'person_ref_person': False}

expr: ( var:person.friend.age > 35 )
expr: ( var:person.friend.name == 'pesho' )
expr: ( var:person.friend.friend.friend.name == 'pesho' )
expr: ( var:person.friend.db_id == 2 )
-> no result:
    ????? невалиден тест - friend -> Human, а му се дава Person - не работи за concrete_table/PM
expr: ( var:person.friend.adr.owner.friend.name == 'pesho' )
-> err: <type 'exceptions.KeyError'> 'adr'
    грешна таблица? friend -> Human а там няма adr

3
=== {'person_inh': 'joined_table', 'address_inh': '', 'person_ref_person': False}
=== {'person_inh': 'joined_table', 'address_inh': 'concrete_table', 'person_ref_person': False}
expr: ( var:person.friend.adr.owner.friend.name == 'pesho' )
err: <type 'exceptions.KeyError'> 'adr'
    грешна таблица? friend -> Human а там няма adr

4
=== {'person_inh': 'concrete_table', 'address_inh': 'joined_table', 'person_ref_person': False}
1+2

5
=== {'person_inh': 'joined_table', 'address_inh': 'joined_table', 'person_ref_person': False}
1+3
'''

# vim:ts=4:sw=4:expandtab
