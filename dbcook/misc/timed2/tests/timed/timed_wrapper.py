#$Id$
# -*- coding: cp1251 -*-
from disabled import Disabled4Timed

class Timed_Wrapper4Disabled( Disabled4Timed):  #wrap
    '''testing purposes only'''
    def __init__( me, timed ):
        me.val = timed()
        me.N_TIMES = timed.N_TIMES
        me.NOT_FOUND = timed.NOT_FOUND

        # from Disabled4Timed
    def _get_val( me, time, **kargs):   return me.val.get( time, **kargs )
    def _get_range_val( me, timeFrom, timeTo, **kargs): return me.val.getRange( timeFrom, timeTo, **kargs ) #not quite clear, but works
    def _put_val( me, value, time):     return me.val.put( value, time)
        # from _Timed2_withDisabled_protocol
    def get( me, trans, valid, include_deleted =False):
        r = Disabled4Timed._get( me, (trans,valid), include_disabled=include_deleted)
        if r is me.NOT_FOUND: return None
        return r
    def getRange( me, trans, validFrom, validTo, include_deleted =False): #not quite clear, but works
        return Disabled4Timed._getRange( me, (trans,validFrom), (trans,validTo), include_disabled=include_deleted)
    def put( me, value, trans, valid, deleted =False):
        return Disabled4Timed._put( me, value, (trans,valid), disabled=deleted)

    def __str__( me): return 'Timed_Wrapper/'+str(me.val)


# vim:ts=4:sw=4:expandtab
