#$Id$
# -*- coding: cp1251 -*-

''' XXX HACK за повтаряемост на тестове/sql, подменя Set на OrderedSet изобщо, и
dict на OrderedDict в конструктори (Metadata); както и _вътре_ в някои функции.
Може да има и още места, в непробвани случаи.

XXX НЕ забравяй входните извиквания/"заявки" също да са повтаряеми/подредени!!!
e.g. SAdb( ..force_ordered=True)

------------

XXX HACK to achieve repeatability of tests over sql-output. Replaces Set with OrderedSet wholy,
and dict/{} with OrderedDict in some constructors (MetaData) and _inside_ some fuctions.
Probably there are more places, for untried cases.

XXX DONT forget to make "requests"/calls also repeatable/ordered!!!
e.g. SAdb( ..force_ordered=True)
'''
from dbcook.util.hacksrc import hacksrc

def hack4repeat():
    import sqlalchemy
    _v03 = hasattr( sqlalchemy, 'mapper')
    if not _v03:
        print 'v04 - cant hack4repeat'
        return
    # HACKALL
    import sqlalchemy.util
    sqlalchemy.util.Set = sqlalchemy.util.OrderedSet
    DICT = sqlalchemy.util.OrderedDict
    SET  = sqlalchemy.util.OrderedSet

    import sqlalchemy.topological

    def init2old( x, newfunc): #, name ='__init__', oldname = 'oldinit'):
        x.oldinit = x.__init__
        x.__init__ = newfunc

    if 0:
        class SortedList( list):
            def __iter__( me):
                try: sorted = me._sorted
                except AttributeError:
                    sorted = me._sorted = me._do_sort()
                assert len(me) == len(sorted)
                return iter( sorted)
            def _do_sort( me):
                #if not me: me = r
                r = me[:]   #copy
                r.sort( key= lambda t:t.item.name)
    #                print 'sorted-', ','.join( t.item.name for t in r)
                return r

        def init( me, *a,**k):
            me.oldinit( *a,**k)
            me.children = SortedList()
            #print 'hacked', type(me)
        init2old( sqlalchemy.topological._Node, init)

    #see also:
        # unitofwork.UnitOfWork.identity_map ??
        # unitofwork.UOWTask.objects
        # sql_util.Aliasizer.tables

    if 1:
        def init( me, *a,**k):
            me.oldinit( *a,**k)
            me.tables = DICT()
            #print 'hacked', type(me)
        init2old( sqlalchemy.schema.MetaData, init)

    if 10:
        def init( me, *a,**k):
            me.oldinit( *a,**k)
            if isinstance( me.dependencies, sqlalchemy.util.Set):
                me.dependencies = SET()
            else:
                me.dependencies = DICT()
            #me.tasks = DICT()
            #print 'hacked', type(me)
        init2old( sqlalchemy.orm.unitofwork.UOWTransaction, init)

    if 10:
        def init( me, *a,**k):
            me.oldinit( *a,**k)
            me.objects = DICT()
            #print 'hacked', type(me)
        init2old( sqlalchemy.orm.unitofwork.UOWTask, init)

    if 0:
        import weakref
        def init( me, dict=None):
            me.oldinit( None)
            me.data = DICT( dict)
            print 'hacked', type(me)
        init2old( weakref.WeakKeyDictionary, init)

    from sqlalchemy.orm import mapperlib
    assert not  mapperlib.mapper_registry.data
    mapperlib.mapper_registry.data = DICT()


    if 10:
        #these must be done via source:
        #orm/mapper.py: Mapper.save_obj(): line 848
        #   table_to_mapper = util.OrderedDict() #{}
        #topological.py: QueueDependencySorter.sort(): line 138
        #   nodes = util.OrderedDict()  #{}


        #ver 0.3.3
        hacksrc( mapperlib.Mapper.save_obj,
                    'table_to_mapper = {}', 'table_to_mapper = util.OrderedDict()' )
        hacksrc( mapperlib.Mapper._compile_properties,
                    'self.__props = {}', 'self.__props = util.OrderedDict()' )
        hacksrc( sqlalchemy.topological.QueueDependencySorter.sort,
                    'nodes = {}', 'nodes = util.OrderedDict()' )

    if 0:   #partial
        def _set_constraints( me,v):
            from sqlalchemy.util import OrderedSet, Set
            assert not v
            assert isinstance( v, Set)
            me._constraints = OrderedSet()
        sqlalchemy.Table.constraints  = property( lambda me: me._constraints, _set_constraints)
        sqlalchemy.Column.constraints = property( lambda me: me._constraints, _set_constraints)

### these are some fixes/hacks for this or that ###
if 0:   #orm.query.Query
    def _locate_prop(self, key, start=None):
        '''the original func searches down the reference hierarchy for the key attribute,
            e.g. q(A).select_by(age=44} will find A.b.c.d.age (if no .age is found above that);
        use this instead to also search for multilevel keys/references,
            e.g. q(A).select_by(**{'c.d.age': 134}'''
        import properties
        keys = []
        seen = util.Set()
        def search_for_prop(mapper_, fullkey):
            if mapper_ in seen:
                return None
            seen.add(mapper_)
            key = fullkey[0]
            if mapper_.props.has_key(key):
                prop = mapper_.props[key]
                if len(fullkey)==1:
                    if isinstance(prop, properties.SynonymProperty):
                        prop = mapper_.props[prop.name]
                    if isinstance(prop, properties.PropertyLoader):
                        keys.insert(0, prop.key)
                    return prop
                else:
                    props = [prop]
                    fullkey = fullkey[1:]
            for prop in mapper_.props.values():
                if not isinstance(prop, properties.PropertyLoader):
                    continue
                x = search_for_prop(prop.mapper, fullkey)
                if x:
                    keys.insert(0, prop.key)
                    return x

            return None
        p = search_for_prop(start or self.mapper, key.split('.') )
        if p is None:
            raise exceptions.InvalidRequestError("Cant locate property named '%s'" % key)
        return [keys, p]
# vim:ts=4:sw=4:expandtab
