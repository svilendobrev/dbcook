#$Id$
from sqlalchemy import *
db = create_engine( 'sqlite:///:memory:')
meta = BoundMetaData( db)
meta.engine.echo = 0

    #decomposed by joined_table inheritance
table_Employee = Table( 'Employee', meta,
    Column( 'name', type= String, ),
    Column( 'id', primary_key= True, type= Integer, ),
    Column( 'atype', type= String, ),
)

table_Engineer = Table( 'Engineer', meta,
    Column( 'machine', type= String, ),
    Column( 'id', Integer, ForeignKey( 'Employee.id', ), primary_key= True, ),
)

table_Manager = Table( 'Manager', meta,
    Column( 'duties', type= String, ),
    Column( 'id', Integer, ForeignKey( 'Engineer.id', ), primary_key= True, ),
)

class Employee( object):
    def set( me, **kargs):
        for k,v in kargs.iteritems(): setattr( me, k, v)
        return me
    def __str__(me): return str(me.__class__.__name__)+':'+str(me.name)
    __repr__ = __str__
class Engineer( Employee): pass
class Manager( Engineer): pass

meta.create_all()

pu_Employee = polymorphic_union( {
            'Manager':  table_Employee.join( table_Engineer).join( table_Manager),
            'Engineer': table_Employee.join( table_Engineer).select( table_Employee.c.atype == 'Engineer', ),
            'Employee': table_Employee.select( table_Employee.c.atype == 'Employee', ),
        }, None, 'pu_Employee', )
mapper_Employee = mapper( Employee, table_Employee,
            polymorphic_identity= 'Employee',
            polymorphic_on= pu_Employee.c.atype,
            select_table= pu_Employee,
        )


pu_Engineer = polymorphic_union( {
            'Manager':  table_Employee.join( table_Engineer).join( table_Manager),
            'Engineer': table_Employee.join( table_Engineer).select( table_Employee.c.atype == 'Engineer', ),
        }, None, 'pu_Engineer', )
mapper_Engineer = mapper( Engineer, table_Engineer,
            inherit_condition= table_Engineer.c.id == table_Employee.c.id,
            inherits= mapper_Employee,
            polymorphic_identity= 'Engineer',
            polymorphic_on= pu_Engineer.c.atype,
            select_table= pu_Engineer,
        )

mapper_Manager = mapper( Manager, table_Manager,
            inherit_condition= table_Manager.c.id == table_Engineer.c.id,
            inherits= mapper_Engineer,
            polymorphic_identity= 'Manager',
        )

a = Employee().set( name= 'one')
b = Engineer().set( egn= 'two', machine= 'any')
c = Manager().set( name= 'head', machine= 'fast', duties= 'many')

session = create_session()
session.save(a)
session.save(b)
session.save(c)
session.flush()

print a,b,c
import sys

if 'noA' not in sys.argv: print session.query( Employee).select()
print session.query( Engineer).select()
print session.query( Manager).select()

query_Engineer_sql = '''
SELECT "pu_Engineer".machine AS pu_Engineer_machine, "pu_Engineer".atype AS pu_Engineer_atype, "pu_Engineer".name AS pu_Engineer_name, pu_Engineer.duties AS "pu_Engineer_duties", "pu_Engineer".id AS pu_Engineer_id
FROM (
	SELECT "Engineer".machine AS machine,
			"Employee".atype AS atype, "Employee".name AS name,
			"Manager".duties AS duties, "Manager".id AS id
	FROM "Employee" JOIN "Engineer" ON "Employee".id = "Engineer".id JOIN "Manager" ON "Engineer".id = "Manager".id
  UNION ALL
	SELECT anon.machine AS machine, anon.atype AS atype, anon.name AS name, CAST(NULL AS TEXT) AS duties, anon.id AS id
	FROM (
		SELECT "Employee".name AS name, "Employee".id AS id, "Employee".atype AS atype,
				"Engineer".machine AS machine, "Engineer".id AS id
		FROM "Employee" JOIN "Engineer" ON "Employee".id = "Engineer".id
		WHERE "Employee".atype = ?
	) AS anon
) AS "pu_Engineer" ORDER BY "pu_Engineer".oid
'''

# vim:ts=4:sw=4:expandtab
