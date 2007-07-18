#$Id$
# -*- coding: cp1251 -*-

import dbcook.config
dbcook.config.table_namer = lambda klas: klas.__name__.lower()

from tests.util.context import *
if USE_STATIC_TYPE:
    Base.auto_set = False
    from dbcook import builder
    def _str( me): return Builder.reflector.obj2str( me, Base, builder.column4ID.name)
    if 'one-line-str':
        Base.__str__ = Base.__repr__ = _str


#############

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

    def in_(*args, **kargs): return args[0] in args[1:]

    def asc(*args, **kargs):
        return 'asc/'+str(args)


##############  model-definition
import sys
from dbcook.util.attr import get_attrib

DB_inheritance = 'joined' in sys.argv and 'joined_table' or 'concrete_table'

class Home( Base):
    num = Int()

class Addr0( Base):
    DB_NO_MAPPING = 'addr0' not in sys.argv
    name = property( lambda me: str(getattr( me, 'street','none')) +'#'+str(get_attrib( me, 'home.num', 'none')) )
    street = Text()
    kvartal = Text()
    home = Type4SubStruct( Home)

class Address( Addr0):
    DB_inheritance = DB_inheritance
    street1 = Text()
    home1 = Type4SubStruct( Home)
    owner = Type4SubStruct( 'Person')

class Human( Base):
    DB_NO_MAPPING = 'human' not in sys.argv
    DB_HAS_INSTANCES = 1
    name    = Text()
    age     = Int()
    friend  = Type4SubStruct( DB_NO_MAPPING and 'Person' or 'Human')

class Person( Human):
    DB_inheritance = DB_inheritance
    alias   = Text()
    address = Type4SubStruct( Address)

    def __eq__( me, other):     #for person.friend == otherperson
        if other is None: return False
        if isinstance( other, Base): return me.db_id == other.db_id
        if isinstance( other, int):  return me.db_id == other
        raise NotImplementedError, `other`

######## use it

SAdb.config.getopt()
sa = SAdb()
sa.open( recreate=True)
sa.bind( locals(), base_klas= Base)
session = sa.session()

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
            person.address          = Address()
            person.address.street   = street
            person.address.kvartal  = street.replace('str', 'kv')
            person.address.home     = Home()
            person.address.home.num = homenum
            person.address.owner = r.get( 'pesho')
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

popu= populate()
sa.saveall( session, popu)
session.flush()
print '-----objects:'
for p in popu.itervalues():
    print p
session.clear()

print '-----tables:'
sa.query_all_tables()
print '======\n'

p2 = session.query( Person).get_by_name( 'pesho')
#print p2
#    session.clear()

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

# XXX XXX XXX XXX
# be careful with possible NULLs - anyop(NULL) is NUL except true | NUL, false & NUL; bool(NUL) is False;
# http://firebird.sourceforge.net/manual/nullguide-dealing-with-nulls.html
# XXX XXX XXX XXX

do_nested = 1
do_method = 1
do_recursive = 1

plains = [
####plain
#1 level
    lambda person: (person.name == 'pesho'),
    lambda person: ( (person.name == 'pencho') & (person.age == 33) ),
    lambda person: ( (person.age > 45) & (person.name != 'mencho') & (person.age < 80) ),
#multilevel
    lambda person: (person.address.street == 'str.22'),
    lambda person: (person.address.street == None),
    lambda person: (person.address.street != None),
    lambda person: (person.address.home.num == 33),

    lambda person: (person.address == None),        #the reference itself; property

    lambda person: (
           (  (person.address.home.num > 20)
            & (person.address.home.num < 70)
            | (person.address.street != 'str.22')
           )
           & (person.address.kvartal >='kv.17')
       ),

    #these must raise
    #[AttributeError,    lambda person: (alabala > 45) ],
    [KeyError,          lambda person: (person.alabala > 45) ],


] + do_nested* [
 #nested no joins
    lambda person: (person.name + 'o') == 'peshoo',
    lambda person: ('p' + person.name ) == 'ppesho',

 #nested with joins
    lambda person: ((person.address.street + 'o') == 'str.1o'),
    #lambda person: (person.address.street != None) & ((person.address.street + 'o') == 'str.1o'),   #must be same as above
] + do_recursive *[
 #multilevel self-referential/recursive
    lambda person: (person.friend != None),
    lambda person: (person.friend.age >35),
    lambda person: (person.friend.name == 'pesho'),
    lambda person: (person.friend.friend.friend.name == 'pesho'),
    lambda person: (person.friend.address.owner.friend.name == 'pesho'),
 #db_id comparison - precalculated ("const")
    lambda person : (person.friend.db_id == 2),         #ok
    lambda person : (person.friend.db_id == p2.db_id),  #ok
    lambda person : (person.friend == p2),              #means "is"; needs op.__eq @python-test
    lambda person : (person.friend == p2.db_id),        #same as above; fails @python
]

