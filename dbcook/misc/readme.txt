#$Id$

various stuff which isn't directly an usage of dbcook, 
but is related in a way or another.


metadata/: (SA-only)
  metadata autoload and diff

bitemporal/: (SA-only for now)
  addon for objects that have 2-time-history and state(enabled/disabled)
  needs following properties per object: 
        obj_id  = ObjId()  		#incremented by special ObjectCounter
        time_valid  = Date()
        time_trans  = Date()
        disabled    = Bool( default_value= False)

multilang/: (dbcook/SA)
  addon for transparent multi-language textual properties, allowing for history

nested_user_transactions/: (dbcook/SA)
  addon to support nested user transactions aspect (NOT nested DB transactions).
  needs following properties per object: 
  	transact    = TransactID( default_value= 0)

cache_results/: (dbcook/SA)
  addon for automaticaly-updated database denormalisation caches of intermediate results,
  each one depending on particular pattern of usage. wishful syntax:
    class Cache4averagePerson( Base):
        fieldname = cache_aggregator( klas.field, AggrFilterCriteria)
        #e.g.
        #age    = cache_agregators.Average( Person.age, FilterCriteria1 )
        #salary = cache_agregators.Sum( Person.salary, FilterCriteria2 )

may be invented or may not:

  Numerator - something that gives numbers/ids to objects in whatever special way. 
              Think of invoices, incoming/outgoing/reference documents, inventories etc.

  multivalue - a value that is represented/representable in many currencies/ways/measurements.
              Think of money, items that can be measured either as volumen or as weight, etc.


# vim:ts=4:sw=4:expandtab
