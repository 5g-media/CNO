#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 25 22:57:51 2018

@author: miguelrocha
"""

import sys
import pandas as pd
import timeit

#sys.path.append('..')
from netcore.topology import Network
from users import Users
from services import ServicesTree
from servers import Servers
from composite import CompositeServices
from ea_composite import EACompositeServices
from deap_composite import DeapComposite

#### RUN SCRIPT ####
## for command line usage ###

def run():
    ## FORMAT: type_optimization network_file services_tree instance_file results_file
    ## type_optimization:
    ##      nc - no congestion
    ##      d - congestion costs; shortest path delays
    ##      sp - congestion costs; EA optimizing weights
    ##      oc - congestion costs; MILP optimizaing congestion
    ## network file - assuming sndlib format
    ## services tree - file with "tree" of services
    ## instance_file - defines "name" of instance
    ## assuming: instance_file + "-users.txt" - users demands
    ## assuming: instance_file + "-user_topo.txt" - users topologies
    ## assuming: instance_file + "-costs.txt" - server costs
    ## results_file: prefix of the files for results
    ## - files will be results_file + "-stats.txt" and results_file+ "-pop.txt"
    ## Options: 
    ## -mo - do multiobjective optimization (NSGA 2)
    ## -p numcpus - activates parallel evaluation of OF with numcpus as maximum
    ## -ev maxevals - maximum number of evaluations (default: 10000)
    ## -mr rate - set mutation rate (per element)
    ## -lr rate - local opt rate (per individual)
    ## -r runs - number of runs (1 if not specified)
    
    ## -deap - engine will be DEAP (default)
    ## -inspyred - engine will be inspyred
    
    network_file = sys.argv[2]
    n = Network(network_file, "sndlib")#, engine = "igraph")
    
    filename_tree = sys.argv[3]
    loops = False
    t = ServicesTree(loops, filename_tree)
    
    servers_file = sys.argv[4] + "-costs.txt"
    s = Servers(t, n, servers_file)

    users_dem_file = sys.argv[4] + "-users.txt"
    users_top_file = sys.argv[4] + "-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)

    optimize_routing_weig = False
    if sys.argv[1] == "nc":
        cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = False, cong_of = "fortz")
    elif sys.argv[1] == "d":
        cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = True,
                               cong_of = "fortz")
    elif sys.argv[1] == "oc":
        cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True,
                               cong_opt_method = "milp", cong_of = "fortz")
    elif sys.argv[1] == "sp": 
        cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True,
                               cong_opt_method = "sp", cong_of = "fortz")
        optimize_routing_weig = True

    ## options 
    par = False
    maxcpus = 1
    multiobj = False
    numruns = 1
    engine = "deap"
    eapars = {}
    if len(sys.argv) > 6:
        i = 6
        while i < len(sys.argv):
            if sys.argv[i] == "-p":
                par = True
                maxcpus = int(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == "-mo":
                multiobj = True
                i += 1
            elif sys.argv[i] == "-deap":
                engine = "deap"
                i += 1
            elif sys.argv[i] == "-inspyred":
                engine = "inspyred"
                i += 1
            elif sys.argv[i] == "-ev":
                eapars["max_evaluations"] = int(sys.argv[i+1])
                i += 2
#            elif sys.argv[i] == "-mr":
#                eapars["mutation_rate"] = float(sys.argv[i+1])
#                i += 2
            elif sys.argv[i] == "-lr":
                eapars["local_opt_rate"] = float(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == "-r":
                numruns = int(sys.argv[i+1])
                i += 2  
            else:
                print("Invalid option")
                sys.exit(1)
    
    res = {}
    
    if multiobj:
        res_keys = ["type", "network", "tree", "instance", "engine",
                    "popsize", "evals", "local_rate"]
    else:
        res_keys = ["type", "network", "tree", "instance", "engine",
                    "popsize", "evals", "local_rate",
                    "of_value", "of_cost", "of_e2e", "of_fh", "of_cong"]
        
    for k in res_keys:
        res[k] = []

    network_name = sys.argv[2].split("/").pop()
    tree_name = sys.argv[3].split("/").pop()
    instance_name = sys.argv[4].split("/").pop()
      
    for r in range(numruns):
        
        start = timeit.default_timer()
        
        if engine == "inspyred":
            ea = EACompositeServices(cs,optimize_routing_weights = optimize_routing_weig)
        elif engine == "deap":
            ea = DeapComposite(cs,optimize_routing_weights = optimize_routing_weig)
        
        res["type"].append(sys.argv[1])
        res["network"].append(network_name)
        res["tree"].append(tree_name)
        res["instance"].append(instance_name)
        res["engine"] = engine
    
        if multiobj:
            file_run = sys.argv[5] + "-run" + str(r)
            res_ea = ea.run_mo(ea_pars = eapars, display = False, save_file = file_run)
            
            res["popsize"].append(res_ea["popsize"])
            res["evals"].append(res_ea["evals"])
#                res["selected"].append(res_ea["selected"])
#                res["elites"].append(res_ea["elites"])
#                res["mutation_rate"].append(res_ea["mutation_rate"])
            res["local_rate"].append(res_ea["local_rate"])
            
            res_pd = pd.DataFrame(data = res)
            res_pd.to_csv(sys.argv[5] + "-results.csv")

        
        else:
            if sys.argv[5] == 'None':
                _, res_ea = ea.run_evol_alg(parallel = par, max_cpus = maxcpus, ea_pars = eapars)
            else:
                file_run = sys.argv[5] + "-run" + str(r)
                _, res_ea = ea.run_evol_alg(parallel = par, max_cpus = maxcpus, ea_pars = eapars, 
                        save_file = file_run)
        
                res["of_value"].append(res_ea["of_value"])
                res["of_fh"].append(res_ea["of_fh"])
                res["of_e2e"].append(res_ea["of_e2e"])
                res["of_cost"].append(res_ea["of_cost"])
                res["of_cong"].append(res_ea["of_cong"])

                res["popsize"].append(res_ea["popsize"])
                res["evals"].append(res_ea["evals"])
#                res["selected"].append(res_ea["selected"])
#                res["elites"].append(res_ea["elites"])
#                res["mutation_rate"].append(res_ea["mutation_rate"])
                res["local_rate"].append(res_ea["local_rate"])
                
                res_pd = pd.DataFrame(data = res)
                res_pd.to_csv(sys.argv[5] + "-results.csv")

        stop = timeit.default_timer()
        print('Time EA: ', stop - start) 

if __name__ == '__main__': 
    run()