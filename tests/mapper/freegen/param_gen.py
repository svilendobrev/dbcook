
def str2list( s):
    l = s.strip().split(' ')
    l = filter( lambda s: len(s), l) #TODO remove duplicates
    return l

def listify_elements( all):  # [' A  B C  ', ' a b'] --> [ ['A','B','C'], ['a','b']]
    res = [ str2list( s) for s in all]
    return res

def get_combs( all):
    all_elem = listify_elements( all)
    col_count = 1
    for elements in all_elem:
        col_count *= len( elements)
    seg_sz = col_count
    rows = []
    for elements in all_elem:
        seg_sz /= len( elements)
        pattern = []
        for e in elements:
            pattern.extend( seg_sz * [e])
        repeats = col_count / len( pattern)
        rows.append( repeats * pattern)

    for i in range( len( rows[ 0])):
        yield [ rows[ j][ i] for j in range( len( rows))]

from test.util import dictOrder
def order_dict( d):
    res = dictOrder()
    for k,v in d.iteritems():
        if isinstance( v, dict):
            res[k] = order_dict( v)
        else:
            res[k] = v
    return res


def gen_classes_schema( classes_unordered):
    classes = order_dict( classes_unordered)
    inh_sets = [ inh[ 0] for inh in classes.values()]  #i.e. [ 'concrete joined single', 'joined concrete']
    base_sets = [ inh[ 1] for inh in classes.values()] #i.e. [ 'Base A', 'B']

    for bases in get_combs( base_sets):
        reduced_inh_sets = list( inh_sets)
        for i in range( len( bases)):
            if bases[ i] == 'Base':
                reduced_inh_sets[ i] = 'concrete' #dont cycle inhs for Base

        for inhs in get_combs( reduced_inh_sets):
            assert len(inhs) == len( bases)
            schema = dictOrder()
            for klas, inh_data in classes.iteritems():
                i = classes.keys().index( klas)
                schema[ klas] = [ inhs[ i], bases[ i]]
            yield schema

def flat_link_valuesets( links_ordered):
    clas_links = links_ordered.values()  # [ {'Alink': 'A B'}, ... ]
    link_sets = []
    for dic in clas_links:
        for v in dic.values():
            link_sets.append( v)
    return link_sets

def gen_links_schema( links_ordered, link_sets):
    res = []
    for lcomb in get_combs( link_sets):
        schema = {}
        i = 0
        for klas, klas_links in links_ordered.iteritems():
            new = klas_links.copy()
            for lname in klas_links.keys():
                new[ lname] = lcomb[ i]
                i += 1
            schema[ klas] = new
        res.append( schema)
    return res


link_suffix = 'link'
def clasname_from_link( link):
    if link.endswith( link_suffix):
        return link[ : -len( link_suffix)]
    return None

def get_class_parents( classes, cls):
    res = []
    parent = cls
    while parent in classes:
        parent = classes[ parent][1]
        res.append( parent)
    return res

def refers( cls, target, links):
    refs = links.get( cls)
    if refs:
        own_link = cls + link_suffix
        if refs.get( own_link) == target:
            return True
    return False

def valid_params( classes, links):
    for k,v in links.iteritems(): # v == { 'Alink': 'A', 'Blink':'C', ...}
        parents = get_class_parents( classes, k)
        for link, ref in v.iteritems():
            parent = link[ : -len( link_suffix)] #clasname_from_link()
            if parent != k: # parent's link
                if parent not in parents:
                    return 'class %(k)s does not inherit %(parent)s; %(k)s cant have %(link)s' % locals()

                target_class = ref[0]
                if not refers( parent, target_class, links):
                    return 'cls %(k)s: %(link)s cannot refer to %(target_class)s' % locals()
    return None

from tests.util.context import table_inheritance_types as INH
known_inh_types = {
    'concrete': INH.CONCRETE,
    'joined'  : INH.JOINED,
    'single'  : INH.SINGLE,
    'default' : INH.DEFAULT,
}

def check4duplicates( s):
    l = str2list(s)
    return len( set(l) ) < len(l)

def check_classes( classes):
    for k,v in classes.iteritems():
        msg = 'classes: %(k)s: ' % locals()
        if not isinstance( v, list) or len(v) != 2:
            return msg + 'all classes.values() must be lists like [ inh_type, PARENT ]'

        for s in v:
            if check4duplicates( s):
                return msg + 'found duplicates'

        inh_types, bases = [ str2list( s) for s in v ]
        for inh in inh_types:
            if not inh in known_inh_types:
                s = ' '.join( known_inh_types.keys())
                return msg + 'unknown type of inheritance: %(inh)s\nuse any of: %(s)s' % locals()

        for b in bases:
            if b == k:
                return msg + 'a class cannot inherit itself'
    return None

def check_links( classes, links):
    msg_no_class = 'no such class "%s" is declared in classes'
    for k,v in links.iteritems():
        msg = 'links: class %(k)s: ' % locals()
        if not isinstance( v, dict):
            return msg + 'all links.values() must look like dict(Alink="A B C", Blink="A B")'

        if k not in classes:
            return msg + msg_no_class % k

        for link, refs in v.iteritems():    # 'Alink', 'A B C'
            msg2 = msg + 'link %(link)s: ' % locals()

            if check4duplicates( refs):
                return msg2 + 'found duplicates'

            cls = clasname_from_link( link)
            if not cls:
                return msg2 + 'must end with "%s"' % link_suffix
            if cls not in classes:
                return msg2 + msg_no_class % cls

            is_own_link = cls == k
            if not is_own_link: #parent's link
                try:
                    parent_links = links[ cls]
                    parent_own_link = parent_links[ link]
                except KeyError:
                    return msg2 + 'parent %(cls)s does not have its own link and child can not define such' % locals()
                parent_targets = [ t[0] for t in str2list( parent_own_link) ]

            targets = str2list( refs)
            for t in targets:
                t_cls = t[0]
                if not t_cls.isupper():
                    return msg2 + 'use only capital letters for target classes'
                if not t_cls in classes:
                    return msg2 + msg_no_class % t_cls
                if not is_own_link and t_cls not in parent_targets:
                    return msg2 + 'parent %(cls)s can not refer to %(t)s' % locals()
    return None

def check_input( classes, links):
    if not isinstance( classes, dict) or not isinstance( links, dict):
        return 'classes and links must be instance of dict'

    err = check_classes( classes) or check_links( classes, links)
    return err

def gen_case_params( classes, links):
    err = check_input( classes, links)
    if err:
        print '======================================================'
        print 'INPUT ERROR:', err
        print '======================================================'
        return

    links_ordered = order_dict( links)
    link_sets = flat_link_valuesets( links_ordered)
    all_link_schemas = gen_links_schema( links_ordered, link_sets)

    for clas_schema in gen_classes_schema( classes):
        for links_schema in all_link_schemas:
            err = valid_params( clas_schema, links_schema)
            if err:
                #print err, '(skipping ...)'
                continue
            yield dict( classes = clas_schema, links = links_schema)

def str_schema( classes, links):
    res = ''
    for k,v in classes.iteritems():
        bracket = v[0] == 'concrete' and '()' or '<>'
        res += k + bracket[0] + v[1] + bracket[1] + ' '

    res += '| '
    for k,v in links.iteritems():
        pfx = k
        res += ' '.join( pfx + link + '->' + ref.ljust(2)
                            for link, ref in v.iteritems() )
        res += ' | '
    return res

# vim:ts=4:sw=4:expandtab
