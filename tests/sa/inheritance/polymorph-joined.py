
from sqlalchemy import *
from sqlalchemy.orm import *
import sets, sys

metadata = MetaData( 'sqlite://')
metadata.bind.echo='echo' in sys.argv

people = Table('people', metadata,
   Column('person_id', Integer, primary_key=True),
   Column('name', String(50)),
   Column('type', String(30)))

engineers = Table('engineers', metadata,
   Column('person_id', Integer, ForeignKey('people.person_id'), primary_key=True),
   Column('status', String(30)),
   Column('engineer_name', String(50)),
   Column('secretary', Integer, ForeignKey('people.person_id'), ),
   Column('primary_language', String(50)),
  )

managers = Table('managers', metadata,
   Column('person_id', Integer, ForeignKey('people.person_id'), primary_key=True),
   Column('color_id',  Integer, ForeignKey('colors.color_id' ), unique=True, nullable=False),
   Column('status', String(30)),
   Column('manager_name', String(50))
   )

hackers= Table('hackers', metadata,
   Column('person_id', Integer, ForeignKey('engineers.person_id'), primary_key=True),
   Column('second_lang', String(30)),
   )

zackers= Table('zackers', metadata,
   Column('person_id', Integer, ForeignKey('hackers.person_id'), primary_key=True),
   Column('third_lang', String(30)),
   )



colors = Table('colors', metadata,
   Column('color_id', Integer, primary_key=True),
   Column('name', String(50)),
   Column('type', String(30))
)

paint = Table('paints', metadata,
   Column('paint_id', Integer, ForeignKey('colors.color_id'), primary_key=True),
   Column('smell', String(30)),
)



metadata.create_all()

class Person(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
    def __repr__(self):
        return "Ordinary person %s" % self.name
class Engineer(Person):
    def __repr__(self):
        return "Engineer %s, status %s, engineer_name %s, primary_language %s" % (self.name, self.status, self.engineer_name, self.primary_language)
class Hacker(Engineer):
    def __repr__(self):
        return "Hacker %s, status %s, engineer_name %s, primary_language %s, second_lang %s" % (self.name, self.status, self.engineer_name, self.primary_language, self.second_lang)
class Zacker(Hacker):
    def __repr__(self):
        return "Zacker %s, status %s, engineer_name %s, 1_language %s, 2_lang %s, 3_lang %s" % (self.name, self.status, self.engineer_name, self.primary_language, self.second_lang, self.third_lang)
class Manager(Person):
    def __repr__(self):
        return "Manager %s, status %s, manager_name %s" % (self.name, self.status, self.manager_name)

person_join = people.outerjoin(engineers, engineers.c.person_id == people.c.person_id).outerjoin(managers).outerjoin(hackers).outerjoin(zackers)

person_mapper = mapper( Person, people, select_table=person_join,polymorphic_on=people.c.type, polymorphic_identity='person')
engsel = people.join(engineers, engineers.c.person_id == people.c.person_id)
engineer_mapper = mapper( Engineer, engineers, inherits=person_mapper, polymorphic_identity='engineer',
        select_table = engsel.outerjoin(hackers).outerjoin(zackers),
        inherit_condition = engineers.c.person_id == people.c.person_id
    )
mapper( Manager, managers, inherits=person_mapper, polymorphic_identity='manager')
hacksel = people.join(engineers, engineers.c.person_id == people.c.person_id).join(hackers)
hacker_mapper = mapper(Hacker, hackers, inherits=engineer_mapper, polymorphic_identity='hacker',
        select_table = hacksel.outerjoin(zackers)
)
mapper( Zacker, zackers, inherits=hacker_mapper, polymorphic_identity='zacker')

session = create_session(echo_uow=False)
employees=[]
employees.append( Manager(  name='boss', status='AAB', manager_name='manager1'))
employees.append( Engineer( name='dilbert', status='BBA', engineer_name='engineer1', primary_language='java'))
employees.append( Person(   name='joesmith', status='HHH'))
employees.append( Engineer( name='wally', status='CGG', engineer_name='engineer2', primary_language='python'))
employees.append( Hacker(   name='bo', status='XXX', engineer_name='engo', primary_language='punion', second_lang='asm'))
employees.append( Zacker(   name='jsmith', status='A', engineer_name='e2', third_lang = 'PL'))
for c in employees:
    session.save(c)

print session.new
session.flush()
session.clear()

print ' > for each class, see all items/heirs'
for P in (Person, Manager, Engineer, Hacker, Zacker):
    print '----', P
    q = session.query(P)
    for e in q: print e

#print 'anyone missing?'
q = session.query( Person)
assert sets.Set( e.name for e in q) == sets.Set(
    ['boss', 'dilbert', 'joesmith', 'wally', 'jsmith', 'bo'])
print

q = session.query( Engineer)
assert sets.Set( e.name for e in q) == sets.Set(
    ['dilbert', 'wally', 'jsmith', 'bo'])
print


#print ' > check identity between inheritance levels'
jsmith_s = [ session.query( P).get_by( name='jsmith')
                for P in [ Person, Engineer, Hacker, Zacker] ]
for c in jsmith_s[1:]:
    assert c is jsmith_s[0]

print '>>>>> base-only'
print ' ---', Person
q = list(session.query( Person).select_by( type='person'))
for e in q: print e
assert len(q)==1 #and q[0] ==

print ' ---', Hacker
q = list(session.query( Hacker).select_by( type='hacker'))
for e in q: print e
assert len(q)==1 #and q[0] ==


print '>>>>> base-only, 2'
print ' ---', Person
q = list(session.query( Person).from_statement( select( [people], people.c.type == 'person') ))
for e in q: print e
assert len(q)==1 #and q[0] ==

print ' ---', Hacker
q = list(session.query( Hacker).from_statement( select( [hacksel], people.c.type=='hacker' ) ))
for e in q: print e
assert len(q)==1 #and q[0] ==


print '>>>>> subclasses-only'
print ' ---', Person
q = list(session.query( Person).filter( people.c.type != 'person'))
for e in q: print e
assert len(q)==5 #and q[0] ==

print ' ---', Hacker
q = list(session.query( Hacker).filter( people.c.type != 'hacker'))
for e in q: print e
assert len(q)==1 #and q[0] ==


# vim:ts=4:sw=4:expandtab
