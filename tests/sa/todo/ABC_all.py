#$Id$

from sqlalchemy import *
from tests.util import runCBA

class Config( runCBA.Config):
    relink = True

config = Config()

from dbcook.baseobj import Base

def test( session, klas, aid, single, expect, **kargs_ignore):
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


from dbcook.sa_generator import *   #override some sqlalchemy items used below

def test_inh_ref_ABC(
        poly =True, inh ='concrete',
        Alink ='', Blink ='', BAlink ='', inhB='',
        Alazy =True, Blazy =True,
        Clink ='', Clazy =True, CAlink ='', CBlink ='', inhC='',
        printer =None, ):
    doC = config.doC
    Alink0 = Alink
    if Alink: Alink = Alink[0]
    Blink0 = Blink
    if Blink: Blink = Blink[0]
    Clink0 = Clink
    if Clink: Clink = Clink[0]

    db = create_engine( 'sqlite:///:memory:')
    meta = BoundMetaData( db)
    meta.engine.echo = config.echo

    class A( Base):
        props = [ 'id', 'name' ] + bool(Alink)*['link1' ]
        data = property( lambda me: me.name)
    class B( inhB and A or Base ):
        props = (inhB and A.props or ['id']) + ['data2' ] + bool(Blink)*['link2' ]
        data = property( lambda me: me.data2)
    clasi = dict( A=A,B=B)
    if doC:
        class C( inhC=='A' and A or inhC=='B' and B or Base ):
            props = (inhC=='A' and A.props or inhC=='B' and B.props or ['id']) + ['data3' ] + bool(Clink)*['link3' ]
            data = property( lambda me: me.data3)
        clasi['C'] = C

######
    table_A = Table('A', meta,
            Column('id', Integer, primary_key=True),
            Column('name', String, ),
        )
    if poly and inh and inh != 'concrete' and inhB=='A' or inhC=='A':
        table_A.append_column( Column('atype', String) )

    def col_A( t):
        t.append_column( Column('name', String ))
        if Alink:
            t.append_column( Column('link1_id', Integer,
                            ForeignKey( Alink+'.id', use_alter=True, name='whatever1')
                    ))
    col_A( table_A)


######
    table_B = Table('B', meta,
            Column('id', Integer, primary_key=True,
                        *(inhB and inh=='joined' and [ForeignKey( 'A.id')] or [])
                ))
    if poly and inh and inh != 'concrete' and inhC=='A' and inhB!='A':
        table_B.append_column( Column('atype', String) )

    def col_B( t ):
        if inh == 'concrete' and inhB=='A':
            col_A( t)
        t.append_column( Column('data2', String ))
        if Blink:
            t.append_column( Column('link2_id', Integer,
                            ForeignKey( Blink+'.id', use_alter=True, name='whatever2')
                    ))
    col_B( table_B)

######
    if config.doC:
        table_C = Table('C', meta,
                Column('data3', String, ),
                Column('id', Integer, primary_key=True,
                            *(inhC and inh=='joined' and [ForeignKey( inhC+'.id')] or [])
                    ),
        )
        if inh == 'concrete':
            if inhC =='B': col_B( table_C)
            elif inhC =='A': col_A( table_C)

        if Clink:
            table_C.append_column( Column('link3_id', Integer,
                            ForeignKey( Clink+'.id', use_alter=True, name='whatever3')
                    ))

