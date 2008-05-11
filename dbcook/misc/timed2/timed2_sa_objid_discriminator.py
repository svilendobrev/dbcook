#$Id$
# -*- coding: cp1251 -*-

from sqlalchemy import select, func
from sqlalchemy.orm import class_mapper
_fmax = func.max

_debug = 0

def _get_discriminating_clause( klas, aliased_table):
    'needed if polymorphic'
    mapper = class_mapper( klas)

    discriminator_column = mapper.polymorphic_on
    if not discriminator_column: return None

    if aliased_table:   #XXX трябва да мине през aliased_table.corresponding_column()
        #import copy
        #discriminator_column = copy.copy( discriminator_column)
        #discriminator_column.table = aliased_table  #XXX is this legitimate use of .table???
        discriminator_column = aliased_table.corresponding_column( discriminator_column)
    #print '\n\nDISC_COL:', discriminator_column, discriminator_column.table

    discriminating_clause = discriminator_column.in_(
        [m.polymorphic_identity for m in mapper.polymorphic_iterator()])
    return discriminating_clause

def _timed_clause( klas, table, timeTrans, timeValid):
    t=table
    return (  (t.c.time_trans <= timeTrans)
            & (t.c.time_valid <= timeValid)
            & _get_discriminating_clause( klas, t) )     #seems needed but not proven by test

def get_time_clause( klas,  time,
            basemost_table, time2key_valid_trans,
            db_id_name ='id'
        ):
    timeValid, timeTrans = time2key_valid_trans( time)

    tbl = basemost_table
    t = tbl.alias('t')
    s = select( [
                _fmax( t.c.time_valid).label('time_valid'),
                t.c.obj_id
            ],
            _timed_clause( klas, t, timeTrans, timeValid),
            from_obj= [ t],
            group_by= [ t.c.obj_id ],
        ).alias('t1')

    if _debug: klas.debug_statement( s, 'DBG max( time_valid)')

    tt = tbl.alias('tt')
    s1 = select( [
                _fmax( tt.c.time_trans).label('time_trans'),
                tt.c.time_valid.label('time_valid'),
                tt.c.obj_id.label('obj_id')
            ],
            _timed_clause( klas, tt, timeTrans, timeValid),
            from_obj= [ tt.join( s,
                              (tt.c.obj_id == s.c.obj_id)
                            & (tt.c.time_valid == s.c.time_valid))],
            group_by= [ tt.c.obj_id, tt.c.time_valid],
        ).alias('t2')
    '''
test case for 'disappearing blake' is created blake with time_valid below current time and in the db there is
object(s) from other klas with same obj_id and time_valid > blake.time_valid
'''

    if _debug: klas.debug_statement( s1, 'DBG max( time_trans)')

    ttt = tbl   #.alias('ttt')
    s2 = select( [
            _fmax( getattr( ttt.c, db_id_name )).label( db_id_name),
            ] + _debug * [
                ttt.c.time_trans.label('time_trans'),
                ttt.c.time_valid.label('time_valid'),
                ttt.c.obj_id.label('obj_id')
            ],
            _get_discriminating_clause( klas, tbl),
            from_obj= [ ttt.join( s1,
                              (ttt.c.obj_id == s1.c.obj_id)
                            & (ttt.c.time_trans == s1.c.time_trans)
                            & (ttt.c.time_valid == s1.c.time_valid) )
            ],
            group_by= [ ttt.c.obj_id, ttt.c.time_trans, ttt.c.time_valid],
        )

    if _debug: klas.debug_statement( s2, 'DBG max( db_id)')

    timed_clause = s2.alias('timed')
    clause = (getattr( tbl.c, db_id_name) == getattr( timed_clause.c, db_id_name) )
    return clause   #s2

def get_time_range_clause( klas, obj_id, timeFrom, timeTo,
            basemost_table, time2key_valid_trans,
            group =True, db_id_name ='id'
        ):
    timeValidFrom, timeTrans = time2key_valid_trans( timeFrom)
    timeValidTo, timeTrans   = time2key_valid_trans( timeTo)
    if _debug: print '\n\nIN_TIMES:', timeTrans, timeValidFrom, timeValidTo

    tbl = basemost_table
    discriminating_clause = _get_discriminating_clause( klas, tbl)
    t = tbl #.alias('t')
    obj_clause = (t.c.obj_id == obj_id) & discriminating_clause
    where_clause = ( (t.c.time_trans <= timeTrans)
                   & (t.c.time_valid >= timeValidFrom)
                   & (t.c.time_valid <= timeValidTo) & obj_clause)

    if _debug: print '\nGROUP:', group
    if not group:
        return where_clause

    s = select( [
                _fmax( t.c.time_trans).label('time_trans'),
                t.c.time_valid
            ],
            where_clause,
            group_by= [ t.c.time_valid],
            from_obj = [t]
        ).alias('t1')
    if _debug: klas.debug_statement( s)

    s1 = select( [
                _fmax( getattr( t.c, db_id_name )).label( db_id_name),
                t.c.time_trans.label('time_trans'),
                t.c.time_valid.label('time_valid')
            ],
            obj_clause,
            from_obj= [ t.join( s,
                              (t.c.time_valid==s.c.time_valid)
                            & (t.c.time_trans==s.c.time_trans))],
            group_by= [ t.c.time_valid, t.c.time_trans],
        ).alias('t2')
    if _debug: klas.debug_statement( s1)

    #print 'S1:', s1
    timed_clause = s1.alias('timedr')
    clause = (getattr(tbl.c, db_id_name) == getattr( timed_clause.c, db_id_name) )
    #print 'ST:', clause
    return clause

