#$Id$
#sdobrev
'''attempt of tree-comparison over metadata.
recognised primitives are insert, delete, change of detail.
cannot recognise rename/move.
links/dependencies are not looked at.
'''

import sqlalchemy

_debug = 0

def getprivate( c, name):
    return getattr( c, '_'+c.__class__.__name__+'__'+name)

def diff( a1, a2):
    if isinstance( a1, sqlalchemy.types.TypeEngine):
        return a1.__dict__ != a2.__dict__
    if isinstance( a1, (sqlalchemy.PrimaryKeyConstraint, sqlalchemy.UniqueConstraint) ):
        return getprivate( a1, 'colnames') != getprivate( a2, 'colnames')
    return a1 != a2

class _Absent: pass

class DiffNode:
    _level = 0

    #override
    @staticmethod
    def itemnamer( c): return c.name

    def different( me):
        return bool( me.data_diff or me.subs_diff)

    @classmethod
    def set_cmp_names( differ, s1, s2):
        d1 = dict( (differ.itemnamer(i),i) for i in s1)
        d2 = dict( (differ.itemnamer(i),i) for i in s2)
        a1 = set( d1 )
        a2 = set( d2 )
        inserts = [ d2[k] for k in a2 - a1 ]
        deletes = [ d1[k] for k in a1 - a2 ]
        samename= [ (d1[k],d2[k]) for k in a1 & a2 ]
        subdiffs= []
        for i1,i2 in samename:
            d = differ( i1,i2 )
            if d.different(): subdiffs.append( d )
        return inserts, deletes, subdiffs

    def cmp( me, c1,c2):
        me.name = c1.name

        DiffNode._level +=1
        l = DiffNode._level
        indent = l * '  '
        if _debug: print (l-1)*'  ', me.__class__.__name__, ':', me.name

        d = me.data_diff = me.cmp_data( c1,c2)      # { key:(oldv,newv) }
        if _debug and d: print indent, 'data', d

        sd = me.subs_diff = me.cmp_subs( c1,c2)     # { key:(ins,del,subdiff) }
        for k,(kins,kdel,ksub) in sd.items():
            if not kins and not kdel and not ksub:
                del sd[k]
            for ktyp in 'kins kdel ksub'.split():
                kval = locals()[ ktyp]
                if _debug and kval: print indent, k, ktyp, kval
        if _debug:
            if me.different():
                print indent, '* DIFFERENT *'

        DiffNode._level -=1

    __init__ = cmp

    def dump( me):
        if not me.different(): return
        DiffNode._level +=1
        l = DiffNode._level
        indent = l * '  '
        print (l-1)*'  '+ me.__class__.__name__, ':', me.name

        d = me.data_diff
        if d: print indent+ 'data', d

        sd = me.subs_diff
        for k,(kins,kdel,ksub) in sd.items():
            if kins: print indent+ k, 'ins', kins
            if kdel: print indent+ k, 'del', kdel
            if ksub:
                print indent+ k, 'sub', ksub
                for a in ksub: a.dump()
        DiffNode._level -=1


    #override
    _data_member_names = () # [ name ]

    def cmp_data( me, c1, c2):
        diffs = {}
        for a in me._data_member_names:
            a1 = getattr( c1, a, _Absent)
            a2 = getattr( c2, a, _Absent)
            if a1 is _Absent or a2 is _Absent or diff( a1, a2):
                diffs[ a ] = (a1,a2)
        return diffs


    #override
    _subnames = {}  # {name:DiffNodeSubclass}

    def cmp_subs( me, c1,c2):
        return dict(
            (subname, me._cmp_subs( c1,c2,subname,differ ) )
                for subname,differ in me._subnames.iteritems() )
    def _cmp_subs( me, c1,c2, subname, differ):
        try:
            differ, getter = differ
        except:
            getter = lambda m: getattr( m,subname)
        return differ.set_cmp_names( getter(c1), getter(c2) )

class Diff_nameOnly( DiffNode):
    _data_member_names = 'name'.split()

DiffConstraint = DiffForeignKey = Diff_nameOnly

class DiffColumn( DiffNode):
    _data_member_names = 'name type key primary_key nullable onupdate default  index unique quote autoincrement'.split()
    _subnames = dict( constraints= DiffConstraint, foreign_keys= DiffForeignKey)

class DiffIndex( DiffNode):
    _data_member_names = 'name unique'.split()
    _subnames = dict( columns= DiffColumn)

class DiffTable( DiffNode):
    _data_member_names = 'name primary_key  quote owner schema'.split()
    _subnames = dict( columns= DiffColumn, constraints= DiffConstraint, indexes= DiffIndex)

class DiffMetaData( DiffNode):
    _subnames = dict( tables = (DiffTable, lambda m: m.tables.values() ) )


###############

if __name__ == '__main__':

    import dbcook.usage.plainwrap as o2r
    o2r.Base.DBCOOK_inheritance = 'joined_table'

    class Text( o2r.Type): pass
    class Text2( o2r.Type): pass
    class Int( o2r.Type): pass

    class Address( o2r.Base):
        place = Text()
        size  = Int()
    class Person( o2r.Base):
        name = Text()
        address = o2r.Reference( Address)
        friend  = o2r.Reference( 'Person')
    class Employee( Person):
        job = Text()

    fm = {  Text:   dict( type=sqlalchemy.String(10) ),
            Int:    dict( type=sqlalchemy.Integer),
            Text2:  dict( type=sqlalchemy.String(30) ),
        }
    m1 = sqlalchemy.MetaData()
    b1 = o2r.Builder( m1, locals(), fm, only_table_defs= True)

    class Address( o2r.Base):
        size  = Text()          #change type
        place = Text2()         #change type-details
    class Employee( o2r.Base):  #no inheritance
        jobe = Text()           #change name
    class Employee2( Person):   #new class
        lazy = Text()

    m2 = sqlalchemy.MetaData()
    b2 = o2r.Builder( m2, locals(), fm, only_table_defs= True)


    def tt( m, name):
        print name, m
        ts = sorted( (t.name, t) for t in m.table_iterator( reverse=False ) )
        print ', '.join( name for name,t in ts )
        return ts



    d = DiffMetaData( m1,m2)
    print '=============='
    d.dump()
# vim:ts=4:sw=4:expandtab
