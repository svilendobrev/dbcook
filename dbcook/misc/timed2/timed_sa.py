#$Id$
# -*- coding: cp1251 -*-

'''
 times: 1t/2t
 last_ver
    upto_time / any
    single obj / many/ all obj
 all_ver-history in time range
    single obj / many/ all obj
 result: clause / query
'''
from sqlalchemy import select, func

class _versions( object):
    def __init__( me, query, **kargs):
        me.query = query
        me._initkargs( **kargs)

    _where0 = None
    def _get_where( me, where =None):
        where0 = me._where0
        if where0:
            if where: return where0 & where
            return where0
        return where

    def _query( me, filter, query =None):
        if query is None: query = me.query
        return query.filter( filter)

    def single_lastver( me, oid_value, where =None, query =None ):
        '''1t: last version of single object / последната версия на един обект'''
        if query is None: query = me.query
        where = me._get_where( where)
        if where: query = query.filter( where)
        return query.filter( me.c_oid == oid_value
                    ).order_by( *(c.desc() for c in me._order_by4single() )
                    ).first()

    _upto_time_value = None
    def upto_time( me, time):
        '''before and inclusive time'''
        me._upto_time_value = time
        if time is None: return None
        me._where0 = me._upto_time( time)
        return me

    def single_lastver_upto_time( me, oid, time, where =None):
        return me.upto_time( time).single_lastver( oid, where=where)

    def _initkargs( me, time_attr, oid_attr ='obj_id', dbid_attr ='db_id', klas =None ):
        if not klas: klas = me.query.mapper.class_
        me.klas = klas
        me.c_oid  = getattr( klas, oid_attr ).expression_element()
        me.c_time = getattr( klas, time_attr).expression_element()
        me.c_dbid = dbid_attr and getattr( klas, dbid_attr ).expression_element()


class versions_1t( _versions):
    def _order_by4single( me): return me.c_time, me.c_dbid
    def _upto_time( me, time):
        '''before and inclusive time'''
        return me.c_time <= time

    def _alv_1( me, where =None, alias ='g1'):
        where = me._get_where( where)
        c_oid  = me.c_oid
        c_time = me.c_time

        g1 = select( [  c_oid.label( 'oid'),
                        func.max( c_time).label( 'time')
                    ], where
                ).group_by( c_oid
                ).alias( alias)
        where1 = ( (c_oid== g1.c.oid) & (c_time== g1.c.time) )
        return g1, where1

    c_time2 = None
    def _alv_2_dbid( me, where =None, no_oid =False, alias =None):
        #1t:  sel1=oid,time,dbid       sel2=max/dbid           group_by=oid,time         where=c_dbid==g2.dbid
        #     no_dbid=0, c_time2=0
        #2t-b:sel1=oid,time,time2,dbid sel2=max/dbid           group_by=oid,time,time2   where=c_dbid==g2.dbid
        #     no_dbid=0, c_time2=1

        c_oid  = not no_oid and me.c_oid or None
        c_time = me.c_time
        c_dbid = me.c_dbid
        c_time2= me.c_time2

        t = select( [                   c_time.label( 'time'  ),
                                        c_dbid.label( 'dbid'  ),
                    ]+( c_oid   and [   c_oid.label(  'oid'   )] or []
                    )+( c_time2 and [   c_time2.label('time2' )] or []
                    ), where )

        g2= select( [   func.max( t.c.dbid ).label( 'dbid' ) ]
                ).group_by( *(  #order in the group_by does not matter?
                        ( c_oid   and [ t.c.oid   ] or []) +
                        [               t.c.time  ] +
                        ( c_time2 and [ t.c.time2 ] or [])
                ))

        if alias: g2 = g2.alias( alias)
        where2 = (c_dbid == g2.c.dbid)
        return g2, where2


    def _all_lastver( me, where =None, alias =None):
        '''last versions of all objects: / последните версии на много обекти:
            for each distinct .oid,
                get those of maximum .time      #g1
                    of which for each distinct .time,
                        get the one of max .dbid  #g2
            #1: select a.* from a,
                        (select oid,max(time_attr) as mtime from a group by oid) as r
                    where a.oid==r.oid and a.time_attr==r.mtime ;
        '''
        g1, where1 = me._alv_1( where=where )
        if not me.c_dbid:
            return where1
        g2, where2 = me._alv_2_dbid( where=where1, alias=alias)
        return where2

    def all_lastver( me, query =None):
        return me._query( me._all_lastver(), query )

    def _all_lastver_upto_time( me, time, where =None):
        me.upto_time( time)
        return me._all_lastver( where= where)
    def all_lastver_upto_time( me, time, where =None, query =None):
        return me._query( me._all_lastver_upto_time( time, where), query )

    def range( me, *a, **k):
        where = me._range( *a,**k)
        return me.query.filter( where)


    def filter_disabled( me, query, disabled_attr ='disabled'):
        c_disabled = getattr( me.klas, disabled_attr) #.expression_element()
        if hasattr( query, 'filter'):
            query = query.filter( ~c_disabled)
        else:   #clause
            c_disabled = c_disabled.expression_element()
            if query is None:
                query = ~c_disabled
            else:
                query &= ~c_disabled
        return query

