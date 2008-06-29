#$Id$
# -*- coding: cp1251 -*-

#TODO XXX test forw.decl Association.Relation( klasname)

from tests.util.context import *
if USE_STATIC_TYPE:
    Base.auto_set = False
else:
    from dbcook.util.attr import setattr_kargs
    class Base( Base):
        __init__ = setattr_kargs

SAdb.config.getopt()
print 'config:', SAdb.config

class Base4Association( Base, orm.Association):
    DBCOOK_no_mapping = True

class X( Base):
    'test forw-decl assoc'
    x = Text()
    x_ab = Base4Association.Relation( 'IntermediateAB')

class IntermediateAB( Base4Association):    #color
    color = Text()
    a_link = Base4Association.Link( 'A')
    b_boza = Base4Association.Link( 'B', attr= 'all_ba')
#    a = Reference('A')     #plain reference - nothing to do with the AB association
    a2_link = Base4Association.Link( 'A', attr= 'alla2', nullable= True)
    c_link = Base4Association.Link( 'C', 'cccc' )
    x_link = Base4Association.Link( X, nullable= True )
#    DBCOOK_hidden = True

if 0:
    class IntermedADE( Base4Association):   #weigth
        weigth = Text()
        a = Base4Association.Link( 'A', )
        d = Base4Association.Link( 'D', attr= 'all_ade')
        e = Base4Association.Link( 'E', attr= 'all_ade')

    class IntermediateABC2( IntermediateAB):   #color and length
        length = Text()
        c = Base4Association.Link( 'C', attr= 'all_abc2')

class A( Base):
    name = Text()
    all_ab  = IntermediateAB.Relation()
#    all_abc = IntermediateABC2.Relation()
#    all_ade = IntermedADE.Relation()
#    x = Reference( 'A')
    alla2   = IntermediateAB.Relation()

class B( Base):
    name    = Text()
#    my_ab   = IntermediateAB.Relation()  #override -> error
#    all_ab2 = Base4Association.Relation( 'IntermediateAB2' )
#        a = Reference( A)#.Instance()
#    all_ba  = IntermediateAB.Relation()

if 10:
    class C( Base):
        name = Text()
#        cccc = IntermediateAB.Relation()
if 0:
    class D( Base):
        dname = Text()
    class E( Base):
        ename = Text()

if 0:
    class IntermediateAB2( Base4Association): #just relation, after klases
        a = Base4Association.Link( A )
        b = Base4Association.Link( B )

sa = SAdb()
sa.open( recreate=True)
types = locals()
sa.bind( types, base_klas= Base )

#############

a  = A( name= 'a1')
a3 = A( name= 'a3')
b1 = B( name= 'b1' )
b2 = B( name= 'b2' )
c = C( name = 'c')
c2 = C( name = 'c2')
#a.all_ab.append( b) )
a.all_ab.append( IntermediateAB( b_boza= b1, color='green', a2_link = a3, c_link=c2) )
a.all_ab.append( b_boza= b2, color='rrrr', a2_link = None, c_link= c)
#b1.all_ab2.append( IntermediateAB2( a= a, ) )
print '1111', [i.b_boza for i in a.all_ab]

s= sa.session()
sa.saveall( s, locals() )
s.flush()

if hasattr( b2.__class__, 'all_ba'):
    print 'b2.all_ba', b2.all_ba
print 'a3.alla2', a3.alla2
if hasattr( c.__class__, 'cccc'):
    print 'c.cccc', c.cccc

s.clear()
sa.query_all_tables()
s= sa.session()
aa = s.query( A ).filter_by(name='a1').first()
print aa
print 'xxxxxxx'
l = [i.b_boza for i in aa.all_ab]
print '2222', l
assert len(l) ==2

# vim:ts=4:sw=4:expandtab
