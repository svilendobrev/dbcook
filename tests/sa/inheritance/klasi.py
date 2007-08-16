#$Id$

from sqlalchemy import *
from sqlalchemy.orm import *

def _printcallfunc( func, *args,**kargs):
    print func,'(\n ', args, '\n  '+ '\n  '.join( '%s=%s' % kv for kv in kargs.iteritems()), '\n)'
    return func( *args, **kargs)


class A(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.__class__.__name__ + " " + self.name
    def __eq__(self, o): return str(self) == str(o)
    def __ne__(self, o): return str(self) != str(o)

class B(A):
    def __init__(self, name, B_data):
        self.name = name
        self.B_data = B_data
    def __repr__(self):
        return A.__repr__(self) + " " + self.B_data

class C(B):
    def __init__(self, name, B_data, man2):
        self.name = name
        self.B_data = B_data
        self.man2= man2
    def __repr__(self):
        return B.__repr__(self) + "/" + self.man2

class E(B):
    def __init__(self, name, B_data, eee):
        self.name = name
        self.B_data = B_data
        self.eee= eee
        self.root = None
        self.next = None
    def __repr__(self):
        return B.__repr__(self) + "/" + self.eee +' :(' + str(self.root) + ')'+' :(' + str(self.next) + ')'

class D(A):
    def __init__(self, name, D_info):
        self.name = name
        self.D_info = D_info
        self.other = None
    def __repr__(self):
        return A.__repr__(self) + " " + self.D_info + ' :::(' + str(self.other) + ')'

###############

metadata = MetaData( 'sqlite:///')

class DB:
    #XXX unbound MetaData can't print joins/unions
    #bound MetaData: 'sqlalchemy.exceptions.NoSuchColumnError: "Could not locate column in row for column 'A.imea'"

    USE_D_LINKS = 1
    USE_B = 1
    USE_C = 1
    USE_D = 1
    USE_E = 1
    def __init__( me, echo =False, meta =None, dont_init =False):
        if not dont_init:
            meta = meta or metadata
            if echo: meta.bind.echo = True     #Debug Show SQL statements only
            meta.create_all()

    def populate( me, mappers):
        session = create_session()
        me.session = session

        a1 = A("A1")
        if me.USE_B:
            b1 = B("B1", "b1data")
        if me.USE_C:
            c1 = C("C1", 'c1data1', 'c1data2')
        if me.USE_D:
            d1 = D("D1", "d1data")
            d2 = D("D2", "d2data")
            if me.USE_D_LINKS:
               d2.other = d1
               d1.other = a1

        allE = []
        if me.USE_E:
            e1 = E("E1", 'e1data1', 'ee')
            e2 = E("E2", 'e2data1', 'ii')
            e2.root = e1
            e2.next = e1
            allE = [e1,e2]

            session.save(e1)
            session.save(e2)

        session.save(a1)
        if me.USE_B:
            session.save(b1)
        if me.USE_C:
            session.save(c1)
        if me.USE_D:
            session.save(d1)
            session.save(d2)
        session.flush()
        session.clear()

        class tests:
            def test( t, name, r ):
                ex = getattr( t, name, None)
                if ex is None: return
                ex = [str(e).strip() for e in ex]
                ex.sort()
                assert len(r) == len(ex), '%s!=%s: %s' % (len(r),len(ex),ex)
                print 'r ',r
                print 'ex',ex
                for a in ex:
                    assert a in r, 'item %s not in \n\t%s' % (a, ',\n\t'.join(r) )
            E  = allE
            C = D = []
            if me.USE_C: C = [c1, ]
            if me.USE_D: D = [d1, d2]
            B1 = []
            if me.USE_B: B1 = [b1, ]
            B  = B1 + C + E
            A1 = [a1, ]
            A  = A1 + B + D

        tests = tests()
        for mn in (['A', 'A1', ]+
                    + bool( me.USE_B)*['B', 'B1', ]
                    + bool( me.USE_C)*['C']+
                    + bool( me.USE_D)*['D']+
                    + bool( me.USE_E)*['E'] ):
            m = getattr( mappers, mn)
            print '--------', mn, m #.class_#__name__
            if 10:
                #ok if all join-union names are _same_
                x = session.query(m).select()
            else:
                #else, join-unions do not has to be in select_table
                y = session.execute( m, m.select_table, {})
                x = m.instances( y, session)
            res = [str(e).strip() for e in x]
            res.sort()
            print '  ', res
            tests.test( mn, res)

    def pipequery( me, mapper, selectable):
        y = me.session.execute( mapper, selectable, {})
        #XXX
        #y = selectable.execute()   #this one raises NotImplementedError for unions; same as print'ing them
        return mapper.instances( y, me.session)


# vim:ts=4:sw=4:expandtab
