#$Id$

from dbcook.util.config import Config

#####################

def always_lazy( klas, link, bases):
    if not klas or not link: return True
    klas=klas[0]
    link=link[0]
    if klas == link: return True  #self-ref
    if klas in bases[ link] or link in bases[ klas]: return True  #inh-self-ref
    return False
def lazyies( klas, link, bases):
    return always_lazy( klas,link,bases) and [True] or [True,False]


class ConfigCombinator( Config):
    poly_all = False
    sisters = True
    polymorphic = True
    eager = True

    inhs = [ None, 'concrete', 'joined']  #all valid ones
    #Binhs = [ '', 'A']         #all valid ones
    #Cinhs = Binhs + [ 'B']     #all valid ones

    links = ['',] #'A','B','C']    #all valid ones; [0] is nolink
    #Alinks = Blinks = Clinks = None #=use .links

    _nolink = property( lambda me: me.__class__.links[0] )

    _inhs_validator = dict.fromkeys( ['', None, 'None'],  None )
    _inhs_validator.update( dict.fromkeys( ['concrete', 'conc', 'c'], 'concrete'))
    _inhs_validator.update( dict.fromkeys( ['joined',   'join', 'j'], 'joined'))


    _help = '''\
combination options:
  no_sisters  :: only link to A,B,C themselves; no additional instances (A1,B1,C1)
  no_polymorphic:: only link to exact class instances (A), not to subclassed (B for A, if B inhs A)
  poly_all    :: do non-polymorphic even for inherit (default bool(poly)==bool(inherit)
  inhs=       :: which inheritance-kinds to use, one or more of (None,concrete,joined) (default:all)
  links=      :: all links to which types, e.g. =A,C  (default:all=None,A,B,C); uses C only if enabled (doC)
  Alinks=     :: A links to which types, e.g. =A,C    (default:=links)
  Blinks=     :: B links to which types, e.g. =A,None (default:=links)
'''

    _help_eager = '''\
  eager       :: also do eager/non-lazy references (default: no, only lazy)
'''
    _help_no_eager = '''\
  no_eager    :: don't do eagers, i.e. only lazy references (default: do lazy and eager if possible)
'''


    def inhpolycomb( config):
        inhs = config.get_inhs()
        polys = config.get_polys()
        for inh in inhs:
            for poly in (inh and polys or [0]):     #no inh->no poly
                yield inh,poly

    def linklazycomb( config, klas, links, bases):
        for link in links:
            for lazy in (config.eager and lazyies( klas, link, bases) or [True]):
                yield link,lazy

    def __init__( config, *args,**kargs):
        #TODO: remake it with sets
        dvalidlink = dict.fromkeys( ['None', None, ''], config._nolink)
        for i in config.__class__.links[1:]:
            dvalidlink[i]=i
            j = i+'0'
            dvalidlink[j]=j
            j = i+'1'
            dvalidlink[j]=j

        for i in config.__class__.links[1:-1]:  #non-leaf
            j = i+'PM'
            dvalidlink[j]=j
            j = i+'1PM'
            dvalidlink[j]=j

        config._links_validator = dvalidlink
        Config.__init__( config, *args,**kargs)

    def getXlinks( config, X, ignores =[]):
        ll = getattr( config, X+'links') or config.links or ['']
        ll = [config._links_validator[v] for v in ll] #assert all valid
        if ignores:
            ll = [a for a in ll if not a or a[0] not in ignores]
        if config.sisters:  #B0,B1- means just B0/B1; B means B+B1 eventualy
            ll += [ k+'1' for k in ll if k
                                        and '1' not in k
                                        and '0' not in k
                                        and k+'1' not in ll
                    ]
        if config.polymorphic:
            ll += [ k+'PM' for k in ll if k
                                        and 'PM' not in k
                                        and k+'PM' not in ll
                    ]
        ll = [ k and k.replace( '0','') or k for k in ll    #B0->B
                                                if k in config._links_validator     #filter valids
                    ]
        return ll

    def get_polys( config):
        return config.poly_all and [0,1] or [1]
    def get_inhs( config):
        return [ config._inhs_validator[k] for k in config.inhs]
    def getXinhs( config, X):
        name = X+'inhs'
        return [ k for k in getattr( config, name)
                    if k in getattr( config.__class__, name) ]


# vim:ts=4:sw=4:expandtab
