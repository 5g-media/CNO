#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  7 21:58:09 2018

@author: miguelrocha
"""
#import sys

from netcore.topology import Network

import random

class Users:
    
    def __init__(self, network = None, file_demands = None, file_topo = None, sep = "\t"):
        self.network = network
        self.demands = {}  ## demands + QoS constraints
        self.topology = {} ## connection to nodes in a network
        if file_demands is not None:
            self.read_users(file_demands, sep)
        if file_topo is not None:
            self.read_users_topo(file_topo, sep)
        if not self.check_users():
            print("Users check: demands and topology not matching !!")
        #else: print("Check ok")
    
    def read_users(self, filename, sep = "\t"):
        f = open(filename)
        self.demands = {}
        for lines in f:
            if not lines.startswith("#"):
                tokens = lines.split(sep)
                key = tokens[0].strip()
                self.demands[key] = (float(tokens[1].strip()), float(tokens[2].strip()), float(tokens[3].strip()), 
                                float(tokens[4].strip()),float(tokens[5].strip()))
        f.close()

    def read_users_topo(self, filename, sep = "\t"):
        f = open(filename)
        self.topology = {}
        for lines in f:
            if not lines.startswith("#"):
                tokens = lines.split(sep)
                key = tokens[0].strip()
                node = tokens[1].strip()
                if self.network is not None and node not in self.network.nodes:
                    print("Warning: Topology file has node not in the network", node)
                else:
                    self.topology[key] = node
        f.close()

    def check_users(self):
        if len(self.demands) != len(self.topology):
            return False
        for u in self.topology.keys():
            if u not in self.demands:
                return False
        return True

    def get_users(self):
        return self.demands.keys()

    def ord_users(self):
        return sorted(self.demands.keys())

    def __len__(self):
        return len(self.demands.keys())

    def get_demand(self, user_id):
        return self.demands[user_id][0]
    
    def get_latencies(self, user_id):
        return self.demands[user_id][1], self.demands[user_id][2]

    def get_fh_latencies(self, user_id):
        return self.demands[user_id][3], self.demands[user_id][4]
    
    def get_user_node(self, user_id):
        return self.topology[user_id]
    
    def total_demands(self):
        total = 0.0
        for u in self.demands.keys():
            total += self.demands[u][0]
        return total
    
    def __str__(self):
        res = "Users:\n"
        res += "Demands / QoS:\n"
        for (k,v) in self.demands.items():
            res += str(k) + " -> " + str(v) + "\n" 
        res += "Users topology:\n"
        for (k,v) in self.topology.items():
            res += str(k) + " -> " + str(v) + "\n" 
        return res
 
    def generate_users(self, num_services, perc_switch_service = 0.3, num_users_mult = 5, 
                       target_alu = 0.2, target_delay = 0.5, delay_mult = 1.5):
                
        nodes = self.network.list_nodes()
        num_links = self.network.number_edges()
        avg_del = self.network.avg_delays()
        avg_cap = self.network.avg_capacities()
        avg_hops = (1 / perc_switch_service - 1) * (num_services-1) 
        num_users = num_users_mult * len(nodes)
        
        avg_demand = (avg_cap * num_links) / (avg_hops * num_users) * target_alu
        avg_min_fh_delay = avg_del * (1 / perc_switch_service - 1) * target_delay
        avg_min_e2e_delay = avg_del * avg_hops * target_delay
        
        self.demands = {}
        self.topology = {}
        
        for i in range(num_users):
            # select node to connect
            user_node = random.randint(0, len(nodes)-1)
            demand_user=  avg_demand * (0.5 + random.random())
            fh_min_lat =  avg_min_fh_delay #* (0.75 + 0.5*random.random())
            fh_max_lat = fh_min_lat * delay_mult #* (0.75 + 0.5*random.random())
            e2e_min_lat = avg_min_e2e_delay #* (0.75 + 0.5*random.random())
            e2e_max_lat = e2e_min_lat * delay_mult #* (0.75 + 0.5*random.random())
            self.demands["u"+str(i+1)] = (demand_user, e2e_min_lat, e2e_max_lat, fh_min_lat, fh_max_lat)
            self.topology["u"+str(i+1)] = nodes[user_node]
    
    def write_demands(self, filename, sep = "\t"):
        f = open(filename, "w")
        for (u, v) in self.demands.items():
            f.write(u + sep)
            f.write(str(v[0]) + sep + str(v[1]) + sep + str(v[2]) + sep + str(v[3]) + sep + str(v[4]) + "\n")
        f.close()
    
    def write_user_topo(self, filename, sep = "\t"):
        f = open(filename, "w")
        for (u, v) in self.topology.items():
            f.write(u + sep)
            f.write(v + "\n")
        f.close()

    
### Testing ####

            
def test1():
    n = Network("../Networks/isno_5_2")
    u = Users(n, "../DataComposite/isno_5_2-users.txt", "../DataComposite/isno_5_2-user_topo.txt")
    print(u)
    
def test2():
    n = Network("../Networks/isno_5_2")
    u = Users(n)
    u.generate_users(3, 0.3, 3)
    print(u)
    u.write_demands("../DataComposite/test-users.txt")
    u.write_user_topo("../DataComposite/test-user_topo.txt")

def test_germany():
    n = Network("../Networks/germany50.txt", "sndlib")
    u = Users(n)
    u.generate_users(3, 0.2, 3)
    print(u)
    u.write_demands("../DataComposite/germany50-users.txt")
    u.write_user_topo("../DataComposite/germany50-user_topo.txt")
    
    
if __name__ == '__main__': 
    test2()
    #test_germany()