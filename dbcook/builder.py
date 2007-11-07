#$Id$
# -*- coding: cp1251 -*-

'''
текущо състояние и разни забележки:
    * StaticType и пр:
        - None <-> _NONE/notSetYet
            - get/set може да се оправи, виж  _typeprocess
            - обаче маперите ползват 'is None' !!! напр. db_id не работеше заради това
        - enum_value = r.StaticType['enum'].dict[ r.enum ]
            !! БОЗАА a мойе ли да се забършат InstrumentedAttributes отгоре

    * структура:
        - вградени-структури - НЕ МОГАТ да се направят!
    * fieldtypemap
        - ?? дати/времена
    * mappers:
        - наследявания: ОК
            + joined_table & concrete_table; all-same, all-same-at-node; mixed
            + query_BASE_instances, query_ALL_instances, query_SUB_instances
            - single_table
        + references - ?? =relation /uselist=False
            + обикновени A.b->B
            + циклични: A.b->B.a->A  A.b->B.c->C.a->А; cut-cyclic-deps, use_alter, post_update, foreign keys
            + само-сочещи се: A.a->A: същото като горното
                auto_set = FALSE!!
        ~ колекции - няма-още  =relation /uselist=True (1-to-many, many-to-many)

    * персистентен обект:
        + 1. сплав от StaticType-obj и SA-obj в едно, със съответните огъвки и персистентни гадости.
            + работи, малко бавно
        - 2. може да се направи StaticType-obj != SA-obj:
            ++решават се всички грижи по съвместимостта - вградени структури, None<>notSetYet, персистентна семантика
            --допълнителен .save/.load/(semi-deep-copy)+dirty слой за прехвърляне от/към; синхронизация??
'''

#print 'builder...', __name__

from reflector import Reflector
from mapcontext import table_inheritance_types, MappingContext, issubclass
import walkklas
import relation
import sqlalchemy
import sqlalchemy.orm
import warnings


from config import config_components, config,  column4type, column4ID, table_namer, _v03

if not config_components.polymunion_from_SA:
    from polymunion import polymorphic_union
else:
    polymorphic_union = sqlalchemy.polymorphic_union
    #this cannot handle mixed inheritances


if config_components.no_generator:
    sa = sqlalchemy
    sa.mapper = sa.orm.mapper
    sa.relation = sa.orm.relation
    SrcGenerator = None
else:
    import sa_generator
    sa = sa_generator
    polymorphic_union = sa.duper4polymorphic_union( polymorphic_union,
                            no_kargs= dict(
                                allow_empty_typecolname= False,     #same as below
                                dont_alias_selects= True,
                            ))
    sa.Column = sa.duper2( sqlalchemy.Column)
    sa.ForeignKey= sa.duper2( sqlalchemy.ForeignKey)
    SrcGenerator = sa.Printer

if not config_components.polymunion_from_SA:
    def _polymorphic_union( table_map, typecolname, aliasname, *args_ignore):
        if config.lower_pu: aliasname = aliasname.lower()
        return polymorphic_union( table_map, typecolname, aliasname,
                allow_empty_typecolname =False,
                dont_alias_selects  =True,
            )
else:
    def _polymorphic_union( table_map, typecolname, aliasname, inheritype):
        if config.lower_pu: aliasname = aliasname.lower()
        if inheritype == table_inheritance_types.JOINED:
            typecolname = None
        return polymorphic_union( table_map, typecolname, aliasname )


###########################################



