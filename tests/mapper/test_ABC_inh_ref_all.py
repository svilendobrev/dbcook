#$Id$
# -*- coding: cp1251 -*-

from tests.util.context import * #Type4Reference, Builder, SAdb, Base, Text, fieldtypemap

querys = [ SAdb.query_BASE_instances, SAdb.query_ALL_instances, SAdb.query_SUB_instances]
inhtr = {
    'concrete': Builder.table_inheritance_types.CONCRETE,
    'joined'  : Builder.table_inheritance_types.JOINED,
    None: None,
}

def test_inh_ref_ABC_any( config,
        poly =True, inh ='concrete',
        Alink ='', Blink ='', BAlink ='', inhB='',
        Alazy =True, Blazy =True,
        Clink ='', Clazy =True, CAlink ='', CBlink ='', inhC='',
        insts = 'ABC',
    ):
    inh = inhtr[ inh]
    doC = config.doC
    if Alink: Alink = Alink[0]
    if Blink: Blink = Blink[0]
    if Clink: Clink = Clink[0]

    class A( Base):
        auto_set = False    #StaticTypeing; else: recursion
        if Alink:
            linkA = Type4Reference( Alink, lazy=Alazy)
        DB_inheritance = inh
        DB_HAS_INSTANCES = 'A' in insts
        name = Text()

    class B( inhB and A or Base):
        auto_set = False    #StaticTypeing; else: recursion
        if Blink:
            linkB = Type4Reference( Blink, lazy=Blazy)
        DB_inheritance = inh
        DB_HAS_INSTANCES = 'B' in insts
        dataB = Text()

    if doC:
        class C( inhC=='B' and B or inhC=='A' and A or Base):
            auto_set = False    #StaticTypeing; else: recursion
            if Clink:
                linkC = Type4Reference( Clink, lazy=Clazy)
            DB_inheritance = inh
            DB_HAS_INSTANCES = 'C' in insts
            dataC = Text()
        if 0:
            class D(C):
                dataD = Text()

    args = locals()
    def populate():
        return runCBA.populate( **args )

    if config.query:
        query = querys
    return locals()


def populate( sam, namespace):
    get_all_objects = namespace['populate']
    session = sam.session()
    sam.saveall( session, get_all_objects() )
    session.flush()


######################################
from tests.util import runCBA
config = runCBA.Config( SAdb.config)
config.getopt()


#    def abbr(a): return a.replace('link','p').replace('lazy','lz')
fmt = ', '.join( arg+'=%%(%(arg)s)' % locals() +('link' in arg  and '2.2s' or 'inst' in arg and '3.3s' or '1.1s')
                for arg in ('poly inh insts Alink inhB Blink BAlink'
                            +bool(config.doC)*' inhC Clink CAlink CBlink'
                        ).split()
            )

class Fmt:
    def __init__( me, fmt):
        me.fmt = fmt
    def __mod__(me, p):
        r = me.fmt % p
        for k,v in p.iteritems():
            if not k.endswith('lazy'): continue
            lz = v and 'lazy' or 'eagr'
            r = r.replace( k[0]+'link', k[0]+lz) #both Alink and BAlink
        return r
fmt = Fmt( fmt)

######################################

from tests.util import multi_tester, tester

class MyABCtester( multi_tester.MultiTester):
    Printer = Builder.SrcGenerator
    def _run_one( me, printer, **parameters):
        namespace = test_inh_ref_ABC_any( config, **parameters)
        err = tester.test( namespace, SAdb,
                    quiet= True,
                    reuse_db= True,
                    dump= config.dump,
                    generator= printer,
            )
        return err

    def run_all( me):
        for parameters in runCBA.allABC( me.config ):
            me.run_one( **parameters)
        me.do_report()
        me.do_generate()

    def str_params( me, parameters):
        return fmt % parameters

print 'config:', config

import sys
sys.setrecursionlimit( 300)

t = MyABCtester( config)
t.run_all()

# vim:ts=4:sw=4:expandtab

