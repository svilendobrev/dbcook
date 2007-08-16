#$Id$
from klasi import *
from klasi import _printcallfunc

from dbcook.builder import table_inheritance_types, column4ID
A.DBCOOK_inheritance = table_inheritance_types.JOINED
from dbcook.samanager import SAdb

i_d = column4ID.name
sa = SAdb( 'memory', debug='sql')
sa.open( recreate=True)

all = dict(
    A=A,
 #   B=B,
 #   C=C,
    D=D,
#   E=E,
)

DB.USE_B = 'B' in all
DB.USE_C = 'C' in all
DB.USE_D = 'D' in all
DB.USE_E = 'E' in all

sa.bind( None, base_klas= A.__bases__[0] )
sa.namespace = all
sa.make_subklasi()
metadata = sa.metadata

if 10:
    class tables:
        A = Table('A', metadata,
            Column('name', String),
            Column( i_d , Integer, primary_key=True),
            Column('atype', String),
        )

        B = Table('B', metadata,
            Column('B_data', String),
            Column( i_d , Integer, ForeignKey( 'A.'+i_d), primary_key=True, ),
        )

        C = Table('C', metadata,
            Column( i_d , Integer, ForeignKey( 'B.'+i_d), primary_key=True, ),
            Column('man2', String),
        )
        if DB.USE_D:
            D = Table('D', metadata,
                Column( i_d, Integer, ForeignKey( 'A.'+i_d), primary_key=True, ),
                Column('D_info', String),
                Column('other_id', Integer, ForeignKey('A.'+i_d) )
            )

        if DB.USE_E:
            E = Table('E', metadata,
                Column( i_d , Integer, ForeignKey( 'B.'+i_d), primary_key=True, ),
                Column('eee', String),
                Column('root_id', Integer, ForeignKey('E.'+i_d) ), #self-ref
                Column('next_id', Integer, ForeignKey('E.'+i_d) ), #self-ref
            )
print repr(tables.A)
print repr(tables.B)
ECHO=10
db = DB( ECHO, meta=metadata)#dont_init=True)

if 0*'use_SAmapper':

    sa.tables = {}
    sa.mappers = {}
    for k,v in all.iteritems():
        if not k or k.startswith('__'): continue
        sa.tables[ v] = getattr( tables,k)
    sa.make_mappers()

    class X:
        def __init__(me, all,o):
            me.all = all
            me.o = o
        def __getattr__(me,k):
            m = me.o[ me.all[k]]
            if k.endswith('1'): return m.plain
            return m.polymorphic_all

    x = X( all,sa.mappers)

else:

    ajoin = {
        'A':tables.A.select( tables.A.c.atype=='A'),
        'B':tables.A.join( tables.B).select( tables.A.c.atype =='B'),
    }
    if DB.USE_C: ajoin['C'] = tables.A.join( tables.B).join(tables.C)
    if DB.USE_E: ajoin['E'] = tables.A.join( tables.B).join(tables.E)
    if DB.USE_D:
        #ajoin['D'] = tables.A.join( tables.D)
        ajoin['D'] = join( tables.A, tables.D, column4ID( tables.D) == column4ID( tables.A) )  #explicit

    Ajoin = polymorphic_union( ajoin.copy(), None)#'type', )#'ajoin')


    bjoin = {}
    for t in 'BCE':
        try:
            bjoin[t] = ajoin[t]
        except KeyError: pass
    Bjoin = polymorphic_union( bjoin, None)#'type', )#'zajoin')

    class mappers: pass
    mappers.A= _printcallfunc( mapper, A, tables.A,
        select_table=Ajoin, polymorphic_on=Ajoin.c.atype,
        polymorphic_identity='A')
    mappers.A1= _printcallfunc( mapper, A,
            ajoin['A'].alias('abz'),
            #tables.A, select_table=ajoin['A'].alias('abz'), - does not work
        non_primary=True,
        polymorphic_identity='A')

    mappers.B= _printcallfunc( mapper, B, tables.B,
        select_table=Bjoin, polymorphic_on=Bjoin.c.atype,
        inherits=mappers.A,
        polymorphic_identity='B')

    if len(bjoin)>1:
        mappers.B1= mapper( B, ajoin['B'].alias('tbs'),   #tables.B, select_table=
            #inherits=mappers.A1,
            non_primary=True,
            polymorphic_identity='B')
    else:
        mappers.B1= mappers.B

    if DB.USE_C:
        mappers.C= mapper( C, tables.C,
            inherits=mappers.B,
            polymorphic_identity='C')

    if DB.USE_D:
        mappers.D= mapper( D, tables.D,
            inherits=mappers.A,
            inherit_condition= column4ID( tables.D) == column4ID( tables.A),
            polymorphic_identity='D'
        )
        mappers.D.add_property( 'other',
            relation( A, lazy=True, uselist=False,
                primaryjoin= column4ID( tables.A) == tables.D.c.other_id))

    if DB.USE_E:
        mappers.E= mapper( E, tables.E,
            inherits=mappers.B,
            polymorphic_identity='E')

    x = mappers

print x.A
db.populate( x)
print '======'

'subklas_instances_only'
A2join = polymorphic_union( dict( (k,v) for (k,v) in bjoin.iteritems() if k !='A' ), 'type', )#'bjoin')
if 10:
    m = mappers.A
    x = db.pipequery( m, A2join.select())
else:
    mappers.A2= mapper( A, tables.A,
        select_table=A2join, polymorphic_on=B2join.c.type,
        non_primary=True,

        polymorphic_identity='A',
        _polymorphic_map = mappers.A.polymorphic_map    #biggest of all
        )
    #needs _polymorphic_map = {}
    x = db.session.query( mappers.A2).all()

res = [e for e in x]
print '  ', res

# vim:ts=4:sw=4:expandtab
