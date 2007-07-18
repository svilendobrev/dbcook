#$Id$
# -*- coding: cp1251 -*-

def test_case_factory( case_params, TestCaseClass):
    class Case2Test( TestCaseClass):
        params = case_params
        name = case_params.descr
    return Case2Test

import unittest

class Case( unittest.TestCase):
    name = None
    params = None

    def __str__( me):
        try:
            return "  %s (%s)" % (me._testMethodName, me.name )
        except AttributeError:
            return "  %s (%s)" % (me._TestCase__testMethodName, me.name )

def get_test_suite( cases, TestCaseClass):
    cases = [ unittest.defaultTestLoader.loadTestsFromTestCase(
                test_case_factory( c, TestCaseClass) ) for c in cases
            ]
    return unittest.TestSuite( cases)

# vim:ts=4:sw=4:expandtab
