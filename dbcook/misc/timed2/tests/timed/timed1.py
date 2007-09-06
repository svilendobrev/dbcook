#$Id$
# -*- coding: cp1251 -*-

import bisect

class Timed1:
    '''
    Single-timestamp history (i.e. versioned) object. use any (ascending) representation of time.

    нещо с 1-времева история (т.е. версии).
    Работи с всякакво (нарастващо) представяне на времето.

    версии с еднакви времена не се заместват, а се подреждат в реда на добавяне,
    и винаги се връща последната (т.е все едно че се заместват - но историята си остава).

    изключване/включване (enable=exists/disable=deleted) на нещото трябва да се направи
    като огъвка - състоянието на нещото си е само негова работа.
    '''
    N_TIMES = 1
    _WITH_DIRECT_ACCESS = 0     #not really needed, maybe internal testing only
    class NOT_FOUND: pass
    def __init__( me):
        me.order = []
        if me._WITH_DIRECT_ACCESS:
            me.all = {}

    def put( me, obj_version, time):
        assert time
        order = me.order

            # the middle 0 is used as stepper: to be able to _search_ for a step AFTER an
            # existing time but before next valid one - as the way to make a valid 'next' is unknown
            #
            # 0-та в средата се ползва като стъпало/разделител - да може да се търси една стъпка СЛЕД някакво
            # съществуващо време но преди следващото валидно - като пресмятането на 'следващо' не е известно

        #if 0:   #разчита на подредбата на obj_version при еднакви времена
        #    bisect.insort_right( me.order, (time,0,obj_version) )

        ##при еднакви времена, това винаги добавя в края им
        time_next = (time,1, None)
        ix = bisect.bisect_left( order, time_next)
        order.insert( ix, (time,0,obj_version) )

        if me._WITH_DIRECT_ACCESS: #follows direct access - not really needed
            me.all[ time ] = obj_version
            if not time.startswith('_'): time='_'+time
            setattr( me, time, obj_version)

    def _get_ix( me, time ):
        assert time
        order = me.order
            #see put() for explaining the middle 1
        time_next = (time,1, None)          #преди следващото
        ix = bisect.bisect_left( order, time_next )
        return ix   #0 значи няма запис

    def _get_ix2( me, timefrom, timeto ):   #включително
        assert timefrom
        assert timeto       #символ/маркер ? напр. до-края
        order = me.order

        # *from is different from _get_ix() -
        time_prev = (timefrom,-1, None)     #след предното ????
        ix_from = bisect.bisect_right( order, time_prev )

        if ix_from: ix_from -= 1    #XXX ????

        # *to is same like _get_ix() ; 0 means not found
        time_next = (timeto,1, None)        #преди следващото
        ix_to   = bisect.bisect_left( order, time_next )
        #if ix_to >= ix_from: return None    # няма намерени ???????????? нещо такова
        return ix_from,ix_to   #ix_to is like _get_ix(); ix_from is not

    def get( me, time, only_value =True ):
        ix = me._get_ix( time)
        if ix:
            r = me.order[ix-1]
            if only_value: return r[-1]
            return (r[0],r[-1])         #skip the middle stepper
        return me.NOT_FOUND #None
    __getitem__ = get

    def __str__(me):
        return me.__class__.__name__ + '\n ' + '\n '.join( str(f) for f in me.order )

    def __eq__( me, other): return me.order == other.order
    def __ne__( me, other): return me.order != other.order

###################### test base

class Test0( object):
    def fill( me, timed, inputs =None, input2time =None):
        print 'fill:',
        if not input2time: input2time = me.input2time
        input_times = me.input_times
        objects = input_times[:]
        for i in (inputs or range( 1,1+len(input_times))):
            o = 'v'+str(i)
            print o,
            timed.put( o, input2time( input_times[i-1] ))
            objects[ i-1] = o
        print
        if me.verbose: print timed
        return objects

    input_printer = repr
    def test_db( me, timed,
                timekey2input   =None,
                input_times     =None,
                input_printer   =None,
            ):
        print 'test_internal_contents',
        if not timekey2input: timekey2input = me.timekey2input
        if not input_times: input_times = me.input_times
        if not input_printer: input_printer = me.input_printer
        err = 0
        res_db = timed.order
        res_times = [ timekey2input( timed, row[0]) for row in res_db ]
        if res_times != list( input_times):
            l_in = len( input_times)
            l_db = len( res_db)
            print '  ERR:'
            print '   result_db: len=%(l_db)s %(timed)s' % locals()
            print '   template:  len=', len(input_times)
            for tm in input_times:
                print '   ', input_printer( tm)
            err += 1
        else:
            print ' OK'
        me.err += err
        return err

    input2time = staticmethod( lambda t:t )
    def test_get( me, timed,
                objects,
                cases       =None,
                input2time  =None,
                obj_titler      =lambda r:r,
                timed_printer   =lambda t:t,
                obj_printer     =None,
                timed_titler    =lambda t:t.__class__.__name__,
            ):
        if not cases: cases= me.cases
        if not input2time: input2time = me.input2time
        err = 0
        verbose = me.verbose
        print 'test_get', timed_titler and timed_titler( timed),
        first = 1
        for row in cases:
            tm, name, iresult = row
            m = timed.get( input2time( tm), only_value=False )
            if m is not timed.NOT_FOUND: r = m[-1]
            else: r = None
            if iresult: r_expect = objects[ iresult-1]
            else: r_expect = None
            ok = (r_expect == r)
            if verbose or not ok:
                if first: print
                print ok and '  OK  ' or '  ERR!', ':', name, tm, '->', r and obj_titler(r)
            if verbose>1 or not ok:
                print '   expect:', r_expect and obj_titler( r_expect)
                print '   result:', m, r and obj_printer and obj_printer( r) or ''
            err += not ok
            first = 0
        if verbose>1 or err:
            print timed_printer( timed)
        print err and ' ERR' or ' OK'
        if verbose or err: print
        me.err += err
        return err

    __slots__ = ()
    _err = 0
    def seterr( me, v): Test0._err = v
    err = property( lambda me:me._err, seterr)

    def __init__( me, verbose =0 ):
        import sys
        me.verbose = sys.argv.count('-v') or verbose
    def exit( me):
        raise SystemExit, me.err

####### test timed1

class Test( Test0):
    input_times = [ 20060901, 20061002, ]
    cases= [    #time   #case-name      #result-obj = 1+index over input_times
            [ 20061002, 'exact'         , 2    ],
            [ 20060901, 'exact'         , 1    ],
            [ 20060900, '1 step-before' , None ],
            [ 20060910, 'between'       , 1    ],
            [ 20060202, 'before all'    , None ],
            [ 20061010, 'after all'     , 2    ],
           ]
    timekey2input = staticmethod( lambda timed, k: k )

    def fill4sametime( me, timed, shade, objects, shade_out =None ):
        objs = objects[:]
        if not shade_out: shade_out = shade
        print 'setup same-time sequencing',
        if me.verbose: print ':', shade_out, 'must hide the original', objs[0]
        else: print
        timed.put( shade, me.input2time( me.input_times[0]) )
        objs[0] = shade_out
        return objs

if __name__ == '__main__':
    test = Test()
    t = Timed1()

    objects = test.fill( t, [1,2] )
    test.test_db( t)

    for sametime in (0,1):
        objs = objects
        if sametime:
            objs = test.fill4sametime( t, 'shade', objects )
        test.test_get( t, objs )

    test.exit()

# vim:ts=4:sw=4:expandtab
