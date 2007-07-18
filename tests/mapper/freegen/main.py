#$Id$
# -*- coding: cp1251 -*-

from tests.util import context
from case_gen import NamespaceGen
from param_gen import gen_case_params, str_schema


all_inh = 'concrete table '

from dbcook.util.dictOrder import dictOrder
classes = dictOrder((
           ('A', ['concrete', 'Base']),
           ('B', [ all_inh, 'A Base']),
           ('C', [ all_inh, 'A B']),
           ('D', [ all_inh, 'A B C']),
#           ('E', [ all_inh, 'A B C D']),
          # ('F', [ all_inh, 'A B C D E']),
          ))

links = dict(
          A=  dict( Alink= 'A B C'),#E F'),
          B=  dict( Alink= 'A B C', Blink= 'A B C' ),
          C=  dict( Alink= 'A B C1', Blink= 'A'    , Clink= 'C1' ),
#          D=  dict( Alink= 'A B C', Blink= 'A C'    , Clink= 'C' ),
#          E=  dict( Alink= 'A B C', Blink= 'A C'    ,  ),
            )

from tests.util import multi_tester, tester

class MyTester( multi_tester.MultiTester):
    Printer = Builder.SrcGenerator
    def _run_one( me, printer, **parameters):
        nms_gen = NamespaceGen( context, parameters.get('classes'), parameters.get('links'))
        namespace = nms_gen.make_namespace()

        return tester.test( namespace, context.SAdb,
                    quiet= True,
                    dump= me.config.dump,
                    reuse_db= True,
                    generator= printer,
                )

    def run_all( me):
        for parameters in gen_case_params( classes, links):
            me.run_one( **parameters)
        me.do_report()
        me.do_generate()

    def str_params( me, parameters):
        return str_schema( **parameters)

if __name__ == '__main__':
    from tests.util import runCBA
    config = runCBA.Config( context.SAdb.config)
    config.getopt()
    config.poly_all = True
    config.polymorphic = True
    config.generate = ['failed']
    print 'config:', config

    t= MyTester( config)
    t.run_all()

# vim:ts=4:sw=4:expandtab
