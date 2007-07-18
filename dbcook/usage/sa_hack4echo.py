#$Id$
# -*- coding: cp1251 -*-
from util.hacksrc import hacksrc
from sqlalchemy import sql, ansisql

def accept_visitor(self, visitor):
    try: visitor.tablevel += 1
    except: pass
    self._old_accept_visitor( visitor)
    try: visitor.tablevel -= 1
    except: pass

Select = sql.Select
Select._old_accept_visitor = Select.accept_visitor
Select.accept_visitor = accept_visitor

ANSICompiler = ansisql.ANSICompiler
#ANSICompiler.tablevel = -1

def traverse(self, obj, stop_on=None):
    stack = [(obj,0)]   #X
    traversal = []
    xtraversal = []     #X
    while len(stack) > 0:
        t,lvl = stack.pop()     #X
        if stop_on is None or t not in stop_on:
            traversal.insert(0, t)
            xtraversal.append( lvl )    #X
            for c in t.get_children(**self.__traverse_options__):
                stack.append( (c,lvl+isinstance(t,Select) ) )   #X
    for target in traversal:
        xtra = xtraversal.pop() #X
        v = self
        while v is not None:
            v.tablevel = xtra   #X
            target.accept_visitor(v)
            v = getattr(v, '_next', None)
    return obj
sql.ClauseVisitor.traverse = traverse

#tabbing1 = '\\n"+self.tablevel*4*" "+'
tabbing = '\\n"+tabbing'

for func in ANSICompiler.visit_select, ANSICompiler.visit_compound_select:
    hacksrc( func,
        [
        ( '):\n', '''):
        tabbing = self.tablevel*4*" "
''', 1)
    ] + [
        ('\\n'+word, word )     for word in 'SELECT FROM WHERE ORDER GROUP HAVING'.split()    #kill pre-newlines
    ] + [
        (' '+word, word )       for word in 'SELECT FROM WHERE ORDER GROUP HAVING'.split()    #kill pre-spaces
    ] + [
        ('"'+word, '"'+tabbing+'+"'+word )   for word in 'FROM WHERE ORDER GROUP HAVING'.split()
    ] + [
        ('"'+word, 'tabbing+"'+word )   for word in 'SELECT'.split()
    ] + [
        ('"("', '"(\\n"', 5 ),  # w/o it nested select appears on the same row

        ('")"', '"'+tabbing+'[:-4]+")"', 5 ),

        ('cs.keyword', '"'+tabbing+' + cs.keyword + "'+tabbing ),      #visit_compound_select
    ] + 0*[   #newline at end ?
        ('self.for_update_clause(select)', 'self.for_update_clause(select) +"\\n"'), #visit_select
        ('self.visit_select_postclauses(cs)', 'self.visit_select_postclauses(cs) +"\\n"'), #visit_compound_select
    ],

    None, allow_not_found=1,
    #debug=1,
)

#hacksrc( ANSICompiler.limit_clause, [

# vim:ts=4:sw=4:expandtab