class versions_2t( versions_1t):
    def _initkargs( me, timeTrans_attr, timeValid_attr, time2key_valid_trans=lambda x:x, **kargs):
        versions_1t._initkargs( me, time_attr= timeValid_attr, **kargs)
        me.c_time2 = getattr( me.klas, timeTrans_attr).expression_element()
        me.time2key_valid_trans = time2key_valid_trans
    def _order_by4single( me): return me.c_time, me.c_time2, me.c_dbid

    def _upto_time( me, time =None, c_time =None, c_time2 =None ):
        '''before and inclusive timestamp / validity'''
        if time is None: time = me._upto_time_value
        if time is None: return None
        timeValid, timeTrans = me.time2key_valid_trans( time)
        if c_time  is None: c_time  = me.c_time
        if c_time2 is None: c_time2 = me.c_time2
        return (c_time <= timeValid) & (c_time2 <= timeTrans)

    def _alv_2_nodbid( me, where =None, no_oid =False, alias ='g2'):
        #2t-a: sel1=oid,time,time2      sel2=oid,time,max/time2 group_by=oid,time         where=c_oid=g2.oid & c_time==g2.time & c_time2==g2.time2
        #     no_dbid=1, c_time2=1

        c_time2 = me.c_time2
        assert c_time2
        c_oid  = me.c_oid #not no_oid and me.c_oid or None
        c_time = me.c_time

        t = select( [   c_time.label(   'time'  ),
                        c_time2.label(  'time2' ),
                        c_oid.label(    'oid'   ),
                    ], where )

        g2= select( [   func.max( t.c.time2 ).label( 'time2'),
                        t.c.time,
                        t.c.oid,
                    ],  me._upto_time( c_time= t.c.time, c_time2= t.c.time2 )
                ).group_by(
                        t.c.oid,
                        t.c.time
                        #(not no_oid and [ t.c.oid] or []) +
                        #[t.c.time ]
                )

        if alias: g2 = g2.alias( alias)
        where2 = (c_time == g2.c.time) & (c_time2 == g2.c.time2) & (c_oid == g2.c.oid)
        return g2, where2


    def _all_lastver( me, where =None):
        '''last versions of all objects: / последните версии на много обекти:
            for each distinct .oid,
                get those of maximum .time                  #g1
                    of which for each distinct .time,
                        get those of maximum .time2         #g2
                            of which for each distinct .time2,
                                get the one of max .dbid    #g3
        '''
        g1, where1 = me._alv_1( where= where)
        g2, where2 = me._alv_2_nodbid( where= where1 )
        g3, where3 = me._alv_2_dbid(   where= where2, alias= 'g3')
        return where3

    def _range( me, timeFrom, timeTo, oid_value =None, lastver_only_if_same_time =True):
        '''oid_value =None should give all oids
            for each distinct .oid,
                for each distinct .time,
                    get those of maximum .time2         #r1
                        of which for each distinct .time2,
                            get the one of max .dbid    #r2
        '''
        me.upto_time( None)
        timeValidFrom, timeTransFrom = me.time2key_valid_trans( timeFrom)
        timeValidTo,   timeTransTo   = me.time2key_valid_trans( timeTo)
        timeTrans = timeTransTo
        where = ( (me.c_time2 <= timeTransTo)
                & (me.c_time >= timeValidFrom)
                & (me.c_time <= timeValidTo) )
        single_oid = oid_value is not None
        if single_oid:
            where &= (me.c_oid == oid_value)
        if not lastver_only_if_same_time:
            return where
        r1,where2 = me._alv_2_nodbid( where=where,  no_oid= single_oid, alias= 'r1')
        r2,where3 = me._alv_2_dbid(   where=where2, no_oid= single_oid, alias= 'r2')
        return where3