def make_klas_selectable( mapcontext, klas, tables, test =False):
    '''construct the selectable for extracting objects of
    exactly this klas (and not subklasses);
    for all cases of inheritance-represention (concrete,multitable,single)
    '''
    joined_tables = []
    base_klas = klas
    while True:     #go toward base, stop on first concrete-table
        tbase = tables[ base_klas]
        joined_tables.insert( 0, tbase)
        base_klas, inheritype = mapcontext.base4table_inheritance( base_klas)
        if inheritype == table_inheritance_types.CONCRETE:
            break

    j = joined_tables[0]
    if test:
        jtest = joined_tables[0].name

    if len(joined_tables)>1:
        for t in joined_tables[1:]:
            # explicit, allow other relations via id
            other_table = isinstance( j, sqlalchemy.Table) and j or j.right
            j = sa.join( j, t,
                    column4ID( t) == column4ID( other_table) )
            if test:
                jtest += '.join( '+t.name
                #jtest += ' /on '+ other_table.name +'.id'
                jtest += ' )'

    jfiltered = exprfilter = None
    is_non_concrete_inherited = mapcontext.is_direct_inherited_non_concrete( klas)
    if is_non_concrete_inherited:   # -> нуждае се от филтър по тип; correlate=False и в двата случая
        #X.select(X.atype==X)
        exprfilter = column4type( tbase) == klas.__name__
        if isinstance( j, sqlalchemy.sql.Join): #if len(joined_tables)>1
            jfiltered = j.select( exprfilter, fold_equivalents=True)
        else:
            jfiltered = j.select( exprfilter)

        jfiltered = jfiltered.alias( 'bz4' + table_namer( klas) )
        if test:
            jtest += '.select( '+tbase.name+ '.typ=='+klas.__name__ + ' )'
    else:
        jfiltered = j

    if test: j = jtest
    return dict( filtered= jfiltered, plain= j,
                    filter= exprfilter,   #fold_equivalents=True) XXX???
                    base_table= tbase,
                )

_subklas_selectable_doc = '''
    наследявания: B наследява А:
    във всички случаи има една (междинна) таблица, с колони =обединението
    на колоните на всички таблици + колона тип/дискриминатор,
    и по един ред за всеки обект, с всички не-негови колони =NULL
    в случая single_table ТОВА е таблицата; иначе се прави (виртуална) таблица чрез union.

    /:  concrete_table - B съдържа всички колони на A (А и B са съвсем независими);
            id-тата на А и B са съвсем независими;
            дискриминаторът/atype се разписва като константа за таблицата от union-а ;

    //: joined_table - B има само допълнителните си колони; +join към А
            A трябва да има поле atype, по което се познава типа (дискриминатор);
            А съдържа всички id-та на А и B; дискриминаторът/atype е А.atype

    *:  single_table - B не съществува като таблица - всичките и колони са в А;
            (ако А също не съществува като таблица, тогава това е първата база която съществува)
            A трябва да има поле atype, по което се познава типа (дискриминатор);
            А съдържа всички id-та на А и B; дискриминаторът/atype е А.atype;
            освен добавянето на колони в А, B не се вижда по никакъв друг начин - наследяването и
            е същото като пряко наследяване на А

    повечето проверки са всъщност дали се разглобява на парчета
    (not concrete_table) или не (concrete_table)



вариант 0. еднакво наследяване, на всички нива (няма смесване) - ОК
variant 0. same inheritance, on all levels (no mixing)
           A                      A                                          A
          / \                   // \\                                       * *
         B   D                 B     D                                     B   D
        /                     //                                          *
       C                     C                                           C
                            А.atype= (A,B,C,D)                          А.atype= (A,B,C,D)

    A.only = А              A.only = А.select( A.atype==A)              A.only = А.select( A.atype==A)
    B.only = B              B.only = A.join(B).select( A.atype==B)      B.only = A.select( A.atype==B)
    C.only = C              C.only = A.join(B).join(C)                  C.only = A.select( A.atype==C)
    D.only = A              D.only = A.join(D)                          D.only = A.select( A.atype==D)

вариант 1. смесено наследяване, нееднакво във възела и между нивата
variant 1. mixed inheritance, different within a node and between the levels
          A                                       A
         / \\                                    / \\
        B   D                                   B   D
       / \\                                    / *   *
      C   E                                   C   E   F
                                                 //  //\
                                                 P   Q  R
                                                *
                                               S
    А.atype = (А,D)                     А.atype = (А,D,F,Q)
    B.atype = (B,E)                     B.atype = (B,E,P,S)

    A.only = А.select( A.atype==A)      A.only = А.select( A.atype==A)
    B.only = B.select( B.atype==B)      B.only = B.select( B.atype==B)
    C.only = C                          C.only = C
    D.only = A.join(D)                  D.only = A.join(D).select( A.atype==D)
    E.only = B.join(E)                  E.only = B.select( B.atype==E)
                                        F.only = A.join(D).select( A.atype==F)
                                        R.only = R
                                        Q.only = A.join(D).select( A.atype==Q).join(Q)
                                        P.only = B.select( B.atype==P).join(P)
                                        S.only = B.select( B.atype==S).join(P)

вариант 2. смесено наследяване, но еднакво в един възел (различно в различните възли)
variant 2. mixed inheritance, but same within a node (and different between nodes)
           A                                  A                                   A
          / \                               // \\                               // \\
         B   D                             B     D                             B     D
       //\\                               / \                                // \\
      C   E                              C   E                              C    E
     / \                               //\\                                / \
    P   Q                              P  Q                               P   Q
  B.atype = (B,C)                   A.atype= (A,B,D); C.atype= (C,P,Q)   A.atype= (A,B,C,D,E)

  A.only= А                         A.only= А.select( A.atype==A)        A.only= А.select( A.atype==A)
  B.only= B.select( B.atype==B)     B.only= A.join(B)                    B.only= A.join(B).select( A.atype=B)
  C.only= B.join(C)                 C.only= C.select( C.atype==C)        C.only= A.join(B).join(C)
  D.only= D                         D.only= A.join(D)                    D.only= A.join(D)
  E.only= B.join(E)                 E.only= E                            E.only= A.join(B).join(E)
  P.only= P                         P.only= C.join(P)                    P.only= P
  Q.only= Q                         Q.only= C.join(Q)                    Q.only= Q


в някои частни случаи при joined_table може да се избегне union-a:
in some special cases with joined_table, the union can be avoided:
 class A: pass
 class B(A): pass
 class C(B): pass
 A_join = A_table.outerjoin( B_table).outerjoin( C_table)
 B_join = A_table.join( B_table).outerjoin( C_table)
 A_mapper = mapper( A, A_table, select_table= A_join,
    polymorphic_on= A_table.c.type, polymorphic_identity= 'p')
 B_page_mapper = mapper( B, magazine_page_table,
    select_table= B_join, inherits= A_mapper, polymorphic_identity= 'm')
 C_mapper = mapper( C, C_table,
    inherits= B_mapper, polymorphic_identity= 'c')
това засега не се ползва тъй-като не е ясно как се комбинира при разклонени дървета.
this is not used for now, as it is not clear how it combines in branched trees.
'''




