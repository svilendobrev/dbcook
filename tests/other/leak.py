#$Id$
# -*- coding: cp1251 -*-
from dbcook.config import config_components
config_components.no_generator = True
import dbcook.usage.plainwrap as o2r
import sys

from sqlalchemy import MetaData, create_engine, Table, Column, ForeignKey, String, Integer, outerjoin
from sqlalchemy.orm import create_session, mapper, clear_mappers, compile_mappers
#from pprint import pprint

gc = 'gc' in sys.argv

if   'sa'     in sys.argv: what = 'sa'
elif 'safunc' in sys.argv: what = 'safunc'
else: what = 'dbcook'

Base = 'object' in sys.argv and object or o2r.Base

OUT = 'out' in sys.argv

if OUT:
    class Text( o2r.Type): pass
    class A0( Base):
        name    = Text()
        DBCOOK_inheritance = 'joined'   #for subclasses - this(base) one is always concrete anyway
        DBCOOK_has_instances = True     #by default only class-tree leaves have instances
    class B0( A0):
        alaba   = Text()
    fieldtypemap0 = { Text: dict( type= String, ), }# map attr-types to sql-column-types

def safunc( meta, Alaba,Balama ):
        table_A = Table( 'Alaba', meta,
            Column( 'name', String, ),
            Column( 'atype',   type_= String, ),
            Column( 'db_id',   primary_key= True,   type_= Integer, ),
        )
        table_B = Table( 'Balama', meta,
            Column( 'dataB', String, ),
            Column( 'db_id', Integer, ForeignKey( 'Alaba.db_id', ),   primary_key= True, ),
        )

        meta.create_all()
        mapper_A = mapper( Alaba, table_A,
                    polymorphic_identity= 'Alaba',
                    polymorphic_on= table_A.c.atype,
                    select_table= outerjoin( table_A, table_B, table_B.c.db_id == table_A.c.db_id, ),
                    )
        mapper_B = mapper( Balama, table_B,
                    inherit_condition= table_B.c.db_id == table_A.c.db_id,
                    inherits= mapper_A,
                    polymorphic_identity= 'Balama',
                    )
        compile_mappers()

def test():
    if not OUT:
        class Text( o2r.Type): pass
        class Alaba( Base):
            name    = Text()
            DBCOOK_inheritance = 'joined'   #for subclasses - this(base) one is always concrete anyway
            DBCOOK_has_instances = True     #by default only class-tree leaves have instances
        class Balama( Alaba):
            alaba   = Text()
        fieldtypemap = { Text: dict( type= String, ), }# map attr-types to sql-column-types
    else:
        Alaba=A0
        Balama=B0
        fieldtypemap = fieldtypemap0

    meta = MetaData( create_engine('sqlite:///', echo= 'echo' in sys.argv ))

    assert what in 'sa safunc dbcook'.split()
    TBL = 0
    if what == 'sa' or TBL:
        table_A = Table( 'Alaba', meta,
            Column( 'name', String, ),
            Column( 'atype',   type_= String, ),
            Column( 'db_id',   primary_key= True,   type_= Integer, ),
        )
        table_B = Table( 'Balama', meta,
            Column( 'dataB', String, ),
            Column( 'db_id', Integer, ForeignKey( 'Alaba.db_id', ),   primary_key= True, ),
        )
        #tables = { Alaba:table_A, Balama:table_B}
    #else: tables = ()

    if what == 'sa':
        meta.create_all()
        mapper_A = mapper( Alaba, table_A,
                    polymorphic_identity= 'Alaba',
                    polymorphic_on= table_A.c.atype,
                    select_table= outerjoin( table_A, table_B, table_B.c.db_id == table_A.c.db_id, ),
                    )
        mapper( Balama, table_B,
                    inherit_condition= table_B.c.db_id == table_A.c.db_id,
                    inherits= mapper_A,
                    polymorphic_identity= 'Balama',
                    )
        compile_mappers()
    elif what=='safunc':
        safunc( meta, Alaba, Balama)
    else:
        print 'dbcook'
        mybuild = o2r.Builder( meta,
                dict( Alaba=Alaba, Balama=Balama),       #just scan anything here that looks like subclass of Base
                fieldtypemap,
                base_klas=Base,
                #tables = tables,
            )
#        del mybuild

    if 10:
        def populate():
            a = Alaba()
            a.name = 'anna'
            b = Balama()
            b.name = 'x'
            return locals()

        session = create_session()
        #anything off Base, go to db
        for x in populate().values():
            if isinstance( x, Base) and not isinstance( x, type): session.save( x)
        session.flush()

        session = create_session()
        all = session.query( Alaba).all()
        assert len(all)==2
        for q in all: print 'o', q
    clear_mappers()
    return meta

if gc:
    import gc
    gc.set_debug( gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_INSTANCES | gc.DEBUG_STATS | gc.DEBUG_OBJECTS ) #OBJECTS gc.DEBUG_SAVEALL | DEBUG_LEAK
    #print gc.get_threshold()
    #gc.set_threshold(300, 2,1)
#gc=0
for a in range(gc and 3 or 400):
    meta = test()
    meta.drop_all()
    del meta
    if gc:
        print '======================================================'
        gc.collect()

        #def s(me): return me.__class__.__name__ + '/'+me.name
        #Table.__str__  = s
        #Table.__repr__  = s
        #Column.__str__ = s
        #Column.__repr__  = s
        print len(gc.garbage), 'garbage'

        for x in gc.garbage:
            rc, grc = sys.getrefcount(x), len(gc.get_referrers(x))
            if rc>grc+1:
                print object.__repr__(x), getattr( x,'__name__', ''), x
                #try: pprint(x)
                #except:
                #    try: print `x`
                #    except: print 'sorry'
                ##rr = gc.get_referrers( x)
                ##if rr: print '  ref by', ','.join( object.__repr__( a) for a in rr)
                print '  ', rc,grc#, (rc>grc+1) and 'aaaaaaaaaaaaaaaaaaa' or ''
        del gc.garbage[:]
   # break
    print 'qqqqqqqqqqqqqqqqqqqqq'

# vim:ts=4:sw=4:expandtab
