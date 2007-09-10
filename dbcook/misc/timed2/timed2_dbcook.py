#$Id$
# -*- coding: cp1251 -*-
'''Timed2 aspect'''

import timed2_sa_objid_discriminator as timed2

_debug_notimed = False

class Timed2Mixin( object):
    ''' requires the following fields in the database model object:
        db_id: uniq
        obj_id: distinguishes between different objects
        time_valid: time(stamp) of start of validity of the object - usually user-filled with default from the clock
        time_trans: time(stamp) of transaction - usually comes directly from the clock
       requires allInstances_basic() method
    '''
    __slots__ = ()

    #config
    BaseClas = object   #only subclasses of this are allowed to be bitemporal
    @classmethod
    def rootTable( klas ):
        raise NotImplementedError
        return mostBaseMappableDBTable_of_klas
    @classmethod
    def defaultTimeContext( klas):
        raise NotImplementedError
        return bitemporal_tuple
    db_id_name = 'dbid'    #dbcook.config.column4ID.name
    #eo config

    @classmethod
    def allInstances( klas, time= None, with_disabled =False):
        if not time: time = klas.defaultTimeContext()
        query4klas = klas.allInstances_basic()
        if _debug_notimed: return query4klas    #shunt4testing
        return timed2.get_all_objects_by_time( klas, query4klas,
                        time,
                        with_disabled= with_disabled,
                        basemost_table= klas.rootTable(),
                        time2key_valid_trans= klas.time2key_valid_trans,
                        db_id_name = klas.db_id_name
                )

    @classmethod
    def get_time_clause( klas, time= None):
        if not time: time = klas.defaultTimeContext()
        if _debug_notimed: return None    #shunt4testing
        assert issubclass( klas, klas.BaseClas), klas
        query4klas = klas.allInstances_basic()
        return timed2.get_time_clause( klas,
                        time,
                        basemost_table= klas.rootTable(),
                        time2key_valid_trans= klas.time2key_valid_trans,
                        db_id_name = klas.db_id_name
                    )

    @classmethod
    def get_obj_history_in_range( klas, obj_id, timeFrom= None, timeTo= None, group =True):
        if not timeFrom:
            timeTo = timeFrom = klas.defaultTimeContext()
        if _debug_notimed: return None    #shunt4testing
        assert issubclass( klas, klas.BaseClas), klas
        query4klas = klas.allInstances_basic()
        return timed2.get_obj_history_in_timerange( klas, query4klas,
                        obj_id, timeFrom, timeTo,
                        group= group,
                        basemost_table= klas.rootTable(),
                        time2key_valid_trans= klas.time2key_valid_trans,
                        db_id_name = klas.db_id_name
                )

    def key_valid_trans2time( tkey):
        timeValid, timeTrans = tkey
        return timeTrans,timeValid
    key_valid_trans2time = staticmethod( key_valid_trans2time)
    def time2key_valid_trans( time):
        timeTrans, timeValid = time
        return timeValid,timeTrans
    time2key_valid_trans = staticmethod( time2key_valid_trans)

#### end of Timed2 aspect

# vim:ts=4:sw=4:expandtab
