#$Id$
# -*- coding: cp1251 -*-
import sqlalchemy

import sys
if 'sa' not in sys.argv:
    if 'static' not in sys.argv:
        from dbcook.usage import plainwrap as saw
        class Text( saw.Type): pass
        TextD = Text
        class Number(  saw.Type): pass
        class Date(  saw.Type): pass
        class Bool(  saw.Type): pass
        Element = saw.Base
        class Entity( Element):
            must_be_reference = True
            auto_set = False

            DB_inheritance = 'joined_table'
            if 1:
                obj_id  = Number()
                time_valid  = Date()
                time_trans  = Date()
                disabled    = Bool()

        fmap = {
            Text: dict( type= sqlalchemy.String, ),
            Number: dict( type= sqlalchemy.Integer, ),
            Date: dict( type= sqlalchemy.Date ),
            Bool: dict( type= sqlalchemy.Boolean),
        }
    else:
        from model.types_base import *
        #sa2static._debug = 'dict'
        from dbcook.usage.static_type import fieldtypemapper
        import datetime
        typemap_upper = {
            Text: dict( type= sqlalchemy.String, ),
            Bool: dict( type= sqlalchemy.Boolean), #Integer ?
            Date: dict( type= sqlalchemy.Date ),
        }
        typemap_lower= {
            str:    dict( type= sqlalchemy.String ),
            float:  dict( type= sqlalchemy.Float ),
            int:    dict( type= sqlalchemy.Integer),
            datetime.datetime:  dict( type= sqlalchemy.DateTime ),
            datetime.date:  dict( type= sqlalchemy.Date ),
            datetime.time:  dict( type= sqlalchemy.Time ),
            datetime.timedelta:  dict( type= sqlalchemy.DateTime ),
        }
        fmap = fieldtypemapper.FieldTypeMapper( typemap_upper, typemap_lower)
        saw = sa2static
    from dbcook.usage.samanager import SAdb

    if 'model' in sys.argv:
        class Model( Entity):
            DB_NO_MAPPING = True
            pass
    else: Model=Entity

    class Name( Element):
        name = TextD()
    class Darzhava( Model): #by ISO 3166
        name = saw.Type4Reference( Name)

    s = SAdb( 'sqlite')
    s.open( recreate=False)

    from dbcook.usage.sa_hack4repeatability import hack4repeat
    hack4repeat()
    s.bind( locals(), fieldtypemap=fmap, builder=saw.Builder, base_klas= Element, force_ordered=True)
    #s.query_all_tables()
    session = s.session()

else:
    from sqlalchemy import *
    db = create_engine( 'sqlite:///proba1.db')
    meta = BoundMetaData( db)
    meta.engine.echo = 'echo' in sys.argv

        #decomposed by joined_table
    table_Entity = Table( 'Entity', meta,
        Column( 'disabled', type= Boolean, ),
        Column( 'time_trans', type= Date, ),
        Column( 'time_valid', type= Date, ),
        Column( 'obj_id', type= Integer, ),
        Column( 'db_id', primary_key= True, type= Integer, ),
        Column( 'atype', type= String, ),
    )

    table_Darzhava = Table( 'Darzhava', meta,
        Column( 'name_id', Integer, ForeignKey( 'Name.db_id', ), ),
        Column( 'db_id', Integer, ForeignKey( 'Entity.db_id', ), primary_key= True, ),
    )

    table_Name = Table( 'Name', meta,
        Column( 'name', type= String, ),
        Column( 'db_id', primary_key= True, type= Integer, ),
    )


    class Base( object):
        props = ['name']
        def set( me, **kargs):
            for k,v in kargs.iteritems(): setattr( me, k, v)
            return me
        def __str__(me):
            r = str(me.__class__.__name__)
            if me.props: r+=';'+';'.join(k+'='+str(getattr(me,k,'<unset>')) for k in me.props)
            return r
        __repr__ = __str__
    class Entity( Base):     props=['atype', 'disabled']
    if 'model' in sys.argv:
        class Model( Entity): pass
    else:
        Model=Entity
    class Darzhava( Model): props=['name' ]
    class Name( Base):       props=['name' ]

    meta.create_all()

    pu_Entity = polymorphic_union( {
                    'Darzhava': join( table_Entity, table_Darzhava, table_Darzhava.c.db_id == table_Entity.c.db_id, ),
                    'Entity': table_Entity.select( table_Entity.c.atype == 'Entity', ),
                    }, None, 'pu_Entity', ) #joined
    mapper_Entity = mapper( Entity, table_Entity,
                inherit_condition= None,
                inherits= None,
                polymorphic_identity= 'Entity',
                polymorphic_on= pu_Entity.c.atype,
                select_table= pu_Entity,
                )

    mapper_Name = mapper( Name, table_Name,
                    inherit_condition= None,
                    inherits= None,
                    polymorphic_identity= 'Name',
                    polymorphic_on= None,
                    select_table= None,
                )

    mapper_Darzhava = mapper( Darzhava, table_Darzhava,
                    inherit_condition= table_Darzhava.c.db_id == table_Entity.c.db_id,
                    inherits= mapper_Entity,
                    polymorphic_identity= 'Darzhava',
                    polymorphic_on= None,
                    select_table= None,
                )
    mapper_Darzhava.add_property( 'name', relation( Name,
                    foreignkey= table_Darzhava.c.name_id,
                    lazy= True,
                    post_update= False,
                    primaryjoin= table_Darzhava.c.name_id == table_Name.c.db_id,
                    remote_side= table_Name.c.db_id,
                    uselist= False,
                ) )

    if 'create' in sys.argv:
        a = Employee().set( name= 'one')
        b = Engineer().set( egn= 'two', machine= 'any')
        c = Manager().set( name= 'head', machine= 'fast', duties= 'many')
    #    a.info1 = Info().set( name= 'i1')
        b.info2 = Info().set( name= 'i2')
    #    c.info3 = Info().set( name= 'i3')

        session = create_session()
        session.save(a)
        session.save(b)
        session.save(c)
        session.flush()

        print a,b,c

        session.clear()
    else:
        session = create_session()

    if 'Entity' in sys.argv:
        print session.query( Entity).select()
    if 'Name' in sys.argv:
        print session.query( Name).select()
    #print session.query( Darzhava).select()

print '------'
q = session.query( Darzhava).select()
print '------', [a.name.name for a in q]

# vim:ts=4:sw=4:expandtab
