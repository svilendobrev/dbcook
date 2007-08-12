#$Id$
# -*- coding: cp1251 -*-

import dbcook.config
dbcook.config.table_namer = lambda klas: klas.__name__ + '_tbl'

from tests.util import context
SAdb = context.SAdb

JOINED = context.JOINED
CONCRETE = context.CONCRETE

def gen_inh_types( inh_types, n):
    if n==0:
        yield []
    else:
        for i in range(len(inh_types)):
            for s in gen_inh_types( inh_types, n-1):
                yield [ inh_types[ i]] + s

def inh_symb( inh_type, dir):
    direction = dict( l=0, r=1)
    pos = direction[ dir]
    symbols = { context.CONCRETE : ['/','\\'],
                context.JOINED   : ['//','\\\\'],
                context.SINGLE   : 2 * '*'
              }
    symb = symbols[ inh_type][ pos]
    return symb

#################################


def test_plain_attr( context):
    class C( context.Base):
        ime = context.Text()
        alias = context.Text()

    def populate():
        c = C()
        c.ime = 'cc'
        c.alias = 'c-2'
        return locals()
    return locals()

def test_struct_embedded( context):
    assert NotImplementedError
    class MasValue( context.Base): pass
    def checker4substruct_as_value(t): return issubclass( t, MasValue)
    class C( MasValue):
        ime  = context.Text()
        cvet = context.Text()
    class B( MasValue):
        ime = context.Text()
        c = context.SubStruct( C)
    class A( context.Base):
        ime = context.Text()
        a = context.SubStruct( B)

    def populate():
        a = A()
        a.b.ime = 'bime'
        a.b.c.ime = 'cime'
        a.b_c_ime = 'bcime'
        print 'zzzzzzz', a.b_c_ime
        print 'zzzzzzz', a.b.c.ime
        return locals()
    return locals()

def test_struct_ref( context):
    class C( context.Base):
        ime = context.Text()
    class A( context.Base):
        ime = context.Text()
        c = context.SubStruct( C)
    class B( context.Base):
        ime = context.Text()
        a = context.SubStruct( A)

    def populate():
        c = C()
        c.ime = 'c ime'
        if 0:
            d = D()
            d.ime = 'd ime'
            d.aforward = c
            c.aback = d
        return locals()
    return locals()

def test_forw_ref( context):
    class D( context.Base):
        auto_set = False
        ime = context.Text()
        aforward = context.SubStruct('C')
    class C( context.Base):
        auto_set = False
        ime = context.Text()
        aback = context.SubStruct( D)

    def populate():
        c = C()
        c.ime = 'c ime'
        d = D()
        d.ime = 'd ime'
        d.aforward = c
        c.aback = d
        return locals()
    return locals()

def test_forw_ref_A_B_C_A( context):
    class C( context.Base):
        auto_set = False
        ime = context.Text()
        aforward = context.SubStruct('A')
    class B( context.Base):
        auto_set = False
        ime = context.Text()
        aback = context.SubStruct( C)
    class A( context.Base):
        auto_set = False
        ime = context.Text()
        aback = context.SubStruct( B)

    def populate():
        c = C()
        c.ime = 'c ime'
        b = B()
        b.ime = 'b ime'
        b.aback = c
        a = A()
        c.aforward = a
        a.ime = 'a ime'
        a.aback = b
        return locals()
    return locals()

def test_forw_ref_self( context):
    class C( context.Base):
        auto_set = False
        ime = context.Text()
        aself = context.SubStruct('C')

    def populate():
        c1 = C()
        c1.ime = 'ca'
        c2 = C()
        c2.ime = 'cb'
        c1.aself = c2
        return locals()
    return locals()

def test_self_ref_2list( context):
    class A( context.Base):
        auto_set = False
        ime = context.Text()
        prev = context.SubStruct('A')
        next = context.SubStruct('A')

    def populate():
        a0 = A()
        a0.ime = 'a0 ime'
        a1 = A()
        a1.ime = 'a1 ime'
        a2 = A()
        a2.ime = 'a2 ime'
        a1.prev = a0
        a0.next = a1
        a1.next = a2
        a2.prev = a1
        return locals()
    return locals()

