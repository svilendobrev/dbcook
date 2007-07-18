#$Id$

from combinator import ConfigCombinator
class Config4ABCcombination( ConfigCombinator):
#    sisters = False
#    eager   = False
    polymorphic = False

    doC = False
    Binhs = [ '', 'A']
    Cinhs = Binhs + [ 'B']
    links = ['','A','B','C']
    Alinks = Blinks = Clinks = [] #=use links
    insts = ['A','B']

    def getXlinks( config, X):
        return ConfigCombinator.getXlinks( config,X, bool(not config.doC) *['C'] )

    _help = ConfigCombinator._help + '''\
  Binhs=      :: B inherits which types, e.g. =None   (default:all=None,A)
  doC         :: enable C (3rd type) (default:no)
  Cinhs=      :: C inherits which types, e.g. =A,None (default:all=None,A,B)
  Clinks=     :: C links to which types, e.g. =None,B (default:=links)
  insts=      :: which types to have instances when not-leaf, e.g. =B (default:=A,B)
''' + ConfigCombinator._help_no_eager


def allABC( config ):
    doC = config.doC
    nolink = config.__class__.links[0]
    Alinks = config.getXlinks('A')
    Blinks = config.getXlinks('B')
    Clinks = doC and config.getXlinks('C') or ['']
    Binhs = config.getXinhs('B')
    Cinhs = config.getXinhs('C')
    allinsts = config.insts

    '''
inh:
b-a b-0  x  c-a c-b c-0

o a0 b0
i a0 ba
o a0 b0 c0
i a0 ba c0--same
i a0 b0 ca--same
i a0 ba ca
i a0 b0 cb--same
i a0 ba cb
'''
                                 #B #C
    sameinh1 = dict.fromkeys( [ ('','A'), ('','B')], ('A',''))
                                 #B  #C
    sameinh2 = dict.fromkeys( [ (('',''),'concrete'), (('',''),'joined')], (('',''),None))
    usedinh = {}

    bases = dict.fromkeys( ['A', '', None], [''])
    for inh,poly in config.inhpolycomb():  ##no inh->no poly
        inhsB = inh and Binhs or ['']
        inhsC = doC and inh and Cinhs or ['']
#        print allinsts, inhsB+inhsC, inhsC
        for Ainst in     ['A','',][:1+bool( 'A' in allinsts and 'A' in (inhsB + inhsC))]:
            for Binst in ['B','',][:1+bool( 'B' in allinsts and 'B' in inhsC)]:
                usedinh.clear()
                insts = Ainst + Binst + bool(doC)*'C'
#               print 'INST', Ainst,Binst, insts
                for inhB in inhsB:
                    Bbases = bases['B'] = [inhB] + bases[ inhB ]
                    for inhC in inhsC:
                        if inh and not inhB and not inhC:
                            #this happens if inhs=[] is passed as param and None is not there
                            continue
                        bcinh = inhB,inhC
        #                print bcinh
                        bcinh = sameinh1.get( bcinh,bcinh)
                        bcinh2 = bcinh,inh
                        bcinh2 = sameinh2.get( bcinh2,bcinh2)
                        if bcinh2 in usedinh:
        #                    print 'used', bcinh2
                            continue
                        usedinh[ bcinh2] = 1
                        Cbases = bases['C'] = [inhC] + bases[ inhC ]
                        for Alink,Alazy in config.linklazycomb( 'A', Alinks, bases):
                            if Alink and Alink[0] not in insts: continue #XXX PM!
                            for Blink,Blazy in config.linklazycomb( 'B', Blinks, bases):
                                if Blink and Blink[0] not in insts: continue #XXX PM!
                                for BAlink in [nolink] + bool(Alink and inh and 'A' in Bbases)*[ Alink]:

                                    for Clink,Clazy in config.linklazycomb( 'C', Clinks, bases):
                                        if Clink and Clink[0] not in insts: continue    #XXX PM!
                                        for CAlink in [nolink] + bool(Alink and ('A' in Cbases))*[Alink]:
                                            for CBlink in [nolink] + bool(Blink and ('B' in Cbases))*[Blink]:
                                #Clink= Clazy= CAlink= CBlink=''
                                #if 1:
                                                yield dict(
                                                poly=poly, inh=inh,
                                                Alink=Alink, Alazy=Alazy,
                                                Blink=Blink, Blazy=Blazy,
                                                    BAlink=BAlink,
                                                inhB=inhB,
                                                Clink=Clink, Clazy=Clazy,
                                                    CAlink=CAlink,
                                                    CBlink=CBlink,
                                                inhC=inhC,
                                                insts=insts,
                                            )


class Config( Config4ABCcombination):
    session_clear = True
    query = True

    verbose = False
    one_line = False
    generate = []
    dummy = False
    dump  = False

    prnname = '_test_ABC_%s.py'
    funcname = 'test_ABC_'

    _help = Config4ABCcombination._help + '''\
workflow options:
  no_session_clear  :: dont do a session.clear() before querying
  no_query    :: dont do querying
  dummy       :: only show combinations, run nothing

output options:
  generate=   :: create unittest source ('''+prnname%('XXX',)+'''):
                  one:  all-in-one-file, each combination = separate function
                  many: each combination = separate file
                  failed: only the failed tests
                 default=none /=one,all
  one_line    :: show errors as one line
  verbose     :: see what's being tested
  dump        :: dump raw table-contents before querying
'''


def populate(
        doC =False,
        A =None, B =None, C =None,
        inhB ='', inhC ='',
        Alink ='', Blink ='',Clink ='',
        BAlink ='', CAlink ='', CBlink ='',
        **kargs_ignore
    ):
    Alink0 = Alink
    if Alink: Alink = Alink[0]
    Blink0 = Blink
    if Blink: Blink = Blink[0]
    Clink0 = Clink
    if Clink: Clink = Clink[0]

    a = A()
    b = B()
    a.name = 'anna'
    if inhB:
        b.name = 'ben'
    b.dataB = 'gun'
    inhCA = inhC=='A' or inhC=='B' and inhB=='A'

    c = None
    if doC:
        c = C()
        if inhCA:
            c.name = 'cc'
        c.dataC = 'mc'

    a1 = b1 = c1 = None
    ABC0 = [Alink0,Blink0,Clink0]
    if 'A1' in ABC0:
        a1 = A()
        a1.name = 'a1'
    if 'B1' in ABC0:
        b1 = B()
        if inhB:
            b1.name = 'bb1'
        b1.dataB = 'b1'
    if doC:
        if 'C1' in ABC0:
            c1 = C()
            if inhCA:
                c1.name  = 'cc1'
            c1.dataC = 'mc1'

    links = dict( A=a, B=b, A1=a1, B1=b1, C=c, C1=c1)
    links['']=None

    if Alink:
        a.linkA = links[ Alink0]
        if inhB and BAlink:
            b.linkA = links[ BAlink]
    if Blink:
        b.linkB = links[ Blink0]

    if doC:
        if Clink:
            c.linkC = links[ Clink0]
        if inhCA and CAlink and Alink:
            c.linkA = links[ CAlink]
        if inhC=='B' and CBlink and Blink:
            c.linkB = links[ CBlink]

    return locals()

# vim:ts=4:sw=4:expandtab
