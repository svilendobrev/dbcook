#$Id$
# -*- coding: cp1251 -*-
'''Timed2 aspect'''

import timed2_sa_objid_discriminator as timed2

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
    BaseClass4check = object   #only subclasses of this are allowed to be bitemporal
    @classmethod
    def rootTable( klas ):
        raise NotImplementedError
        return mostBaseMappableDBTable_of_klas
    @classmethod
    def defaultTimeContext( klas):
        raise NotImplementedError
        return bitemporal_tuple     #type,order XXX ???
    def now( me):
        raise NotImplementedError
        return transaction_time     #type same as me.time_valid and me.time_trans
    class config:
        forced_trans = False
        validAsTrans = False
        notimed = False
    db_id_name = 'dbid'    #dbcook.config.column4ID.name
    #eo config

    @classmethod
    def allInstances( klas, time= None, with_disabled =False):
        if time is None: time = klas.defaultTimeContext()
        query4klas = klas.allInstances_basic()
        if klas.config.notimed: return query4klas    #shunt4testing
        return timed2.get_all_objects_by_time( klas, query4klas,
                        time,
                        with_disabled= with_disabled,
                        basemost_table= klas.rootTable(),
                        time2key_valid_trans= klas.time2key_valid_trans,
                        db_id_name = klas.db_id_name
                )

    @classmethod
    def get_time_clause( klas, time= None):
        if time is None: time = klas.defaultTimeContext()
        if klas.config.notimed: return None    #shunt4testing
        assert issubclass( klas, klas.BaseClass4check), klas
        query4klas = klas.allInstances_basic()
        return timed2.get_time_clause( klas,
                        time,
                        basemost_table= klas.rootTable(),
                        time2key_valid_trans= klas.time2key_valid_trans,
                        db_id_name = klas.db_id_name
                    )

    @classmethod
    def get_obj_history_in_range( klas, obj_id, timeFrom= None, timeTo= None, group =True):
        if timeFrom is None:
            timeTo = timeFrom = klas.defaultTimeContext()
        if klas.config.notimed: return None    #shunt4testing
        assert issubclass( klas, klas.BaseClass4check), klas
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

    def pre_save( me):
        trans = me.now()
        if not me.config.forced_trans:
            me.time_trans = trans
        if me.config.validAsTrans:
            me.time_valid = me.time_trans
        elif not me.time_valid:
            me.time_valid = trans

#### end of Timed2 aspect

# vim:ts=4:sw=4:expandtab