def last_version1_1t( query, oid_attr, time_attr, dbid_attr, oid_value, klas =None):
    v = versions_1t( query, oid_attr=oid_attr, dbid_attr=dbid_attr, time_attr=time_attr, klas=klas)
    return v.single_lastver( oid_value)

def last_versions_1t( query, oid_attr, time_attr =None, dbid_attr =None, klas =None):
    v = versions_1t( query, oid_attr=oid_attr, dbid_attr=dbid_attr, time_attr=time_attr, klas=klas)
    return v.all_lastver()


def get_obj_by_time( klas, query4klas,
        obj_id, time,
        with_disabled =False,
        time2key_valid_trans= None,
    ):

    v = versions_2t( query4klas,
            klas= klas,
            timeTrans_attr='time_trans', timeValid_attr='time_valid',
            time2key_valid_trans= time2key_valid_trans
        )

    q = None
    if not with_disabled: q = v.filter_disabled( None)
    q = v.single_lastver_upto_time( obj_id, time, where=q )
    return q

def get_all_objects_by_time( klas, query4klas, time,
        with_disabled =False,
        time2key_valid_trans= None,
        **kargs4timeclause_ignore
        ):
    #print kargs4timeclause_ignore.keys()

    old = 0
    if old:
        from timed2_sa_objid_discriminator import get_all_objects_by_time
        q = get_all_objects_by_time( klas, query4klas, time,
            with_disabled=with_disabled, time2key_valid_trans=time2key_valid_trans,
            **kargs4timeclause_ignore)
        if dbg:
            print 'OLDDDDDDDDDDDDDDDDD', q
            for a in q._clone(): print a
            print '-----------'

    v = versions_2t( query4klas,
            klas= klas,
            timeTrans_attr='time_trans', timeValid_attr='time_valid',
            time2key_valid_trans= time2key_valid_trans
        )
    if 0:
        v.upto_time( time)
        w2 = v._all_lastver()
        if not with_disabled: w2 = v.filter_disabled( w2)
        return query4klas.filter( w2)

    q = v.all_lastver_upto_time( time )
    if not with_disabled: q = v.filter_disabled( q)
    return q

def get_obj_history_in_timerange( klas, query4klas,
        obj_id, timeFrom, timeTo,
        with_disabled = False,
        time2key_valid_trans= None,
        lastver_only_if_same_time =True,
        times_only =False,
        order_by_time_then_obj =False,
        **kargs4timeclause_ignore
        ):

    #print kargs4timeclause_ignore.keys()
    v = versions_2t( query4klas,
            klas= klas,
            timeTrans_attr='time_trans', timeValid_attr='time_valid',
            time2key_valid_trans= time2key_valid_trans
        )

    order_by = [ v.c_oid, v.c_time ]
    if order_by_time_then_obj: order_by.reverse()

    if times_only:
        #transfirst = isinstance( times_only, str) and ',' in times_only and times_only.startswith('t')
        where = v._range( timeFrom, timeTo, oid_value=obj_id, lastver_only_if_same_time=lastver_only_if_same_time )
        if not with_disabled: where = v.filter_disabled( where)
        q = select( [   v.c_time,
                        v.c_time2,
                    ], where
                ).order_by( *order_by)
        q = query4klas.session.execute( q)
    else:
        q = v.range( timeFrom, timeTo, oid_value=obj_id, lastver_only_if_same_time=lastver_only_if_same_time )
        if not with_disabled: q = v.filter_disabled( q)
        q = q.order_by( *order_by)
    return q

