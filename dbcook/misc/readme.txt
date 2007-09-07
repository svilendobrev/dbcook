#$Id$

various stuff which is or isn't directly using dbcook, 
but is related in a way or another.
############################

timed2/: (SA) - READY
    addon (mixin-class) for objects that have 2-time-history and state( enabled/disabled)
    needs following properties per object: 
        obj_id  = ObjId()       #incremented by special ObjectCounter
        time_valid  = someDate()
        time_trans  = someDate()
        disabled    = Bool( default_value= False)
    All is there together with very thorough test, and a related timed/ library 
    containing things like support of time-versioned src-modules, TimeContext etc.

aggregator/ (SA)    ~READY
    also see http://www.mr-pc.kiev.ua/en/projects/SQLAlchemyAggregator

cache_results/: (dbcook over aggregator/ - not ready)
    addon for automaticaly-updated database denormalisation caches of intermediate results,
    each one depending on particular pattern of usage. wishful syntax:
        class Cache4averagePerson( Base):
            fieldname = cache_aggregator( klas.field, AggrFilterCriteria)
            #e.g.
            #age    = cache_agregators.Average( Person.age, FilterCriteria1 )
            #salary = cache_agregators.Sum( Person.salary, FilterCriteria2 )

metadata/: (SA-only - initial parts)
    handling of DB-structre/metadata consistency, changes, migration
    * autoload    - somewhat ready
    * diff        - first version ready, cannot handle move/rename
    * db-copy     - somewhat ready
    * migration   - ???


multilang/: (dbcook/SA) (not available)
    addon for transparent multi-language textual properties, allowing for history

nested_user_transactions/: (dbcook/SA)  (not available)
    addon to support nested user transactions aspect (NOT nested DB transactions).
    needs following properties per object: 
        transact    = TransactID( default_value= 0)

may be invented or may not:
    Nomerator - something that gives numbers/ids to objects in whatever special way. 
                Think of invoices, incoming/outgoing/reference documents, inventories etc.

    multivalue - value that is representable in many currencies/measures/ways.
                Think of money, items that can be measured either as volume or weight, etc.

    FIFOconsumer - tracking increases of an (accumulated) value and consuming it in same order/ per increase.
                Think of grocery/drugs store, selling items out exactly in the order they came in, 
                and tracking which one comes from which delivery.
    
# vim:ts=4:sw=4:expandtab
