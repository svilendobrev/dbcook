#$Id$

__issubclass = issubclass
def issubclass( obj, klas):
    from types import ClassType
    return isinstance( obj, (type, ClassType)) and __issubclass(obj, klas)

# vim:ts=4:sw=4:expandtab
