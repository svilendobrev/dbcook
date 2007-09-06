#$Id$
# -*- coding: cp1251 -*-

from timed1 import Timed1
import bisect

def range_date( dateFrom, dateTo):
    from datetime import timedelta
    tdelta = dateTo - dateFrom
    res = [dateFrom + timedelta( days) for days in range( tdelta.days+1)] #+1 same as stepper; list compr. or gener. expr.???
    return res

class Timed2( Timed1):
    '''
    2-времева история върху 1-времева
    put() и get() са пренаписани така че тези от timed1 са скрити.
    преобразуването time (timeTrans, timeValid по подразбиране) <-> правилния ключ (вальор,транзакция),
    става с key_valid_trans2time() / time2key_valid_trans().

    bi-temporal over 1-temporal
    '''

    N_TIMES = 2

    #тези може да се подменят - преводачи от/към ключа и външното време
    #by default, time=(trans,valid)
    def key_valid_trans2time( tkey):
        timeValid, timeTrans = tkey
        return timeTrans,timeValid
    key_valid_trans2time = staticmethod( key_valid_trans2time)
    def time2key_valid_trans( time):
        timeTrans, timeValid = time
        return timeValid,timeTrans
    time2key_valid_trans = staticmethod( time2key_valid_trans)

    def put( me, obj, time ):
        return Timed1.put( me, obj, me.time2key_valid_trans( time) )

    def _rkey_obj( me, ix):
            r = me.order[ix]
            rkey = r[0]      #skip the middle stepper
            robj = r[-1]
            return rkey, robj
    def _value_or_tuple( me, rkey, robj, only_value):
        if only_value: return robj
        return me.key_valid_trans2time( rkey), robj

    def get( me, time, only_value =True):
        timeValid, timeTrans = tkey = me.time2key_valid_trans( time)
        ix = me._get_ix( tkey)
        while ix:
            ix -= 1
            rkey, robj = me._rkey_obj( ix)
            i_timeValid, i_timeTrans = rkey
            if i_timeTrans <= timeTrans:
                return me._value_or_tuple( rkey, robj, only_value)
        #not found at all
        return me.NOT_FOUND
    def getRange( me, timeFrom, timeTo, only_value =True):
        '''simple getrange with range for valid and single trans
        both times consist of trans and valid. for now only case with
        trans = const is implemented'''
#        print 'GETRANGE: %(timeFrom)s %(timeTo)s' % vars()
        timeValidFrom, timeTrans = tkeyFrom = me.time2key_valid_trans( timeFrom)
        timeValidTo, timeTrans = tkeyTo   = me.time2key_valid_trans( timeTo)
        ixFrom, ixTo = me._get_ix2( tkeyFrom, tkeyTo )
#        print 'IXs: %(ixFrom)s - %(ixTo)s' % vars()
        order = me.order
        res = []
        lastTimeValid, lastTimeTrans = order[ min( ixTo, len(order)-1)][0]
        while ixTo > ixFrom:
            ixTo -= 1
            rkey, robj = me._rkey_obj( ixTo)
            i_timeValid, i_timeTrans = rkey
            if ( (i_timeValid < lastTimeValid or ixTo == len(order)-1)
                    and i_timeTrans <= timeTrans
                    and timeValidFrom <= i_timeValid
                    and i_timeValid <= timeValidTo
                ):
                lastTimeValid = i_timeValid
                resItem = me._value_or_tuple( rkey, robj, only_value)
                res.append( resItem)
        res.reverse()
        return res

########

from timed1 import Test0
class Test( Test0):
    input_times = [ #trans,valid
         (20060801, 20060901),
         (20060901, 20060901),
         (20061101, 20060901),
         (20061101, 20061002),
    ]
    cases= [  # trans,   valid      name            resultindex
            [ (20061101, 20061002), 'exact'         ,4  ],
            [ (20061101, 20060901), 'exact1'        ,3  ],
            [ (20060901, 20060901), 'exact2'        ,2  ],
            [ (20060900, 20060901), '1 step-before' ,1  ],
            [ (20060910, 20060901), 'between'       ,2  ],
            [ (20060202, 20060901), 'before all'    ,None],
            [ (20061212, 20060901), 'after all'     ,3  ],
            [ (20061212, 20060707), 'after all/before all' ,None ],
            [ (20061213, 20060907), 'after all/before all' ,3 ],
           ]

    input2time = staticmethod(
        lambda (t,v): (t,v) )
    timekey2input = staticmethod(
        lambda timed, k: timed.key_valid_trans2time( k) )
    input_printer = staticmethod(
        lambda (t,v): 't=%(t)s, v=%(v)s' % locals() )


if __name__ == '__main__':
    t = Timed2()
    test = Test()
    objects = test.fill( t, [1,3,2,4] )
    test.test_db( t)
    test.test_get( t, objects )
    test.exit()

# vim:ts=4:sw=4:expandtab
