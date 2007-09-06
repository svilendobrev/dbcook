#$Id$
from datetime import datetime

def d( day):        return datetime( 2006, 9, day)
def dh( day, hour): return datetime( 2006, 9, day, hour)

class InitialState:
    def __init__( me, status, record, actual, value):
        me.status = status
        me.record = record
        me.actual = actual
        me.value = value
    def __str__( me): return 'DB: %(record)s %(actual)s %(value)s %(status)s' % me.__dict__
f = InitialState


idb0 = [  #   op   recDate  actDate val
            f( 'u', d(  8), d(  7), 15 ),
            f( 'd', d(  8), d( 10), 25 ),
            f( 'd', d( 10), d(  7), 10 ),
            f( 'u', d( 12), d(  5), 45 ),
            f( 'u', d( 12), d(  7), 35 ),
            f( 'd', d( 12), d( 10), 55 ),
]

class TestSample:
    def __init__( me, record, actual, ignoreStatusVal, expectedVal, name =''):
        me.record = record
        me.actual = actual
        me.ignoreStatusVal = ignoreStatusVal
        me.expected = expectedVal
        me.name = name
    def testData( me): return '%s %s' % (me.record, me.actual)
    def __str__( me): return 'SAMPLE: %s %s %s' % (me.record, me.actual, me.expected)
t = TestSample

# val1 - ignoring status
# val2 - taking status into account
test0 = [ #     trans   valid  val1  val2
            t(  d( 8),  d(10), 25  , None, 'exact trans and valid'),
            t(  d( 8),  d( 8), 15  , 15  , 'exact trans - valid between'),
            t(  d( 8),  d(12), 25  , None, 'exact trans - valid above max'),
            t(  d( 9),  d( 6), None, None, 'trans between - valid below min'),
            t(  d( 9),  d( 7), 15  , 15  , 'trans between - valid exact min'),
            t(  d( 9),  d( 8), 15  , 15  , 'trans between - valid between'),
            t(  d(15),  d( 4), None, None, 'trans above max - valid below min'),
            t(  d(15),  d(15), 55  , None, 'both above max'),
            t(  d( 1),  d( 1), None, None, 'both below min'),
]

idb1 = [
            f( 'u', d( 7), d(  7),  5 ),
            f( 'd', d( 7), d(  7), 10 ),
            f( 'u', d( 7), d(  7), 15 ),
            f( 'd', d( 7), d(  7), 20 ),

            f( 'u', d( 5), d( 11), 25 ),
            f( 'd', d( 1), d( 14), 30 ),
            f( 'u', d( 8), d(  8), 35 ),
            f( 'd', d( 3), d(  9), 40 ),
            f( 'u', d( 6), d(  9), 45 ),
            f( 'u', d( 8), d(  8), 50 ),
]

test1 = [
            t( d(  7), d(  7),   20, None, 'both exact-in db several same records'),
            t( d(  4), d( 11),   40, None, 'both - between'),
            t( d(  4), d(  4), None, None, 'both - between and same'),
            t( d( 15), d( 12),   25,   25, 'trans above max - valid between'),
            t( d(  4), d( 18),   30, None, 'trans between - valid above max'),
]

idb2 = [
        f( 'd', d( 5) , d( 15), 100),
        f( 'u', d( 7) , d(  9), 10 ),
        f( 'd', d( 7) , d( 11), 15 ),
        f( 'u', d( 9) , d(  9), 20 ),
        f( 'u', d( 9) , d( 11), 25 ),
        f( 'd', d( 11), d(  9), 30 ),
        f( 'u', d( 11), d( 11), 35 ),
        f( 'u', d( 11), d( 16), 45 ),
        f( 'u', d( 18), d( 18), 75 ),
        f( 'u', d( 18), d( 18), 65 ),
]

