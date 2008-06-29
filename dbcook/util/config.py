#$Id$

import sys

class Config:
    def __init__( me, *chain):
        me._chain = list(chain)
    def __getattr__( me, a):
        for c in me._chain:
            try: return getattr( c, a)
            except AttributeError: pass
        raise AttributeError

    def __str__( me):
        all = set( dir(me) )
        for c in me._chain:
            all = all | set( dir( c))
        all = sorted( all)
        return ', '.join( '%s=%s' % (k,getattr(me,k))
                    for k in all
                    if not k.startswith('_') and not callable( getattr(me,k))
                )

    def allhelp( me):
        'ignoring duplicate entries; first is used'
        h = ''
        chain = [ me ] + me._chain
        for c in chain:
            try: h += c._help
            except AttributeError: pass

        ikeys = []
        out = []
        ikey = item = ''

        def add( ikey,item):
            ik = ikey.strip()
            if ik and ik not in ikeys and ik+'=' not in ikeys:
                ikeys.append( ik)
                out.append( '::'.join( (ikey,item) ))

        for l in h.split('\n'):
            ischapter = not l.startswith(' ')
            if '::' in l or ischapter:
                add( ikey,item)
                if ischapter:
                    out.append( l)
                    ikey,item = '',''
                else:
                    ikey,item = l.split('::')
            else:
                item += '\n'+l
        add( ikey,item)
        return '\n'.join(out)

    def getopt( me, help =None):
#        if help is None and not use_own: help = me.allhelp() #_help
        for h in ['help', '-h', '--help']:
            if h in sys.argv:
                print help or me.allhelp()
                print 'default config:', me
                raise SystemExit, 1

        me._getopt( help)

        try: sys.argv.remove( 'cfg_warning')
        except ValueError: pass
        else:
            for a in sys.argv:  #what's left
                print '!cfg: ignoring arg', a

    def _getopt( me, help =None, use_own =None):
        if use_own is None: use_own = me._chain
        myhelp = help
        if use_own: myhelp = me._help
        possible_args = [ak.strip().split()[-1] for ak in myhelp.split('::')[:-1]]
        for a in sys.argv[1:]:
            aa = a.split('=')
            if len(aa)<2:
                if a in possible_args:
                    sys.argv.remove( a)
                    if a.startswith('no_'):
                        a = a[3:]
                        v = False
                    else: v = True
                    setattr( me, a, v)
            else:
                k = aa[0]
                if k+'=' in possible_args:
                    sys.argv.remove( a)
                    val = '='.join( aa[1:])   #XXX working in case >= 2 = like "db=sapdb:///sap?kliuche=abdahalia"
                    uselist = isinstance( getattr( me.__class__, k, ''), (list,tuple) )
                    if uselist:
                        val = val.split(',')
                    setattr( me, k, val)

        for c in me._chain:
            c._getopt( help, use_own)    #having _chain and not use_own ... useless - argv is empty

Config.Config = Config  #easy available as cfg.Config, instead of cfg.__base__[0].__class__...

# vim:ts=4:sw=4:expandtab
