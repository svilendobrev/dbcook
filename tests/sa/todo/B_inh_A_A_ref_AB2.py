#$Id$

from sqlalchemy import *
from sqlalchemy.orm import *

#joined_table, polymorphic
def case( Alink='Manager' ):

    class Employee( object):
        name = '<notset>'
        def __str__(me):
            return ' '.join( [me.__class__.__name__, str(me.id), str(me.name), getattr( me.manager, 'name', '<none>') ])

    class Manager( Employee ):
        bonus = '<notset>'
        def __str__(me):
            return Employee.__str__(me) + ' ' + str(me.bonus)

    meta = MetaData( 'sqlite:///')

    employee_table = Table('Employee', meta,
            Column('id', Integer, primary_key=True),
            Column('name', String, ),
            Column('atype', String),
            Column('manager_id', Integer,
                        ForeignKey( Alink+'.id',
                           use_alter=True, name='whatever1'
                        )
                )
        )

    manager_table = Table('Manager', meta,
            Column('bonus', String, ),
            Column('id', Integer,
                        ForeignKey( 'Employee.id'),
                        primary_key=True,
                ),
    )
    meta.create_all()

    ajoin = {
        'Employee': employee_table.select( employee_table.c.atype == 'Employee'),
        'Manager': join( employee_table, manager_table, manager_table.c.id ==employee_table.c.id),
    }

    Ajoin = polymorphic_union( ajoin, None )
    mA = mapper( Employee, employee_table,
        select_table=Ajoin, polymorphic_on=Ajoin.c.atype,
        polymorphic_identity='Employee',
        properties={
            'manager': relation( Alink == 'Employee' and Employee or Manager,
                    primaryjoin=employee_table.c.manager_id==(Alink=='Employee' and employee_table or manager_table).c.id,
                    foreign_keys=employee_table.c.manager_id,
                    lazy=True,
                    uselist=False, post_update=True)
                }
        )

    mB = mapper( Manager, manager_table,
            polymorphic_identity='Manager',
            inherits = mA,
            inherit_condition = (employee_table.c.id ==manager_table.c.id),
    )

    #populate
    session = create_session()

    a = Employee()
    a.name = 'Dilberto'
    b = Manager()
    b.name = 'Boss'
    b.bonus = 'big'

    b.manager = (Alink == 'Employee' and a or b)

    session.save(a)
    session.save(b)

    session.flush()

    print a
    print b

    print list( employee_table.select().execute() )
    print list( manager_table.select().execute() )

    def test( klas, xid, xstr):
        one = session.query( klas).get_by_id( xid)
        x = str(one)
        r = 'single %(x)s ; expect: %(xstr)s' % locals()
        print '>>>>>', r
        assert x == xstr, r

        all = session.query( klas).all()
        x = '; '.join( str(z) for z in all )
        r = 'multiple %(x)s ; expect[0]: %(xstr)s' % locals()
        print '>>>>>', r
        assert len(all) >= 1, 'size? '+ r
        assert str(all[0]) == xstr, r

    test( a.__class__, a.id, str(a))
    test( b.__class__, b.id, str(b))


import sys
kargs = dict( kv.split('=') for kv in sys.argv[1:])
case( **kargs)

# vim:ts=4:sw=4:expandtab
