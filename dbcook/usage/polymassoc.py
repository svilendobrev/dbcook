#$Id$
# -*- coding: cp1251 -*-

#import polymassoc_cfg as cfg

class PolymorphicAssociation( object):  #cfg.Base):
    '''
    full many-to-many association.
    Subclass it and setup config__non_owner_linknames - usualy just the owned_thing.
    Requires participating owner-classes and the owned_thing to have
    Association.Relation()s to this.

    setup config__owner_order if some participating classes inherit each other - put them there.

    owner is made as union/switch to allow any object classes to
    be owners, not really having common inheritance base/tree.
    It's a sort of multiple aspects, like simulating multiple inheritance but one level only.
    Each aspect is represented by different PolymorphicAssociation-heir,
    and different classes can participate in them.

    1-to-many variant:
    http://wiki.rubyonrails.org/rails/pages/UnderstandingPolymorphicAssociations
    sqlalchemy/examples/poly_assoc/

    beware: these are not equivalent anymore as in plain SA:
        1: this.owner = someowner   #works ok via selector
        2: someowner.ownedthings.append( this)  #works low-level but misses higher: which_owner selector etc
    '''
    __slots__ = ()
    DBCOOK_no_mapping = True

    #owned_thing = Association.Link( OwnedClass, attr= 'owners')    #into OwnedClass
    config__non_owner_linknames = ()    #at least the one above pointing to OwnedClass
    config__owner_order = ()     #put classes that inherit each-other here, in child-to-root order

    #type-selector
    if 0:
        #db-written: easy but could do without it
        which_owner = None  #Text() - some textual Type #cfg.which_owner_TextType
    else:
        # implicit: needs walking all refs once-per-load, finding a non-zero one.
        NEEDS__slots__ = ['_which_owner']   #add this yourself to the inherting class

        def get_which_owner( me):
            try: return me._which_owner
            except AttributeError: pass

            # here is walking refs at column-level; maybe mapperExt @ populate_instance
            from dbcook.aboutrel import about_relation
            for selector in me.possible_owners():
                ab = about_relation( me.__class__, selector)
                column = ab.thisside.column
                if getattr( me, column.key) is not None:
                    me._which_owner = selector
                    return selector

            # above alone is not enough -
            #  - a newly-created object + low-level copy of refs (not via .owner)
            # would not have column_id set-up yet (but would have an attr)

            # warning: this may fire lazy-loads
            for selector in me.possible_owners():
                if getattr( me, selector) is not None:
                    me._which_owner = selector
                    return selector

            return None

        def set_which_owner( me, v):
            me._which_owner = v
        which_owner = property( get_which_owner, set_which_owner)

    _possible_owners = None
    @classmethod
    def possible_owners( me):
        'forward name->klas'
        r = me._possible_owners
        if r is None:
            r = dict( (k,v) for k,v in me._DBCOOK_references.iteritems()
                            if k not in me.config__non_owner_linknames)
            me._possible_owners = r
        return r

    _possible_owners2 = None
    @classmethod
    def possible_owners2( me):
        'backward klas->name'
        r = me._possible_owners2
        if r is None:
            r1 = me.possible_owners()
            r = dict( (v,k) for k,v in r1.iteritems() )
            assert len(r) == len(r1)
            me._possible_owners2 = r
        return r

    @classmethod
    def find_which_owner( me, someowner, is_class =False):
        #the backward mapping _possible_owners2 won't do direct, must use isinstance/issubclass
        func = is_class and issubclass or isinstance
        r1 = me.possible_owners()
        r2 = me.possible_owners2()
        #these can be either classes or selector-names
        prefered_order = me.config__owner_order
        #p = [ isinstance( i, str) and r1[i] or i for i in prefered_order]
        for item in prefered_order:
            if isinstance( item, str):
                if func( someowner, r1[ item]): return item
            else:
                klas = item
                assert klas in r2
                if func( someowner, klas): return r2[ klas]
        for klas, selector in r2.iteritems():
            #if klas not in prefered_order and selector not in prefered_order:  not really needed
                if func( someowner, klas): return selector
        return None

    'exactly one of owner-links must exist'
    def get_owner( me):
        return getattr( me, me.which_owner)
    def set_owner( me, someowner):
        #print 'set_owner', object.__repr__( someowner)
        selector = me.find_which_owner( someowner)
        assert selector, '%s.owner cannot be %s, but one of %s' % ( me.__class__, someowner.__class__, me.possible_owners2().keys() )
        for sel in me.possible_owners():
            if sel != selector:
                setattr( me, sel, None)
        setattr( me, selector, someowner)
        me.which_owner = selector
    owner = property( get_owner, set_owner)

if __name__ == '__main__':
    from plainwrap import Type, Base, Association, Builder
    class Text( Type): pass
    class Int( Type): pass
    Base.DBCOOK_inheritance = 'joined'   #for subclasses

    #value aspect
    class ValueOwnership( Base, Association, PolymorphicAssociation):
        config__non_owner_linknames = [ 'value']
        which_owner = Text()
    class Value( Base):
        owners = Association.Relation( ValueOwnership, backref= 'value')
        value = Int()
        currency = Text()
    class _ValueOwner( Base): # mixin
        DBCOOK_no_mapping = True
        #automatic as of class-name
        values = Association.Relation( ValueOwnership,
                    backref= lambda klas,attr: '_'+klas.__name__)

    #color aspect
    class ColorOwnership( Base, Association, PolymorphicAssociation):
        config__non_owner_linknames = [ 'color']
        which_owner = Text()
    class Color( Base):
        owners = Association.Relation( ColorOwnership, backref= 'color')
        paint = Text()
    class _ColorOwner( Base): # mixin
        DBCOOK_no_mapping = True
        #manual
        #colors = Association.Relation( ColorOwnership, backref= lambda klas,attr: '_'+klas.__name__)

    #Estates hierarchy
    class Estate( Base):
        name = Text()
        area = Int()
    class House( Estate, _ValueOwner, _ColorOwner):
        floors = Int()
        colors = Association.Relation( ColorOwnership, backref= '_house')

    class Forest( Estate, _ValueOwner):
        treetype = Text()

    #Items hierarchy
    class Item( Base):
        lifetime = Int()
    class Bag( Item, _ValueOwner, _ColorOwner):
        material = Text()
        colors = Association.Relation( ColorOwnership, backref= '_bag')
    class Car( Item, _ValueOwner, _ColorOwner):
        wheels = Int()
        colors = Association.Relation( ColorOwnership, backref= '_car')
    class BankAccount( Item, _ValueOwner):
        bank = Text()
    #...

    from sqlalchemy import String, Integer, MetaData, create_engine
    fieldtypemap = {
        Text: dict( type= String(100), ),
        Int : dict( type= Integer, ),
    }
    import sys
    meta = MetaData( create_engine('sqlite:///', echo= 'echo' in sys.argv ))
    b = Builder( meta, locals(), fieldtypemap,
            generator ='generate' in sys.argv   #lets see how this would look in plain sqlalchemy
        )
    if b.generator:
        print '========= generated SA set-up'
        print b.generator.out
        print '========= eo generated SA set-up'
        #XXX TODO Relation.backrefs are not shown well

    from sqlalchemy.orm import create_session
    s = create_session()
    #...
# vim:ts=4:sw=4:expandtab
