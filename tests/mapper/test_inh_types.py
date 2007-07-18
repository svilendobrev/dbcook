#$Id$
# -*- coding: cp1251 -*-
from tests.util import context
from test4mapper import gen_inh_types, inh_symb, MapperCase

def picture( inh):
    nl = '\n'
    s = 10*'/'+ 'Trying ... ' + 10*'\\'+nl
    t = ' '
    s += 9*t + 'A' + nl
    s += 7*t + inh_symb( inh[0], 'l') + t + inh_symb( inh[1], 'r') + nl
    s += 6*t + 'B' + 4*t + 'D'+nl
    s += 4*t + inh_symb( inh[2], 'l') + t + inh_symb( inh[3], 'r') + nl
    s += 3*t + 'C' + 4*t + 'E'+nl
    return s


class InhCaseParams( object):
    def __init__( me, namespace, descr =None):
        me.namespace = namespace
        me.base_klas = context.Base
        me.descr = descr

def param_gen( context):
    '''вариант 3. наследявания в случаен ред'''
    for inh in gen_inh_types( ['concrete_table', 'joined_table'], 4):
        #print picture( inh)
        class A( context.Base):    #root
            DB_inheritance = 'concrete_table'
            imea = context.Text()
        class B( A):    # A_nodes
            DB_inheritance = inh[0]
            imeb = context.Text()
        class D( A):
            DB_inheritance = inh[1]
            imed = context.Text()
        class C( B):    # B_nodes
            DB_inheritance = inh[2]
            imec = context.Text()
        class E( B):
            DB_inheritance = inh[3]
            imee = context.Text()

        def populate():
            a = A()
            a.imea = 'ime a'

            b = B()
            b.imeb = 'ime b'
            b.imea = 'b.imea'

            c = C()
            c.imec = 'ime c'
            c.imeb = 'c.imeb'
            c.imea = 'c.imea'

            d = D()
            d.imed = 'ime d'
            d.imea = 'd.imea'

            e = E()
            e.imee = 'ime e'
            e.imea = 'e.imea'
            return locals()
        yield InhCaseParams( namespace= locals(), descr= picture( inh))


class InhCase( MapperCase):
    def setUp( me):
        MapperCase.setUp( me)
        if 0:
            print 'need_typcolumn:',
            print ', '.join( klas.__name__+':'+str( me.sadb.mapcontext.need_typcolumn(klas))
                             for klas in me.sadb.iterklasi())
            for klas in me.sadb.iterklasi():
                print '==============', klas.__name__, '============='
                print '\n'.join( str(q) for q in me.builder.make_klas_selectable( klas, test=True))
        me.save_session()
        me.flush_session()

    def test_mapper( me):
        me.queryall()

from tests.util.case2unittest import get_test_suite
testsuite = get_test_suite( param_gen( context), InhCase)

if __name__ == '__main__':
    import unittest
    unittest.TextTestRunner( unittest.sys.stdout,
            verbosity=2, descriptions=True, ).run( testsuite)


# vim:ts=4:sw=4:expandtab
