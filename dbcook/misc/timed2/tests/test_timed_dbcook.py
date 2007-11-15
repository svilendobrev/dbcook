#$Id$
# -*- coding: cp1251 -*-
'''
this must test all additional aspects of bitemporal behaviour in "real database":
    - allInstances from certain TimeContext point of view, with >1 timed objects in same db table
    - range of history records for one concrete timed object
        between 2 certain TimeContexts - from to
it uses more basic testing data from engine/timed that tests only bitemporal behavior by its one
when obj is alone in the table/collection. These must be tested with simple and with polymorphic
klasses. Supposes that simple db aspects as allinstances_basic are working perfectly.

subject under test:
    def get_time_clause( klas, time= defaultTimeContext(), only_value =True):
    def get_obj_history_in_range( klas, obj_id, timeFrom= defaultTimeContext(),
            timeTo= defaultTimeContext(), group =True):
'''
import timed.tests.test_base as satest

if 0:
    from dbcook.usage.static_type import sa2static as orm
    from static_type.types.atomary  import Number
else:
    from dbcook.usage import plainwrap as orm
    class Number( orm.Type): pass

import dbcook.usage.samanager as sam
SAdb = sam.SAdb
SAdb.Builder = orm.Builder

import sqlalchemy
SAdb.fieldtypemap = { Number: dict( type= sqlalchemy.Integer, ), }

class Config( sam.config.Config):
    repeat      = 1
    notimed     = False
    _help = '''
test_timed:
  repeat= :: number of times to test each sample
  notimed :: not used here
'''
config = Config( sam.config )
sam.config = config

class TEST:
    only_days = True
    Time = only_days and Number or Date
    @classmethod
    def _timeconvert1( klas, time):
        if klas.only_days: return time.day
        return time.date()
    PolymBase = None            #must be set before run
    PolymLeaf = None            #must be set before run
    ObjectCounter = None        #must be set before run
    config = config             #XXX
    namespace = None            #must be set before run
    NUM_OF_OBJID = 3
    DB = None

import dbcook.misc.timed2.config as timed2_config
timed2_config.db_id_name    = orm.builder.column4ID.name
timed2_config.ValidTimeType = TEST.Time
timed2_config.TransTimeType = TEST.Time
import dbcook.misc.timed2.timed2_dbcook as timed2


def setupBase( me):
    if getattr( TEST.DB, 'sa', None): TEST.DB.sa.destroy()
    me.db = TEST.DB.reset( TEST.namespace, counterBase= TEST.ObjectCounter, recreate= True, get_config= False) #XXX DBCookTest

def setupSimple( me):
    setupBase( me)
    satest.Case.setup( me)
    TEST.DB.session.flush()

def setupEach_diff_klas( me, f):
    me.oldSetupEach( f)
    me.obj.age.timed.val = TEST.PolymLeaf()
    me.oldSetupEach( f)
    me.obj.age.timed.val = TEST.PolymBase()

def setupSimple_objid( me):
    setupBase( me)
    for i in range( 1, TEST.NUM_OF_OBJID+1): #obj_id 0 means autoinc
        me.obj.age.timed.val.__class__.OBJ_ID = i #Ooh poor Demeter, Demeter.....
        satest.Case.setup( me)
        #print 'SETUP: %s' % me.obj.age.timed.val.__class__.OBJ_ID
    me.obj.age.timed.val.__class__.OBJ_ID = 1
    TEST.DB.session.flush()

def setupCombination( me):
    setupBase( me)
    me.oldSetup()
    TEST.DB.session.flush()

def setupCombination_objid( me):
    setupBase( me)
    for i in range( 1, TEST.NUM_OF_OBJID+1):
        me.obj.age.timed.val.__class__.OBJ_ID = i
        me.oldSetup()
    me.obj.age.timed.val.__class__.OBJ_ID = 1
    TEST.DB.session.flush()

def testEach_timed_base( me, t):
    for i in range( int( TEST.config.repeat)):
        res = me.oldTestEach( t)
    return res

# as testdata expects single result expected is wrapped into list
def singleObjId( t):
    if t.expected: t.expected = [ t.expected]
    return t
def multyObjId( t):
    if t.expected: t.expected = [ t.expected for i in range( TEST.NUM_OF_OBJID)]
    return t

def testEach_timed( me, t): return testEach_timed_base( me, singleObjId( t))
def testEach_timed_objid( me, t): return testEach_timed_base( me, multyObjId( t))

def testEach_default_base( me, t):
    print "- STUB - Not actually testing",
    import datetime
    res = None
    if me.obj:
        t.record = t.actual = datetime.datetime( 2007, 1, 27)
        res = me.obj.age.get( trans=t.record, valid=t.actual, include_deleted=False)
    return res

def testEach_default( me, t): return testEach_default_base( me, singleObjId( t))
def testEach_default_objid( me, t): return testEach_default_base( me, multyObjId( t))

