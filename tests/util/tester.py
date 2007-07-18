#$Id$
# -*- coding: cp1251 -*-

from util.base import issubclass

def klasify( sadb, namespace, converter =lambda x:x, only_has_instances =True):
    '''for building test's expected results -
    classify mapped items in namespace according to item's class position in
    class-hierarchy; i.e. which class and for which type-subset queries:
        (exact class, all+subclasses, subclasses only)
    returns dict( klas: querytype.set( instances) ).
    usage: setup a namespace of values, klasify() it and store result, then do saveall(),
        the results from the queries for a klas should match the expected ones
        for that klas as of klasify().
    '''
    mapcontext = sadb.mapcontext
    klasi = sadb.iterklasi()
    SET = mapcontext.SET
    class KI:
        def __init__( me):
            me.query_ALL_instances = SET()
            me.query_BASE_instances= SET()
            me.query_SUB_instances = SET()
    has_instances = mapcontext.has_instances
    klasitems = mapcontext.DICT()
    for klas in klasi:
        klasitems[ klas] = ki = KI()
        for v in namespace.itervalues():
            if isinstance( v,klas):
                if not only_has_instances or has_instances( v.__class__):
                    vv = converter(v)
                    ki.query_ALL_instances.add( vv)
                    if v.__class__ is klas: ki.query_BASE_instances.add(vv)
                    else: ki.query_SUB_instances.add(vv)
    return klasitems

def types_sorted( sadb):
    'make a sorted list of all mapped classes - for repeatable tests etc'
    klasi = list( sadb.iterklasi())
    klasi.sort( key=lambda k: k.__name__)
    return klasi



def get_populate_namespace( namespace, base_klas, popreflector, generator):
    populate = namespace.get( 'populate', None)
    if not populate: return {}
    if generator:
        #make a separate population for the generator only
        # hide the __init__ ctor's (SA-made) to avoid mapper-construction-errors
        inits = {}
        for k in namespace.itervalues():
            if issubclass( k, base_klas):
                try:
                    r = k.__dict__[ '__init__' ]
                except KeyError: pass
                else:
                    inits[k] = r
                    k.__init__ = base_klas.__init__

        from dbcook import builder
        generator.populate( populate(), reflector= popreflector, idname= builder.column4ID.name)

        #restore
        for k,v in inits.iteritems():
            k.__init__ = v
    return populate()

def do_query( query, sadb, session, klas, klasitems, quiet):
    res = []
    hdr = False
    SET = sadb.mapcontext.SET
    for qy in (callable(query) and [query] or query):       #if not callable/single then iterable
        qname = qy.__name__
        if hdr:
            if not quiet: print ' --', klas.__name__,
            hdr = 0
        if not quiet: print qname,

        assert callable( qy)
        er = None

        try:
            r = SET( q for q in qy( sadb, session=session, klas=klas) )       #load all
        except KeyboardInterrupt: raise
        except Exception,e:
            print '\n   ', klas.__name__, qname,' fail:'
            import traceback
            traceback.print_exc()
            #print e
            er = e
        else:
            rq = getattr( klasitems[ klas], qname, None)
            if rq is None:
                print '\n   ', klas.__name__, qname,' result:', '\n'.join( str(q) for q in r)
                hdr = True
            else:
                srq = [ str(q) for q in rq]
                sr  = [ str(q) for q in r ]
                srq.sort()
                sr.sort()
                ok = srq == sr
                if not ok:
                    print '\n   ', klas.__name__, qname,' fail:'
                    print ' result:', '; '.join( sr)
                    print ' expect:', '; '.join( srq), '/size:', len(rq)
                    er = 'AssertionError:\n result=%(sr)s\n expect=%(srq)s' % locals()
        if er:
            hdr = True
            res.append( klas.__name__+'.'+qname+': '+str(er) )

    return res

def query_all_klasi( query, sadb, session, klasitems, quiet):
    res = []
    klasi = types_sorted( sadb)
    for klas in klasi:
        if not quiet: print '==', klas.__name__,
        errors = do_query( query, sadb, session, klas, klasitems, quiet)
        res.extend( errors)
        if not quiet: print
    return res

def popreflector_factory( reflector):
    def popreflector(o):
        #avoid see-through class-level-declarations: if klas.x is obj.x -> x is class-level decl
        for k,v in reflector.iter_attrtype_all( o.__class__):
            try:
                if v is getattr( o, k): continue
            except AttributeError: pass
            yield k
    return popreflector

_db = None

def test( namespace, SAdb,
            fieldtypemap=None,
            base_klas   =None,
            quiet       =False,
            reuse_db    =False,
            dump        =False,
            generator   =None, #4builder
            debug       =None, #4builder
            **kargs4SAdb
        ):
    all_errors = []
    sa = SAdb( **kargs4SAdb )
    popreflector = popreflector_factory( SAdb.Builder.reflector)

    global _db
    try:
        if reuse_db and _db:
            sa.db = _db
        else:
            sa.open( recreate=True)

        b = sa.bind( namespace, fieldtypemap,
                    base_klas= base_klas,
                    print_srcgenerator =False,
                    generator= generator,
                    debug= debug )
        base_klas = b.Base

        query = namespace.get( 'query', None)
        populate_namespace = get_populate_namespace( namespace, base_klas, popreflector, generator )

        session = sa.session()
        sa.saveall( session, populate_namespace)
        session.flush()

        #this before session.close
        klasitems = query and klasify( sa, populate_namespace, converter=str )   #expected results

        session.close()
        if dump: sa.query_all_tables()

        session = sa.session()
        if query:
            errors = query_all_klasi( query, sa, session, klasitems, quiet)
            all_errors.extend( errors)
        session.close()

    finally:
        if reuse_db: _db = getattr( sa, 'db', None)
        sa.destroy( full= not reuse_db)

    return all_errors

# vim:ts=4:sw=4:expandtab
