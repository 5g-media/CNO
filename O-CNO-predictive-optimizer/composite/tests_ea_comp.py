#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 12 15:14:19 2018

@author: miguelrocha
"""

from users import Users
from services import ServicesTree
from servers import Servers
from netcore.topology import Network
from composite import CompositeServices
from ea_composite import EACompositeServices

def test1():
    #etwork_file = "../Networks/isno_30_4"
    network_file = "../Networks/isno_5_2"
    n = Network(network_file)
    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    #servers_file = "../DataComposite/test-cost.txt"
    #servers_file = "../DataComposite/isno_30_4-t1-costs.txt"
    servers_file = "../DataComposite/isno_5_2-t1-costs.txt"
    s = Servers(t, n, servers_file)

    #users_dem_file = "../DataComposite/test-users.txt"
    #users_top_file = "../DataComposite/test-user_topo.txt"
    #users_dem_file = "../DataComposite/isno_30_4-t1-users.txt"
    #users_top_file = "../DataComposite/isno_30_4-t1-user_topo.txt"
    users_dem_file = "../DataComposite/isno_5_2-t2-users.txt"
    users_top_file = "../DataComposite/isno_5_2-t1-user_topo.txt"

    u = Users(n, users_dem_file, users_top_file)
    
    cs = CompositeServices(n, t, s, u, opt_cong = False, 
                           congestion_cost = True, cong_of = "fortz")    
    
    print("Starting EA:")
    ea_par = {"max_evaluations":500}
    ea = EACompositeServices(cs)
    
    assig = ea.run_evol_alg(ea_pars = ea_par)
    #assig = ea.run_evol_alg(True, max_cpus = 50)
    
    print("Best solution:")
    print(assig)
    
    #of = cs.of_normalized_penalty(bestsol, True)
    #print("Objective function:", of)

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
    
    cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True)    
    
    print("Starting EA:")
    ea = EACompositeServices(cs)
    
    #bestsol = ea.run_evol_alg()
    bestsol = ea.run_evol_alg(True, max_cpus = 50)
    
    of = cs.of_normalized_penalty(bestsol, True)
    print("Objective function:", of)

def test_sp():
    network_file = "../Networks/isno_30_4"
    #network_file = "../Networks/isno_5_2"
    n = Network(network_file)
    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    #servers_file = "../DataComposite/test-cost.txt"
    servers_file = "../DataComposite/isno_30_4-t2-costs.txt"
    s = Servers(t, n, servers_file)

    #users_dem_file = "../DataComposite/test-users.txt"
    #users_top_file = "../DataComposite/test-user_topo.txt"
    users_dem_file = "../DataComposite/isno_30_4-t2-users.txt"
    users_top_file = "../DataComposite/isno_30_4-t2-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)
    
    cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True,
                           cong_opt_method = "sp", cong_of = "fortz")    
    
    print("Starting EA:")
    ea = EACompositeServices(cs,optimize_routing_weights = True)
    
    ea_par = {"max_evaluations":50000}
    #bestsol = ea.run_evol_alg(ea_pars = ea_par)
    
    ea.run_evol_alg(True, max_cpus = 4, ea_pars = ea_par)
    
    #of = cs.of_normalized_penalty(bestsol, True)
    #print("Objective function:", of)

def test_tree():
    network_file = "../Networks/test_tree"
    n = Network(network_file)
    
    filename_tree = "../DataComposite/tree_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    servers_file = "../DataComposite/test_tree-cost.txt"
    s = Servers(t, n, servers_file)

    users_dem_file = "../DataComposite/test_tree-users.txt"
    users_top_file = "../DataComposite/test_tree-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)
    
    cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True)    
    
    print(cs)
    
    print("Starting EA:")
    ea = EACompositeServices(cs)
    ea_par = {"max_evaluations":5000}
    bestsol = ea.run_evol_alg(ea_pars = ea_par)
    #bestsol = ea.run_evol_alg(True, max_cpus = 50)
    
    of = cs.of_normalized_penalty(bestsol, True)
    print("Objective function:", of)

def test_geant():
    network_file = "../Networks/geant.txt"
    n = Network(network_file, "sndlib")
    
    #filename_tree = "../DataComposite/tree_syn_structure.txt"
    filename_tree = "../DataComposite/linear_structure_loops.txt"
    loops = True
    t = ServicesTree(loops, filename_tree)
    
    #servers_file = "../DataComposite/geant-loops-costs.txt"
    servers_file = "../DataComposite/geant-lin-alu30-del09-costs.txt"

    s = Servers(t, n, servers_file)

    #users_dem_file = "../DataComposite/geant-treeloops-alu25-del07-users.txt"
    users_dem_file = "../DataComposite/geant-lin-alu30-del09-users.txt"
    #users_top_file = "../DataComposite/geant-treeloops-alu25-del07-user_topo.txt"
    users_top_file = "../DataComposite/geant-user_topo.txt"
    
    u = Users(n, users_dem_file, users_top_file)
    
#    cs = CompositeServices(n, t, s, u, opt_cong = True, cong_opt_method = "sp", 
#                           congestion_cost = True, cong_of = "fortz")    
    
    cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = False,  cong_of = "fortz")

    
    
    ea_par = {"max_evaluations":20000, "pop_size": 100}
    ea = EACompositeServices(cs)
    #ea = EACompositeServices(cs,optimize_routing_weights = True)
    
    assig = ea.run_evol_alg(ea_pars = ea_par)
    
    print("Best solution:")
    print(assig)
    
def test_mo():
    network_file = "../Networks/geant.txt"
    n = Network(network_file, "sndlib")
    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    servers_file = "../DataComposite/geant-t2-costs.txt"
    s = Servers(t, n, servers_file)

    users_dem_file = "../DataComposite/geant-t2-users.txt"
    users_top_file = "../DataComposite/geant-t2-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)
    
    cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True, 
                           cong_of = "fortz")    
    
    
    ea_par = {"max_evaluations":10000}
    ea = EACompositeServices(cs)
    #ea = EACompositeServices(cs,optimize_routing_weights = True)
    
    ea.run_mo(ea_pars = ea_par, plot = True)
    
    #print("Best solution:")
    #print(assig)
    
#test_mo()
test_geant()
#test_sp()
#test1()