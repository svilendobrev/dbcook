#$Id$
# -*- coding: cp1251 -*-
from dbcook.util.hacksrc import hacksrc
import sqlalchemy

from dbcook.util.attr import find_valid_fullname_import
compiler = find_valid_fullname_import( '''
    sqlalchemy.sql.compiler.DefaultCompiler
''')

for func in compiler.visit_select, compiler.visit_compound_select:
    hacksrc( func,
        1*[
        ( '):\n', '''):
        tabbing = len(self.stack)*4*" "
''', 1)
    ] + 0*[
        ( 'self.stack.append(stack_entry)', '''self.stack.append(stack_entry)
        tabbing = len(self.stack)*4*" "
''', 1)
    ] + [
        ('\\n'+word, word )     for word in 'SELECT FROM WHERE ORDER GROUP HAVING'.split()    #kill pre-newlines
    ] + [
        (' '+word, word )       for word in 'SELECT FROM WHERE ORDER GROUP HAVING'.split()    #kill pre-spaces
    ] + [
        ('"'+word, '"\\n"+tabbing+"'+word )   for word in 'FROM WHERE ORDER GROUP HAVING'.split()
    ] + [
        ('"'+word, 'tabbing+"'+word )   for word in 'SELECT'.split()
    ] + [
        ('"("', '"(\\n"', 5 ),  # w/o it nested select appears on the same row

        ('")"', '"\\n"+tabbing[:-4]+")"', 5 ),

        ('cs.keyword + " "', '"\\n"+tabbing + cs.keyword + "\\n"'),      #visit_compound_select
    ] + 0*[   #newline at end ?
        ('self.for_update_clause(select)', 'self.for_update_clause(select) +"\\n"'), #visit_select
        ('self.visit_select_postclauses(cs)', 'self.visit_select_postclauses(cs) +"\\n"'), #visit_compound_select
    ],

    None, allow_not_found=1,
    #debug=1,
)

# vim:ts=4:sw=4:expandtab