def test_self_ref_tree( context):
    'виж /usr/share/doc/python-sqlalchemy-doc/examples/backref/backref_tree.py'
    class A( context.Base):
        auto_set = False
        ime = context.Text()
        parent = context.SubStruct('A')
        #children = context.Sequence( context.SubStruct('A') )     #ТОВА е дървото; иначе е просто ref-self

    def populate():
        a0 = A()
        a0.ime = 'koren'
        a1 = A()
        a1.ime = 'a'
        a1.parent = a0
        return locals()
    return locals()

def test_inh_empty( context, inh):
    class A( context.Base):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = inh
        imea = context.Text()
    class B( A):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = inh
    class C( B):
        DBCOOK_inheritance = inh
    class D( A):
        DBCOOK_inheritance = inh

    def populate():
        a = A()
        a.imea = 'ime a'
        b = B()
        c = C()
        d = D()
        return locals()

#    query  = [ Functor( func, klas=A) for func in querys]
#    query += [ Functor( func, klas=B) for func in querys]
    return locals()

def test_inh_nonempty( context, inh):
    class A( context.Base):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = inh # JOINED or else:CONCRETE
        imea = context.Text()
    class B( A):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = inh
        imeb = context.Text()
    if 10:
        class C( B):
            DBCOOK_inheritance = inh #CONCRETE
            imec = context.Text()
    use_D =0
    if use_D:
        class D( A):
            DBCOOK_inheritance = inh
            imed = context.Text()

    def populate():
        a = A()
        b = B()
        a.imea = 'ai'
        #b.imea = 'bia'
        b.imeb = '1'
        if 10:
            c = C()
            c.imea = 'ci'
            c.imec = 'cci'
        if use_D:
            d = D()
            d.imea = 'di'
            d.imed = 'di2'
        return locals()

#    query  = [ Functor( func, klas=A) for func in querys]
#    query += [ Functor( func, klas=B) for func in querys]
    return locals()


def test_inh_diff_at_node( context):
    '''вариант 1. нееднакво наследяване'''

    #root
    class A( context.Base):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = CONCRETE
        imea = context.Text()
    # A_nodes
    class B( A):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = CONCRETE
        imeb = context.Text()
    class D( A):
        DBCOOK_inheritance = JOINED
        imed = context.Text()
    # B_nodes
    class C( B):
        DBCOOK_inheritance = CONCRETE
        imec = context.Text()
    class E( B):
        DBCOOK_inheritance = JOINED
        imee = context.Text()

    def populate():
        a = A()
        a.imea = 'a'
        b = B()
        b.imea = 'ba'
        b.imeb = 'b'
        c = C()
        c.imea = 'ca'
        c.imec = 'ci'
        d = D()
        d.imea = 'da'
        d.imed = 'd'
        e = E()
        e.imea = 'e'
        return locals()

    return locals()


def test_inh_same_at_node( context, nodes =None):
    '''вариант 2. еднакво наследяване на всяко ниво - но различно на различните нива'''

    if nodes is None:
        nodes = dict( A_nodes= JOINED,
                      B_nodes= CONCRETE,
                      C_nodes= JOINED)
    #root
    class A( context.Base):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = CONCRETE
        imea = context.Text()
    # A_nodes
    class B( A):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = nodes['A_nodes']
        imeb = context.Text()
    class D( A):
        DBCOOK_inheritance = nodes['A_nodes']
        imed = context.Text()
    # B_nodes
    class C( B):
        DBCOOK_has_instances = True
        DBCOOK_inheritance = nodes['B_nodes']
        imec = context.Text()
    class E( B):
        DBCOOK_inheritance = nodes['B_nodes']
        imee = context.Text()
    # C_nodes
    class P( C):
        DBCOOK_inheritance = nodes['C_nodes']
        imep = context.Text()
    class Q( C):
        DBCOOK_inheritance = nodes['C_nodes']
        imeq = context.Text()


    def populate():
        a = A()
        a.imea = 'a'
        b = B()
        b.imea = 'ba'
        b.imeb = 'b'
        c = C()
        c.imea = 'ca'
        c.imec = 'c'
        d = D()
        d.imea = 'da'
        d.imed = 'd'
        e = E()
        e.imea = 'ea'
        p = P()
        p.imea = 'pa'
        q = Q()
        q.imeq = 'q'
        return locals()

    return locals()

