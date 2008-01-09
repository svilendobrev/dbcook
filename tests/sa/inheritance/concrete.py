#$Id$
from klasi import *
from klasi import _printcallfunc
DB.USE_D=0
DB.USE_B=1
DB.USE_C=0
DB.USE_E=0

class tables:
    A = Table('A', metadata,
        Column('i_d', Integer, primary_key=True),
        Column('name', Text),
    )
    if DB.USE_B:
        B = Table('B', metadata,
            Column('i_d', Integer, primary_key=True),
            Column('name', Text),
            Column('B_data', Text)
        )

    if DB.USE_C:
        C = Table('C', metadata,
            Column('i_d', Integer, primary_key=True),
            Column('name', Text),
            Column('B_data', Text),
            Column('man2', Text),
        )

    if DB.USE_D:
        D = Table('D', metadata,
            Column('i_d', Integer, primary_key=True),
            Column('name', Text),
            Column('D_info', Text),
            Column('other_id', Integer,
                ForeignKey('A.i_d',
                               use_alter=True, name='zt3id_fk'
                ),
            )
        )
    if DB.USE_E:
        E = Table('E', metadata,
            Column('i_d', Integer, primary_key=True),
            Column('name', Text),
            Column('eee', Text),
            Column('root_id', Integer, ForeignKey('E.i_d') ), #self-ref
            Column('next_id', Integer, ForeignKey('E.i_d') ), #self-ref
        )

ECHO=0
db = DB( ECHO)
corr = dict(correlate=False)
ajoin = { 'A':tables.A.select(**corr), }
if db.USE_B: ajoin['B'] = tables.B.select(**corr)
if db.USE_C: ajoin['C'] = tables.C.select(**corr)
if db.USE_D: ajoin['D'] = tables.D.select(**corr)
if db.USE_E: ajoin['E'] = tables.E.select(**corr)
Ajoin = polymorphic_union( ajoin,'atype', )
print Ajoin

if db.USE_B:
    bjoin = {}
    for t in 'BCE':
        try:
            bjoin[t] = ajoin[t]
        except KeyError: pass
    Bjoin = polymorphic_union( bjoin,'atype', )

class mappers: pass
mappers.A= _printcallfunc( mapper, A, tables.A,
    select_table=Ajoin, polymorphic_on=Ajoin.c.atype,
    concrete=True, polymorphic_identity='A')
mappers.A1= mapper( A, tables.A,
    non_primary=True,
    concrete=True, polymorphic_identity='A')

if db.USE_B:
    mappers.B= _printcallfunc( mapper, B,  tables.B,
        select_table=Bjoin, polymorphic_on=Bjoin.c.atype,
        inherits=mappers.A,
        concrete=True, polymorphic_identity='B')
    mappers.B1= mapper( B,  tables.B,
        #inherits=mappers.A1,
        non_primary=True,
        concrete=True, polymorphic_identity='B')

if db.USE_C:
    mappers.C= mapper( C, tables.C,
        inherits=mappers.B,
        concrete=True, polymorphic_identity='C')

if db.USE_D:
    mappers.D= _printcallfunc( mapper, D, tables.D,
        concrete=True, polymorphic_identity='D',
        inherits=mappers.A,    #XXX
    )
    #mappers.A.polymorphic_map.update( { 'D':mappers.D} ) #XXX ?concrete-inheritance
    mappers.D.add_property( 'other', relation(
        A, lazy=True, uselist=False,
                    primaryjoin= tables.D.c.other_id==tables.A.c.i_d,
        post_update=True,
        )
    )

if db.USE_E:
    mappers.E= mapper( E, tables.E,
        inherits=mappers.B,
        concrete=True,
        polymorphic_identity='E')
    mappers.E.add_property( 'root',
        relation( A, lazy=True, uselist=False,
            primaryjoin= tables.E.c.i_d == tables.E.c.root_id))
    mappers.E.add_property( 'next',
        relation( A, lazy=True, uselist=False,
            primaryjoin= tables.E.c.i_d == tables.E.c.next_id))


db.populate( mappers)

print '======'

if db.USE_B:
    #'subklas_instances_only'
    bB2join = dict( (k,v) for (k,v) in bjoin.iteritems() if k !='B' )
    B2join = polymorphic_union( dict( (k,v) for (k,v) in bjoin.iteritems() if k !='B' ), 'atype', )
    #print B2join#.select()
    if 10:
        m = mappers.B
        x = db.pipequery( m, B2join.select())
    else:
        mappers.B2= mapper( B, tables.B,
            select_table=B2join, polymorphic_on=B2join.c.atype,
            non_primary=True,
            polymorphic_identity='B',
            _polymorphic_map = mappers.A.polymorphic_map,
            concrete=True,
            )
        #needs _polymorphic_map = {}
        x = db.session.query( mappers.B2).all()

    res = [e for e in x]
    print '  ', res

# vim:ts=4:sw=4:expandtab
