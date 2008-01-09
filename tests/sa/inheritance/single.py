#$Id$
# -*- coding: cp1251 -*-
from klasi import *
from klasi import _printcallfunc

class tables:
    A = Table('A', metadata,
        Column('i_d', Integer, primary_key=True),
        Column('atype', Text),

        Column('name', Text),
        Column('B_data', Text),
        Column('man2', Text),
    )


ECHO=10
db = DB( ECHO)

DB.USE_E = DB.USE_D = 0

class mappers: pass

mappers.A= _printcallfunc( mapper, A, tables.A,
    polymorphic_on=tables.A.c.atype,
    polymorphic_identity='A')

mappers.A1= mapper( A, tables.A.select( tables.A.c.atype=='A').alias('abz'),
    non_primary=True,
    )

mappers.B= _printcallfunc( mapper, B,  None,
    inherits=mappers.A,
    polymorphic_identity='B')

mappers.B1= _printcallfunc( mapper, B,  tables.A.select( tables.A.c.atype=='B').alias('bbz'),
    non_primary=True,
    )

mappers.C= mapper( C, None,
    inherits=mappers.B,
    polymorphic_identity='C')

db.populate( mappers)
print '======'


'subklas_instances_only'
#B2select = polymorphic_union( dict( (k,v) for (k,v) in bjoin.iteritems() if k !='B' ), 'type', ).select()
B_subklasi = [ m.polymorphic_identity  for m in mappers.B._inheriting_mappers]
B2select = tables.A.select( tables.A.c.atype.in_( *B_subklasi ) )

if 10:
    m = mappers.B
    x = db.pipequery( m, B2select)

res = [e for e in x]
print '  ', res

if 0:
    employees_table = Table('employees', metadata,
        Column('employee_id', Integer, primary_key=True),
        Column('name', String(50)),
        Column('manager_data', String(50)),
        Column('engineer_info', String(50)),
        Column('type', String(20))
    )

    employee_mapper = mapper(Employee, employees_table, polymorphic_on=employees_table.c.type)
    manager_mapper = mapper(Manager, inherits=employee_mapper, polymorphic_identity='manager')
    engineer_mapper = mapper(Engineer, inherits=employee_mapper, polymorphic_identity='engineer')
# vim:ts=4:sw=4:expandtab
