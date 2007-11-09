#$Id$
#store+print SA constructor-args in order to recreate the source

import sqlalchemy
import sqlalchemy.orm
import operator
from dbcook.util.attr import issubclass, find_valid_fullname_import

def traverse( visitor, obj):
    try: f = visitor.traverse
    except: return obj.accept_visitor( visitor)
    else: return f( obj)

class CV( sqlalchemy.sql.ClauseVisitor):
    ops = {
        '=':'==',
        operator.eq: '==',
        operator.ne: '!=',
    }
    def __init__(me):
        me.stack = []
    def visit_bindparam(me, c):
        t = repr(c.value)
        me.stack.append( t)
    def visit_column(me, c):
        if isinstance( c.table, sqlalchemy.Table):
            varname= table_varname( c.table)
        else:
            varname= c.table.name
        t = varname + '.c.' + c.name
        me.stack.append( t)
    def visit_binary(me, b):
        r = me.stack.pop()
        l = me.stack.pop()
        try:
            op = me.ops[ b.operator]
        except KeyError:
            print 'XXXXXXXX', type(l), b.operator, type(r)
            op = b.operator
        t = ' '.join( [l, op, r ])
        me.stack.append( t)

class _state:
    do_columns = False

_BinaryThing = find_valid_fullname_import( '''
    sqlalchemy.sql.expression._BinaryExpression
    sqlalchemy.sql._BinaryExpression
    sqlalchemy.sql._BinaryClause
''')

if 0:
    def props_iter( mapr, klas =sqlalchemy.orm.PropertyLoader ):
        try: i = mapr.properties
        except:     # about r3740
            for p in mapr.iterate_properties:
                if isinstance( p, klas):
                    yield p.key, p
        else:
            for k,p in i.iteritems():
                yield k,p

    def props_get( mapr, key):
        try:
            return mapr.properties[ key]
        except KeyError: raise
        except:     # about r3740
            return mapr.get_property( key)


level = 0
def tstr(o):
    global level
    level+=1
    if isinstance(o,type):  r = o.__name__
    elif isinstance(o,str): r = repr(o)
    elif isinstance(o,dict):
        r = ('\n'+16*' ').join( ['{']+ ['%r: %r,' % kv for kv in o.iteritems() ] + ['}'] )
#    elif _state.do_columns and isinstance(o, sqlalchemy.Column):
#        r = o.table.name+'.c.'+o.name
    elif (_state.do_columns and isinstance(o, sqlalchemy.sql.ColumnElement) or
           isinstance(o, _BinaryThing) ):
#        print 'do_columnex', getattr(o,'name','<noname>'),
        cv = CV()
        traverse( cv,o)
        r = cv.stack.pop()
        assert not cv.stack
    else:
        try: r = str( o.tstr)
        except AttributeError:
            if isinstance( o, sqlalchemy.sql.Alias):
                r = repr2alias(o)
            else:
                r = str(o)
    level-=1
    assert isinstance( r,str), type(r)
    return r

def tstr2(o):
    'infinite recursion here == duplicated module, probably by different paths - e.g. db.dbcook.x and dbcook.x elsewhere'
    try: return str(o.tstr)
    except AttributeError: return o.org__repr__()

def repr2tstr( klas, funcrepr =tstr2):
    klas.org__repr__ = klas.__repr__
    klas.__repr__ = funcrepr

class Tstr:
    nl = ''
    nl4args = None
    no_kargs = {}   #ignore these kargs of these values
    def __init__( me, nl=None, nl4args=None, no_kargs =None):
        if nl is None: nl = me.nl
        if nl4args is None: nl4args = me.nl4args
        if no_kargs is None: no_kargs = me.no_kargs

        if nl4args is None: nl4args = nl
        me.nl = nl
        me.nl4args = nl4args
        me.no_kargs = no_kargs

    def thestr( me, tself, name, args, kargs):
        nl = me.nl
        nl4args = me.nl4args
        t = tself and (tself + '.') or ''
        ks = kargs.keys()
        ks.sort()
        return ( t + name+ '( '+
                nl.join(
                    [ nl4args.join( [str(tstr(a))+', ' for a in args]) ] +
                    [ (level*'  '+'%s= %s, ') % (k,tstr(kargs[k]))
                        for k in ks #kargs.iteritems()
                        if kargs[k] is not me.no_kargs.get( k,'_any_any_')
                    ] + [')'] )
                )
