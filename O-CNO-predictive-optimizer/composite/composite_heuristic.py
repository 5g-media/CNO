#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 30 10:48:30 2018

@author: miguelrocha
"""

import math

import sys
#sys.path.append('..')

from users import Users
from services import ServicesTree
from servers import Servers
from netcore.topology import Network
from netcore.loads import Loads
from composite import CompositeServices
from solution_comp import ServicesAssignment
from congopt.congoptim import CongestionOptimization

class CompositeHeuristic:
    
    ## weights - dict with weights for the different components of OF
    def __init__(self, composite, weights = None):
        self.composite = composite
        self.ord_services = self.composite.tree.services_list_from_tree() 

    def heuristic(self, solution):
        
        ord_users = self.composite.users.ord_users()
        
        num_services = len(self.ord_services)
        assig_dic = {}
        fixed_cost_dic = {} ## includes servers used by previous users
        
        servers_per_service = {} 
        for s in self.ord_services:
            servers_per_service[s] = self.composite.servers.servers_for_service(s)
          
        # each user in the provided order
        for u in solution: 
            print(u)
            user_id = ord_users[u]
            # update min cost for user
            dem = self.composite.users.get_demand(user_id)
            for service_id in self.ord_services:
                ls = servers_per_service[service_id]
                mc = None
                for server_id in ls:
                    fcost = self.composite.servers.get_fixed_cost(service_id, server_id)
                    vcost = self.composite.servers.get_var_cost(service_id, server_id)
                    if (service_id,server_id) not in fixed_cost_dic:
                        cost_server = fcost + dem * vcost
                    else: cost_server = dem * vcost
                    if mc is None or cost_server < mc:
                        mc = cost_server        
     
            # for each possible assignment of servers to services (try all for this user)
            nxt_assig = [0]*len(self.ord_services)
            opt_assig = None
            opt_cost = math.inf
    
            while nxt_assig is not None:
                # build the solution
                cur_sol_dic = {}
                for s in range(len(nxt_assig)):
                    service_id = self.ord_services[s]
                    server_id = servers_per_service[service_id][nxt_assig[s]]
                    cur_sol_dic[service_id] = server_id 

                assig_dic[user_id] = cur_sol_dic
                
                # calculate added cost 
                added_cost = 0
                for s in assig_dic[user_id].keys():
                    server_id = assig_dic[user_id][s]
                    if (s, server_id) not in fixed_cost_dic:
                        added_cost += self.composite.servers.get_fixed_cost(s, server_id)
                    added_cost += self.composite.var_cost(user_id, s, server_id)
                    
                cost_pen = self.composite.cost_norm_penalty(added_cost, mc)
    
                if self.composite.opt_cong or self.composite.congestion_cost:
                    dem = self.composite.generate_e2e_demands(assig_dic)
            
                if self.composite.opt_cong:
                        cong, paths = self.composite.best_routing(assig_dic, dem, self.composite.cong_of)
                        self.composite.update_delays_from_routing(paths)
                elif self.composite.congestion_cost:
                        l = Loads(self.composite.network)
                        l.add_loads_from_paths(self.composite.del_paths, dem) 
                                                
                        if self.composite.cong_of == "mlu": cong = l.mlu()[0]
                        elif self.composite.cong_of == "alu": cong = l.alu()
                        elif self.composite.cong_of == "fortz": 
                            co = CongestionOptimization(self.composite.network, dem)
                            phiu = co.phi_uncap()
                            if phiu <= 0.0: 
                                cong = 0.0
                            else:
                                cong = l.fortz_of(phiu) - 1.0
                            
                lat = self.composite.latency_user(user_id, assig_dic[user_id])
                minlat, maxlat = self.composite.users.get_latencies(user_id)
                lat_pen = self.composite.latency_norm_penalty(lat, minlat, maxlat)
    
                fh_lat = self.composite.get_fh_latency(user_id, assig_dic[user_id])
                minlat_fh, maxlat_fh = self.composite.users.get_fh_latencies(user_id)      
                lat_fh = self.composite.latency_norm_penalty(fh_lat, minlat_fh, maxlat_fh)    

                if self.composite.congestion_cost:
                    cost = self.composite.weights["cost"]*cost_pen + self.composite.weights["e2e"]*lat_pen 
                    + self.composite.weights["fh"]*lat_fh + self.composite.weights["congestion"]*cong
                else:
                    cost = self.composite.weights["cost"]*cost_pen + self.composite.weights["e2e"]*lat_pen 
                    + self.composite.weights["fh"]*lat_fh
    
                del(assig_dic[user_id])

                if opt_assig is None or cost < opt_cost:
                    opt_assig = nxt_assig
                    opt_cost = cost
                
                nxt_assig = self.next_assig(nxt_assig, num_services, servers_per_service, self.ord_services)  
            # update optimal solution with best assignment for this user
            opt_sol_dic = {}
            for s in range(len(opt_assig)):
                service_id = self.ord_services[s]
                server_id = servers_per_service[service_id][opt_assig[s]]
                opt_sol_dic[service_id] = server_id 
                if (service_id,server_id) not in fixed_cost_dic:
                    fixed_cost_dic[(service_id,server_id)] = True
            assig_dic[user_id] = opt_sol_dic
                          
        return ServicesAssignment(self.composite, assig_dic)
            

    def next_assig(self, cur_assign, num_services, servers_per_service, ord_services):
        index = 0
        while index < num_services and cur_assign[index] == ( len(servers_per_service[ord_services[index]]) - 1):
            index += 1
        if index == num_services: 
            return None
        else:
            nxt_assign = list(cur_assign)
            nxt_assign[index] += 1
            for i in range(index): nxt_assign[i] = 0
            return nxt_assign
        
## Testing ###
            


def run():
    ## FORMAT: type_optimization network_file services_tree instance_file
    ## type_optimization:
    ##      nc - no congestion
    ##      d - congestion costs; shortest path delays
    ##      oc - congestion costs; MILP optimizaing congestion
    ## network file - assuming sndlib format
    ## services tree - file with "tree" of services
    ## instance_file - defines "name" of instance
    ## assuming: instance_file + "-users.txt" - users demands
    ## assuming: instance_file + "-user_topo.txt" - users topologies
    ## assuming: instance_file + "-costs.txt" - server costs
    
    network_file = sys.argv[2]
    n = Network(network_file, "sndlib")
    
    filename_tree = sys.argv[3]
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    servers_file = sys.argv[4] + "-costs.txt"
    s = Servers(t, n, servers_file)

    users_dem_file = sys.argv[4] + "-users.txt"
    users_top_file = sys.argv[4] + "-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)
    
    if sys.argv[1] == "nc":
        cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = False, 
                               cong_of = "fortz")
    elif sys.argv[1] == "d":
        cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = True,
                               cong_of = "fortz")
    elif sys.argv[1] == "oc":
        cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True,
                               cong_opt_method = "milp", cong_of = "fortz")
    else:
        print("Type of optimization not defined")
        sys.exit(1)

    hcs = CompositeHeuristic(cs)
    order = list(range(len(cs.users)))
    sol = hcs.heuristic(order)
    
    of = cs.of_normalized_penalty(sol, True)
    
    if not cs.congestion_cost: ## reporting congestion even if not used in the optimization
        dem = cs.generate_e2e_demands(sol.dic_assig)
        l = Loads(n)
        l.add_loads_from_paths(cs.del_paths, dem)
        if cs.cong_of == "mlu": cong = l.mlu()[0]
        elif cs.cong_of == "alu": cong = l.alu()
        elif cs.cong_of == "fortz": 
            co = CongestionOptimization(n,dem)
            phiu = co.phi_uncap()
            cong = l.fortz_of(phiu) - 1.0
        print("Congestion (not optimized):", cong)
    
    print("Objective function:", of)
    
    
if __name__ == '__main__':   
   run()