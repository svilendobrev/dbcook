if 10:
    from model.base import *
    #Model=Element
else:
    from model.struct_base import *
    from model.struct_base import _Base
    Model = _Base
    from dbcook.usage.samanager import SAdb
    class DB_( object):
        session = None #have flush()
        def reset( me, namespace, counterBase= None, recreate =True, get_config =False):
            me.sa = SAdb()
            me.sa.open( recreate=True)
            import sqlalchemy
            fieldtypemap = {
                Number: dict( type= sqlalchemy.Integer, ),
                Text:   dict( type= sqlalchemy.String(30), ),
            }
            me.sa.bind( namespace, base_klas=_Base, builder=o2r.Builder, fieldtypemap=fieldtypemap)
            me.session = me.sa.session()
            if counterBase: counterBase.fill( *me.sa.klasi.iterkeys() )
        def save( me, *args):
            assert args
            me.sa.saveall( me.session, *args)
            me.session.flush()
        def query( me, *a, **k):
            return me.session.query(*a,**k)

    DB=DB_()
if 10:
    from model.m2 import Zakon, Firma
    from model.pravilnik import ParamValueOwnership
else:
    class Boza(Element):
        auto_set = True
        xx = Number( default_value=33)
    class Zakon( Model):
        ime = Text()

    class Firma( Model):
        ime = Text()
        _zakon = Reference2( Zakon, 'firmi')
        boza = Reference( Boza, auto_set=True)

DB.reset( locals())
zakon = Zakon(ime = 'Z')
DB.save( zakon)
def prints( s):
    print 20*'s'
    allnew = s.new
    allmod = [ i for i in s.dirty if s.is_modified( i) ]
    alldel = s.deleted
    if 1:
        print ':to-be-inserted'
        for i in allnew: print i

        print ':to-be-modified'
        for i in allmod: print i

        print ':to-be-deleted'
        for i in alldel: print i


print 1111111111111
prints( DB.session)
print 22222222222
#firma = Firma( ime= 'aaa')
#z = DB.query( Zakon).first()
#firma.zakon= z
#DB.session.flush()

update = 0#True

firma = Firma( ime= 'F')
z = DB.query( Zakon).first()
if update:
    DB.save(firma)
#firma.zakon= z
firma._zakon.append(z)

print 33333333333
#firma._zakon = []
def hist( instance, attr):
    aa=  added,unchanged,deleted = getattr( instance.__class__, attr).get_history( instance)
    return aa
def restore( instance, attr):
    added,unchanged,deleted = getattr( instance.__class__, attr).get_history( instance)
    setattr( instance, attr, unchanged)

print hist( z, 'firmi')
#restore( z,'firmi')
#restore( firma, '_zakon')
#firma._zakon.remove( z)
if update:
    DB.session.expire(firma)
else:
    for k in firma._DBCOOK_references:  #for prop in klas.props if not prop.use_list
        print 'AAAAAAA', k
        DB.session.expunge( getattr( firma, k))
    DB.session.expunge( firma)
print 1000000000000000000000000
prints( DB.session)
print 444444444
DB.session.flush()