###############################

def make_table_column4id_fk( column_name, other_klas,
                            type =None, fk_kargs ={}, **column_kargs):
    dbg = 'column' in config.debug
    if dbg: print 'make_table_column4id_fk', column_name, other_klas.__name__
    assert type
    assert other_klas
    fk = sa.ForeignKey(
                table_namer( other_klas)+'.'+column4ID.name,
                **fk_kargs
            )
    if dbg: print '  foreignkey', column_name, column_kargs, fk, fk_kargs
    c = sa.Column( column_name,
                type,
                fk,     #must be in *args
                #, nullable= True
                **column_kargs  #typemap_kargs
            )
    if dbg: print '    = ', repr(c)
    return c

def make_table_column4struct_reference( klas, attrname, attrklas, mapcontext, **column_kargs):
#    print '  as_reference', attrname,attrklas
    c = make_table_column4id_fk(
            column4ID.ref_make_name( attrname),
            other_klas = attrklas,
            type = column4ID.typemap['type'],
            **column_kargs
        )
    return c




def make_table_columns( klas, mapcontext, fieldtype_mapper, name_prefix ='', ):
    dbg = 'column' in config.debug
    if dbg: print 'make_table_columns', klas, name_prefix
    columns = []

    reflector = mapcontext.reflector
    base_klas, inheritype = mapcontext.base4table_inheritance( klas)
    is_joined_table = (inheritype == table_inheritance_types.JOINED)
    assert base_klas or not is_joined_table
    for attr,typ in reflector.iter_attrtype_all( klas):
        if is_joined_table:
            #joined_table: subclass' tables consist of extra attributes -> joins
            if reflector.owns_attr( base_klas, attr):
                if dbg: print '  inherited:', attr
                continue

        #else: 'concrete_table' - each class OWN table
        k = name_prefix + attr
        is_substruct = reflector.type_is_substruct( typ)
        if is_substruct:
            attrklas = is_substruct[ 'klas']
            if not is_substruct[ 'as_value']:
                if dbg: print '  as_reference', k,typ
