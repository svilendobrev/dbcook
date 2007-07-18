#$Id$

from sqlalchemy import *
import traceback

from tests.util.combinator import ConfigCombinator
class Config( ConfigCombinator):
    session_clear = True
    query = True
    relink = True

    debug = False
    echo = False
    one_line = False
    generate = []
    dump = False

    dummy = False
    db = 'sqlite:///:memory:'

    funcname = 'test_AB_'
    prnname = '_test_AB_%s.py'

    links = [None,'A','B']      #the valid ones
    Alinks = Blinks = []        #=links by default

config = Config()

if 0:
    from dbcook.polymunion import polymorphic_union

class Base( object):
    _dataname = 'name'
    def __str__( self):
        r = self.__class__.__name__ + '('
        for k in self.props:
            v = getattr( self, k, '<notset>')
            if isinstance( v, Base):
                v = '>'+str(getattr(v, v._dataname))
            r+= ' '+k+'='+str(v)
        return r+' )'

def test( session, klas, aid, single, expect, **kargs_ignore):
    if config.session_clear: session.clear()
    klasname = klas.__name__
    if single:
        s = session.query( klas).get_by_id( aid)
        x = str(s)
        r = 'single %(klasname)s %(aid)s \t%(x)s \n   expect: \t%(expect)s' % locals()
    else:
        expect.sort()
        s = session.query( klas).select()
        x = [ str(z) for z in s ]
        x.sort()
        r = 'multi  %(klasname)s     \t%(x)s \n   expect: \t%(expect)s' % locals()
    if config.debug: print '>>>', r
    assert x == expect, r

if 0:
    def lazy( klas, link):
        attrklas = link=='A' and A or B
        r = config.lazy
        if issubclass( attrklas, klas) or issubclass( klas, attrklas): r = True  #self-referential
        return r

from dbcook.sa_generator import *   #override some sqlalchemy items used below

def declarator( klas):
    return '''\
    _dataname = ''' + repr(klas._dataname)