from timed.timed_wrapper import Timed_Wrapper4Disabled
class Timed_Wrapper( Timed_Wrapper4Disabled):
    '''testing purposes only'''
    def __init__( me, timed =TEST.PolymBase):
        Timed_Wrapper4Disabled.__init__( me, timed)
    def _timeconvert( me, time):
        return tuple( TEST._timeconvert1(t) for t in time )

    def _get_val( me, time, **kargs):
        time = me._timeconvert( time)
        q = me.val.allInstances( time, **kargs )
        res = [ getattr( each, 'val', each) for each in q ] or None
        return res
    def _get_range_val( me, timeFrom, timeTo, **kargs):
        q = me.val.get_obj_history_in_range( me.val.OBJ_ID, timeFrom, timeTo).all()
        return [ getattr( each, 'val', each) for each in q ]
    def _put_val( me, value, time):
        return me.val.put( value, time)
    def getRange( me, trans, validFrom, validTo, include_deleted =False):
        trans, validFrom, validTo = me._timeconvert( (trans, validFrom, validTo) )
        return Timed_Wrapper4Disabled._getRange( me, (trans, validFrom), (trans, validTo), include_disabled=include_deleted)


def tm2_simple():   return Timed_Wrapper( TEST.PolymLeaf)
def tm2_poly():     return Timed_Wrapper( TEST.PolymBase)

def run( config):
    TEST.config = config
    timed2_config.runtime = config
    config.getopt()
    timed2_config.runtime.forced_trans = True
    print config

    #single OBJ_ID suites
    satest.TimedTestSimpleCase.setup = setupSimple
    satest.TimedTestSimpleCase.oldTestEach = satest.TimedTestSimpleCase.testEach
    satest.TimedTestSimpleCase.testEach = testEach_timed
    satest.TimedCombinationsTestCase.oldSetup = satest.TimedCombinationsTestCase.setup
    satest.TimedCombinationsTestCase.setup = setupCombination
    satest.TimedDefaultGetTestCase.testEach = testEach_default
    rr = satest.test( staticmethod( tm2_poly), True, title ='base only - single obj-type')
    rr = rr and satest.test( staticmethod( tm2_simple), True, title ='leafs only, both types available')
    satest.TimedTestSimpleCase.oldSetupEach = satest.TimedTestSimpleCase.setupEach
    satest.TimedTestSimpleCase.setupEach = setupEach_diff_klas
    rr = rr and satest.test( staticmethod( tm2_poly), True, title ='base+leafs via base')

    # many OBJ_IDs suites, same testdata for every OBJ_ID
    satest.TimedTestSimpleCase.setup = setupSimple_objid
    satest.TimedCombinationsTestCase.setup = setupCombination_objid
    satest.TimedTestSimpleCase.testEach = testEach_timed_objid
    satest.TimedCombinationsTestCase.testEach = testEach_timed_objid
    satest.TimedDefaultGetTestCase.testEach = testEach_default_objid
    rr = rr and satest.test( staticmethod( tm2_poly), True, title ='base only - single obj-type, many OBJIDs')
    rr = rr and satest.test( staticmethod( tm2_simple), True, title ='leafs only, both types available, many OBJIDs')
    satest.TimedTestSimpleCase.setupEach = setupEach_diff_klas
    rr = rr and satest.test( staticmethod( tm2_poly), True, title ='base+leafs via base, many OBJIDs')

    print '\nTOTAL RESULT:', rr and 'OK' or 'Failed'
    print


if __name__ == '__main__':

    class DB_( object):
        session = None #have flush()
        def reset( me, namespace, counterBase= None, recreate =True, get_config =False):
            me.sa = SAdb()
            me.sa.open( recreate=True)
            me.sa.bind( namespace, base_klas=orm.Base) #, force_ordered= True)
            me.session = me.sa.session()
            if counterBase: counterBase.fill( *me.sa.klasi.iterkeys() )
        def save( me, *args):
            assert args
            me.sa.saveall( me.session, *args)
            me.session.flush()

    TEST.DB = DB_()
    class PolymBase( orm.Base, timed2.Timed2Mixin):
        #Timed2Mixin setup
        #BaseClass4check = object   #default ok
        @classmethod
        def rootTable( klas ): return TEST.DB.sa.rootTable( klas)
        #defaultTimeContext = .. not needed
        def now( me): return TEST._timeconvert1( datatime.now() )
        #eo Timed2Mixin
        def pre_save( me): pass     #stub

        DBCOOK_has_instances = True
        DBCOOK_inheritance = 'joined_table'
        N_TIMES = 2
        class NOT_FOUND: pass

        # bitemporal-required fields - TODO move in separate mixins
        obj_id      = Number()
        disabled    = Number()
        # eo

        val = Number()
        OBJ_ID = 1  #for multiple obj testing

        @classmethod
        def allInstances_basic( klas):
            return TEST.DB.session.query( klas)
        def put( me, obj, time ):
            tn = me.__class__()
            timeValid, timeTrans = me.time2key_valid_trans( time)
            tn.time_valid, tn.time_trans = timeValid.day, timeTrans.day
            #print "put times:", tn.time_trans, tn.time_valid
            if not isinstance( obj, int): obj = None
            #print 'OBJ_ID: %s:%s' % ( me.OBJ_ID, me.__class__.OBJ_ID)
            tn.obj_id = me.OBJ_ID
            tn.val = obj
            tn.disabled = (obj is None)
            #print 'OBJ:', obj, tn.disabled
            TEST.DB.save( tn)
            return tn

    class PolymLeaf( PolymBase): pass
    TEST.namespace = locals()
    TEST.PolymBase = PolymBase
    TEST.PolymLeaf = PolymLeaf
    run( config)

# vim:ts=4:sw=4:expandtab