#                print klas.__name__, k, typ
                assoc_kargs, assoc_columner= relation.is_association_reference( klas, typ, attrklas)
                c = make_table_column4struct_reference( klas, k, attrklas, mapcontext, **assoc_kargs)
                if assoc_columner: assoc_columner(c)
                columns.append( c)
            else:   #inline_inside_table/embedded
                #... разписване на колоните на подструктурата като колони тука
                if dbg: print '  as_value', k,typ
                raise NotImplementedError

        else:   #plain non-struct attribute, no foreign-keys
            if dbg: print '  plain non-struct attribute', k, typ
            mt = fieldtype_mapper( typ )
            if dbg: print '    ->', mt
            mt = mt.copy()      #just for the sake of it
            constraints = mt.pop( 'constraints', ())
            type = mt.pop( 'type' )
            c = sa.Column( k, type, *constraints, **mt )
            if dbg: print '    = ', repr(c)
            columns.append( c)

    ## column4type
    if mapcontext.need_typcolumn( klas):
        c = sa.Column( column4type.name, **column4type.typemap_() )
        if dbg: print '  need_typcolumn', c
        columns.append( c)


    ## separate column4ID primary_key?
    #only 1 primary_key allowed, so options are:
    # - no primary_keys whatsoever
    # - predefined primary_key columns, and no need for explicit db_id
    # - db_id as primary_key if joined_table or being referenced;
    #   all else wanna-be-primary-keys become just unique constraints

    primary_key = [ c for c in columns if c.primary_key]
    needs_id_primary_key = is_joined_table or mapcontext.needs_id( klas) # needs such, because of being referenced / inherits via joined_table
    if not primary_key or needs_id_primary_key:
        if dbg: print '  invent primary_key', column4ID.name
        if is_joined_table:
            c = make_table_column4id_fk( column4ID.name, base_klas, **column4ID.typemap)
        else:
            c = sa.Column( column4ID.name, **column4ID.typemap_() )
        columns.append( c)
        if primary_key:     #convert it to just uniq constraint
            for c in primary_key: c.primary_key = False
            columns.append( sa.UniqueConstraint( *primary_key) )

    for u in mapcontext.uniques( klas):
        key = [ getattr( c, 'name', c) for c in u ]
        columns.append( sa.UniqueConstraint( *key) )

    ## check for duplicate column-names/constraint-names
    chk = set()
    for c in columns:
        key = c.name    #type
        assert key not in chk, 'multiple columns named '+repr( key)
        chk.add( key)

    return columns

def make_table( klas, metadata, mapcontext, **kargs):
    dbg = 'table' in config.debug
    if dbg: print '\n'+'make_table for:', klas.__name__, kargs
    columns = make_table_columns( klas, mapcontext, **kargs)
    name = table_namer( klas)
    t = sa.Table( name, metadata, *columns )
    if dbg: print repr(t)
    return t

def fix_one2many_relations( klas, builder, mapcontext):
    dbg = 'table' in config.debug or 'relation' in config.debug
    if dbg: print 'make_one2many_table_columns', klas

    for k,collect_klas in mapcontext.iter_attr_local( klas, attr_base_klas= relation.Collection, dbg=dbg ):
        child_klas = collect_klas.assoc_klas
        if isinstance( child_klas, str):
            try: child_klas = builder.klasi[ child_klas]
            except KeyError: assert 0, '''undefined relation/association class %(child_klas)r in %(klas)s.%(name)s''' % locals()
        #one2many rels can be >1 between 2 tables
        #and many classes can relate to one child klas with relation with same name

        backref = collect_klas.backref
        if backref:
            #if isinstance( backref, dict):
            backrefname = backref[ 'name']
            #else: backrefname = backref
        else:
            backrefname = column4ID.backref_make_name( klas, k)
        collect_klas.backrefname = backrefname
        fk_column_name = backrefname
        fk_column = make_table_column4struct_reference( klas, fk_column_name, klas, mapcontext)
        if dbg: print '  attr:', k, 'child_klas:', repr(child_klas), 'fk_column:', repr(fk_column)
        child_tbl = builder.tables[ child_klas]
        child_tbl.append_column( fk_column)

        class assoc_details:
            primary_key= True
            nullable= True
            relation_attr= k
        relation._associate( child_klas, klas, assoc_details, fk_column)


