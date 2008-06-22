#$Id$
# -*- coding: cp1251 -*-

import sys

class config_components:
    polymunion_from_SA = False      #this cannot handle mixed inheritances
    outerjoin_for_joined_tables_instead_of_polymunion = 1   # ok >= 0.3.9
    non_primary_mappers_dont_need_props = 0                 # ok ??? >= 0.3.9

    try: sys.argv.remove( 'no_generator')
    except ValueError: no_generator = False
    else: no_generator = True

#######################

from dbcook.util import config
class Config( config.Config):
    force_lazy = False      #ignore all specifying/defaults
    default_lazy = False    #unspecified relations try to achieve this
    lower_pu   = True       #lowercase polymorphic_union's name - better 'echo' readability

#    no_generator= False     #disable generator completely - use for production
    generate    = False     #do generate SA source (if generator allowed)
    debug    = ''           #some of 'graph table column mapper prop'# call

    _help = '''
mapping options:
  force_lazy  :: no eager-loading, only lazy references (default: do eager where requested/possible)
  default_lazy:: unspecified-loading become lazy (default: unspecifieds are eager if possible)
  no_lower_pu :: don't lowercase polymorphic_union's name
debug/output options:
  no_generator:: do not plug SA-source-generator underneath, use for production  [default:generator is on]
  generate    :: dump generated SA-source for making the tables and mappers [default:no]
  debug=      :: debug what's happening - some of walk,table,column,graph,mapper,prop [default:none]
'''

config = Config()


################################
#### column and table naming

#### automatic-columns - names and configuration

import sqlalchemy
#_v03 = hasattr( sqlalchemy, 'mapper')

class _column4( object):
    'used as a function with subclassable default args'
    @classmethod
    def get_column( klas, selectable):
        name = klas.name
        try:
            return getattr( selectable.c, name)
        except AttributeError, e:
            e.args = [e.args[0] + '\n:: %(selectable)s .%(name)s' % locals() ]
            raise
    def __new__( klas, selectable): return klas.get_column( selectable)

    @classmethod
    def typemap_( klas):
        t = klas.typemap.copy()
        t[ 'type_' ] = t.pop('type')
        return t


class column4ID( _column4):
    'use as column4ID( selectable)'
    name = 'db_id'
    typemap = dict( type= sqlalchemy.Integer, primary_key= True)

    special_reference_ext = '_id'
    special_back_reference_ext = '_back'
    @classmethod
    def ref_make_name( klas, name): return name + klas.special_reference_ext
    #@classmethod
    #def ref_is_name( klas, name): return name.endswith( klas.special_reference_ext)
    @classmethod
    def ref_strip_name( klas, name):
        ext = klas.special_reference_ext
        assert name.endswith( ext)
        return name[: -len( ext)]
    @classmethod
    def backref_make_name( klas, parent_klas, name):
        return name + '_' + parent_klas.__name__ + klas.special_back_reference_ext

    #XXX e.g. postgres does not want nulls in a primarykey composed of foreignkeys
    #XXX the default value must exist (stub record?) else the foreignkeys constraint fails
    #typemap4pkfk = dict( autoincrement= False)  #default= 0,
    '''www.postgresql.org/docs/8.1/interactive/sql-createtable.html
PRIMARY KEY (column constraint)
PRIMARY KEY ( column_name [, ... ] ) (table constraint)

    The primary key constraint specifies that a column or columns of a table may
    contain only unique (non-duplicate), nonnull values. Technically, PRIMARY KEY
    is merely a combination of UNIQUE and NOT NULL, but identifying a set of
    columns as primary key also provides metadata about the design of the schema,
    as a primary key implies that other tables may rely on this set of columns as a
    unique identifier for rows.

    Only one primary key can be specified for a table, whether as a column
    constraint or a table constraint.

    The primary key constraint should name a set of columns that is different from
    other sets of columns named by any unique constraint defined for the same
    table. '''

class column4type( _column4):
    'use as column4type( selectable)'
    name = 'atype'
    typemap = dict( type= sqlalchemy.String(100) )   #stores the class-name


#### table naming

from dbcook.util.attr import getattr_local_instance_only
def table_namer( klas):
    'table auto-naming'
    r = getattr_local_instance_only( klas, 'DBCOOK_dbname', klas.__name__)
    if isinstance( r, classmethod): r = klas.DBCOOK_dbname()
    return r

# vim:ts=4:sw=4:expandtab
