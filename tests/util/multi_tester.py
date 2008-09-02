#$Id$
# -*- coding: cp1251 -*-

import traceback, sys

class MultiTester( object):
    Printer = None
    def __init__( me, config):
        me.config = config

        me.ok_cases = []
        me.fail_cases = []
        me.failed_counter = 0
        me.prn = []

    _any_echos = 'debug echo verbose log_sa'
    def any_echo( me):
        for k in me._any_echos.split():
            if getattr( me.config, k, None): return True
        return False

    def _run_one( me, printer, **parameters):
        return None or ['all SA errors during case execution']

    def run_one( me, **parameters):
        if me.config.dummy:
            me.fail_cases.append( (parameters, 'dummy') )
            me.failed_counter+=1
            return

        error = ''
        if me.any_echo(): print '=============='
        print '>'+ me.str_params( parameters)

        printer = me.config.generate and me.Printer and me.Printer()
        try:
            err = me._run_one( printer, **parameters)
        except KeyboardInterrupt : raise
        except Exception, e:
            sys.stdout.flush()
            print ' ?? failed'
            traceback.print_exc()
            me.fail_cases.append( (parameters, str(e)) )
            inf = sys.exc_info()
            error = ''.join( traceback.format_exception(inf[0], inf[1], None)[-1])
            del inf
            me.failed_counter+=1
        else:
            if err:
                for e in err:
                    print ' ? failed', e
                    me.fail_cases.append( (parameters, str(e)) )
                    error += str(e) + '\n'
                me.failed_counter+=1
            else:
                me.ok_cases.append( parameters)

        if printer:
            if error or 'failed' not in me.config.generate:
                me.prn.append( printer.testcase( me.config.funcname + me.str_params( parameters), error ))

    def run_all( me):
        pass

    def do_report( me):
        str_config = 'config:' + str( me.config)

        all = len( me.ok_cases) + me.failed_counter
        perc = (100 * me.failed_counter) / all
        fails = me.failed_counter
        str_fails = '---------- fail: %(fails)s  of total %(all)s ; %(perc)s%%' % locals()

        print str_config
        print '============ ok:'
        print '\n'.join( me.str_params( a) for a in me.ok_cases)

        print str_fails
        print '\n'.join( me.str_params( a) +' :::  '+e.replace('\n', me.config.one_line and '; ' or '\n\t') for a,e in me.fail_cases)
        print str_fails
        print str_config

    def do_generate( me, header =''):
        if not me.config.generate: return
        if not me.prn:
            print 'nothing to generate'
        else:
            Printer = me.Printer
            assert Printer, '?? no .Printer in ' + str(me.__class__)
            if 'many' in me.config.generate:
                prnname = me.config.prnname
                print 'creating many', prnname
                for p in me.prn:
                    fname = Printer.testcasedef2name( p.split('\n',1)[0], me.config.funcname )
                    fname = prnname % (fname,)
                    file( fname, 'w').write( Printer._head + header + Printer.classdef + p + Printer.tail )
            else:    #_one:
                prnname = me.config.prnname % ('all',)
                print 'creating', prnname
                file( prnname,'w').write( Printer._head + header + Printer.classdef + '\n'.join( me.prn) + Printer.tail )

    def str_params( parameters):
        return str( parameters)

# vim:ts=4:sw=4:expandtab
