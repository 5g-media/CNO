#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  5 23:40:38 2018

@author: miguelrocha
"""

import pulp
from netcore.topology import Network
from netcore.demands import Demands
from netcore.loads import Loads
from pulp.solvers import CPLEX_PY
import math
import timeit

class CongestionOptimization:
    
    def __init__(self, network, demands = None):
        self.network = network
        self.demands = demands
        self.problem = None
        self.f_var = None
        self.phiuncap = None
        
    ## previous_loads: dictionary edge_id -> load
    def setup_problem(self, obj_func = "mlu", single_path = True, enforce_cap_const = False, 
                      previous_loads = None, fail_links = []):
        
        self.prob = pulp.LpProblem("Optimal Congestion", pulp.LpMinimize)
        V = self.network.list_nodes()
        L = self.network.link_ids()
        D = self.demands.list_e2e_demands()
        self.single_path = single_path

        for lf in fail_links:
            L.remove(lf)

        # Define Variables
        if single_path: cat = "Binary"
        else: cat = "Continuous"
        self.f_var = pulp.LpVariable.dicts("f",((e,i,j) for e in L for (i,j) in D),lowBound=0, upBound=1, cat=cat)
        self.loads = pulp.LpVariable.dicts("l", (e for e in L) ,lowBound=0, cat="Continuous")
        if obj_func == "mlu":
            congestion = pulp.LpVariable('C', lowBound=0, cat='Continuous')
        if obj_func == "fortz":
            phis = pulp.LpVariable.dicts("phi", (e for e in L) ,lowBound=0, cat="Continuous") 

        # Define Objective Function
        if obj_func == "mlu": 
            self.prob += congestion
        elif obj_func == "alu":
            self.prob += (1.0/len(L)) * pulp.lpSum([self.loads[e] * (1.0/self.network.link_capacity(e))] for e in L) 
        elif obj_func == "fortz":
            phi_u = self.phi_uncap()
            self.prob += (1.0/ phi_u) * pulp.lpSum([phis[e]] for e in L) 
        else:
            print("OF not defined")
            return None
    
        # Flux conservation
        for (i,j) in D:
            i_in = self.network.in_edges(i)
            i_out = self.network.out_edges(i)
            j_in = self.network.in_edges(j)
            j_out = self.network.out_edges(j)
            for lf in fail_links:
                if lf in i_in: i_in.remove(lf)
                if lf in i_out: i_out.remove(lf)
                if lf in j_in: j_in.remove(lf)
                if lf in j_out: j_out.remove(lf)
        
            self.prob += pulp.lpSum([self.f_var[(e,i,j)] for e in i_in]) == 0
            self.prob += pulp.lpSum([self.f_var[(e,i,j)] for e in i_out]) == 1
            self.prob += pulp.lpSum([self.f_var[(e,i,j)] for e in j_in]) == 1
            self.prob += pulp.lpSum([self.f_var[(e,i,j)] for e in j_out]) == 0

        for k in V:
            for (i,j) in D:
                if i != k and j != k:
                    k_in = self.network.in_edges(k)
                    k_out = self.network.out_edges(k)
                    for lf in fail_links:
                        if lf in k_in: k_in.remove(lf)
                        if lf in k_out: k_out.remove(lf)                
                    self.prob += pulp.lpSum([self.f_var[(e,i,j)] for e in k_out]) - pulp.lpSum([self.f_var[(e,i,j)] for e in k_in]) == 0              

        for e in L:
            if previous_loads is None: pl = 0
            else: pl = previous_loads[e]            
            self.prob += self.loads[e] - (pulp.lpSum([self.demands.demands[(i,j)]*self.f_var[(e,i,j)] for (i,j) in D]) + pl) == 0
 
        if obj_func == "mlu":
            for e in L:
                cap = self.network.link_capacity(e)
                self.prob += self.loads[e] * (1.0/cap) <= congestion
#                if previous_loads is None: pl = 0
#                else: pl = previous_loads[e]
#                self.prob += (pulp.lpSum([self.demands.demands[(i,j)]*self.f_var[(e,i,j)] for (i,j) in D]) + pl) / cap <= congestion
#    
        if obj_func == "fortz":
            for e in L:
                cap = self.network.link_capacity(e)
                self.prob += phis[e] - self.loads[e] >= 0
                self.prob += phis[e] - 3 * self.loads[e] >= (-2.0/3.0 * cap)
                self.prob += phis[e] - 10 * self.loads[e] >= (-16.0/3.0 * cap)
                self.prob += phis[e] - 70 * self.loads[e] >= (-178.0/3.0 * cap)
                self.prob += phis[e] - 500 * self.loads[e] >= (-1468.0/3.0 * cap)
                self.prob += phis[e] - 5000 * self.loads[e] >= (-16318.0/3.0 * cap)
                
        # Capacity constraints
        if enforce_cap_const:
           for e in L:
               cap = self.network.link_capacity(e)
               self.prob += self.loads[e] <= cap
               
               #cap = self.network.link_capacity(e) - previous_loads[e]
               #self.prob += pulp.lpSum([self.demands.get_demands(i,j)*self.f_var[(e,i,j)] for (i,j) in D]) <= cap

        return self.prob


    def setup_single_flow(self, flow_src, flow_dest, flow_val, obj_func = "mlu", 
                          enforce_cap_const = False, previous_loads = None,
                          fail_links = []):
        self.demands = Demands(self.network, None)
        self.demands.add_demands(flow_src, flow_dest, flow_val)
        return self.setup_problem(obj_func, True, enforce_cap_const, previous_loads, fail_links)
 
    def solve_problem(self,solver = None):
        if self.prob is None: self.setup_problem()
        if solver is None: 
            self.prob.solve()            
        elif solver == "cplex":
            #self.prob.solve(CPLEX_PY())
            self.prob.solve(CPLEX_PY(mip=self.single_path, msg=False))
        #print("Status:", pulp.LpStatus[self.prob.status])
        if self.prob.status != pulp.constants.LpStatusOptimal:
            return None

        return self.prob.variables(), pulp.value(self.prob.objective)
      
    def write_problem(self, filename = "problem.lp"):
        self.prob.writeLP(filename)

    def print_optimal_sol(self):
        for v in self.prob.variables():
            print(v.name, " = ", v.varValue)

    def get_links_single_path(self, src, dest):
        res = []
        L = self.network.link_ids()
        for e in L:
            if (e,src,dest) in self.f_var and pulp.value(self.f_var[(e,src,dest)]) == 1:
                res.append(e)
        return res

    def get_all_used_links(self):
        res = {}
        L = self.network.link_ids()
        D = self.demands.list_e2e_demands()
        for e in L:
            for (i,j) in D:
                if pulp.value(self.f_var[(e,i,j)]) > 0:
                    res[(e, i, j)] = pulp.value(self.f_var[(e,i,j)])
        return res

    def route_single_flow(self, src, dest, demand, obj_func = "mlu", enforce_cap_const = False, 
                          previous_loads = None, fail_links = []):
        
        self.setup_single_flow(src, dest, demand, obj_func, enforce_cap_const, 
                               previous_loads, fail_links)
        res = self.solve_problem()
        if res is None: ## check this later !!!!
            self.setup_single_flow(src, dest, demand, "mlu", enforce_cap_const, 
                                   previous_loads, fail_links)
            res = self.solve_problem()
        
        return self.get_links_single_path(src,dest), res[1]
        
   
    def phi_uncap(self):
        res = 0.0
        D = self.demands.list_e2e_demands()
        for (i,j) in D:
            dist_1 = self.network.dist_unit_weights(i,j)
            res += dist_1 * self.demands.demands[(i,j)]
        return res
    
    def sp_congestion(self, weights, of = "mlu", compute_links_used = True):
        links_used = {}
        loads = Loads(self.network)
        D = self.demands.list_e2e_demands()
        paths = self.network.all_shortest_paths(weights)
        for p in paths:
            src = p[0]
            for dst in p[1].keys():
                if (src, dst) in D:
                    lp = self.network.get_links_from_path(p[1][dst]) 
                    loads.add_loads_path(lp, self.demands.demands[(src,dst)])
                    if compute_links_used:
                        for e in lp: links_used[(e, src, dst)] = 1
        if of == "mlu":
            of = loads.mlu()[0]
        elif of == "alu":
            of = loads.alu()
        elif of == "fortz":
            if self.phiuncap is None:
                self.phiuncap = self.phi_uncap()
            of= loads.fortz_of(self.phiuncap)
        return of, links_used

    def sp_congestion_ties(self, weights, of = "mlu", compute_links_used = True):
        links_used = {}
        loads = Loads(self.network)
        D = self.demands.list_e2e_demands()
        
        #start = timeit.default_timer()
        paths = self.network.all_shortest_paths_with_ties(weights)
        #stop = timeit.default_timer()
        #print('Time sp: ', stop - start) 
        
        #start = timeit.default_timer()
        dists = {}
        for n1 in self.network.nodes.keys():
            dists_src,_  = self.network.dijkstra(n1, weights = weights)
            for n2 in dists_src.keys():
                dists[(n1,n2)] = dists_src[n2]
        #stop = timeit.default_timer()
        #print('Time dists: ', stop - start) 

        #start = timeit.default_timer()
        out_edges = self.network.all_out_edges()
        for (s,d) in D:
            paths_sd = paths[(s,d)]
            self.split_paths_sd (s, d, paths_sd, links_used, dists, out_edges)
        #stop = timeit.default_timer()
        #print('Time split: ', stop - start) 

        loads.loads_from_link_fvars(links_used, self.demands)

#        for (s,d) in D:
#            paths_sd = paths[(s,d)]
#            num_paths = len(paths_sd)
#            for p in paths_sd:
#                lp = self.network.get_links_from_path(p) 
#                loads.add_loads_path(lp, self.demands.demands[(s,d)]/num_paths)
#                if compute_links_used:
#                    for e in lp: 
#                        if (e,s,d) in links_used:
#                            links_used[(e, s, d)] += 1.0/num_paths
#                        else:
#                            links_used[(e, s, d)] = 1.0/num_paths
        if of == "mlu":
            of = loads.mlu()[0]
        elif of == "alu":
            of = loads.alu()
        elif of == "fortz":
            if self.phiuncap is None:
                self.phiuncap = self.phi_uncap()
            of= loads.fortz_of(self.phiuncap)
        return of, links_used


    def split_paths_sd (self, src, dst, paths_sd, links_used, dists, out_edges):
        
        links_paths = []
        for p in paths_sd:
            lp = self.network.get_links_from_path(p)
            links_paths.append(lp)
        
        if len(links_paths) == 1:
            for link in links_paths[0]:
                links_used[(link, src, dst)] = 1.0
            return None
        
        if len(paths_sd) == 2:
            for lp in links_paths:
                for link in lp:
                    if (link, src, dst) in links_used:
                        links_used[(link, src, dst)] = 1.0
                    else:
                        links_used[(link, src, dst)] = 0.5
            return None
        
        cur = [ (src,1.0) ]
        while cur != []:
            if len(cur) == 1:
                cur_node, cur_val = cur[0]
            else:
                min_dist = math.inf
                cur_node = None
                cur_val = None
                for (node, p) in cur:
                    if dists[(src,node)] < min_dist: 
                        min_dist = dists[(src,node)]
                        cur_node = node 
                        cur_val = p
            cur.remove( (cur_node, cur_val) )

            if cur_node != dst:
                all_out_links = out_edges[cur_node]
                out_links_sp = []
                for lp in links_paths:
                    for link in lp:
                        if link not in out_links_sp and link in all_out_links:
                            out_links_sp.append(link)
                
                val = cur_val * (1.0 / len(out_links_sp))
                for l in out_links_sp:
                    links_used[(l, src, dst)] = val
                
                for l in out_links_sp:
                    out_node = self.network.edges[l][1]
                    exists = False
                    for (n,v) in cur:
                        if n == out_node:
                            exists = True
                            #cur[i] = (n, v + val)
                            cur.remove((n,v))
                            cur.append((n, v + val))
                    if not exists:
                        cur.append( (out_node, val) )
        
        return None
        

    
### Testing ### 
 
def test1():
    n = Network("../Networks/germany50.txt", "sndlib")
    d = Demands(n, "../Networks/germany50.txt")
    d.multiply_demands(0.2)
    p = CongestionOptimization(n, d)
    p.setup_problem("mlu", False, False)
    opt_vars, opt_of = p.solve_problem("cplex")
    #opt_vars, opt_of = p.solve_problem()
    print("Optimal", opt_of)
    #for v in opt_vars:
    #    if v.varValue > 0:
    #        print (v.name, "=", v.varValue)
    #p.write_problem()


def test2():
    n = Network("../Networks/isno_5_2")
    print(n)
    p = CongestionOptimization(n)
    links, of = p.route_single_flow("1","3",4600)
    print(of)
    print(links)

    l = Loads(n)
    l.add_loads_path(links, 4600) 
    
    links, of = p.route_single_flow("0","4",1000, previous_loads = l)
    print(of)
    print(links)
    
    l.add_loads_path(links, 1000)  
    
    links, of = p.route_single_flow("1","3",3000, previous_loads = l)
    print(of)
    print(links)


def test3():
    n = Network("../Networks/isno_5_2")
    print(n)
    d = Demands(n, None)
    d.add_demands("1","3",8000)
    p = CongestionOptimization(n,d)
    p.setup_problem("mlu", False, False)
    opt_vars, opt_of = p.solve_problem()
    p.print_optimal_sol()
    print(opt_of)
    print(p.get_links_single_path("1","3"))

def test4():
    n = Network("../Networks/isno_30_4")
    d = Demands(n, "../Networks/isno_30_4-D0.3.dem", "csv")
    p = CongestionOptimization(n,d)
    p.setup_problem("fortz", False, False)
    opt_vars, opt_of = p.solve_problem()
    print(opt_of)
    
    links = p.get_all_used_links()
    loads = Loads(n)
    loads.loads_from_link_fvars(links, d)
    phi_u = p.phi_uncap()
    of = loads.fortz_of(phi_u)
    print(of)

if __name__ == '__main__': 
    test4()
    #test2()
    #test3()
    #test4()
    