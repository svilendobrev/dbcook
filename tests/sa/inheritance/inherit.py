#$Id$
from klasi import *
from klasi import _printcallfunc
DB.USE_D = 1
DB.USE_E = 0

class tables:
    A = Table('A', metadata,
        Column('i_d', Integer, primary_key=True),
        Column('name', String),
        Column('atype', String),
    )

    if DB.USE_B:
        B = Table('B', metadata,
            Column('i_d', Integer, ForeignKey( 'A.i_d'), primary_key=True, ),
            Column('B_data', String)
        )

    if DB.USE_C:
        C = Table('C', metadata,
            Column('i_d', Integer, ForeignKey( 'B.i_d'), primary_key=True, ),
            Column('man2', String),
        )
    if DB.USE_E:
        E = Table('E', metadata,
            Column('i_d', Integer, ForeignKey( 'B.i_d'), primary_key=True, ),
            Column('eee', String),
            Column('root_id', Integer, ForeignKey('E.i_d') ), #self-ref
            Column('next_id', Integer, ForeignKey('E.i_d') ), #self-ref
        )

    if DB.USE_D:
        D = Table('D', metadata,
            Column('i_d', Integer, ForeignKey( 'A.i_d'), primary_key=True, ),
            Column('D_info', String),
            Column('other_id', Integer, ForeignKey('A.i_d') )
        )

ECHO=0
db = DB( ECHO)
corr = {}#dict(correlate=False)
ajoin={
    'A':tables.A.select( tables.A.c.atype=='A', **corr),
}
if DB.USE_B: ajoin['B']=tables.A.join( tables.B).select( tables.A.c.atype =='B', **corr)
if DB.USE_C: ajoin['C']=tables.A.join( tables.B).join(tables.C)
if DB.USE_D: ajoin['D']=join( tables.A, tables.D, tables.D.c.i_d == tables.A.c.i_d)   #explicit
if DB.USE_E: ajoin['E']=tables.A.join( tables.B).join(tables.E)

if 0:
    tb = join( tables.A, tables.B, tables.B.c.i_d == tables.A.c.i_d)  #explicit
    print tb.foreign_keys
    tbz=join( tb, tables.E, tables.E.c.i_d == tb.left.c.i_d )
    print 'zzzzzzzzz', tbz
    te = join( tables.B, tables.E, tables.B.c.i_d == tables.E.c.i_d)  #explicit
    tbx=join( tables.A, tb, tables.A.c.i_d == tb.left.c.i_d )

Ajoin = polymorphic_union( ajoin.copy(), None)

if db.USE_B:
    bjoin = {}
    for t in 'BCE':
        try:
            bjoin[t] = ajoin[t]
        except KeyError: pass
    Bjoin = polymorphic_union( bjoin, None)

class mappers: pass
mappers.A= _printcallfunc( mapper, A, tables.A,
    select_table=Ajoin, polymorphic_on=Ajoin.c.atype,
    polymorphic_identity='A')
mappers.A1= _printcallfunc( mapper, A,
        ajoin['A'].alias('abz'),
        #tables.A, select_table=ajoin['A'].alias('abz'), - does not work
    non_primary=True,
    polymorphic_identity='A')

if db.USE_B:
    mappers.B= _printcallfunc( mapper, B, tables.B,
        select_table= Bjoin, polymorphic_on= Bjoin.c.atype,
        inherits=mappers.A,
        polymorphic_identity='B')
    mappers.B1= mapper( B, bjoin['B'].alias('bbz'), #tables.B.select( tables.B.c.atype == 'B').alias('tbs'),   #tables.B, select_table=
    #    inherits=mappers.A1,       XXX breaks
        non_primary=True,
        polymorphic_identity='B')

if db.USE_C:
    mappers.C= mapper( C, tables.C,
        inherits=mappers.B,
        polymorphic_identity='C')

if db.USE_D:
    mappers.D= mapper( D, tables.D,
        inherits=mappers.A,
        inherit_condition= (tables.D.c.i_d == tables.A.c.i_d),
        polymorphic_identity='D'
    )
    mappers.D.add_property( 'other',
        relation( A, lazy=True, uselist=False,
            primaryjoin= tables.A.c.i_d == tables.D.c.other_id))

if db.USE_E:
    mappers.E= mapper( E, tables.E,
        inherits=mappers.B,
        polymorphic_identity='E')
    mappers.E.add_property( 'root',
        relation( A, lazy=True, uselist=False,
            primaryjoin= tables.E.c.i_d == tables.E.c.root_id))
    mappers.E.add_property( 'next',
        relation( A, lazy=True, uselist=False,
            primaryjoin= tables.E.c.i_d == tables.E.c.next_id))

db.populate( mappers)
print '======'

if 0:
    'subklas_instances_only'
    B2join = polymorphic_union( dict( (k,v) for (k,v) in bjoin.iteritems() if k !='B' ), 'type', )
    if 10:
        m = mappers.B
        x = db.pipequery( m, B2join.select())
    else:
        mappers.B2= mapper( B, tables.B,
            select_table=B2join, polymorphic_on=B2join.c.type,
            non_primary=True,

            polymorphic_identity='B',
            _polymorphic_map = mappers.A.polymorphic_map
            )
        #needs _polymorphic_map = {}
        x = db.session.query( mappers.B2).all()

    res = [e for e in x]
    print '  ', res

# vim:ts=4:sw=4:expandtab