test2 = [
         t( d( 15), d(  9),  30, None, 'trans between, valid exact, trans > valid'),
         t( d(  9), d( 15), 100, None, 'both exact, trans < valid'),
         t( d( 12), d( 18),  45,   45, 'trans between - valid exact as max'),
         t( d(  9), d( 16), 100, None, 'both exact - trans > valid'),
         t( d(  7), d(  9),  10,   10, 'both exact - trans > valid _2'),
         t( d(  7), d( 10),  10,   10, 'trans exact, valid between'),
         t( d(  7), d( 12),  15, None, 'trans exact, valid between _2'),
         t( d( 18), d( 18),  65 ,  65, 'both exact as max, db have same records'),
         t( d( 19), d( 17),  45 ,  45, 'suspicious for bug'), #pants crash
]

idb3 = [
            f( 'u', d(  8), d(  3), 50 ),
            f( 'u', d(  8), d(  3), 55 ),
            f( 'u', d(  4), d(  3), 60 ),
            f( 'd', d( 12), d(  3), 65 ),
            f( 'u', d( 14), d(  3), 70 ),

            f( 'u', d(  8), d(  7),  5 ),
            f( 'd', d(  8), d(  7), 10 ),
            f( 'u', d(  4), d(  7), 15 ),
            f( 'u', d( 12), d(  7), 20 ),

            f( 'u', d(  8), d( 10), 25 ),
            f( 'u', d(  8), d( 10), 30 ),
            f( 'u', d(  4), d( 10), 35 ),
            f( 'd', d( 12), d( 10), 40 ),
            f( 'u', d( 14), d( 10), 45 ),
        ]

test3 = [
         t( d(  1), d(  1), None, None, ''),
         t( d(  1), d(  3), None, None, ''),
         t( d(  1), d(  4), None, None, ''),

         t( d(  4), d(  1), None, None, ''),
         t( d(  4), d(  3),   60,   60, ''),
         t( d(  4), d(  4),   60,   60, ''),

         t( d(  6), d(  1), None, None, ''),
         t( d(  6), d(  3),   60,   60, ''),
         t( d(  6), d(  4),   60,   60, ''),
         t( d(  6), d(  7),   60,   60, ''),
         t( d(  6), d(  8),   15,   15, ''),
        # more to be added
        ]


idb4 = [
            f( 'u', d(  8), d(  3), 55 ),
            f( 'd', d(  4), d(  3), 60 ),
            f( 'd', d( 12), d(  3), 65 ),
            f( 'u', d( 14), d(  3), 70 ),

            f( 'u', d(  8), d(  7),  5 ),
            f( 'd', d(  8), d(  7), 10 ),
            f( 'd', d(  4), d(  7), 15 ),
            f( 'u', d( 12), d(  7), 20 ),

            f( 'd', d(  8), d( 10), 30 ),
            f( 'u', d(  4), d( 10), 35 ),
            f( 'u', d( 12), d( 10), 40 ),
            f( 'd', d( 14), d( 10), 45 ),
        ]


datetime_max = datetime( 2078, 12, 31)  #was datetime.max but mssql smalldatetime supports max 20790601
dm_1 = datetime_max.replace( year =datetime_max.year-1)
idbDefault = idb2 + [
        f( 'u', datetime_max, datetime_max, 18 ),
        f( 'u', dm_1, dm_1, 1821 ),

]
testDefault = [
         t( None, None,  65, 65, 'default object (not same as last one)'),
]

def d2( day): return datetime( 2006, 2, day)

testComb = [
            t( d2(  7), d2( 12),  53, 53, ''),
            t( d2( 12), d2(  2),   4,  4, '' ),
            t( d2( 11), d2(  1),   4,  4, '' ),
            t( d2(  1), d2( 11),  50, 50, '' ),
            t( d2( 25), d2(  2),   8,  8, '' ),
            t( d2(  2), d2( 25),  90, 90, '' ),
            t( d2( 25), d2(  7),  38, 38, '' ),
            t( d2(  7), d2( 25),  93, 93, '' ),
            t( d2( 25), d2( 25),  99, 99, '' ),
]