def test_inh_all_nodes_same( context, inh):
    '''вариант 0. еднакво наследяване, на всички нива (няма смесване)'''
    nodes = dict.fromkeys( ['A_nodes', 'B_nodes', 'C_nodes'], inh)
    return test_inh_same_at_node( context, nodes)


def test_B_inh_A_ref( context, inh, refs):
    '''всичките случаи inh+ref: А->А Б(А);  А->Б б(А);  Б(А) Б->А;  Б(А) Б->Б'''
    class A( context.Base):
        DBCOOK_has_instances = True
        auto_set = False
        if 'A' in refs:
            aref = context.SubStruct( refs['A'])
        DBCOOK_inheritance = CONCRETE
        imea = context.Text()
    class B( A):
        if 'B' in refs:
            bref = context.SubStruct( refs['B'])
        DBCOOK_inheritance = inh
        imeb = context.Text()
    def populate():
        a = A()
        b = B()
        a.imea = 'a'
        if 'A' in refs:
            if refs['A'] == 'A':    #XXX A1 -> a1; A->a#self
                a1 = A()
                a.aref = a1
            else:
                a.aref = b
        if 'B' in refs:
            if refs['B'] == 'B':
                b1 = B()
                b.bref = b1
            else:
                b.bref = a
        b.imea = 'ba'
        b.imeb = 'b'
        return locals()
    return locals()


class test_user_defined( object):
    def __init__( me, context, klasi, refs):
        me.klasi = klasi
        me.refs = refs
        me.context = context

    def make_classes_code( me):
        class_gen = '''
Base = context.Base'''
        for clas, inh_data in me.klasi.iteritems():
            lower = clas.lower()
            ref = me.refs[ clas]
            inh, base = inh_data
            class_gen += '''
class %(clas)s( %(base)s):
    auto_set = False
    DBCOOK_has_instances = True
    DBCOOK_inheritance='%(inh)s'
    %(lower)sime  = context.Text()
    %(lower)slink = context.SubStruct('%(ref)s')
''' % locals()
        return class_gen

    def make_populate_code( me):
        pcode = """
def populate():"""
        for clas in me.klasi.keys():
            lower = clas.lower()
            pcode += """
    %(lower)s = %(clas)s()""" % locals()
        for clas in me.klasi:
            lower = clas.lower()
            pcode += """
    %(lower)s.%(lower)sime = '%(clas)s ime'""" % locals()
            if clas in me.refs.keys():
                ref = me.refs[ clas].lower()
                pcode += """
    %(lower)s.%(lower)slink = %(ref)s""" % locals()
        pcode += """
    return locals()"""
        return pcode

    def make_namespace( me):
        context = me.context
        exec ( me.make_classes_code(), locals())
        exec ( me.make_populate_code(), locals())
        return locals()


####################################

import os, os.path

SHOW_DEFAULT_QUERY_RESULTS = False

## XXX HACK за повтаряемост на теста, подменя Set/dict на OrderedSet/Dict
## XXX НЕ забравяй SAdb също да е подреден!!! force_ordered=True
from dbcook.usage.sa_hack4repeatability import hack4repeat
hack4repeat()

TEST_OUT_ROOT = 'simple/output'
#import sys
#if len( sys.argv) > 1:
#    TEST_OUT_ROOT = sys.argv[1]
#else:
#    print 'usage: ', sys.argv[0], ' path_to_output_dirs'

from dbcook.util.dictOrder import dictOrder

class Config( SAdb.config.Config):
    session_clear = True
    _help = '''\
workflow control:
    no_session_clear :: do not session.clear() before querying
'''

config = Config( SAdb.config)

def str2( x, ignored =(), start =True):
    if isinstance(x,dict):
        keys = x.keys()
        keys.sort()
        r = ' '.join( k+'='+str2( x[k], start=False) for k in keys if k not in ignored)
        if not start: r = '('+r+')'
        return r
    elif isinstance(x,list):
        r = ','.join( x)
        return r

    return str(x)


