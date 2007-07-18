#$Id$
# -*- coding: cp1251 -*-

####administrative stuff

import sys
if 'statictype' not in sys.argv:
    import dbcook.usage.plainwrap as o2r
    class Text( o2r.Type): pass
    class Int(  o2r.Type): pass
else:
    import dbcook.usage.static_type.sa2static as o2r
    from static_type.types.atomary import Text
    from static_type.types.atomary import Number as Int
    o2r.Base.auto_set = False

Base = o2r.Base
from dbcook.usage.samanager import SAdb

class Config( SAdb.config.__class__):
    inh             = 'joined' #, 'concrete']
    director_base   = 'Manager'  #'Employee', 'Engineer']

    _help = '''\
inh=            :: the way of inheritance-decomposition: concrete or joined    [=joined]
director_base=  :: base-class of Director: one of Employee, Engineer, Manager  [=Manager]
'''

config = Config( chain= SAdb.config)
config.getopt()
print 'config:', config

inh = (config.inh == 'concrete' and 'concrete_table' or 'joined_table')
print 'using', o2r.__name__, inh


####### start actual model-definition

class Employee( Base):
    name    = Text()
    age     = Int()
    dept    = o2r.Type4SubStruct( 'Dept')
    lover   = o2r.Type4SubStruct( 'Employee')
    manager = o2r.Type4SubStruct( 'Employee')    #or 'Manager'
    DB_inheritance = inh        #for subclasses - this one is always concrete anyway
    DB_HAS_INSTANCES = True     #by default only class-tree leaves have instances

class Manager( Employee):
    secretary = o2r.Type4SubStruct( Employee)
    extras = Text()
    DB_HAS_INSTANCES = True

Engineer =  Employee
class Engineer( Employee):
    machine = Text()

#want them switchable? no probs
director_base = dict(
        Employee=Employee, Manager=Manager, Engineer=Engineer
    ).get( config.director_base, Manager)
class Director( director_base):
    if 'secretary' not in director_base.__dict__:   #no life without a secretary!
        secretary = o2r.Type4SubStruct( Employee)
    salary = Int()

class Dept( Base):
    manager = o2r.Type4SubStruct( Manager)
    name = Text()
    director = o2r.Type4SubStruct( 'Director')
    #employees = Collection/one2many(???) TODO

####### endof model-definition

import sqlalchemy

fieldtypemap = {
    Text: dict( type= sqlalchemy.String, ),
    Int : dict( type= sqlalchemy.Integer, ),
}

sa = SAdb()
sa.open( recreate=True)

types = locals()
b = sa.bind( types, builder= o2r.Builder, fieldtypemap= fieldtypemap, base_klas= Base )
#if b.generator:
#    print '====generated SA set-up'
#    print b.generator.out
#    print '========= eo generated SA set-up'


def populate():
    a = Employee()
    a.name = 'anna'
    a.age = 30

    m = Manager()
    m.name = 'mummy'
    m.extras= 'big'

    dept = Dept()
    dept.name = 'cubics'

    dept.manager = m
    a.manager = m
    a.dept = dept

    a1 = Employee()
    a1.name = 'popo'
    a1.manager = m
    a1.age = 24
    a1.dept = dept

    m.secretary = a1
    m.manager = m       #self-boss ? uncommenting this AND h.manager = h fixes circ-dep???

    e = Engineer()
    e.name = 'engo'
    e.manager = m
    e.age = 40
    e.machine = 'fast'
    e.lover = a1
    e.dept = dept

    e2 = Engineer()
    e2.name = 'ena'
    e2.manager = m
    e2.age = 30
    e2.machine = 'deep'
    e2.lover = e
    e2.dept = dept

    h = Director()
    h.name = 'heady'
    h.secretary = a
    h.dept = dept

    m.manager = h
#   h.manager = h   #self-boss ?

    session = sa.session()
    sa.saveall( session, locals() )
    session.flush()

    session.clear()


def test():
    session = sa.session()
    q2 = sa.query_all_tables()

    for kl in 1*[Employee] + [Manager, Engineer, Director, Dept]:

        print '== query_ALL', kl.__name__
        q1 = sa.query_ALL_instances( session, klas=kl)
        print  '\n'.join( '  '+str(x) for x in q1)

        print '== query_BASE', kl.__name__
        q2 = sa.query_BASE_instances( session, klas=kl)
        print  '\n'.join( '  '+str(x) for x in q2)

        print '== query_SUB', kl.__name__
        q3 = sa.query_SUB_instances( session, klas=kl)
        print  '\n'.join( '  '+str(x) for x in q3)

populate()
#test()

session = sa.session()
from dbcook import expression

age= 30
print '--------------------, all Employee with lover.age<',age
# XXX XXX
## - self=Engineer works, self=Employee ->wrong clause
## - where clause gives wrong results??? age=30 ->no items; age=100 -> 2 items incl. popo None ????
def myquery( self =Engineer, min_age =20, max_age =age ):
#    return self.age < max_age
    return self.lover.age < max_age
#    return self.lover.age.between( min_age, max_age)
#    return self.age.between( min_age, max_age)
#    return (self.lover.age >= min_age) #& (self.lover.age <= max_age)
#    return (self.age >= min_age)

expression._debug=1
#expr-query
r = expression.query1( myquery, klas=Employee, session=session)
for a in r: print '  ', a.name, '->', a.lover#.name, a.lover.age

if 1:
    print '------, same, plain select'
    ee = sa.tables[Employee]
    aa = ee.alias()
    q = ee.select(
            (aa.c.db_id == ee.c.lover_id) &
            (aa.c.age < age) ).execute()
    for a in q: print '  ', a.name, a.lover_id

# vim:ts=4:sw=4:expandtab
