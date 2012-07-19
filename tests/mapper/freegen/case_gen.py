
from param_gen import clasname_from_link, known_inh_types

class NamespaceGen( object):
    def __init__( me, context, classes, clasref):
        me.classes_descr = classes
        me.links_descr = clasref
        me.context = context

    def make_classes( me):
        Base = me.context.Base
        base_metaclass = hasattr( Base, '__metaclass__') and Base.__metaclass__ or type
        class Dyn_factory( base_metaclass):
            def __new__( meta, name, bases, adict):
                try:
                    dynamics = adict['_DYNAMIC_']
                    del adict['_DYNAMIC_']
                    adict.update( dynamics )
                except KeyError: pass
                return base_metaclass.__new__( meta, name, bases, adict)

        all = dict()
        for klas, inh_data in me.classes_descr.iteritems():
            dyn_attrs = {}
            if klas in me.links_descr:
                for link, target_class in me.links_descr[ klas].iteritems():
                    if clasname_from_link( link) == klas: #make only my own link
                        if target_class not in me.classes_descr: # like A1, B2, C1 ...
                            target_class = target_class[0]
                        dyn_attrs[ link] = me.context.Reference( target_class)
            dyn_attrs['ime'+klas] = me.context.Text()

            inh_type, base_name = inh_data
            #print known_inh_types[ inh_type]
            class TemplateClass( base_name == 'Base' and Base or all[ base_name] ):
                __metaclass__ = Dyn_factory
                auto_set = False
                DBCOOK_inheritance = known_inh_types[ inh_type]
                DBCOOK_has_instances = True

                _DYNAMIC_ = dyn_attrs

            TemplateClass.__name__ = klas # unused
            all[ klas] = TemplateClass
        return all

    def make_populate_code( me):
        code = """
def populate():"""

        created_instances = []
        for klas in me.classes_descr:
            obj_name = klas.lower()
            created_instances.append( obj_name)
            code += """
    %(obj_name)s = %(klas)s()
    %(obj_name)s.ime%(klas)s = 'ime %(klas)s'""" % locals()

        for klas, links in me.links_descr.iteritems():
            obj_name = klas.lower()
            for link_name, target_class in links.iteritems():
                target_obj = target_class.lower()

                if target_obj not in created_instances: # like a1, b1, c2 ...
                    created_instances.append( target_obj)
                    klas_name = target_class[ 0] # A1 -> A
                    code += """
    %(target_obj)s = %(klas_name)s()
    %(target_obj)s.ime%(klas_name)s = 'ime %(target_class)s'""" % locals()

                code += """
    %(obj_name)s.%(link_name)s = %(target_obj)s""" % locals()
        code += """
    return locals()"""
        return code

    def make_namespace( me):
        nms = me.make_classes()
        #print 'ZZZZZZZZZZZZZZZZZZ', nms
        exec ( me.make_populate_code(), nms)
        return nms



# vim:ts=4:sw=4:expandtab
