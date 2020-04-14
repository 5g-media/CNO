#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 12 15:50:19 2018

@author: miguelrocha
"""

from users import Users
from services import ServicesTree
from servers import Servers
from netcore.topology import Network
from composite import CompositeServices
from composite.composite_heuristic import CompositeHeuristic

def test1():
    n = Network("../Networks/isno_5_2")    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    s = Servers(t, n, "../DataComposite/isno_5_2-costs.txt")
    u = Users(n, "../DataComposite/isno_5_2-users.txt", "../DataComposite/isno_5_2-user_topo.txt")
    
    cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = True,
                           cong_of = "fortz")
    
    hcs = CompositeHeuristic(cs)
    
    order = list(range(len(cs.users)))
    
    sol = hcs.heuristic(order)
    
    print(sol)
    
    of = cs.of_normalized_penalty(sol, True)
    print("Objective function:", of)

 
def test2():
    network_file = "../Networks/isno_30_4"
    #network_file = "../Networks/isno_5_2"
    n = Network(network_file)
    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    #servers_file = "../DataComposite/test-cost.txt"
    servers_file = "../DataComposite/isno_30_4-t1-costs.txt"
    s = Servers(t, n, servers_file)

    #users_dem_file = "../DataComposite/test-users.txt"
    #sers_top_file = "../DataComposite/test-user_topo.txt"
    users_dem_file = "../DataComposite/isno_30_4-t1-users.txt"
    users_top_file = "../DataComposite/isno_30_4-t1-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)
    
    cs = CompositeServices(n, t, s, u, opt_cong = False, 
                           congestion_cost = True, cong_of = "mlu")
    
    hcs = CompositeHeuristic(cs)
    
    order = list(range(len(cs.users)))
    
    sol = hcs.heuristic(order)
    print(sol)
    
    of = cs.of_normalized_penalty(sol, True)
    print("Objective function:", of)

def test_germany():
    network_file = "../Networks/germany50.txt"
    n = Network(network_file, "sndlib")
    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    servers_file = "../DataComposite/germany50-cost.txt"
    s = Servers(t, n, servers_file)

    users_dem_file = "../DataComposite/germany50-users.txt"
    users_top_file = "../DataComposite/germany50-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)
    
    cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = False)
    
    hcs = CompositeHeuristic(cs)
    
    order = list(range(len(cs.users)))
    
    sol = hcs.heuristic(order)
    print(sol)
    
    of = cs.of_normalized_penalty(sol, True)
    print("Objective function:", of)

def test_geant():
    
    network_file = "../Networks/geant.txt"
    n = Network(network_file, "sndlib")
    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    servers_file = "../DataComposite/geant-t1-costs.txt"
    s = Servers(t, n, servers_file)

    users_dem_file = "../DataComposite/geant-t1-users.txt"
    users_top_file = "../DataComposite/geant-t1-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)
    
    cs = CompositeServices(n, t, s, u, opt_cong = False, 
                           congestion_cost = False)#, cong_of = "mlu")
    
    hcs = CompositeHeuristic(cs)
    
    order = list(range(len(cs.users)))
    
    sol = hcs.heuristic(order)
    print(sol)
    
    of = cs.of_normalized_penalty(sol, True)
    print("Objective function:", of)