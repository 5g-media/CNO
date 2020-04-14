#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  6 14:52:15 2018

@author: miguelrocha
"""
#import sys
import random

#sys.path.append('..')

from netcore.topology import Network
from services import ServicesTree


class Servers:
    
    def __init__(self, serv_tree, network = None, filename = None, sep = "\t"):
        self.tree = serv_tree
        self.network = network
        if filename is not None:
            self.read_servers(filename, sep)
        else: self.dic_serv = {}

    ## reads servers and cost: assuming format: IdService IdServer Fixed_cost Var_cost [Capacity] 
    ## returns dictionary: key is service id; values are dictionaries with servers (key), (fixed, var costs, cap) as values
    def read_servers(self, filename, sep = "\t"):
        f = open(filename)
        self.dic_serv = {}
        for lines in f:
            if not lines.startswith("#"):
                tokens = lines.split(sep)
                service = tokens[0].strip()
                server = tokens[1].strip()
                fcost = float(tokens[2].strip())
                vcost = float(tokens[3].strip())
                if len(tokens) > 4:
                    capacity = float(tokens[4].strip())
                else:
                    capacity = float("inf") # set capacity to inf if not defined
                  
                if service not in self.tree.services_list_from_tree():
                    print("Service in file not defined in tree of services:", service)
                elif self.network is not None and server not in self.network.list_nodes():
                    print("Server is not a node of the network :", server)
                else:
                    if service not in self.dic_serv: self.dic_serv[service] = {}
                    self.dic_serv[service][server] = (fcost, vcost, capacity)
        f.close()

    def servers_for_service(self, service_id):
        servers = self.dic_serv[service_id]
        return sorted(servers.keys())
    
    def num_servers_per_service(self, ord_services):
        num_servers = []
        for s in ord_services:
            num_servers.append(len(self.servers_for_service(s)))
        return num_servers
    
    def get_capacity(self, service_id, server_id):
        return self.dic_serv[service_id][server_id][2]
    
    def get_fixed_cost(self, service_id, server_id):
        return self.dic_serv[service_id][server_id][0]
    
    def get_var_cost(self, service_id, server_id):
        return self.dic_serv[service_id][server_id][1]

    def __str__(self):
        res = ""
        res += "Servers:\n"
        for (k,v) in self.dic_serv.items():
            res += ("Service: " + str(k) + "\n")
            for (k1, v1) in v.items():
                res += ("\t" + str(k1) + " -> " + str(v1) + "\n" )
            res += "\n"
        return res


    ## for now not considering capacity of servers
    def generate_servers(self, perc_switch_service = 0.3, avg_fixed_cost = 100.0, avg_var_cost = 1.0):
        services_list = self.tree.services_list_from_tree()
        switches_services = {}
        nodes = self.network.list_nodes()
        for switch in nodes:
            switches_services[switch] = []
            for serv in services_list:
                if random.random() < perc_switch_service:
                    switches_services[switch].append(serv)
        
        self.dic_serv = {}
        for sw in switches_services:
            for serv in switches_services[sw]:
                fixed_cost = avg_fixed_cost * (0.75+random.random()*0.5)
                var_cost = avg_var_cost * (0.75+random.random()*0.5)
                if serv not in self.dic_serv: self.dic_serv[serv] = {}
                self.dic_serv[serv][sw] = (fixed_cost, var_cost, 10000000)
    
    def write_servers(self, filename, sep = "\t"):
        f = open(filename, "w")
        for (k,v) in self.dic_serv.items():
            for (k1, v1) in v.items():
                f.write (k + sep + str(k1) + sep + str(v1[0]) + sep + str(v1[1]) + sep + str(v1[2]) + "\n")
        f.close()
    
## Testing ###
        
def test1():
    n = Network("../Networks/isno_5_2")
    filename = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename)
    s = Servers(t, n, "../DataComposite/isno_5_2-costs.txt")
    print(s)
 
def test2():
    filename = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename)
    s = Servers(t, None, "../DataComposite/isno_30_4-costs.txt")
    ## no capacities defined
    print(s)
    
def test3():
    n = Network("../Networks/isno_5_2")
    filename = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename)
    s = Servers(t,n)
    s.generate_servers(0.4, 100.0, 1.0)
    print(s)
    s.write_servers("../DataComposite/test-cost.txt")
    
def test4():
    n = Network("../Networks/isno_5_2")
    filename = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename)
    s = Servers(t, n, "../DataComposite/test-cost.txt")
    print(s)

def test_germany():
    n = Network("../Networks/germany50.txt", "sndlib")
    filename = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename)
    s = Servers(t,n)
    s.generate_servers(0.2, 100.0, 1.0)
    print(s)
    s.write_servers("../DataComposite/germany50-cost.txt")

def test_tree_syn_geant():
    n = Network("./Networks/geant.txt", "sndlib")
    filename = "./DataComposite/tree_syn_structure.txt"
    loops = False
    t = ServicesTree(loops, filename)
    s = Servers(t,n)
    s.generate_servers(0.5, 20000.0, 1.0)
    print(s)
    s.write_servers("./DataComposite/geant-tree-syn-costs.txt")

if __name__ == '__main__':   
    #test_germany()
    test1()
    #test2()
    #test3()
    #print()
    #test4()
    #test_tree_syn_geant()



