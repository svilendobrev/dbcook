#$Id$
# -*- coding: cp1251 -*-
'''Timed2 aspect'''

import config
import timed2_sa_objid_discriminator as timed2

class Timed2Mixin( config.BaseClass4Mixin):
    ''' requires the following fields in the database model object:
        db_id: uniq
        obj_id: distinguishes between different objects
        time_valid: time(stamp) of start of validity of the object - usually user-filled with default from the clock
        time_trans: time(stamp) of transaction - usually comes directly from the clock
       requires allInstances_basic() method
    '''
    __slots__ = ()

    time_valid  = config.ValidTimeType()
    time_trans  = config.TransTimeType()

    #config
    rootTable           = classmethod( config.rootTable)
    defaultTimeContext  = classmethod( config.defaultTimeContext)
    now = config.now
    #eo config

    @classmethod
    def allInstances( klas, time= None, with_disabled =False):
        if time is None: time = klas.defaultTimeContext()
        query4klas = klas.allInstances_basic()
        if config.runtime.notimed: return query4klas    #shunt4testing
        return timed2.get_all_objects_by_time( klas, query4klas,
                        time,
                        with_disabled= with_disabled,
                        basemost_table= klas.rootTable(),
                        time2key_valid_trans= klas.time2key_valid_trans,
                        db_id_name = config.db_id_name
                )

    @classmethod
    def get_time_clause( klas, time= None):
        if time is None: time = klas.defaultTimeContext()
        if config.runtime.notimed: return None    #shunt4testing
        assert issubclass( klas, config.BaseClass4check), klas
        query4klas = klas.allInstances_basic()
        return timed2.get_time_clause( klas,
                        time,
                        basemost_table= klas.rootTable(),
                        time2key_valid_trans= klas.time2key_valid_trans,
                        db_id_name = config.db_id_name
                    )

    @classmethod
    def get_obj_history_in_range( klas, obj_id, timeFrom= None, timeTo= None, group =True):
        if timeFrom is None:
            timeTo = timeFrom = klas.defaultTimeContext()
        if config.runtime.notimed: return None    #shunt4testing
        assert issubclass( klas, config.BaseClass4check), klas
        query4klas = klas.allInstances_basic()
        return timed2.get_obj_history_in_timerange( klas, query4klas,
                        obj_id, timeFrom, timeTo,
                        group= group,
                        basemost_table= klas.rootTable(),
                        time2key_valid_trans= klas.time2key_valid_trans,
                        db_id_name = config.db_id_name
                )

    def key_valid_trans2time( tkey):
        timeValid, timeTrans = tkey
        return timeTrans,timeValid
    key_valid_trans2time = staticmethod( key_valid_trans2time)
    def time2key_valid_trans( time):
        timeTrans, timeValid = time
        return timeValid,timeTrans
    time2key_valid_trans = staticmethod( time2key_valid_trans)

    def pre_save( me):
        trans = me.now()
        if not config.runtime.forced_trans:
            me.time_trans = trans
        if config.runtime.validAsTrans:
            me.time_valid = me.time_trans
        elif not me.time_valid:
            me.time_valid = trans

#### end of Timed2 aspect

# vim:ts=4:sw=4:expandtab
