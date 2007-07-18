#$Id$
# -*- coding: cp1251 -*-

import kjbuckets as kj

def prngraph(g):
    print [ '%s:%s' % t for t in g.items()]

class Amin:
    '''find minimal set of edges to cut from a (cyclic) directed graph to break it into acyclic ones'''

    #n_del_edges = 0
    #n_cycles = 0
    def __init__( me, g, **kargs):
        me.cut = None
        me.cost = 0
        me.edge_cost = None
        me.calc_mincut( g, **kargs)

    def _find( me, g, cut =kj.kjGraph(), cost4cut =0 ):
        mincost = me.cost
        #me.n_cycles +=1
        cycles = g & ~g.tclosure()      #get core-cycle(s)
#        print mincost
#        prngraph( cycles)
        if not cycles:
            if cut:
                if not mincost or mincost > cost4cut:
                    mincost = me.cost = cost4cut
                    me.cut = cut.items()  #copy
                #else: print 'ignoring',
                #print 'cut:', cost4cut,':',
                #prngraph(cut)
        else:
            for edge in cycles.items():
                #XXX is it cheaper to cut 1 single links than 1 double-link? if not, then multiplicity doesnot matter; cost=1
                #XXX and, is it same to cut 2 single links than 1 double-link???
                c = me.edge_cost[ edge]

                cost = cost4cut+c
                if mincost and cost >= mincost:
                    #print 'abandon', cut
                    continue
                #me.n_del_edges + =1
                cut.add( *edge)
                g = cycles - cut        #delete edge
                mincost = me._find( g, cut, cost)   #update mincost
                cut.delete_arc( *edge)  #restore
        return mincost

    def calc_mincut( me, g, uncutables =(), exclude_selfrefs =True, count_multiples =True):
        edge_cost = me.edge_cost = {}
        for edge in g:
            if edge in uncutables: cost = len(g)
            else:
                cost = count_multiples and g.count(edge) or 1
            edge_cost[ edge] = cost

        g = kj.kjGraph( g)

        #prngraph( g & ~g.tclosure() ) #- core-cycle

        if exclude_selfrefs:
    #        self_refs = kj.kjSet(g).ident() & g
    #        g = g - self_refs
             g = g - kj.kjSet(g).ident()

        me._find( g)
#        print me.n_del_edges, me.n_cycles



if __name__ == '__main__':

    g_0     = [ (1,2), (2,3), (3,4), ]
    g_self  = [ (1,2), (2,3), (3,3), ]
    g_1a    = [ (1,2), (2,3), (3,2), ]
    g_1b    = [ (1,2), (2,3), (3,1), ]

    g_2     = [ (1,2), (2,3), (3,1),
                (11,12), (12,11),
            ]

    g_connect = [ (12,1), (2,11), ]
    g_multiple = [ (3,1), (3,1), (11,12) ]

    for gcost, gg in {
                0: [ g_0, g_self ],
                1: [ g_1a, g_1b, ],
                2: [ g_2,
                    g_2 + g_connect,
                    g_2 + g_multiple,
                    g_2 + g_connect + g_multiple,
                    g_2 + g_self,
                    ],
            }.iteritems():
        for g in gg:
            print g
            a = Amin( g)
    #        print a.edge_cost
            print '   :', a.cut, 'cost:', a.cost
            assert a.cost == gcost
    print 'ok'
# vim:ts=4:sw=4:expandtab