class RangeSample( TestSample):
    def __init__( me, record, actualFrom, actualTo, ignoreStatusVal, expectedVal, name =''):
        TestSample.__init__( me, record, actualFrom, ignoreStatusVal, expectedVal, name)
        me.actualTo = actualTo
    def testData( me): return '%s %s-%s' % (me.record, me.actual, me.actualTo)
    def __str__( me): return 'SAMPLE: %s %s %s %s' % (me.record, me.actual, me.actualTo, me.expected)
t = RangeSample

from copy import copy
def idb2RangeItem( it):
    i = copy( it)
    i.status = 'u'  #TODO check that getRange supports enabled/disabled too
    return i
idb_range = [idb2RangeItem( each) for each in idb2]
idb_range += f( 'u', d( 11), d( 14), 35 ),

testRange = [
         t( d(  9), d( 15), d( 11), 100 ,   []
            , 'all exact, from > to, trans < valid'),
         t( d( 12), d( 18), d( 18),  45 ,   []
            , 'trans between, from/to exact as max'),
         t( d( 11), d( 12), d( 14),  15,    [35]      #XXX blowing oldGetRage
            , 'trans exact, valids between _2'),
         t( d( 15), d(  9), d( 11),  30 ,   [30,35]
            , 'trans between, from/to exact, trans > valid, >1 res'),
         t( d(  7), d(  8), d( 12),  10,    [10,15]
            , 'trans exact, from below min, to between, >1 res'),
         t( d( 19), d( 10), d( 17),  10,    [35,35,100,45]  #XXX blowing oldGetRage
            , 'trans above max, valids between, db-same records'),
         t( d(  9), d( 11), d( 16), 100,    [25,100]
            , 'all exact, trans < valid from/to'),
         t( d( 18), d( 18), d( 18),  65 ,   [65]
            , 'all exact as max, db-same records'),
# TODO cases with dh
]
# tests for evaluated to False objects with same times in state and in query
# tests for getrange with empty init state and state with 1 record and test with ix_from = 0
idb_false = [
            f( 'u', d( 6), d(  6), None),
            f( 'u', d( 6), d(  6), False),
            f( 'u', d( 6), d(  6), []),
            f( 'u', d( 6), d(  6), 0),

            f( 'u', d( 7), d(  7), None),
            f( 'u', d( 7), d(  7), False),
            f( 'u', d( 7), d(  7), 0),
            f( 'u', d( 7), d(  7), []),

            f( 'u', d( 8), d(  8), False),
            f( 'u', d( 8), d(  8), 0),
            f( 'u', d( 8), d(  8), []),
            f( 'u', d( 8), d(  8), None),

            f( 'u', d( 9), d(  9), None),
            f( 'u', d( 9), d(  9), 0),
            f( 'u', d( 9), d(  9), []),
            f( 'u', d( 9), d(  9), False),
]

t = TestSample
test_false = [
            t( d(  6), d(  6),    0,    0, 'exact in db, last 0'),
            t( d(  7), d(  7),    0,   [], 'exact in db, last empty collection'),
            t( d(  8), d(  8), None, None, 'exact in db, last None'),
            t( d(  9), d(  9),    0,False, 'exact in db, last False'),
]

class RangeSample( RangeSample):
    def testResult( me, res): return '\nRESULT: %s ; EXPECTED: %s\n' % (res, me.expected)
t = RangeSample
test_range_false = [
         t( d( 9), d( 6), d( 9), 100 ,   [0,[],None,False]
            , 'all exact, from > to, trans >= valid'),
         t( d(19), d( 2), d(19), 100 ,   [0,[],None,False]
            , 'valid outside, trans above, from > to, trans >= valid'),
]
# vim:ts=4:sw=4:expandtab
