#$Id$
# -*- coding: cp1251 -*-

from dbcook.util.attr import issubclass
import sys

'''wave-like non recursive dependency extract/resolve; same job as topology sort
вълново нерекурсивно извличане/разрешаване на зависимости - върши работата на топологична сортировка
'''
_debug = 0

def walker( namespace, reflector, baseklas):
    'aliases are ignored; same-name items are overwritten'
    klasi = {}
    for k,klas in namespace.iteritems():
        if not issubclass( klas, baseklas): continue

        name = klas.__name__
        key = (name, klas.__module__)
        if klas is klasi.get( key, (None,))[0]:
            if _debug: print 'walk:   ignoring dup', k,'=',name
            continue
        if _debug: print 'walk:  got', name, klas.__module__
        klasi[ key ] = klas, 'namespace'
    if _debug: print 'walk 0', '\n'.join( str(kv) for kv in klasi.iteritems() )

    pas = 0
    new = 1
    while new:
        pas +=1
        if _debug: print 'walk: ------ pass', pas
        new = 0
        for (kname,kmod),(klas,isnamespace) in klasi.items(): #copy
            if isinstance( klas, str): continue
            new += walk1( klas,isnamespace, kname,kmod, klasi, reflector, namespace)
        if _debug: print 'eopass', '\n       '.join( str(kv) for kv in klasi.iteritems() )

    for (kname,kmod),(klas,isnamespace) in klasi.items(): #copy
        add_bases( klas, klasi, baseklas)

    r = dict( (kname,klas) for (kname,kmod),(klas,isnamespace) in klasi.iteritems() )
    if _debug: print r
    if _debug: print 'walk: end'
    return r


def add_bases( klas, klasi, baseklas):
    b = klas.__bases__
    while b and issubclass( b[0], baseklas):
        b = b[0]
        key = (b.__name__, b.__module__)
        if key not in klasi:
            klasi[ key ] = b,None
            if _debug: print 'walk: add base', b
        b = b.__bases__

def ownerbase( klas, attr, reflector):
    'откъде идва даден атрибут'
    value = getattr( klas, attr)
    base = klas
    while base:
        b = base.__bases__[0]    #!!!
        #if not reflector.attrtypes_hasattr( b, attr) or getattr( b, attr) is not value:
        if getattr( b, attr, None) is not value:
            break
        base = b
    return base

_level = 0
def walk1( klas, isnamespace, kname, kmod, klasi, reflector, namespace ):
    new = 0
    global _level
    ind = '    '*_level
    if _debug: print ind, 'klas:', `klas`
    _level+=1
    ind += '    '
    for attr,typ in reflector.attrtypes_iteritems( klas):
        is_substruct = reflector.type_is_substruct( typ)
        if not is_substruct:
            if _debug: print ind, attr, 'ignoring non-ref:', typ
            continue
        if _debug: print ind, attr, is_substruct
        oklas = is_substruct[ 'klas']

        if isinstance( oklas, str):
            name = oklas
            mod = klas.__module__
            key = name,mod
            kk = klasi.get( key )
            if kk:
                if _debug: print ind, '  resolvable:', oklas, 'from', mod, '->', `kk`
                isnamespace = kk[1]
                if isnamespace:
                    if _debug: print ind, '  ->resolve', oklas, 'from namespace'
                    dict = namespace
                else:
                    #трябва да гледа в дълбочина на наследяванията, т.е. ако ref('B') е дошло от базовия клас, да се гледа там...
                    base = ownerbase( klas, attr, reflector)
                    mod = sys.modules[ base.__module__]
                    if _debug: print ind, '  ->resolve', oklas, 'from', mod
                    dict = mod.__dict__
                r = reflector._resolve_forward_reference1( typ, dict)
                klasi[ key ] = r,isnamespace
                new += 1
                continue
        else:
            name = oklas.__name__
            mod = oklas.__module__
            if (name,mod) in klasi:
                if _debug: print ind, '  ignoring already present', oklas
                continue
            else:
                if _debug: print ind, '  namespace changed', oklas

        if ownerbase( klas, attr, reflector) != klas:
            if _debug: print ind, '  ignore non-own extern-ref', `oklas`, '/', (name,mod)
            continue

        klasi[ (name,mod) ] = oklas,None
        if _debug: print ind, '  extern-ref', `oklas`, '/', (name,mod)
        new += 1

    _level-=1
    return new

# vim:ts=4:sw=4:expandtab