USE_FILENAME_ABBREVS = 1
class MapperCaseParams( object):
    default_flow_config = ['save', 'flush', 'query']

    filename_abbrevs = {
        JOINED  : 'j',
        CONCRETE: 'c',
        'dictOrder'     : '',
        ', ' : ',',
        ': ' : ':',
        '{' : '(',
        '}' : ')',
        'Base' : 'None',
        'user_defined' : 'user',
        "'"  : '',
    }

    def __init__( me, namespace,
                    func_params ={},
                    base_klas   =None,
                    expected    =None,
                    get_result  =None,   #text-result
                    descr       =None,
                    flow_config =None,
                ):

        me.namespace = namespace
        me.get_result = get_result
        me.base_klas = base_klas or context.Base

        me.func_params = func_params

        if not flow_config:
            flow_config = list( me.default_flow_config) #copy
            if config.session_clear:
                flow_config.insert( flow_config.index( 'query'), 'clear')
        me.flow_config = flow_config

        me.config_descr = ''

        if not expected and callable( namespace):
            case_folder = namespace.__name__
            pfx = 'test_'
            if case_folder.startswith( pfx):
                case_folder = case_folder[ len(pfx):]

            fname = str2( me.func_params, ignored=['context'] )
            #fname += ' '+' '.join( me.flow_config)
            if not config.session_clear:
                fname += ' no_clear'

            if USE_FILENAME_ABBREVS:
                for old, new in me.filename_abbrevs.iteritems():
                    fname = fname.replace( old, new)

            if not fname: fname = 'test'
            me.config_descr = case_folder+'/'+fname

            expected = os.path.join( TEST_OUT_ROOT, case_folder, fname + '.org')
        me.expected = expected  #filename

        if not descr and callable( namespace):
            descr = me.config_descr # namespace.__name__
        me.descr = descr

#########################################

P = MapperCaseParams

def str_joins( mapper_case):
    nl = '\n'
    sadb = mapper_case.sadb
    out = ''
    for klas in sadb.iterklasi():
        out += str(klas) + str(sadb.need_typcolumn( klas)) + nl
    for klas in sadb.iterklasi():
        out += nl + 10*'=' + str(klas) + 10*'=' + nl
        out += nl + str( sadb.subklas_selectable( klas)[0])
    #print out
    return out

all_cases = [
    P( test_plain_attr          , ),
    P( test_plain_attr          , ),
#    P( test_struct_embedded     ,    ),
    P( test_struct_ref          ,    ),
    P( test_forw_ref         ,    ),
    P( test_forw_ref_self    ,    ),
    P( test_forw_ref_A_B_C_A ,    ),
    P( test_self_ref_2list      ,    ),
    P( test_self_ref_tree       ,    ),
    P( test_inh_empty   , func_params= dict( inh=CONCRETE),      ),
    P( test_inh_empty   , func_params= dict( inh=JOINED),   ),
    P( test_inh_nonempty, func_params= dict( inh=CONCRETE),      ),
    P( test_inh_nonempty, func_params= dict( inh=JOINED),   ),
    P( test_inh_all_nodes_same, get_result=str_joins, func_params= dict( inh=CONCRETE)),
    P( test_inh_all_nodes_same, get_result=str_joins, func_params= dict( inh=JOINED)),
    P( test_inh_diff_at_node, get_result=str_joins,    ),
    P( test_inh_same_at_node, get_result=str_joins,
                                    func_params= dict( nodes=dict(A_nodes=CONCRETE,
                                                                  B_nodes=JOINED,
                                                                  C_nodes=CONCRETE))),
    P( test_inh_same_at_node, get_result=str_joins,
                                    func_params= dict( nodes=dict(A_nodes=JOINED,
                                                                  B_nodes=JOINED,
                                                                  C_nodes=CONCRETE))),
    P( test_B_inh_A_ref, func_params= dict( inh=CONCRETE,    refs= dict(A='A'))),
    P( test_B_inh_A_ref, func_params= dict( inh=CONCRETE,    refs= dict(A='B'))),
    P( test_B_inh_A_ref, func_params= dict( inh=CONCRETE,    refs= dict(B='A'))),
    P( test_B_inh_A_ref, func_params= dict( inh=CONCRETE,    refs= dict(B='B'))),
    P( test_B_inh_A_ref, func_params= dict( inh=JOINED, refs= dict(A='A'))),
    P( test_B_inh_A_ref, func_params= dict( inh=JOINED, refs= dict(A='B'))),
    P( test_B_inh_A_ref, func_params= dict( inh=JOINED, refs= dict(B='A'))),
    P( test_B_inh_A_ref, func_params= dict( inh=JOINED, refs= dict(B='B'))),
#    P( test_B_inh_A_ref, func_params= dict( inh=JOINED, refs= dict(B='B')),
]