def make_mapper( klas, table, **kargs):
    dbg = 'mapper' in config.debug
    if dbg:
        print '\n'+'make_mapper for:', klas.__name__
        print '  table=', table, '\n  '.join( '%s=%s' % kv for kv in kargs.iteritems())

    m = sa.mapper( klas, table, **kargs)
    return m

class FKeyExtractor( dict):
    def __init__( me, klas, table, mapcontext, tables):
        dict.__init__( me)
        me.table = table
        me._add_fkeys( table)
        subklasi = mapcontext.subklasi[ klas]
        if '''this is to propagate post_update of a link to concrete-inherited bases AND subklasi,
            because of the required relink'ing of concrete-inherited references in SA 0.3.4
            ''':
            #bases
            kl = klas
            while kl:
                base_klas, inheritype = mapcontext.base4table_inheritance( kl)
                if base_klas and inheritype == table_inheritance_types.CONCRETE:
                    kl = base_klas
                    me._add_fkeys( tables[ kl])
                else: break
            #subklasi
            for kl in subklasi:
                if kl is klas: continue
                base_klas, inheritype = mapcontext.base4table_inheritance( kl)
                assert base_klas
                if inheritype == table_inheritance_types.CONCRETE:
                    me._add_fkeys( tables[ kl])

    def _add_fkeys( me, table ):
        for fk in table.foreign_keys:
            c = fk.parent   #this-table column
            attr = column4ID.ref_strip_name( c.name)
            me.setdefault( attr, []).append( fk)

    def get_relation_kargs( me, k):
        fks = me.get( k, None)
        if not fks: return {}
        post_update = 0
        fk = None
        for f in fks:
            if f.parent.table is me.table:
                fk = f
            post_update += f.use_alter
        assert fk
            #|= the respective fk on any of concrete inherited/inheriting relation because of relinking
        rel_kargs = dict(
                post_update = bool(post_update),
                primaryjoin = (fk.parent == fk.column),
                foreign_keys = fk.parent,
                remote_side = fk.column,
            )
        return rel_kargs

def make_mapper_props( klas, mapcontext, mapper, tables ):
    'as second round - refs can be cyclic'
    dbg = 'mapper' in config.debug or 'prop' in config.debug
    reflector = mapcontext.reflector

    need_mplain = bool( not config_components.non_primary_mappers_dont_need_props
                    and mapper.plain is not mapper.polymorphic_all)
    for m in [mapper.polymorphic_all] + need_mplain*[ mapper.plain]:
        if dbg: print 'make_mapper_props for:', klas.__name__, m
        table = m.local_table

        fkeys = FKeyExtractor( klas, table, mapcontext, tables)

        base_klas, inheritype = mapcontext.base4table_inheritance( klas)
        for k,typ in reflector.iter_attrtype_all( klas):
            if base_klas and reflector.owns_attr( base_klas, k):
                if inheritype != table_inheritance_types.CONCRETE:
                    if dbg: print '  inherited:', k
                    continue
                else:
                    if dbg: print '  concrete-inherited-relink:', k
            is_substruct = reflector.type_is_substruct( typ)
            if is_substruct:
                attrklas = is_substruct[ 'klas']
                if is_substruct[ 'as_value']:
                    raise NotImplementedError
                else:
                    if m.non_primary:
                        if dbg: print ' non-primary, reference ignored:', k    #comes from primary mapper
                        continue

                    rel_kargs = fkeys.get_relation_kargs( k)

                    if (issubclass( attrklas, klas)         #not supported by SA + raise
                            or issubclass( klas, attrklas)  #seems not supported by SA + crash
                        ):
                        lazy = True
                    elif config.force_lazy: lazy = True
                    else:
                        lazy = is_substruct[ 'lazy']
                        if lazy == 'default': lazy = False  ##XXXXXX config? sa_default is lazy

                    rel_kargs[ 'lazy'] = lazy
                    rel_kargs[ 'uselist'] = False
                    if dbg: print '  reference:', k, attrklas, ', '.join( '%s=%s' % kv for kv in rel_kargs.iteritems() )
                    m.add_property( k, sa.relation( attrklas, **rel_kargs))

            if reflector.type_is_collection( typ):
                raise NotImplementedError
                m.add_property( k+'_multi',
                    sa.relation( typ.itemtype,
                        uselist=True    #??typ.forward?
                    )
                )