def test_inh_ref_A_B_A( meta,
        Alink='', Blink='', BAlink='',
        poly=True, inh='concrete',
        Alazy=True, Blazy=True,
        printer =None
    ):
    assert not ( inh =='concrete' and 'PM' in str(Alink) + str(Blink)), 'concrete polymorphism not supported'

    Alink0 = Alink
    if Alink: Alink = Alink[0]
    Blink0 = Blink
    if Blink: Blink = Blink[0]

    class A( Base):
        props = [ 'id', 'name' ] + bool(Alink)*['linkA' ]
        _dataname = 'name'
    class B( inh and A or Base ):
        props = (inh and A.props or ['id']) + ['dataB' ] + bool(Blink)*['linkB', ]
        _dataname = 'dataB'


    table_A = Table('A', meta,
            Column('id', Integer, primary_key=True),
            Column('name', String, ),
        )
    if Alink:
        table_A.append_column( Column('linkA_id', Integer,
                        ForeignKey( Alink+'.id', use_alter=True, name='whatever1')
                )
        )
    if poly and inh and inh != 'concrete':
        table_A.append_column( Column('atype', String) )


    table_B = Table('B', meta,
            Column('dataB', String, ),
            Column('id', Integer, primary_key=True,
                        *(inh=='joined' and [ForeignKey( 'A.id')] or [])
                ),
    )
    if inh == 'concrete':
        table_B.append_column(  Column('name', String, ), )
        if Alink:
            table_B.append_column( Column('linkA_id', Integer,
                            ForeignKey( Alink+'.id', use_alter=True, name='whatever2')
                    )
            )
    if Blink:
        table_B.append_column( Column('linkB_id', Integer,
                        ForeignKey( Blink+'.id', use_alter=True, name='whatever3')
                )
        )

    meta.create_all()
    if printer:
        printer.ptabli( meta)
        printer.pklasi( Base, locals(), declarator=declarator )

    if poly and inh:
        ajoin = {
            'A': inh=='concrete' and table_A or table_A.select( table_A.c.atype == 'A'),
            'B': inh=='concrete' and table_B or join( table_A, table_B, table_B.c.id ==table_A.c.id),
        }
        Ajoin = polymorphic_union( ajoin, inh=='concrete' and 'atype' or None )
        mapper_A = mapper( A, table_A, polymorphic_identity='A',
            select_table=Ajoin, polymorphic_on=Ajoin.c.atype,
        )
    else:
        mapper_A = mapper( A, table_A)
        Ajoin = None

    if Alink:
        mapper_A.add_property( 'linkA',
                relation( Alink == 'A' and A or B,
                    primaryjoin= table_A.c.linkA_id==(Alink=='A' and table_A or table_B).c.id,
                    foreign_keys= table_A.c.linkA_id,    #must
                    remote_side = (Alink=='A' and table_A.c.id or None),    #must
                    lazy= Alazy,
                    uselist=False, post_update=True
                )
        )

    mapper_B = mapper( B, table_B, polymorphic_identity='B',
            concrete= inh=='concrete',
            inherits= inh and mapper_A or None,
            inherit_condition= inh=='joined' and (table_A.c.id == table_B.c.id) or None,
    )

    if Blink:
        mapper_B.add_property( 'linkB',
                relation( Blink == 'A' and A or B,
                    primaryjoin= table_B.c.linkB_id==(Blink=='A' and table_A or table_B).c.id,
                    foreign_keys= table_B.c.linkB_id,
                    remote_side = (Blink=='B' and table_B.c.id or None),
                    lazy= Blazy,
                    uselist=False, post_update=True,
                ),
            )
    if config.relink and Alink and inh=='concrete': #must
        mapper_B.add_property( 'linkA',
                relation( Alink == 'A' and A or B,
                    primaryjoin= table_B.c.linkA_id==(Alink=='A' and table_A or table_B).c.id,
                    foreign_keys= table_B.c.linkA_id,
                    lazy= Alazy,
                    uselist=False, post_update=True
                )
        )

    if printer: printer.pmapi( locals())

    #populate
    session = create_session()

    def popu( AX,BX):
        a = AX()
        a.name = 'anna'
        b = BX()
        if inh:
            b.name = 'ben'
        b.dataB = 'gun'

        a1 = b1 = None
        ABlinks = Alink0, Blink0
        if 'A1' in ABlinks:
            a1 = AX()
            a1.name = 'a1'
        if 'B1' in ABlinks or 'A1PM' in ABlinks:
            b1 = BX()
            b1.dataB = 'b1'

        links = dict( A=a, B=b, A1=a1, B1=b1,
                APM=b,   #b inh a, link of type a points to b
                A1PM=b1, #b inh a, link of type a points to b1
            )

        if Alink:
            a.linkA = links[ Alink0]
            if BAlink:
                b.linkA = links[ BAlink]
        if Blink:
            b.linkB = links[ Blink0]

        return a,b,a1,b1

    if printer:
        class AX(A): pass
        class BX(B): pass
        a,b,a1,b1 = popu( AX,BX)    #fake - to avoid mapper-compilation errors
        printer.populate( dict( a=a, b=b, a1=a1, b1=b1), idname='id', klas_translator= {AX:A,BX:B}.get )

    a,b,a1,b1 = popu( A,B)      #this may fail!

    session.save(a)
    session.save(b)

    session.flush()
    sa = str(a) #does not work after session.clear()
    sb = str(b) #does not work after session.clear()
    expectB = dict( klas=b.__class__, aid=b.id, ssingle=sb,
        smultiple=[sb]+bool(b1)*[str(b1)] )
    expectA = dict( klas=a.__class__, aid=a.id, ssingle=sa,
        smultiple=[sa]+bool(a1)*[str(a1)]+bool(inh)*bool(poly)*expectB['smultiple'] )

    if config.debug:
        print sa
        print sb

    if config.dump:
        print list( table_A.select().execute() )
        print list( table_B.select().execute() )

    err = []
    if config.query:
        for exp in (expectA,expectB):
            for k in ('ssingle', 'smultiple'):
                expect=exp[k]
                try:
                    test( session, expect=expect, single='ssingle'==k, **exp)
                except KeyboardInterrupt: raise
                except AssertionError, e:
                    klas = exp['klas'].__name__
                    eklas = e.__class__.__name__
                    err.append( '%(eklas)s:\n  %(e)s' % locals() )
                except Exception, e:
                    klas = exp['klas'].__name__
                    eklas = e.__class__.__name__
                    err.append( '%(eklas)s: %(e)s\n  << %(k)s %(klas)s' % locals() )    #\n    expect %(expect)s
                    traceback.print_exc()

    return err