class TstrSelf( Tstr):
    def __init__( me, name, args, kargs, tself ='', **kargs4setup):
        me.name = name
        me.tself = tself
        me.args = args
        me.kargs = kargs
        Tstr.__init__( me, **kargs4setup)
    def __str__( me):
        return me.thestr( me.tself, me.name, me.args, me.kargs)

class duper( Tstr):
    def dup( me, self, *args,**kargs):
        base = me.base
        #do not compare things containing columns!
        t = me.thestr( self and tstr2(self) or '', #XXX move to Tstr..
                        base.__name__, args, kargs)
        if self is None:
            r = base( *args, **kargs)
        else:
            r = base( self, *args, **kargs)
        if me.otherstr:
            r.tstr2 = t
            t = me.otherstr(r)
        r.tstr = t
        return r

    def __init__( me, base, otherstr =None, **kargs4setup):
        me.base = base
        me.otherstr = otherstr
        Tstr.__init__( me, **kargs4setup)

    def __call__( me, *args,**kargs):
        return me.dup( None, *args,**kargs)

class duper2( duper):
#    with_attrs = {} #add these attributes as kargs (if not of these values)
    def thestr( me, tself, name, args, kargs):
#        for k,v in me.with_attrs.iteritems():
#            a = getattr(
        return TstrSelf( name, args, kargs, tself=tself,
                            nl= me.nl, nl4args= me.nl4args, no_kargs= me.no_kargs)

#names = {}
def table_varname(t):  return 'table_'+t.name
def punion_varname(u): return u.name #'punion_'+
def mapper_varname(m): return 'mapper_'+m.class_.__name__+(m.non_primary and '1' or '')

class Printer:
    def __init__( me, filename=''):
        me.out = ''
        me.done= []
    def nl(me):
        me.out += '\n'

    def pklas( me, klas, getprops =None, declarator =None, **kargs_ignore):
        base = klas.__bases__[0].__name__
        name = klas.__name__
        if getprops:
            props = getprops(klas)
        else:
            props = klas.props
        r = '''\
class %(name)s( %(base)s):
    props = %(props)s''' % locals()
        if declarator:
            r += '\n'+declarator( klas).rstrip()
        me.out += r + '\n'

    def pklasi( me, Base, namespace, **kargs):
        me.Base = Base
        try:
            namespace = namespace.itervalues()
        except AttributeError: pass
        all = [klas for klas in namespace if issubclass( klas, Base)]
        all.sort( key=lambda kl:kl.__name__)
        for klas in all:
            me.pklas( klas, **kargs)
        me.nl()
        me.done.append( 'pklasi')

    _head4standalone_file = '''
from sqlalchemy import *
from sqlalchemy.orm import *
meta = MetaData( 'sqlite:///')
meta.bind.echo=True)

#import logging
#logging.getLogger( 'sqlalchemy.orm').setLevel( logging.DEBUG)

try:
    from dbcook.baseobj import Base
except:
    try:
        from baseobj import Base
    except:
        class Base( object):
            idname = 'id'
            def __init__( me, **kargs):
                for k,v in kargs.iteritems(): setattr( me, k, v)
            def __str__( me):
                r = me.__class__.__name__ +'/id='+ str( getattr( me, me.__class__.idname))
                try: r += '/'+ str( me.name)
                except AttributeError: pass
                return r

#========= generated SA set-up:
'''
    _tail4standalone_file= '''
#========= eo generated SA set-up
'''

    def ptabli( me, meta):
        _state.do_columns=False
        alltbl = meta.tables.values() #[t1,t2,t3, t11,t12]
        alltbl.sort( key=lambda t:t.name)
        ind = '\n    '
        for t in alltbl:
            name = t.name
            varname = table_varname( t)
            t.tstr = varname