if __name__ == '__main__':
    import dbcook.usage.plainwrap as o2r
    class Txt( o2r.Type): pass
    class Int( o2r.Type): pass
    Base = o2r.Base
    from dbcook.util.attr import setattr_kargs
    Base.__init__ = setattr_kargs
    from dbcook.usage.samanager import SAdb
    SAdb.config.getopt()

    class A( Base):
        oid = Int()
        time = Int()
        z = Txt()

    from sqlalchemy import *

    fieldtypemap = {
        Txt: dict( type= String(100), ),
        Int: dict( type= Integer, ),
    }

    sa = SAdb()# echo=True)
    print sa.config
    sa.open( recreate=True)

    types = locals()
    b = sa.bind( types, builder= o2r.Builder, fieldtypemap= fieldtypemap, base_klas= Base )
    all = [
        A( oid=1, time=12, z='a12-last'),
        A( oid=1, time=2,  z='a2' ),
        A( oid=1, time=6,  z='a6' ),

        A( oid=2, time=2,  z='b1' ),
        A( oid=2, time=4,  z='b-last' ),

        A( oid=3, time=5,  z='c5 time-dup' ),
        A( oid=3, time=5,  z='c-last' ),

        A( oid=4, time=7,  z='d-last' ),
    ]

    session = sa.session()
    sa.saveall( session, *all )
    session.flush()
    session.clear()

    lasts_by_time_obj = set( a for a in all if 'last' in a.z or 'dup' in a.z )
    lasts_by_dbid_obj = set( a for a in all if 'last' in a.z )
    lasts_by_time_id  = set( a.db_id for a in lasts_by_time_obj )
    lasts_by_dbid_id  = set( a.db_id for a in lasts_by_dbid_obj )

    def test( q, expect, obj =True, db_id =True):
        r = set( q )
        for z in r: print z
        assert set( (db_id and (obj and x.db_id or x['db_id']) or x)
                    for x in r ) == set( expect), '''
        result: %(r)r
        expect: %(expect)r''' % locals()

    print '------- A all'
    for a in session.query(A): print a
    if 10*'byhand':
        a = sa.tables[A]

        print '====== oid,time last -group_by time'
        g1 = select( [   a.c.oid.label('mx'),
                        func.max( a.c.time).label('my'),
                ] ).group_by( A.oid)
        for z in session.execute( g1): print z

        print '------- Atbl for last times';
        o = a.select( (A.oid==g1.c.mx) & (A.time==g1.c.my) )
        test( session.execute( o), lasts_by_time_id, obj=False)

        print '======= dbid last -group_by oid,time'
        g2 = select( [ func.max( o.c.db_id).label( 'nid')
                ] ).group_by( o.c.oid, o.c.time)
        for z in session.execute( g2): print z

        print '------- Atbl for last dbid for last times'
        q = a.select( (A.db_id==g2.c.nid) )
        test( session.execute( q), lasts_by_dbid_id, obj=False)


        print '======= A for last times'
        q = session.query(A).filter( (A.oid==g1.c.mx) & (A.time==g1.c.my) )
        test( q, lasts_by_time_id)

        print '------- A for last dbid for last times'
        q = session.query(A).filter( (A.db_id==g2.c.nid) )
        test( q, lasts_by_dbid_id)

        print '=================='

    print '------- last_versions by time'
    q = last_versions_1t( session.query( A), 'oid', 'time')
    test( q, lasts_by_time_id)

    print '------- last_versions by dbid,time'
    q = last_versions_1t( session.query( A), 'oid', 'time', 'db_id' )
    test( q, lasts_by_dbid_id)

    print '=========== single last_version'
    for x in lasts_by_dbid_obj:
        q = last_version1_1t(
            session.query( A), 'oid', 'time', 'db_id',
            oid_value= x.oid )
        test( [q], [x.db_id] )

    print '=========== single last_version upto_time'
    v = versions_1t( session.query(A), oid_attr='oid', time_attr='time', dbid_attr='db_id', )
    f = v.single_lastver_upto_time
    for q,r in [
            [ f( oid=1, time=1)   ,  None  ],
            [ f( oid=1, time=2).z ,  'a2'  ],
            [ f( oid=1, time=4).z ,  'a2'  ],
            [ f( oid=1, time=6).z ,  'a6'  ],
            [ f( oid=1, time=7).z ,  'a6'  ],
            [ f( oid=4, time=9).z ,  'd-last' ],
            [ f( oid=4, time=5)   ,  None  ],
        ]:
        test( [q], [r], db_id= False )

    print '=========== all last_versions time/dbid upto_time'
    v = versions_1t( session.query(A), oid_attr='oid', time_attr='time', dbid_attr='db_id', )
    q = v.all_lastver_upto_time( time=5)
    test( q, [x.db_id for x in all if x.z in 'a2 b-last c-last'.split() ] )

# vim:ts=4:sw=4:expandtab
