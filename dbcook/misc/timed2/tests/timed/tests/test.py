#$Id$
# -*- coding: cp1251 -*-
from test_base import *

if __name__ == '__main__':
    from timed_wrapper import Timed_Wrapper4Disabled
    from timed2 import Timed2
    def tm2(): return Timed_Wrapper4Disabled( Timed2)
    test( staticmethod(tm2) )

if 0:
    class Customer2( Timed2_withDisabled):
        def __init__( me ):
            Timed2_withDisabled.__init__( me, Timed2)
            me.name   = me.age    = me.gender = None    #????
        def get( me, time, include_deleted =False):
            r = Timed2_withDisabled.get( me, time, include_deleted )
            return r.age

# vim:ts=4:sw=4:expandtab