#            names[ t] = varname
            me.out += '%(varname)s = Table( %(name)r, meta,' % locals()
            me.out += ind + ind.join( [str(tstr(c))+',' for c in t.columns ]) + '\n)'
            me.nl()
        me.out += '''
meta.create_all()

'''
        _state.do_columns=True
        me.done.append( 'ptabli')

    def punion( me, pu):
        try:
            pu_tstr = pu.tstr2
        except AttributeError: return
        if 'HACK4inhtype':
            items = pu_tstr.split("':") #n_items+1
            n =0
            for i in items[1:]:
                if '.select(' in i or 'join(' in i:
                    n+=1
            if not n:
                typ = ''
                pu_tstr+= ' #concrete table'
            elif n == len(items)-1:
                pu_tstr = pu_tstr.replace( "'atype',", 'None,')
                pu_tstr+= ' #joined table'
            else:
                #pu_tstr.replace( "'atype',", 'NotImplementedError,')
                pu_tstr+= ' XXX  NotImplementedError - mixed joined and concrete inheritance; use polymunion.py'
        me.out += punion_varname(pu)+ ' = ' + pu_tstr
        me.nl()

    def pmapi( me, iterm):
        maps = [ m for m in iterm if isinstance( m, sqlalchemy.orm.Mapper)]
        maps.sort( key= lambda m: m.class_.__name__)
        for m in maps:
            pu = m.select_table
            if isinstance( pu, sqlalchemy.sql.Alias):  #CompoundSelect
                me.punion( pu)

            varname = mapper_varname( m)
            t2 = m.tstr2
            me.out += varname + ' = '+ t2
            me.nl()
            for p in m.iterate_properties:
                if isinstance( p, sqlalchemy.orm.PropertyLoader ):
                    k = p.key
                    t = tstr(p)
                    me.out += '%(varname)s.add_property( %(k)r, %(t)s )\n' % locals()
            me.nl()
        me.nl()
        me.done.append( 'pmapi')

    def psubs( me, iterm):
        maps = list( iterm)
        maps.sort( key= lambda (pu,m): m.class_.__name__)
        for pu,m in maps:
            if isinstance( pu, sqlalchemy.sql.Alias):  #CompoundSelect
                me.punion( pu)
            else:
                varname = 'psub_'+m.class_.__name__
                t2 = tstr(pu)
                me.out += varname + ' = ( ' + t2 + ' )'
                me.nl()
        me.done.append( 'psubs')


    _head = '''
from sa_gentestbase import *
'''
    classdef = '''
class AB( Test_SA):
'''
    head = _head + classdef
    tail = '''

if __name__ == '__main__':
    setup()
    unittest.main()
'''

    _head4gentestbase_alone = '''
from sa_gentestbase import *
setup()
Base.__repr__ = Base.__str__
#from polymunion import polymorphic_union

t = Test_SA( 'setUp' )
t.setUp()
meta = t.meta
'''

    @staticmethod
    def testcasedef2name( funcdef, stripstart =''):
        return funcdef.strip().replace( 'def '+stripstart,'').replace('( me):','')
    def testcase( me, funcdecl, error ='', metadecl= 'meta=me.meta', header =''):
        tab = 4*' '
        p = tab + 'def '+funcdecl.replace(', ','__').replace('=','_').replace('-','_').replace(' ','')+'( me):\n'
        p += header
        p += 2*tab + metadecl+'\n'
        p += 2*tab + me.out.replace('\n','\n'+2*tab)
        p = p.rstrip() + '\n'
        if error: p += '\n' +2*tab +'"""\n' + error +'\n\n"""\n'
        return p

    def populate( me, namespace, idname='id', reflector =lambda m: m.props, klas_translator =lambda klas: klas):
        Base = me.Base
        r = '''
#populate
'''
        s = [ (k,m) for k,m in namespace.iteritems() if isinstance( m, Base)]
        s.sort()
        names = {}
        for (k,m) in s:
            r += k +' = ' + klas_translator( m.__class__).__name__ +'()\n'
            names[ id(m)] = k
        for (k,m) in s:
            for a in reflector(m):
                v = getattr( m, a, None)
                if v:
                    if isinstance( v, Base): v = names[id(v)]
                    else: v = repr(v)
                    r += k +'.'+a + ' = ' + v + '\n'

        r+= '''
session = create_session()
''' + '\n'.join( 'session.save('+k+')' for k,m in s ) + '''
session.flush()

expects = [
'''
        for k,m in s:
            if '1' in k: continue
            klas = klas_translator( m.__class__)
            klasname = klas.__name__
            r += ('''\
    dict( klas= %(klasname)s, table= table_%(klasname)s, oid= %(k)s.%(idname)s, exp_single= str(%(k)s),
            exp_multi = [ ''' + ', '.join( 'str('+kk+')' for kk,mm in s if isinstance( mm, klas) ) + ''' ]),
''') % locals()

        r+= '''
]

me.query( session, expects, idname=%(idname)r )
''' % locals()

        me.out += r
        me.done.append( 'populate')