#################
    meta.create_all()
    if printer: printer.pklasi_tabli( meta, Base, locals())

    Ajoin = Bjoin = None
    if poly and inh:
        ajoin = {
            'A': inh=='concrete' and table_A.select() or table_A.select( table_A.c.atype == 'A', ),
        }
        jb = None
        if inhB=='A':
            jb = inh=='concrete' and table_B.select() or join( table_A, table_B, table_B.c.id ==table_A.c.id)
            ajoin['B'] = jb
        jc = None
        if inhC:
            if inh=='concrete': jc = table_C.select()
            else:
                if inhC=='A': jc = join( table_A, table_C, table_C.c.id ==table_A.c.id)
                else:
                    assert inhC=='B'
                    if inhB=='A':
                        jc = join( jb, table_C, table_C.c.id ==table_A.c.id)
                        jb = ajoin['B'] = jb.select( table_A.c.atype == 'B', )
                    else:
                        jc = join( table_B, table_C, table_C.c.id ==table_B.c.id)
            ajoin['C'] = jc

        Ajoin = polymorphic_union( ajoin, inh=='concrete' and 'atype' or None )
        mapper_A = mapper( A, table_A, polymorphic_identity='A',
                    select_table=Ajoin,
                    polymorphic_on=Ajoin.c.atype,
                )

        if inhC=='B':
            bjoin = { 'B': jb, 'C': jc }    #???
            Bjoin = polymorphic_union( bjoin, inh=='concrete' and 'atype' or None )

    else:
        mapper_A = mapper( A, table_A)

    def alink( m,t):
        if Alink:
            m.add_property( 'link1',
                    relation( clasi[ Alink],
                        primaryjoin= t.c.link1_id==(Alink=='A' and table_A or table_B).c.id,
                        foreign_keys = t.c.link1_id,    #must
                        remote_side = (Alink=='A' and table_A.c.id or None),    #must
                        lazy= Alazy,
                        uselist=False, post_update=True
                    ))
    alink( mapper_A, table_A)

#########
    mapper_B = mapper( B, table_B, polymorphic_identity='B',
                concrete= inh=='concrete',
                inherits= inhB=='A' and mapper_A or None,
                inherit_condition= inhB=='A' and inh=='joined' and (table_A.c.id == table_B.c.id) or None,
                select_table = Bjoin,
                polymorphic_on= Bjoin and Bjoin.c.atype or None,
            )

    def blink(m,t):
        if Blink:
            m.add_property( 'link2',
                    relation( clasi[ Blink],
                        primaryjoin= t.c.link2_id==(Blink=='A' and table_A or table_B).c.id,
                        foreign_keys = t.c.link2_id,
                        remote_side = (Blink=='B' and table_B.c.id or None),
                        lazy= Blazy,
                        uselist=False, post_update=True,
                    ))

    blink( mapper_B, table_B)
    if config.relink and inh=='concrete': #must
        alink( mapper_B, table_B)

#######
    if doC:
        inhMC = inhC=='A' and mapper_A or inhC=='B' and mapper_B or None
        mapper_C = mapper( C, table_C, polymorphic_identity='C',
                concrete= inh=='concrete',
                inherits= inhC=='A' and mapper_A or inhC=='B' and mapper_B or None,
                inherit_condition= inhM and inh=='joined' and (inhM.local_table.c.id == table_C.c.id) or None,
            )

        if Clink:
            mapper_B.add_property( 'link2',
                    relation( clasi[ Blink],
                        primaryjoin= table_B.c.link2_id==(Blink=='A' and table_A or table_B).c.id,
                        foreign_keys = table_B.c.link2_id,
                        remote_side = (Blink=='B' and table_B.c.id or None),
                        lazy= Blazy,
                        uselist=False, post_update=True,
                    ))

        if config.relink and inh=='concrete': #must
            alink( mapper_C, table_C)
            blink( mapper_C, table_C)

###########################
    if printer: printer.pmapi( locals())

    #populate
    session = create_session()

    #...


help = '''test_inh_ref_ABC [options]
tries all possible cases of single relations of 3 classes A, B, C:
        inheritance (None,concrete,joined)
      x Alink (None,A,B,A1,B1)
      x Blink (None,A,B,A1,B1)
      x BAlink (None,A,B,A1,B1), excluding some meaningless combinations.
        covering any self-ref, cyclic ref, etc. with and without inheritance.
BAlink is B's Alink when B inherits A; linking to A1/B1 means _other_
object of same type, while linking to A/B means same just those initial two
(eventualy getting a self-ref/cyclic-ref).
Think of it as A=Employee, B=Manager, Alink=mymanager, Blink=mysecretary.

''' + runCBA.help_workflow + '''
  no_relink     :: do not overload base-class' references for concrete-inher. mappers
''' + runCBA.help_output + runCBA.help_combination

if __name__ == '__main__':
    #...
# vim:ts=4:sw=4:expandtab
