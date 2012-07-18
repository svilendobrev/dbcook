dbcook
======

language to describe recipes for persistency of python classes, within their declarations. Independent of the database, hides it as much as technicaly possible - so same recipe / queries can be rendered into SQL/Alchemy (working), or others - RDF, key-value, google-datastore (todo). For big class-hierarchies. Has bitemporal extension, aggregations, polymorphic associations (for multiple inheritance), source-code-generator, etc. Even the query filters can be represented as python expressions..


This is dbcook, a framework to cook databases from recipes, written as python declarations. Eventually the result may be edible (;-)

(was at http://dbcook.sf.net)

look at dbcook/usage/example1.py as a start. 
The directory-structure is still in flux. 
To use it, the internal dbcook/ has to be accessible somehow (PYTHONPATH or else).

Licensed under MIT-license. Dependencies:
 * SQLAlchemy, v0.5 or v0.4 series. Support for v0.3 and early-v0.4 is dropped at rev259
 * kjbuckets (from gadfly) for graph-arithmetics


Here a short description what it probably is, and can do:

A framework for declarative abstract mapping of object hierarchies/relations into 
a (relational or not) database, completely hiding the DB where possible.

The "language/syntax" itself is DB-backend independent.
Currently the available builder is over SQLAlchemy as backend
(so it looks like another wrapping declarative translator).
Eventual future backends may include RDFalchemy or other non-SQL data storages.

Usage cases/levels:
 * DB-definition - completely hides/automates the table/ column/ key/ constraint/
    mapper/ whatever creation. The user can control certain characteristics of the way
    the mapping happens, mostly related to hierarchy and relations between objects
    (subclasses, instances, leafs, uniqueness etc).
 * generate a source of equivalent plain SQLAlchemy-calls to build the DB-definition -
    very useful for testing and/or generating routine mappings, with or without
    actualy using dbcook afterwards
 * use plain SQLAlchemy once the definition is done - e.g. session.query( class)..
 * dbcook.expressions can partialy abstract the query generation, converting from plain 
	python functions/expressions (of objects' attributes) into backend/SQL clauses:
    ``lambda self: (self.friend.manager.age < 40) & self.name.endswith('a')``
 * writing own reflectors (that walk the declared classes and
    extracts info from them), eventualy allowing different "language/syntax"

Work started somewhen in october 2006. Now it can handle: 
 * data column types - the actual mapping is separate from object declaration
 * reference columns - plain, forward-declared, self-referential -> foreign keys
 * automatic solving of cyclical references/ dependencies
    (putting proper alter_table / post_update)
 * class inheritance, class inclusion (inheritance without
    database mapping of the base), and virtual classes (those never
    have instances). More in mapcontext._Base
 * polymorphism - giving 3 kinds of queries for each mapped class:
    all, base-only, subclasses only
 * any combination of table-inheritance-types within the tree
    (concrete/joined/no-single-yet) - defined localy or hierarchicaly;
    beware that sql-polymorphism only works with joined-table for now
 * associations (many-to-many) - implicit and explicit
 * collections (one-to-many) 
 * dbcook.usage.samanager is a correct context-like keeper of all db-related SQLAlchemy things in
    one place, on destroy() will try hard to clear _all_ side-effects of its existence,
    allowing use of same objects within several/different subsequent DB-mappings.


Example declarations:

```
import dbcook.usage.plainwrap as o2r
class Text( o2r.Type): pass
class Int( o2r.Type): pass

class Address( o2r.Base):
	place = Text()

class Person( o2r.Base):
	name = Text()
	age  = Int()
	address = o2r.Type4Reference( Address)
	friend  = o2r.Type4Reference( 'Person')

class Employee( Person):
	job = Text()

#build it
o2r.Builder( metadata, locals(), { Text: sqlalchemy.String } )

...
for p in expression.query1(
            lambda self: self.friend.friend.friend.age > 24,
            klas=Person, session=session) ):
	print p

..... thats it. and no mentioning of tables, columns etc whatsoever .....
```

it is just a library. There is no single way to use it. The directory
usage/ has 2 possible reflectors (that walk the declared classes and extract 
info from them), one is just plain python (plainwrap.py), another is for
my static_type/ framework, for makeing staticly-declared structs 
(a-la java/C++ semantics) in python.

Certain pieces are (almost) independent and are usable as is without all the
rest: expression.py, usage/hack*py, sa_generator.py - all SQLAlchemy related.

The tests/ directory contains 2 types of tests - sa/ which proves that the way
SA is used in dbcook is correct/working, and mapper/other which check whether
the cooker does right thing as result. It still uses makefile to run all stuff.

Some todo's, long- or short- term:
 - some documentation, translate it
 - tests for all the stuff, systematically in most of combinations
 - expressions.joins need rethinking (upgraded to SA 0.4 ok)
 - generate sql-server-side functions, triggers etc
 - single-table inheritance
 - concrete-polymorphism: polymunion of (type,id) key - SA doesnot fully do it
 - other reflectors/"syntaxes" - e.g. elixir-like 
 - sub-structures as value (contained IN the parent class, not a reference 
     to elsewhere, but still used as x.y; think C memory layout)
 - user-notion types for reflector, e.g. aggregators are like a relation
 - caching tables/columns - e.g. aggregators
 - autoload / reverse-engineering / upgrade / migration (see misc/metadata/)

see dbcook/misc/readme.txt for some usable recipes.

have fun

svilen

az at svilendobrev . com

or see me at sqlalchemy's newsgroup - sqlalchemy at googlegroups . com

---------------

> Isn't it what does already Elixir?
not really. IMO elixir is sort of syntax sugar over SA, with very little 
decision-making inside. It leaves all the decisions - the routine 
ones too - to the programmer. At least thats how i got it.

while dbcook hides / automates _everything_ possible - the very concept of 
existing of relational SQL underneath is seen only by side-effects, 
e.g. the DB_inheritance types "concrete-", "joined-", "single-" 
table. It decides things like where to break cyclical references with 
alter_table/post_update; makes up the polymorphic inheritances - 
whatever the tree, etc.

Of course this is only the declaration/creation part (model-definition - 
building the DB); after that it can cover only small/simple part of the 
queries (model usage) - possibilities there are endless.
That's why there is plain SA underneath, once the "python function over 
objects converted into SA-expression over tables" path gets too 
narrow - or just ends.

dbcook does not have assign_mapper-like things, putting query methods 
on the objects. it leaves all that to you. Although one day there 
will be a usage-case/example of a way to do it - once i get there.

more differences maybe.. try

