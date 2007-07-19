#$Id$
#s.dobrev 2k4

'''some additional reflection tools - multilevel attrname get/set,
local vs see-through-hierarchy getattr,
fail-proof issubclass()
'''

def set_attrib( self, name, value, getattr =getattr, setattr=setattr):
    if isinstance( name, str):
        name = name.split('.')
    name1 = name[-1]
    if len(name)>1:
        for a in name[:-1]:
            self = getattr( self, a)
    setattr( self, name1, value )
    #exec( 'self.'+name+'=value' )

def get_attrib( self, name, *default_value, **kargs):
    if isinstance( name, str):
        name = name.split('.')
    _getattr = kargs.get( 'getattr', getattr)
    for a in name:
        try:
            self = _getattr( self, a)
        except AttributeError:
            if not default_value: raise
            return default_value[0]
    return self
    #if name.find('.')>0: return eval( 'self.'+name )
    #return getattr( self, name)

class get_itemer:
    'use: "%(a.b.c.d)s %(e)s" % get_itemer( locals() ) '
    def __init__( me, d): me.d = d
    def __getitem__( me, k):
        names = k.split('.', 1)
        r = me.d[ names[0] ]
        if len(names)>1:
            r = get_attrib( r, names[1] )
        return r


#######
# getattr(klas) looks up bases! hence use __dict__.get

def getattr_local_instance_only( me, name, *default_value):
    try:
        return me.__dict__[ name]
    except KeyError:
        if not default_value: raise AttributeError, name
        return default_value[0]

def getattr_local_class_only( me, name, *default_value):
    try:
        return me.__class__.__dict__[ name]
    except KeyError:
        if not default_value: raise AttributeError, name
        return default_value[0]

def getattr_local_instance_or_class( me, name, *default_value):
    try:
        return me.__dict__[ name]
    except (KeyError,AttributeError):
        return getattr_local_class_only( me, name, *default_value)

getattr_global = getattr

def getattr_in( me, local =True, klas =True, *a,**k):
    if local and klas:
        return getattr_local_instance_or_class( me, *a,**k)
    if local:
        return getattr_local_instance_only( me, *a,**k)
    if klas:
        return getattr_local_class_only( me, *a,**k)
    return getattr_global( me, *a,**k)     #plain getattr with all the lookup

#######

def setattr_kargs( *args, **kargs):
    assert len(args)==1
    x = args[0]
    for k,v in kargs.iteritems(): setattr( x, k, v)

########

# util/base.py
__issubclass = issubclass
def issubclass( obj, klas):
    from types import ClassType
    return isinstance( obj, (type, ClassType)) and __issubclass(obj, klas)

# vim:ts=4:sw=4:expandtab
