#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 24 18:49:20 2018

@author: miguelrocha
"""

#import sys
#sys.path.append('..')

from users import Users
from services import ServicesTree
from servers import Servers
from netcore.topology import Network
from netcore.demands import Demands
from congopt.congoptim import CongestionOptimization
from netcore.loads import Loads

class CompositeServices:
    
    def __init__(self, network, tree, servers, users, weights = None, opt_cong = False, congestion_cost = False,
                 cong_opt_method = "milp", cong_of = "mlu"):
        self.network = network
        self.tree = tree
        self.servers = servers
        self.users = users
        self.congestion_cost = congestion_cost   ## specifies if a cost for congestion is used in the OF
        self.opt_cong = opt_cong  ## specifies if routing is optimized for congestion
        self.cong_opt_method = cong_opt_method
        self.cong_of = cong_of
        if weights is None:
            self.weights = {}
            self.set_default_weights()
        else: 
            self.weights = weights
        if not self.opt_cong: ## if routing not optimized consider paths from SP delays
            self.delays, self.del_paths = self.network.calculate_sp_delays()            
        
    def __str__(self):
        res = ""
        res += self.network.__str__()
        res += self.tree.__str__()
        res += self.servers.__str__()
        res += self.users.__str__()
        return res
    
    def set_default_weights(self):
        if self.congestion_cost:
            self.weights["fh"] = 0.2
            self.weights["e2e"] = 0.2
            self.weights["cost"] = 0.3
            self.weights["congestion"] = 0.3 
        else:
            self.weights["fh"] = 0.25
            self.weights["e2e"] = 0.25
            self.weights["cost"] = 0.5
    
    def set_weights(self, w):
       if self.congestion_cost:
            self.weights["fh"] = w.get("fh",0.2)
            self.weights["e2e"] = w.get("e2e", 0.2)
            self.weights["cost"] = w.get("cost", 0.3)
            self.weights["congestion"] = w.get("congestion", 0.3) 
       else:
            self.weights["fh"] = w.get("fh",0.25)
            self.weights["e2e"] = w.get("e2e", 0.25)
            self.weights["cost"] = w.get("cost", 0.5)
    
    ### need to update this to consider capacity ###
    def var_cost (self, user_id, service_id, server_id):
        demand = self.users.get_demand(user_id)
        serv_cost = self.servers.get_var_cost(service_id, server_id)
        return demand * serv_cost
    
    def sum_var_costs (self, assig):
        res = 0
        for u in self.users.get_users():
            for s in assig[u].keys():
                res += self.var_cost(u, s, assig[u][s])    
        return res
    
    def sum_fixed_costs (self, dic_assig):
        aux_dic = {}
        for u in dic_assig.keys():
            for s in dic_assig[u].keys():
                if (s,dic_assig[u][s]) not in aux_dic:
                    aux_dic[(s,dic_assig[u][s])] = self.servers.get_fixed_cost(s, dic_assig[u][s])    
        return sum(aux_dic.values())

    def get_delays(self, src, dest):
        if src != dest:
            return self.delays[(src, dest)]
        else:
            return 0

    def get_user_delays(self, server_id, user_id):
        user_node = self.users.get_user_node(user_id)
        return self.get_delays(server_id, user_node)
        

    def get_fh_latency(self, user_id, user_assig):
        roots = self.tree.root_service()
        fh = self.get_user_delays(user_assig[roots],user_id)
        return fh

    def latency_user(self, user_id, user_assig):
        root = self.tree.root #_service()
        delays = {}
        delays[root] = 0
        current = [root]
        while current != []:
            node = current.pop()
            neigs = self.tree.branches(node)
            for n in neigs:
                if self.tree.has_loops(): 
                    src = user_assig[remove_index_fromid(node)]
                    dest = user_assig[remove_index_fromid(n)]
                else: 
                    src = user_assig[node]
                    dest = user_assig[n]
                if dest == src: lat = 0
                else: lat = self.get_delays(dest,src)
                delays[n] = delays[node] + lat
            current.extend(neigs)
        fh = self.get_fh_latency(user_id,user_assig)
        return max(delays.values()) + fh

    def latency_pen_all_users(self, dic_assig):
        dic_lat_penalties = {}
        for u in dic_assig.keys():
            lat = self.latency_user(u, dic_assig[u])
            minlat, maxlat = self.users.get_latencies(u)
            dic_lat_penalties[u] = self.latency_norm_penalty(lat, minlat, maxlat)
        return sum(dic_lat_penalties.values())/len(dic_assig.keys())

    def firsthop_penalties_all_users(self, dic_assig):
        dic_fh_pen = {}
        root = self.tree.root_service()
        for u in dic_assig.keys():
            root_server = dic_assig[u][root]
            fh_lat = self.get_user_delays(root_server,u)
            minlat, maxlat = self.users.get_fh_latencies(u)     
            dic_fh_pen[u] = self.latency_norm_penalty(fh_lat, minlat, maxlat)
        return sum(dic_fh_pen.values())/len(dic_assig.keys())

# objective function

    def of_normalized_penalty(self, serv_assig, printcomps = False, mincost = None,
                              sp_weights = None, return_dic = False):
        if mincost is None: mincost = self.min_cost()
        
        dic_assig = serv_assig.dic_assig
        fix_costs = self.sum_fixed_costs(dic_assig)
        var_costs = self.sum_var_costs(dic_assig)
        total_costs = fix_costs + var_costs
        cost_pen = self.cost_norm_penalty(total_costs, mincost)
        if printcomps:
            print("Var. costs: ", var_costs)
            print("Fixed costs: ", fix_costs)
            print("Total costs: ", total_costs)
            print("Cost Penalty: ", cost_pen)
        
        if self.opt_cong or self.congestion_cost:
            dem = self.generate_e2e_demands(dic_assig)
            
        if self.opt_cong:
            if self.cong_opt_method == "milp":
                cong, paths = self.best_routing(dic_assig, dem, self.cong_of)
            elif self.cong_opt_method == "sp":
                cong, paths = self.sp_routing(dic_assig, sp_weights, dem, self.cong_of)
            if printcomps: 
                print("Congestion: ", cong)
            self.update_delays_from_routing(paths)
        elif self.congestion_cost:
                l = Loads(self.network)
                l.add_loads_from_paths(self.del_paths, dem)
                if self.cong_of == "mlu": cong = l.mlu()[0]
                elif self.cong_of == "alu": cong = l.alu()
                elif self.cong_of == "fortz": 
                    co = CongestionOptimization(self.network,dem)
                    phiu = co.phi_uncap()
                    cong = l.fortz_of(phiu) - 1.0
                else: 
                    print("OF not defined")
                    return None
                if printcomps: 
                    print("Congestion: ", cong)

        e2e_pen = self.latency_pen_all_users(dic_assig)
        fh_pen = self.firsthop_penalties_all_users(dic_assig)
        
        if printcomps:
            print("E2E penalties: ", e2e_pen)
            print("FH penalties: ", fh_pen)
        
        if return_dic:
            res = {}
            res["fh"] = fh_pen
            res["e2e"] = e2e_pen
            res["cost"] = cost_pen
            if self.congestion_cost: res["cong"] = cong
            return res
#            if self.congestion_cost:
#                return ( (fh_pen+ e2e_pen)/2.0, cost_pen, cong)
#            else:
#                return ( (fh_pen+ e2e_pen)/2.0, cost_pen)
        else:
            if self.congestion_cost:
                return (self.weights["cost"]*cost_pen + self.weights["e2e"]*e2e_pen + 
                        self.weights["fh"]*fh_pen + self.weights["congestion"]* cong)
            else:
                return (self.weights["cost"]*cost_pen + self.weights["e2e"]*e2e_pen + 
                        self.weights["fh"]*fh_pen)

# auxiliary functions for objective function

    def utility(self, lat, minlat, maxlat):
        utility = 0
        if lat <= minlat: 
            utility = 1
        elif lat > maxlat: utility = -1
        else: utility = float(-lat + maxlat) / (maxlat - minlat)
        return utility    
    
    def latency_norm_penalty(self, lat, minlat, maxlat, x = 10.0):
        if lat <= minlat: 
            penalty = 0
        elif lat > maxlat:
            penalty = min(10000, x+x*x*(lat-maxlat)/(maxlat - minlat))
        else:
            penalty = x * float(lat - minlat) / (maxlat - minlat)
        return penalty
    
#    def cost_norm_penalty(self, cost, mincost):
#        if cost <= mincost: return 0.0
#        else:
#            return (cost-mincost) / mincost
    
    def cost_norm_penalty(self, cost, mincost, maxcost = None, x = 10.0):
        if maxcost is None:
            maxcost = 2.0 * mincost
        if cost <= mincost: return 0.0
        elif cost > maxcost:
            return min(10000, x+x*x*(cost-maxcost)/(maxcost - mincost))
        else:
            return (x * float(cost- mincost) / (maxcost - mincost) )
    
    def min_cost(self):
        total_cost = 0
        dem = self.users.total_demands()
        serv_list = self.tree.services_list_from_tree()
        for service_id in serv_list:
            ls = self.servers.servers_for_service(service_id)
            mincost = None
            #selected_server = None
            for server_id in ls:
                fcost = self.servers.get_fixed_cost(service_id, server_id)
                vcost = self.servers.get_var_cost(service_id, server_id)
                cost_server = fcost + dem * vcost
                if mincost is None or cost_server < mincost:
                    mincost = cost_server
                    #selected_server = server_id
            #print("Service: ", service_id)
            #print("Server: ", selected_server)
            total_cost += mincost
        return total_cost


    def generate_e2e_demands(self, dic_assig):
        root = self.tree.root_service()
        edges = self.tree.get_all_edges_fromtree()
        res = Demands(self.network)
        for u in dic_assig.keys():
            root_server = dic_assig[u][root]
            if root_server != self.users.get_user_node(u):
                res.add_demands(root_server,self.users.get_user_node(u), self.users.get_demand(u))
            for (s,d) in edges:
                src_server = dic_assig[u][s]
                dst_server = dic_assig[u][d]
                if src_server != dst_server:
                    res.add_demands(src_server, dst_server, self.users.get_demand(u))
        return res
    
    def best_routing(self, dic_assig, dem  = None, of = "mlu"):
        if dem is None:
            dem = self.generate_e2e_demands(dic_assig)
        cong_opt = CongestionOptimization(self.network, dem)
        cong_opt.setup_problem(of, False, False)
        res = cong_opt.solve_problem()
        if of=="fortz": res_cong = res[1] - 1.0
        else: res_cong = res[1] 
        if (res is not None):
            return res_cong, cong_opt.get_all_used_links()
        else: 
            print("No optimal routing could be found")
            return None
     
    def sp_routing(self, dic_assig, weights, dem  = None, of = "mlu", ecmp = True):
        if dem is None:
            dem = self.generate_e2e_demands(dic_assig)
        cong_opt = CongestionOptimization(self.network, dem)
        
        if ecmp:
            of_val, links =  cong_opt.sp_congestion_ties(weights, of)
        else:
            of_val, links =  cong_opt.sp_congestion(weights, of)
        
        if of == "fortz": of_val -= 1.0
        
        return of_val, links
                    
    
    def update_delays_from_routing(self, paths):
        self.delays = {}
        for (e,i,j) in paths.keys():
            if (i,j) in self.delays:
                self.delays[(i,j)] += paths[(e,i,j)] * self.network.get_link_delay(e)
            else:
                self.delays[(i,j)] = paths[(e,i,j)] * self.network.get_link_delay(e)
        for e in self.network.link_ids():
            self.delays[(e,e)] = 0.0
     
    def minimum_first_hop(self):
        dic_fh_pen = {}
        root = self.tree.root_service()
        servers_root = self.servers.servers_for_service(root)
        for u in self.users.get_users():
            min_fh_pen = None
            for root_server in servers_root:
                fh_lat = self.get_user_delays(root_server,u)
                minlat, maxlat = self.users.get_fh_latencies(u)     
                fhp = self.latency_norm_penalty(fh_lat, minlat, maxlat)
                if min_fh_pen is None or fhp < min_fh_pen:
                    min_fh_pen = fhp
            dic_fh_pen[u] = min_fh_pen
        return dic_fh_pen, sum(dic_fh_pen.values())/len(self.users)

def remove_index_fromid(idnode):
    tokens = idnode.split("-")
    return tokens[0]
        
## Tests ##

def test1():
    from composite_heuristic import CompositeHeuristic
    n = Network("../Networks/isno_5_2")    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    s = Servers(t, n, "../DataComposite/isno_5_2-costs.txt")
    u = Users(n, "../DataComposite/isno_5_2-users-v2.txt", "../DataComposite/isno_5_2-user_topo.txt")
    
    cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True)
    #print(cs)
    
    hcs = CompositeHeuristic(cs)
    order = list(range(len(cs.users)))
    sol = hcs.heuristic(order)
    cs.of_normalized_penalty(sol, printcomps = True)

def test2():
    n = Network("../Networks/isno_5_2")    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    s = Servers(t, n, "../DataComposite/test-cost.txt")
    u = Users(n, "../DataComposite/test-users.txt", "../DataComposite/test-user_topo.txt")
    
    cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True)
    print(cs)

def test3():
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    #n = Network("../Networks/isno_30_4")
    n = Network("../Networks/isno_5_2")   
    u = Users(n)
    u.generate_users(len(t), target_alu = 0.25, target_delay = 0.8)
    u.write_demands("../DataComposite/isno_5_2-t2-users.txt")
    u.write_user_topo("../DataComposite/isno_5_2-t2-user_topo.txt")
    #u.write_demands("../DataComposite/isno_30_4-t1-users.txt")
    #u.write_user_topo("../DataComposite/isno_30_4-t1-user_topo.txt")
    s = Servers(t,n)
    s.generate_servers()
    s.write_servers("../DataComposite/isno_5_2-t2-costs.txt")
    #s.write_servers("../DataComposite/isno_30_4-t1-costs.txt")

def test4():
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = True
    t = ServicesTree(loops, filename_tree)
    n = Network("../Networks/geant.txt", "sndlib")
    u = Users(n)
    u.generate_users(len(t), target_alu = 0.3, target_delay = 1.0)
    u.write_demands("../DataComposite/geant-lin-alu30-del10-users.txt")
    #u.write_user_topo("../DataComposite/geant-lin-user_topo.txt")
    #s = Servers(t,n)
    #s.generate_servers()
    #s.write_servers("../DataComposite/geant-loops-costs.txt")

def test5():
    filename_tree = "../DataComposite/tree_syn_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    n = Network("../Networks/geant.txt", "sndlib")
    
    s = Servers(t, n, "../DataComposite/geant-tree-syn-costs.txt")
    u = Users(n, "../DataComposite/geant-tree-syn-users.txt", "../DataComposite/geant-tree-syn-user_topo.txt")
    
    cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = False)
    
    #print(cs)
    
    print(cs.min_cost())
    print(cs.minimum_first_hop())

def test_tree_syn_structure():
    filename_tree = "../DataComposite/tree_syn_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    n = Network("../Networks/geant.txt", "sndlib")
    u = Users(n)
    u.generate_users(len(t), target_alu = 0.25, target_delay = 0.8)
    u.write_demands("../DataComposite/geant-treesyn-alu25-del08-users.txt")
    u.write_user_topo("../DataComposite/geant-treesyn-alu25-del08-user_topo.txt")
    s = Servers(t,n)
    s.generate_servers()
    s.write_servers("../DataComposite/geant-treesyn-alu25-del08-costs.txt")

if __name__ == '__main__':   
    #test1()
    #test2()
    #test3()
    test4()
    #test5()
    #test_tree_syn_structure()