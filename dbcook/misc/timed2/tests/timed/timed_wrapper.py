#$Id$
# -*- coding: cp1251 -*-
from disabled import Disabled4Timed

class test_protocol2Timed_protocol( object):
    '''testing purposes only'''
    # needs:
    #.timed_get()
    #.timed_put()
    #.timed_getRange()
    #.NOT_FOUND

    @staticmethod
    def _valid_trans2time( valid, trans):
        return (trans,valid)

        # _Timed2_withDisabled_protocol:
    def get( me, trans, valid, with_disabled =False):
        r = me.timed_get(
                me._valid_trans2time( trans=trans, valid=valid),
                with_disabled= with_disabled
        )
        if r is me.NOT_FOUND: return None
        return r
    def getRange( me, trans, validFrom, validTo, with_disabled =False):
        return me.timed_getRange(
                me._valid_trans2time( trans=trans, valid=validFrom),
                me._valid_trans2time( trans=trans, valid=validTo),
                with_disabled= with_disabled
        )
    def put( me, value, trans, valid, disabled =False):
        return me.timed_put( value,
                me._valid_trans2time( trans=trans, valid=valid),
                disabled= disabled
        )

#    def __str__( me): return me.__class__.__name__ + '/' + str( me.__get)

class Timed2_Wrapper4Disabled( Disabled4Timed, test_protocol2Timed_protocol):
    '''testing purposes only'''
    def __init__( me, timed ):
        me.val = timed()
        me.NOT_FOUND = timed.NOT_FOUND

        # test_protocol2Timed_protocol:
    timed_get = Disabled4Timed._get
    timed_put = Disabled4Timed._put
    timed_getRange = Disabled4Timed._getRange

        # Disabled4Timed protocol:
    def _get_val( me, time, **kargs):   return me.val.get( time, **kargs )
    def _get_range_val( me, timeFrom, timeTo, **kargs): return me.val.getRange( timeFrom, timeTo, **kargs ) #not quite clear, but works
    def _put_val( me, value, time):     return me.val.put( value, time)

# vim:ts=4:sw=4:expandtab
