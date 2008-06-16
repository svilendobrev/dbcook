#$Id$
# -*- coding: cp1251 -*-
from engine.testutils import testMain
from engine.testbase import Case
from datetime import datetime
VERBOSE = 0

class _Timed2_withDisabled_protocol:
    '''testing only - Timed protocol for tests to use
        ALWAYS USE KEYWORD-ARGS ONLY!
    '''
    def get( me, trans, valid, include_deleted =False): pass
    def put( me, value, trans, valid, deleted =False): pass

    #FORCE using keyword-args only
    class EnforcingWrapper( object):
        __slots__ = ('timed',)
        def __init__( me, timed_klas ): me.timed = timed_klas()
        def get( me, **kargs): return me.timed.get( **kargs)
        def put( me, **kargs): return me.timed.put( **kargs)
        def __str__( me): return str( me.timed)
        def __getattr__( me, name): return getattr( me.timed, name)


class Customer:
    "Business object to test with"
    Timed2_withDisabled_klas = None               #klas with additional get.include_deleted, put.deleted args
    def __init__( me ):
        me.age  = _Timed2_withDisabled_protocol.EnforcingWrapper( me.Timed2_withDisabled_klas )
#    def get( me, **k): return me.age.get( **k)


class TimedTestSimpleCase( Case):
    "can be used as base class for this side of tests in the future"
    def __init__( me, doc, inputDatabase, testingSamples):
        Case.__init__( me, doc, inputDatabase, testingSamples)
        me._testDefaultTime = False
        me.obj = Customer()
    def setupEach( me, f):
        me.obj.age.put( value=f.value, trans=f.trans, valid=f.valid, deleted=(f.status == 'd') )
    def testEach( me, t):
        res = None
        if me.obj:
            if me._testDefaultTime:
                t.trans = t.valid = datetime.now()
            res = me.obj.age.get( trans=t.trans, valid=t.valid, include_deleted=False)
        return res
    def systemState( me): return str(me.obj.age)


class TimedCombinationsTestCase( TimedTestSimpleCase):
    def setup( me):
        import comb
        i = 0
        comb.res = []
        for vday, rday in comb.makeCombinations( list(range(1, 20, 2)), 2):
            valor = datetime( 2006, 2, vday)
            real  = datetime( 2006, 2, rday)
            me.obj.age.put( value= i, trans= real, valid= valor)
            if me.verbosity > 2: print 'DB:', real, valor, ' value', i
            i += 1

class TimedDefaultGetTestCase( TimedTestSimpleCase):
    ''' tests getting default (most recent) object
        relies on fact that test sequense dates are below current time,
        i.e. current time is after September 2006
    '''
    def __init__( me, doc, inputDatabase, testingSamples):
        TimedTestSimpleCase.__init__( me, doc, inputDatabase, testingSamples)
        me._testDefaultTime = True

class TimedRangeTestCase( TimedTestSimpleCase):
    def testEach( me, t):
        res = None
        if me.obj:
            res = me.obj.age.getRange( trans=t.trans, validFrom=t.valid, validTo=t.validTo, include_deleted=False)
        return res

def test( Timed2_withDisabled_klas, verbosity =VERBOSE, title= None):
    Customer.Timed2_withDisabled_klas = Timed2_withDisabled_klas
    import testdata
    t1 = TimedTestSimpleCase(       'test2_idb2',   testdata.idb2,  testdata.test2)
    t2 = TimedTestSimpleCase(       'test0_idb0',   testdata.idb0,  testdata.test0)
    t3 = TimedTestSimpleCase(       'test1_idb1',   testdata.idb1,  testdata.test1)
    t4 = TimedCombinationsTestCase( 'testComb',     [],             testdata.testComb)
    t5 = TimedDefaultGetTestCase(   'test_default', testdata.idbDefault, testdata.testDefault)
    t6 = TimedRangeTestCase(        'test_range',   testdata.idb_range,  testdata.testRange)
    t7 = TimedTestSimpleCase(       'test_false',   testdata.idb_false,  testdata.test_false)
    t8 = TimedRangeTestCase(        'test_range_false', testdata.idb_false,  testdata.test_range_false)
    cases = [ t1, t2, t3, t4, t5, t6,
        #t7, t8     #fix these to work for SA too - cant as SA is strong-typed
    ]
    sep = '\n\n==================, '
    if title: print sep+title
    return testMain( cases, verbosity= verbosity)

# vim:ts=4:sw=4:expandtab
