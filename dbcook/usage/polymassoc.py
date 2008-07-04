#$Id$
# -*- coding: cp1251 -*-

#import polymassoc_cfg as cfg

class PolymorphicAssociation( object):  #cfg.Base):
    '''
    full many-to-many association.
    Subclass it and setup config__non_owner_linknames - usualy just the owned_thing.
    Requires participating owner-classes and the owned_thing to have
    Association.Relation()s to this.

    probably will not work if participating classes inherit each other.

    owner is made as union/discriminator/switch to allow any object classes to
    be owners, not really having common inheritance base/tree.
    It's a sort of multiple aspects, like simulating multiple inheritance but one level only.
    Each aspect is represented by different PolymorphicAssociation-heir,
    and different classes can participate in them.

    1-to-many variant:
    http://wiki.rubyonrails.org/rails/pages/UnderstandingPolymorphicAssociations
    sqlalchemy/examples/poly_assoc/
    '''
    __slots__ = ()
    DBCOOK_no_mapping = True

    #owned_thing = Association.Link( OwnedClass, attr= 'owners')    #into OwnedClass
    config__non_owner_linknames = ()    #at least the one pointing to Owned_Thing

    #type-selector
    which_owner = None  #Text() - some textual Type #cfg.which_owner_TextType

    _possible_owners = None
    @classmethod
    def possible_owners( me):
        r = me._possible_owners
        if r is None:
            r = dict( (k,v) for k,v in me._DBCOOK_references.iteritems()
                            if k not in me.config__non_owner_linknames)
            me._possible_owners = r
        return r

    @classmethod
    def find_which_owner( me, someowner, is_class =False):
        #обратното пряко съответствие нa possible_owners не върши работа, трябва isinstance/issubclass
        func = is_class and issubclass or isinstance
        for selector, klas in me.possible_owners().iteritems():
            if func( someowner, klas):
                return selector
        return None

    'exactly one of owner-links must exist'
    def get_owner( me):
        return getattr( me, me.which_owner)
    def set_owner( me, someowner):
        #print 'set_owner', object.__repr__( someowner)
        selector = me.find_which_owner( someowner)
        assert selector, '%s.owner cannot be %s, but one of %s' % ( me.__class__, someowner.__class__, me.possible_owners() )
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
        #values = Association.Relation( ColorOwnership, backref= lambda klas,attr: '_'+klas.__name__)

    #Estates hierarchy
    class Estate( Base):
        name = Text()
        area = Int()
    class House( Estate, _ValueOwner, _ColorOwner):
        floors = Int()
    class Forest( Estate, _ValueOwner):
        treetype = Text()

    #Items hierarchy
    class Item( Base):
        lifetime = Int()
    class Bag( Item, _ValueOwner, _ColorOwner):
        material = Text()
    class Car( Item, _ValueOwner, _ColorOwner):
        wheels = Int()
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

    from sqlalchemy.orm import create_session
    s = create_session()
    #...
# vim:ts=4:sw=4:expandtab