#all_cases = []
for inh in gen_inh_types( [CONCRETE, JOINED], 2):
    klasi = dictOrder( ( ('A', [CONCRETE, 'Base']),
                         ('B', [inh[0], 'A']),
                         ('C', [inh[1], 'B']) ) )
    case = P( test_user_defined,
              func_params= dict( klasi= klasi,
                                 refs= dict( A='B', B='A', C='A'),
                                )
            )
    all_cases.append( case)

zall_cases = [
   P( test_inh_nonempty, func_params= dict( inh=JOINED), ),
]


from tests.util import case2unittest, tester
class MapperCase( case2unittest.Case):
    generate_samples = False
    queries = [ SAdb.query_BASE_instances, SAdb.query_ALL_instances, SAdb.query_SUB_instances]
    _db = None
    reuse_db = True
    def setUp( me):
        me.sadb = SAdb( echo=True, log2stream=True)
        if me.reuse_db and MapperCase._db:
            me.sadb.db = MapperCase._db
        else:
            me.sadb.open( recreate=True)

        me.namespace = me.params.namespace
        if callable( me.namespace):
            me.namespace = me.namespace( context=context, **me.params.func_params)
            if hasattr( me.namespace, 'make_namespace'):
                me.namespace = me.namespace.make_namespace()
        me.builder = me.sadb.bind( me.namespace,
                            base_klas= me.params.base_klas,
                            print_srcgenerator =False,
                        )#, force_ordered= True)
        me.session = me.sadb.session()

    def save_session( me):
        me.populate_namespace = tester.get_populate_namespace( namespace=me.namespace,
                base_klas= context.Base,
                popreflector= tester.popreflector_factory( SAdb),
                generator= me.builder.generator
            )
        me.sadb.saveall( me.session, me.populate_namespace)

    def flush_session( me):
        me.session.flush()
        me.klasitems = tester.klasify( me.sadb, me.populate_namespace, converter=str )   #expected results

    def clear_session( me):
        me.session.clear()

    def queryall( me):
        klasi = tester.types_sorted( me.sadb)
        for klas in klasi:
            if SHOW_DEFAULT_QUERY_RESULTS: print '==', klas.__name__

            ki = me.klasitems[ klas]
            queries = []
            for qname in ki.__dict__:
                if 0:
                    if qname.startswith('__'): continue
                    qy = getattr( me.sadb, qname, None)
                    if not callable(qy): continue
                else:
                    qy = me.queries
                err = tester.do_query( qy, sadb=me.sadb, session=me.session,
                               klas=klas, klasitems=me.klasitems,
                               quiet=not SHOW_DEFAULT_QUERY_RESULTS)
                me.failIf( err, '\n'.join(err))

    def test_mapper( me):
        #me.query = me.namespace.get( 'query', None)
        standard_actions = dict(
                save  = me.save_session,
                flush = me.flush_session,
                clear = me.clear_session,
                query = me.queryall,
        )

        for action in me.params.flow_config:
            if action in standard_actions:
                standard_actions[ action]()
            else:
                print 'no method for action: ', action

    def tearDown( me):
        try:
            if me.generate_samples:
                me.gen_sample()
        finally:
            if me.builder.generator: print me.params.expected, '\n#====generated SA set-up\n', me.builder.generator.out,'\n#========= eo generated SA set-up'
            me.builder = None
            if me.reuse_db:
                MapperCase._db = getattr( me.sadb, 'db', None)
            me.sadb.destroy( full= not me.reuse_db)    #ALWAYS!

    def gen_sample( me, fname=None):
        current = ( callable( me.params.get_result) and
                    me.params.get_result( me) or
                    me.sadb.log2stream.getvalue())
        if not fname:
            fname = me.params.expected
        path = os.path.split( fname)[0]
        if path and not os.path.exists( path):
            os.makedirs( path)
        f = file( fname, 'w')
        try:
            f.write(current)
        finally:
            f.close()

if __name__ == '__main__':
    import sys
    sys.setrecursionlimit( 300)
    config.getopt()
    import unittest
    unittest.TextTestRunner(
        unittest.sys.stdout, verbosity=2, descriptions=True, ).run(
            case2unittest.get_test_suite( all_cases, MapperCase))

# vim:ts=4:sw=4:expandtab