class _MapExt( sqlalchemy.orm.MapperExtension):
    def before_insert( self, mapper, connection, instance):
        assert instance.__class__ is not mapper.class_, 'load_only_object - no save: ' + str( instance.__class__) + ':'+str(mapper)
    before_update = before_delete = before_insert
_mapext = _MapExt()

class Builder:
    reflector = None    #Reflector()    #override - just a default
    Base = MappingContext.base_klas     #override - just a default

    SETordered  = sqlalchemy.util.OrderedSet
    DICTordered = sqlalchemy.util.OrderedDict
    DICT = dict
    SrcGenerator = SrcGenerator
    table_inheritance_types = table_inheritance_types

    def __init__( me, metadata, namespace, fieldtype_mapper,
                base_klas =None,
                force_ordered =False,
                reflector =None,

                debug = None,       #same as config.debug
                generator =None,    #None->see config.generate; True->use SrcGenerator; anything non-empty, use it as the src_generator
                only_table_defs = False,
            ):
        #config/setup
        if debug is not None:
            config.debug = debug

        if generator is None: generator = config.generate
        if generator is True:
            me.generator = callable( SrcGenerator) and SrcGenerator()
        else:
            me.generator = generator

        if reflector is None: reflector = me.reflector
        assert isinstance( reflector, Reflector)

        if base_klas is None: base_klas = me.Base
        assert base_klas

        mc = MappingContext()
        mc.base_klas = base_klas
        mc.reflector = reflector
        me.mapcontext = mc

        if isinstance( fieldtype_mapper, dict):
            fm = lambda typ: fieldtype_mapper[ typ.__class__ ]
        else: fm = fieldtype_mapper

        if force_ordered:
            me.DICT = mc.DICT = me.DICTordered
            mc.SET  = me.SETordered

        #get/scan class declarations to be processed
        walkklas._debug = 'walk' in config.debug
        namespace = walkklas.walker( namespace, reflector, base_klas)

        me._loadklasi( namespace)
        reflector._resolve_forward_references( me.klasi, base_klas)
        if force_ordered:
            klasi= me.klasi
            keys = klasi.keys()
            keys.sort()
            me.klasi = me.DICT( (k,klasi[k]) for k in keys )

        #work
        me.make_subklasi()

        me.make_tables( metadata, fieldtype_mapper=fm, only_table_defs= only_table_defs)
        if not only_table_defs:
            me.make_mappers()

    def _loadklasi( me, namespace_or_iterable):
        try: itervalues = namespace_or_iterable.itervalues()        #if dict-like
        except AttributeError: itervalues = namespace_or_iterable   #or iterable

        klasi = me.DICT()
        for typ in itervalues:      #for k in getattr( namespace, '_order', itervalues):
            if me.mapcontext.mappable( typ):
                k = typ.__name__
                assert k and not k.startswith('__')
                klasi[ k] = typ     #aliases are ignored; same-name items are overwritten
        me.klasi = klasi

    def iterklasi( me): return me.klasi.itervalues()
    def column4ID( me, klas):
        return column4ID( me.tables[ klas] )
    def itermapi( me, primary_only =False):
        #primary
        for m in me.mappers.itervalues():
            yield m.polymorphic_all
        if not primary_only:
            # non-primary mappers
            for m in me.mappers.itervalues():
                if m.plain is not m.polymorphic_all:
                   yield m.plain


    def make_subklasi( me):
        me.mapcontext.make_subklasi( me.iterklasi() )


    def make_tables( me, metadata, only_table_defs =False, **kargs):
        me.tables = me.DICT()
        for klas in me.iterklasi():
             me.tables[ klas] = make_table( klas, metadata, me.mapcontext, **kargs)
        for klas in me.iterklasi(): #to be sure all tables exists already
             fix_one2many_relations( klas, me, me.mapcontext)


        from table_circular_deps import fix_table_circular_deps
        cut_fkeys = fix_table_circular_deps(
                            metadata.tables.values(),
                            count_multiples = True,
                            exclude_selfrefs= False,
                            dbg= int('table' in config.debug) + 2*int('graph' in config.debug)
                        )

        #for src-generator/generator
        for fkey in cut_fkeys:
            if hasattr( fkey,'tstr'):
                fkey.tstr.kargs.update( dict( use_alter=True, name=fkey.name))

        def getprops( klas):
            return [ column4ID.name ] + [ k for k,t in me.reflector.iter_attrtype_all( klas) ] #if not k.startswith('link')]

        try:
            if not only_table_defs:
                metadata.create_all()
        finally:
            if me.generator:
                me.generator.ptabli( metadata)
                me.generator.pklasi( me.mapcontext.base_klas, me.iterklasi(),
                        getprops= getprops
                    )


    class Mapper:
        def __init__( me):
            me.plain = me.polymorphic_all = me.polymorphic_sub_only = None

    def make_klas_selectable( me, klas, **kargs):
        return make_klas_selectable( me.mapcontext, klas, me.tables, **kargs)

    def make_mappers( me, **kargs):
        me.mappers = me.DICT()

        me.klas_only_selectables = me.DICT( (klas, me.make_klas_selectable( klas))
                                            for klas in me.iterklasi() )

        try:
            for klas in me.iterklasi():
                me._make_mapper_polymorphic( klas, **kargs)

            for klas in me.iterklasi():    #table=me.tables[ klas],
                make_mapper_props( klas, me.mapcontext, me.mappers[ klas], me.tables )

            relation.make_relations( me, sa.relation, sa.backref, FKeyExtractor)
            sqlalchemy.orm.compile_mappers()
        finally:
            if me.generator:
                me.generator.pmapi( m.polymorphic_all for m in me.mappers.itervalues() )
                me.generator.pmapi( m.plain for m in me.mappers.itervalues()
                                            if m.plain is not m.polymorphic_all)
                me.generator.psubs( (m.polymorphic_sub_only, m.polymorphic_all) for m in me.mappers.itervalues()
                                            if m.polymorphic_sub_only)

    def _outerjoin_polymorphism( me, klas, subklasi, dbg):
        ss = me.klas_only_selectables[ klas ]
        j = ss['plain']
        tbase = ss['base_table']
        for sklas in subklasi:
            if sklas is klas: continue
            s_base_klas, s_inheritype = me.mapcontext.base4table_inheritance( sklas)
            if s_inheritype == table_inheritance_types.CONCRETE:  # or != JOINED ??XXX
                if dbg: print 'outer_join_ok not ok', sklas, s_inheritype
                return None
            t = me.tables[ sklas]
            j = sa.outerjoin( j, t, (column4ID( t) == column4ID( tbase)) )

        if dbg: print 'outer_join_ok', klas, ':', j, '\n',j.c
        outer_join_ok = True
        pjoin = j
        pjoin_key = column4type( tbase)
        return pjoin, pjoin_key


    def _make_mapper_polymorphic( me, klas, **kargs):
        if klas in me.mappers: return
        #polymorphic mapper - things of type klas AND all subtypes
        ''' варианти:
            а) 3 различни съответствия (mapper) за query_BASE_instances, query_ALL_instances, query_SUB_instances
                тук не е ясно как ще се оправят наследяванията между mapper-ите
            б) 1 общ (полиморфен,правилно-наследен,въобще всички екстри) за query_ALL_instances,
                + вх.филтър (pjoin().select) за query_SUB_instances.
                + вх.филтър (table.select) за query_BASE_instances
              това не работи за query_BASE_instances - иска pjoin.atype което го няма в таблицата;
            в) 1 общ (полиморфен,правилно-наследен,въобще всички екстри) за query_ALL_instances,
                вх.филтър за query_SUB_instances,
                и прост (не-полиморфен - но наследен!) за query_BASE_instances.
            ако полиморфният не е първичен, иска _polymorphic_map - не може да се оправи сам при базов клас СЪС таблица
            #submappers = dict( (sklas.__name__, me.mappers[ sklas].plain) for sklas in subklasi.itervalues() if sklas is not excluded )
        '''
        dbg = 'mapper' in config.debug
        if dbg: print '\n--- _make_mappers', klas.__name__
        base_klas, inheritype = me.mapcontext.base4table_inheritance( klas)
        if dbg: print '  inherits', base_klas and base_klas.__name__, 'via', inheritype

        table = me.tables[ klas]
        subklasi = me.mapcontext.subklasi[ klas]
        assert klas in subklasi
        name = klas.__name__

        if 0:
            if 'some inherits this by table_inheritance_types.SINGLE':
                # трябва да се изключат от subtables, но да се добавят в А.atype=='А',
                # t.e. pjoin може да стане == table ->None в частен случай
                pjoin_key = column4type( pjoin or table)

        subtables = None
        outer_join_ok = False
        if len( subklasi)>1:   #има наследници
            if config_components.outerjoin_for_joined_tables_instead_of_polymunion:
                outer_join_ok = me._outerjoin_polymorphism( klas, subklasi, dbg)
            if outer_join_ok:
                pjoin, pjoin_key = outer_join_ok
            else:
                # тези трябва да работят във всички случаи - еднакво/ смесено наследяване
                subtables = me.DICT(
                                    (sklas.__name__, me.klas_only_selectables[ sklas]['filtered'])
                                    for sklas in subklasi
                                        if me.mapcontext.has_instances( sklas)
                                )
                pjoin = _polymorphic_union( subtables.copy(), column4type.name, 'pu_'+name, inheritype)
                pjoin_key = column4type( pjoin)
        else:
            pjoin = None
            pjoin_key = None

        base_mapper = None
        if base_klas:
            if base_klas not in me.mappers:
                me._make_mapper_polymorphic( base_klas, **kargs)
            base_mapper = me.mappers[ base_klas]

        m = me.mappers[ klas] = me.Mapper()

        inherit_condition = None
        is_concrete = False
        if base_mapper:
            if inheritype == table_inheritance_types.JOINED:
                inherit_condition = (column4ID( table) == column4ID( me.tables[ base_klas]))
            is_concrete = (inheritype == table_inheritance_types.CONCRETE)

        if inheritype == table_inheritance_types.SINGLE:
            #primary/all
            table = None
            pjoin = None
            pjoin_key = None
            #me_only
            t_only = THE_base_table_or_join.select( column4type( THE_base_with_type) == name )
            #subclasses_only
            subatypes = [ sk.__name__ for sk in subklasi if sk != name]
            m.polymorphic_sub_only = THE_table.select( column4type( THE_table).in_( *subatypes) )
            #also, explicitly list all properties to be included/excluded from base_klas

        inherits= base_mapper and base_mapper.polymorphic_all or None
        is_pm = inherits and inherits.polymorphic_on or pjoin_key

        has_no_instances = not me.mapcontext.has_instances( klas)
        if has_no_instances:
            if dbg: print ' load-only - disable mapper.save/.delete'

        #primary, eventualy polymorphic_all if pjoin
        pm = make_mapper( klas, table,
                    polymorphic_identity= is_pm and name or None,
                    concrete= is_concrete,
                    select_table= pjoin,
                    polymorphic_on= pjoin_key,
                    inherits= inherits,
                    inherit_condition= inherit_condition,
                    extension = has_no_instances and _mapext or None
                )
        m.polymorphic_all = pm

        if pjoin:
            if 1<len( [ k for k in subklasi if k is not klas and
                        me.mapcontext.base4table_inheritance( k)[1] == table_inheritance_types.CONCRETE
                    ]):
                warnings.warn( 'polymorphism over concrete inheritance not supported/SA - queries may not work' )


        if pjoin:
            #non-primary, plain
            t = me.klas_only_selectables[ klas]['filtered']
            pm = make_mapper( klas,
                    table =t,
#                    polymorphic_identity= is_pm and name or None,
                    concrete= is_concrete,
                    non_primary= True,
                    extension = has_no_instances and _mapext or None
                )

        m.plain = pm

        if pjoin:
            if dbg: print ' non-primary, SUBclasses_only'
            if outer_join_ok:
                #non-mapper - primary over sub-union-select
                m.polymorphic_sub_only = ~ me.klas_only_selectables[ klas]['filter']
            else:
                #non-mapper - primary over sub-union-select
                subtables.pop( name, None)  #all but this
                m.polymorphic_sub_only = _polymorphic_union( subtables,
                                            #v04/r3515: m.polymorphic_all.polymorphic_on._label
                                            column4type.name,
                                            'psub_'+name,
                                            inheritype
                                        )

# vim:ts=4:sw=4:expandtab
