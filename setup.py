#!/usr/bin/env python
#$Id$
# -*- coding: cp1251 -*-

from distutils.core import setup
#from setuptools import setup, find_packages

setup(
    name= 'dbcook',
    version= '0.2',
    description= 'framework to abstract database-mapping of objects/relations as python declarations, completely hiding the DB where possible',
    author= 'svilen dobrev',
    author_email= 'svilen_dobrev@users.sourceforge.net',
    url= 'http://dbcook.sf.net',
    packages= ['dbcook', 'dbcook.util',
                'dbcook.usage', 'dbcook.usage.example',
                ],
    license = "MIT License",

    classifiers='''
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Programming Language :: Python
Topic :: Database :: Front-Ends
Topic :: Software Development :: Libraries :: Python Modules
'''.strip().split('\n'),

    long_description= '''\
A framework for declarative mapping of object hierarchies/relations into a
(relational or not) database. Main idea is to abstract and hide the
DB-related stuff as much as possible, automate all (routine) DB-definition tasks,
still exposing the backend where abstracting is not needed/possible.

The "language/syntax" itself is DB-backend independent.
Currently the available builder is over SQLAlchemy as backend.

repository: svn co https://dbcook.svn.sf.net/svnroot/dbcook/trunk

Additions:
 * complete bitemporal class-mix-in : trunk/dbcook/misc/timed2/
 * (independent) automatic aggregating columns : trunk/dbcook/misc/aggregator*
 * (independent) metadata management (load,copy,diff): trunk/dbcook/misc/metadata/

Usage cases/levels:
 * DB-definition - completely hides/automates the table/ column/ key/ constraint/
    mapper/ whatever creation. The user can control certain characteristics of the way
    the mapping happens, mostly related to hierarchy and relations between objects
    (subclasses, instances, leafs, uniqueness etc).
 * generate a source of equivalent plain SQLAlchemy-calls to build the DB-definition -
    very useful for testing and/or generating routine mappings, with or without
    actualy using dbcook afterwards
 * use plain SQLAlchemy once the definition is done - e.g. session.query( class)..
 * can partialy abstract the query generation, converting from plain
    python functions/expressions (over objects' attributes) into backend/SQL clauses:
    ``lambda self: (self.friend.manager.age < 40) & self.name.endswith('a')``
 * writing own reflectors (that walk the declared classes and
    extract info from them), eventualy allowing different "language/syntax"

Features:
 * data column types - the actual mapping is separate from object declaration
 * reference columns - plain, forward-declared, self-referential -> foreign keys
 * automatic solving of cyclical references/ dependencies (proper alter_table / post_update)
 * class inheritance, class inclusion (inheritance without db-mapping of the base),
    and virtual classes (without instances). More in mapcontext._Base
 * polymorphism - 3 kinds of queries for each mapped class: all, base-only, subclasses only
 * any combination of table-inheritance-types within the tree -
    joined/ concrete/ no-single-yet - defined localy or hierarchicaly;
    beware that sql-polymorphism only works with joined-table for now
 * associations (many-to-many) - implicit and explicit
 * collections  (one-to-many)
 * dbcook.usage.samanager is a correct context-like keeper of all SQLAlchemy
    things in one place; on destroy() will try hard to clear _all_ side-effects of its
    existence, allowing reuse of same objects in several/different subsequent DB-mappings.

To use the framework, the internal dbcook/ has to be accessible somehow (PYTHONPATH or else).
Dependencies:
 * kjbuckets (from gadfly) for graph-arithmetics
 * SQLAlchemy, both 0.3 and 0.4

Example (see trunk/dbcook/usage/example/):
``
import dbcook.usage.plainwrap as o2r
class Text( o2r.Type): pass

class Address( Base):
    place = Text()

class Person( o2r.Base):
    name = Text()
    address = o2r.Type4Reference( Address)
    friend  = o2r.Type4Reference( 'Person')
    DBCOOK_has_instances = True

class Employee( Person):
    job = Text()
    DBCOOK_inheritance = 'joined'

#build it
o2r.Builder( metadata_from_sqlalchemy, locals(),
    fieldtype_mapper= { Text: sqlalchemy.String(100) } )
...
``

'''

)

# vim:ts=4:sw=4:expandtab
