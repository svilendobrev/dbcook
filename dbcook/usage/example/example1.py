#$Id$


'example: all just plain - not using samanager'

#### administrative stuff
from dbcook.usage import sa_hack4echo   #nicer selects echoed PLEAZE

# get a builder
import dbcook.usage.plainwrap as o2r
import sqlalchemy
# define some types
class Text( o2r.Type): pass
class Int(  o2r.Type): pass
class Bool( o2r.Type): #pass
    column_def = sqlalchemy.Boolean(30)

class Base( o2r.Base):
    DBCOOK_no_mapping = True
    def __init__( me, **kargs):
        o2r.Base.__init__( me)
        for k,v in kargs.iteritems():
            setattr( me,k,v)

####### start actual model-definition

class Employee( Base):
    name    = Text()
    age     = Int()
    haskids = Bool()
    manager = o2r.Reference( 'Employee')    #or 'Manager'
    DBCOOK_inheritance = 'joined'   #for subclasses - this(base) one is always concrete anyway
    #or DBCOOK_inheritance = o2r.table_inheritance_types.JOINED
    DBCOOK_has_instances = True     #by default only class-tree leaves have instances

class Manager( Employee):
    secretary = o2r.Reference( Employee)
    DBCOOK_has_instances = True

class Engineer( Employee):
    machine = Text()

#make this switchable
import sys
cfg_dr_base = len(sys.argv)>1 and sys.argv[1]
director_base = dict(
        Employee=Employee, Manager=Manager, Engineer=Engineer
    ).get( cfg_dr_base, Manager)

class Director( director_base):
    if 'secretary' not in director_base.__dict__:   #no life without a secretary!
        secretary = o2r.Reference( Employee)
    salary = Int()

class Work( Base):
    name = Text()
    assignee = o2r.Reference( Employee)

####### endof model-definition


import sqlalchemy
import sqlalchemy.orm
meta = sqlalchemy.MetaData( sqlalchemy.create_engine('sqlite:///', echo= 'echo' in sys.argv ))

# map attr-types to sa-column-types
fieldtypemap = {
    Text: dict( type= sqlalchemy.String(100), ),
    Int : sqlalchemy.Integer,
    Bool: None, #i.e. use Bool.column_def
}

# build the mapping
mybuild = o2r.Builder( meta,
        locals(),       #just scan anything here that looks like subclass of Base
        fieldtypemap,
        generator =True     #lets see how this would look in plain sqlalchemy
    )

#### that was it. lets use it... ####

#see how this should look in plain SA calls
if mybuild.generator:
    print '========= generated SA set-up'
    print mybuild.generator.out
    print '========= eo generated SA set-up'


def populate():
    a = Employee()
    a.name = 'anna'
    a.haskids = True
    a.age = 30

    a1 = Employee()
    a1.name = 'digger'
    a1.age = 24

    m = Manager()
    m.name = 'mummy'
    m.extras= 'big'
    m.age = 50
    m.secretary = a1
    m.manager = m       #self-boss ? uncommenting this AND h.manager = h fixes circ-dep???

    a.manager = m
    a1.manager = m

    e = Engineer()
    e.name = 'engo'
    e.manager = m
    e.age = 40
    e.machine = 'fast'

    e2 = Engineer()
    e2.name = 'ena'
    e2.manager = e
    e2.age = 30
    e2.machine = 'deep'

    h = Director()
    h.name = 'heady'
    h.secretary = a

    m.manager = h

    w1= Work( name='dig', assignee=e2 )
    w2= Work( name='rip', assignee=a1 )
    w3= Work( name='rip', assignee=a  )

    session = sqlalchemy.orm.create_session()
    #anything off Base, go to db
    for a in locals().values():
        if isinstance( a, Base): session.save( a)
    session.flush()


def test_klas_tree_structure():
    #check whats in the tables:
    print '\n-------------- all tables:'
    for klas in [Employee, Manager, Engineer, Director]:
        table = mybuild.tables[ klas]
        print klas,':',[r for r in table.select().execute()]

    print '\n-------------- classes and subclassing:'
    session = sqlalchemy.orm.create_session()
    for klas in [Employee, Manager, Engineer, Director]:
        print '== query_ALL_under', klas.__name__
        q1 = session.query( klas).all()
        for x in q1: print ' ', x

        mapper = mybuild.mappers[ klas]
        print '== query_BASE_only', klas.__name__
        if mapper.plain:
            q2 = session.query( mapper.plain).all()
            for x in q2: print ' ', x
            for a in q2: assert a.__class__ == klas
        else: q2 = []

        print '== query_SUB_classes_only', klas.__name__
        if mapper.polymorphic_sub_only:
            q3 = session.query( klas)
            flt = mapper.polymorphic_sub_only
            if isinstance( flt, sqlalchemy.sql.Selectable):
                q3 = q3.from_statement( flt)
            else:
                q3 = q3.filter( flt)
            q3 = q3.all()
            for x in q3: print ' ', x
            for a in q3: assert a.__class__ != klas and isinstance( a, klas)
        else: q3 = []

        assert len(q2)+len(q3)==len(q1)

def prn(q):
    for x in q: print ' ', x
    print

def test_selects():
    from dbcook import expression
    session = sqlalchemy.orm.create_session()
    empl_table = mybuild.tables[ Employee]

    ######## simple
    age = 40
    print '====== all Employee with age<=', age, ', plain SA'
    prn( session.query( Employee).filter( empl_table.c.age <= age).all() )

    print '       --- same, via expression'
    prn( expression.query1( lambda self: self.age <= age, klas=Employee, session=session) )

    expression._debug = 'dbg' in sys.argv


    ######## 1 level self-ref
    age = 40
    print '====== all Employee with manager of age<=', age, ', plain SA'
    mgr = empl_table.alias()
    prn( session.query( Employee).filter(
            (mgr.c.age <= age)
            & (empl_table.c.manager_id == mgr.c.db_id) ).all() )

    print '       --- same, via expression/equivalent'
    prn( expression.query1(
            lambda self, selfm=Employee: (self.manager == selfm.db_id) & (selfm.age <= age),
            klas=Employee, session=session) )

    print '       --- same, via expression/automatic'
    prn( expression.query1(
            lambda self: self.manager.age <= age,
            klas=Employee, session=session) )


    ######## multilevel self-ref
    mgr2 = empl_table.alias()
    print '====== multilevel: all Employee with manager with manager of age >', age, 'plain SA'
    prn( session.query( Employee).filter(
            (mgr2.c.age > age)
            & (mgr.c.manager_id == mgr2.c.db_id)
            & (empl_table.c.manager_id == mgr.c.db_id) ).all() )

    print '       --- same, via expression/automatic'
    prn( expression.query1(
            lambda self: self.manager.manager.age > age,
            klas=Employee, session=session) )

    print '       --- 2-klas, via expression/automatic - ok if Work owns .name'
    prn( expression.query1(
            lambda self, ot=Work: (ot.name == 'dig') & (self.db_id == ot.assignee),
            klas=Employee, session=session) )

populate()
test_klas_tree_structure()
test_selects()

# vim:ts=4:sw=4:expandtab
