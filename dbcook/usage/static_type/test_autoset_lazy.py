#$Id$
import sys
import dbcook.usage.static_type.sa2static as orm
from static_type.types.atomary import Text
orm.Base.auto_set = False

Base = orm.Base

_debug = 'debug' in sys.argv

def model( is_lazy =True, is_auto_set =True, is_reference =True, is_value_default =False):
    l = locals()
    case = '  '.join( '%s=%5s' % (k,l[k])
                    for k in 'is_reference is_auto_set is_lazy is_value_default'.split() )
    print '--', case

    if is_reference:
        class Name( Base):
            nime = Text()

    class C( Base):
        if is_value_default:
            code = Text( default_value= 'alabala' )
        else:
            code = Text()
        if is_reference:
            ime = orm.Type4Reference( Name, auto_set= is_auto_set, lazy= is_lazy)
        else:
            ime = Text()    #TODO must make a deferred_column when is_lazy

    return locals()

from dbcook.usage.samanager import SAdb
import sqlalchemy
fieldtypemap = {
    Text: dict( type= sqlalchemy.String(100)),
}


def check( is_auto_set =True, is_reference =True, is_value_default =False, **kargs):
    namespace = model( is_auto_set =is_auto_set, is_reference =is_reference, is_value_default =is_value_default, **kargs)

    sa = SAdb()
    sa.open( recreate=True)
    b = sa.bind( namespace, builder= orm.Builder, fieldtypemap= fieldtypemap, base_klas= Base )

    C = namespace[ 'C']
    c = C()
    if not is_value_default:
        c.code = 'alabala'
    if is_reference:
        Name = namespace['Name']
        if not is_auto_set:
            c.ime = Name()
        c.ime.nime = 'aa'
    else:
        c.ime = 'aa'

    s = sa.session()
    s.save( c)
    s.flush()
    cexp = str( c)
    s.expire( c)
    c = None
    s.close()

    s = sa.session()
    #on v03 all this autoset/lazy doesnot work, so no point fixing C.code
    res = s.query( C).filter( C.code == 'alabala' ).all()
    if _debug: print res
    assert len(res) == 1
    r = str(res[0])
    assert r==cexp, '\n'.join( [ namespace['case'], r, '!=', cexp] )

    if is_reference:
        res = s.query( Name).one()
        assert res.nime == 'aa'

    sa.destroy( True)

failed = 0
buli = [ False, True]
for is_ref in buli:
    for is_auto in buli[ :1+is_ref]:
        for is_lazy in buli:
            for is_value_default in buli:
                try:
                    check( is_lazy=is_lazy, is_auto_set=is_auto, is_reference=is_ref, is_value_default=is_value_default)
                except AssertionError, e:
                    import traceback
                    traceback.print_exc()
                    failed +=1
assert not failed

# vim:ts=4:sw=4:expandtab