funcs = [
 #plain func
    lambda person, f: f.substr( person.name, 4,1) == 'h',
 #method-operator-func
    lambda person, f: f.like( person.name, '%sho'),
    lambda person, f: f.like( person.alias, person.name+'%'),
    lambda person, f: f.like( person.address.street, person.name+'%'),
] + do_method *[ #needs fix/hack in SA
 #method-func
    lambda person, f: f.startswith( person.name, 'pe'),
    lambda person, f: f.endswith( person.name, 'sho'),
    lambda person, f: f.startswith( person.alias, person.name),
    lambda person, f: f.endswith( person.address.street, 'o' ),

    lambda person, f: f.in_( person.name, 'pesho', 'mencho' ),
    lambda person, f: f.in_( person.alias, 'peshoali', 'b-'+person.name ),
] + [
    lambda person, f: (f.between( person.age, 10, 45) & f.like( person.address.street, 'str%')),
] + do_method * [
    lambda person: person.name.endswith( 'sho'),
] + do_nested * do_method * [
 #nested + method
    lambda person, f: f.endswith( person.name+ 'o', 'oo' ),
    lambda person, f: f.endswith( person.address.street + 'o', 'oo' ),
 #method off nested
    #lambda person: (person.address.street + 'o').endswith('oo'),   #does not work
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
    lambda person, faggr: faggr.max( person.address.home.num) == person.age,   #??
]
orders = [  #similar thing - any joins should go in the FROM?
    lambda person, forder: forder.asc( person.age),                 #no joins!
    lambda person, forder: forder.asc( person.address.home.num),    #no joins!
]

allfuncs = plains + funcs #+ 0*aggregates

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


from tests.util.struct import Struct
from dbcook import expression
expression._debug = 'dbg' in sys.argv
expr = expression.expr
try:
    for func in allfuncs:
        #print '\n---------'
        expected_err = None
        if isinstance(func, (tuple,list)):
            expected_err, func = func

        e = expr.makeExpresion( func)
        #print e
        print 'expr:', e.walk( expr.as_expr)

        if expected_err:
            expected = None
        elif 'faggr' in e.arg_names: # func in Translator.aggregates:
            for p in popu.itervalues():
                e.walk( expr.Eval( AttrWrap( Struct( person=p, faggr=Funcs))))
            #print Funcs.max.all, Funcs.max.calc()
            print NotImplementedError
            continue

        else:   #filter population by func
            expected = []
            for p in popu.itervalues():

                ##real python eval
                import inspect
                args,vargs,kwargs,defaults = inspect.getargspec( func)
                #print args, vargs, kwargs
                f_kargs = {}
                f_args  = []
                #print p2.db_id, p.db_id
                if kwargs and 'p2' in kwargs or 'p2' in args: f_kargs['p2'] = p2
                if kwargs and 'f'  in kwargs or 'f'  in args: f_kargs['f'] = Funcs
                try:
                    rr = bool( func( p, *f_args, **f_kargs))
                except AttributeError: rr = None

                ##simulated python eval
                try:
                    r = bool( e.walk( expr.Eval( AttrWrap( Struct( person=p, f=Funcs, p2= p2 )))) )
                except AttrWrapError: r = None

                assert rr is r, 'rr:%(rr)s != r:%(r)s' % locals()

                if r: expected.append(p)
        #print expected
        eval = expression.Translator( AttrWrap( Struct( person=Person, f=None, p2= p2 )))
        try:
            sae = e.walk( eval)
        except expected_err:
            #print '  got', expected_err
            continue        #OK

        #print 'querying:', sae

        q = session.query( Human.DB_NO_MAPPING and Person or Human)

        q = q.select(sae)

        def strres( q, title):
            sres = [ str(p) for p in q]
            sres.sort()
            sres1 = ('\n'+2*' ').join( [title+':']+sres)
            return sres,sres1

        sres,sres1 = strres( q, 'result')
        sexp,sexp1 = strres( expected, 'expect')
        #print sres1
        assert sres==sexp, '\n%(sres1)s \n !=\n%(sexp1)s' % locals()
    print '\nOK'

finally:
    #sa.destroy()
    pass


# vim:ts=4:sw=4:expandtab