help = '''test_inh_ref_A_B_A [options]
tries all possible cases of single relations of two classes A and B:
        inheritance (None,concrete,joined)
      x Alink (None,A,B,A1,B1)
      x Blink (None,A,B,A1,B1)
      x BAlink (None,A,B,A1,B1), excluding some meaningless combinations.
        covering any self-ref, cyclic ref, etc. with and without inheritance.
BAlink is B's Alink when B inherits A; linking to A1/B1 means _other_
object of same type, while linking to A/B means same just those initial two
(eventualy getting a self-ref/cyclic-ref).
Think of it as A=Employee, B=Manager, Alink=mymanager, Blink=mysecretary.

''' + ConfigCombinator._help + ConfigCombinator._help_no_eager + '''
workflow/API options:
  no_relink   :: don't do this: for concrete inher. mappers, overload base-class' references with proper ones
  no_session_clear  :: dont do a session.clear() before querying
  db=         :: db-connection (=sqlite:///)

output options:
  generate=   :: create unittest source ('''+config.prnname%('XXX',)+'''):
                  one:  all-in-one-file, each combination = separate function
                  many: each combination = separate file
                  failed: only the failed tests
                 default=none ; e.g. generate=one,failed
  one_line    :: show errors as one line
  debug       :: debug what's being tested
  dump        :: dump tables before querying
  echo        :: echo SQL
  dummy       :: only show combinations, run nothing
'''

if __name__ == '__main__':
    config.getopt( help)
    print 'config:', config

    fmt = ', '.join( '%(arg)s=%%(%(arg)s)4s' % locals() for arg in 'poly inh Alink Blink BAlink Alazy Blazy'.split() )

    from tests.util import multi_tester
    class ABtester( multi_tester.MultiTester):
        Printer = Printer
#        def any_echo( me): return me.config.debug or me.config.echo
        def _run_one( me, printer, **parameters):
            db = create_engine( config.db )
            meta = BoundMetaData( db)
            meta.engine.echo = config.echo

            err = test_inh_ref_A_B_A( meta, printer=printer, **parameters)

            #destroy ALL
            meta.drop_all()
            clear_mappers()
            db.dispose()

            return err

        def run_all( me):
            Alinks = config.getXlinks('A')
            Blinks = config.getXlinks('B')
            bases = dict.fromkeys( ['A', '', None], [None])
            for inh,poly in config.inhpolycomb():  ##no inh->no poly
                bases['B'] = inh and ['A'] or [None]
                for Alink,Alazy in config.linklazycomb( 'A', Alinks, bases):
                    if not inh and Alink and 'PM' in Alink: continue
                    for Blink,Blazy in config.linklazycomb( 'B', Blinks, bases):
                        if not inh and Blink and 'PM' in Blink: continue
                        for BAlink in [config._nolink] + bool(Alink and inh)*[ Alink]:
                            me.run_one( Alink=Alink, Blink=Blink, BAlink=BAlink, poly=poly, inh=inh, Alazy=Alazy, Blazy=Blazy)
            me.do_report()
            me.do_generate()

        def str_params( me, parameters):
            return fmt % parameters

    t = ABtester( config)
    t.run_all()

# vim:ts=4:sw=4:expandtab