if 0:
    #XXX tests only???
    @staticmethod
    def key_valid_trans2time( tkey):
        timeValid, timeTrans = tkey
        return timeTrans,timeValid
    @staticmethod
    def time2key_valid_trans( time):
        timeTrans, timeValid = time
        return timeValid,timeTrans

if 10:
    import sqlalchemy.orm
    if hasattr( sqlalchemy.orm.Mapper, '_equivalent_columns'):
        def equivs( parent): return parent._equivalent_columns
    elif hasattr( sqlalchemy.orm.Mapper, '_get_equivalent_columns'):
        def equivs( parent): return parent._get_equivalent_columns()
    else:
        def equivs( parent): return getattr( parent, '_Mapper__get_equivalent_columns')()

## model bases
def _hack_columns( q, time_stmt, with_valid =False, with_disabled =False):
    'describe WTF this does'
    #hackish code - TODO move this down to samanager maybe or get rid of this at all -
    #needed in polymorphic case

    #XXX
    ''' ТОВА не работи изобщо в 0.5 - няма подобни joinPoint, и най вероятно не е нужно'''

    joinPoint = q.filter( time_stmt)._joinpoint
    assert joinPoint
    dbg=0
    if dbg: print 'jjjjj joinPoint', joinPoint
    if dbg: print 'eeeee equivs', '\n'.join( '%s:%s' % kv for kv in equivs( joinPoint).iteritems() )
    try:
        tbl = time_stmt.left.table
    except AttributeError:
        print '\nWARNING problem in STMT:', time_stmt, time_stmt.__class__
        return (time_stmt, None)    #unmodified
    aliased_tbl = joinPoint.select_table
    if aliased_tbl is None: aliased_tbl = joinPoint.mapped_table
    if dbg: print 'aaaaa aliased_tbl', aliased_tbl #, aliased_tbl.columns
    if dbg: print 'bbbbb tbl', tbl
    #XXX
    ''' т'ва трябва да се пробва да се прави с joinPoint._get_equivalent_columns вместо
    с table.corresponding_column - виж dbcook/expression.py equivs() '''


    id_col = aliased_tbl.corresponding_column( time_stmt.left) #, keys_ok= True)
    if dbg: print 'iiiii id_col', id_col
    assert id_col is time_stmt.left

    if dbg: print 'ttttt time_stmt', time_stmt.left #, equivs( joinPoint)[ time_stmt.left ]
    if dbg: print 'j.c.disabled', joinPoint.c.disabled #, equivs( joinPoint)[ joinPoint.c.disabled ]
    if dbg: print 'j.c.time_valid', joinPoint.c.time_valid

    time_stmt = (id_col==time_stmt.right)
    if not with_disabled:
        disabled_col = aliased_tbl.corresponding_column( tbl.c.disabled) #, keys_ok= True)
        if dbg: print 'ddddd disabled_col', disabled_col, tbl.c.disabled
        assert disabled_col is tbl.c.disabled
        assert joinPoint.c.disabled is tbl.c.disabled
        time_stmt &= (~disabled_col)
    if with_valid:
        valid_col = aliased_tbl.corresponding_column( tbl.c.time_valid) #, keys_ok= True)
        if dbg: print 'vvvvv valid_col', valid_col, tbl.c.time_valid
        assert valid_col is tbl.c.time_valid
        assert joinPoint.c.time_valid is tbl.c.disabled
        time_stmt = (time_stmt, valid_col)
    return time_stmt

def get_all_objects_by_time( klas, query4klas, time, with_disabled =False, **kargs4timeclause):
    time_stmt = get_time_clause( klas, time, **kargs4timeclause)
    if _debug: print 'get_all_objects_by_time clause:', time_stmt
        #klas.debug_statement( time_stmt)
    q = query4klas
    time_stmt = _hack_columns( q, time_stmt, with_disabled= with_disabled)
    q = q.filter( time_stmt)
    if _debug: klas.debug_statement( q, 'full2timed stmt')
    #TODO .order_by( ime) if exist ime
    return q

def get_obj_history_in_timerange( klas, query4klas,  obj_id, timeFrom, timeTo, **kargs4timeclause):
    time_stmt = get_time_range_clause( klas, obj_id, timeFrom, timeTo, **kargs4timeclause)
    q = query4klas
    (time_stmt, valid_col) = _hack_columns( q, time_stmt, with_valid= True)
    q = q.filter( time_stmt)
    if valid_col: q = q.order_by( [valid_col])  #TODO this always
    return q

# vim:ts=4:sw=4:expandtab