def duper4polymorphic_union( polymorphic_union, **kargs):
    return duper( polymorphic_union, otherstr=punion_varname, **kargs)

####################### now redefine these
Column = duper( sqlalchemy.Column)
ForeignKey= duper( sqlalchemy.ForeignKey)
UniqueConstraint= duper( sqlalchemy.UniqueConstraint)

#class Table( sqlalchemy.Table):
tdup = duper( sqlalchemy.Table.select)
def select4tbl( me, *args, **kargs):
    return tdup.dup( me, *args, **kargs)
sqlalchemy.Table.select = select4tbl
repr2tstr( sqlalchemy.Table)
Table = sqlalchemy.Table

repr2tstr( sqlalchemy.Column, tstr)

jdup = duper( sqlalchemy.sql.Join.select)
def select4join( me, *args, **kargs):
    return jdup.dup( me, *args, **kargs)
sqlalchemy.sql.Join.select = select4join

def repr2alias(me):
    baseselectable= me
    while isinstance( baseselectable, sqlalchemy.sql.Alias):
        baseselectable = baseselectable.selectable
        try:
            r = str( baseselectable.tstr )
            break
        except AttributeError: pass
    else:
        r = tstr2(me)
    return r + '.alias( '+ repr(me.name) +' )'

repr2tstr( sqlalchemy.sql.Alias, repr2alias)
repr2tstr( sqlalchemy.sql.Select)
repr2tstr( sqlalchemy.sql.Join)

select = duper( sqlalchemy.select)

mapper= duper( sqlalchemy.orm.mapper, otherstr=mapper_varname, nl='\n'+12*' ', nl4args='',
            no_kargs= dict(
                concrete=False,
                inherit_condition= None,
                inherits= None,
                polymorphic_on= None,
                select_table= None,
                polymorphic_identity= None,
                extension= None,
            ) )
join  = duper( sqlalchemy.join)
outerjoin  = duper( sqlalchemy.outerjoin)
relation = duper( sqlalchemy.orm.relation, nl='\n'+12*' ', nl4args='',
            no_kargs= dict(
                remote_side=None,
                post_update= False,
            ) )  #lazy=True,
backref = duper( sqlalchemy.orm.backref)
polymorphic_union= duper4polymorphic_union( sqlalchemy.orm.polymorphic_union )

# vim:ts=4:sw=4:expandtab
