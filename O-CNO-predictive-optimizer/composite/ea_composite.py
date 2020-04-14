#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 27 17:41:08 2018

@author: miguelrocha
"""

## EVOLUTIONARY ALGORITHM FOR COMPOSITE SERVICES - TREE BASED

# representation - assuming u users and g groups
# solution will have length = u x g 
# users indexed 0 to u-1; groups indexed 1 to g (0 is assumed for user; g+1 for virtual source)
# position 0 - component used from group 1 for user 0
# position 1 - component used from group 2 for user 0 
# ...
# position g - component used from group 1 for user 1
# ...
# position gxu -1 - component used from group g for user u-1

import sys
from random import Random
from time import time
import inspyred
import matplotlib.pyplot as plt
import pandas as pd
import timeit

#sys.path.append('..')
from netcore.topology import Network
from netcore.loads import Loads
from congopt.congoptim import CongestionOptimization
from users import Users
from services import ServicesTree
from servers import Servers
from composite import CompositeServices
from solution_comp import ServicesAssignment

class EACompositeServices:
    
    def __init__(self, composite, optimize_routing_weights = False):        
        self.composite = composite
        self.ord_users = self.composite.users.ord_users()
        self.number_users = len(self.composite.users)
        self.ord_services = self.composite.tree.services_list_from_tree() 
        self.number_servers = self.composite.servers.num_servers_per_service(self.ord_services)

        self.servers_per_service = {} 
        for s in self.ord_services:
            self.servers_per_service[s] = self.composite.servers.servers_for_service(s)
            
        self.mincost = self.composite.min_cost()
        print("Minimum cost: ", self.mincost)
        
        self.opt_rout_weig = optimize_routing_weights 
        if self.opt_rout_weig: self.maxw = 20
        
    def generate_solution_random(self, random, args):
        from random import randint
         
        res = []    
        for i in range(self.number_users):
            for k in range(len(self.number_servers)):
                res.append(randint(0, self.number_servers[k]-1))
        
        if self.opt_rout_weig:
            for i in range(self.composite.network.number_edges()):
                res.append(randint(1, self.maxw))
        
        return res
    
    def decode_serv_assig(self, solution):
    
        if len(solution) != (len(self.ord_users)*len(self.ord_services)):
            print("Bad individual size")
            sys.exit(1)
    
        assig_dic = {}
        index = 0    
        for u in self.ord_users:
            assig_dic[u] = {}
            for s in self.ord_services:
                gene = solution[index]
                server = self.servers_per_service[s][gene]
                assig_dic[u][s] = server
                index += 1
        
        return ServicesAssignment(self.composite, assig_dic)
    
    def decode_weights(self, solution):
        L = self.composite.network.link_ids()
        w = {}
        for i, e in enumerate(L):
            w[e] = solution[i]
        return w
    
    def evaluate_serv_assig(self, candidates, args):    
        fitness = []   
        for cs in candidates:
            if self.opt_rout_weig:
                size_assig = len(self.ord_users)*len(self.ord_services)
                assig = self.decode_serv_assig(cs[:size_assig])
                w = self.decode_weights(cs[size_assig:])
                fit = self.composite.of_normalized_penalty(assig, False, self.mincost, sp_weights = w)
            else:
                assig = self.decode_serv_assig(cs)
                fit = self.composite.of_normalized_penalty(assig, False, self.mincost)
            fitness.append(fit)
        
        return fitness

    def evaluate_serv_mo(self, candidates, args):
        
        fitness = []
    
        for cs in candidates:
            if self.opt_rout_weig:
                size_assig = len(self.ord_users)*len(self.ord_services)
                assig = self.decode_serv_assig(cs[:size_assig])
                w = self.decode_weights(cs[size_assig:])
                fo = self.composite.of_normalized_penalty(assig, False, self.mincost, 
                                                           sp_weights = w, return_dic = True)
            else:
                assig = self.decode_serv_assig(cs)
                fo = self.composite.of_normalized_penalty(assig, False, self.mincost,
                                                           return_dic = True)
            del_pen = (fo["fh"] + fo["e2e"])/ 2.0
            if self.composite.congestion_cost:
                fitness.append(inspyred.ec.emo.Pareto([del_pen, fo["cost"], fo["cong"]]))
            else:
                fitness.append(inspyred.ec.emo.Pareto([del_pen, fo["cost"]]))
        
        return fitness
        

    def increment_mut(self, random, candidates, args):
        import copy

        max_assig = len(self.ord_users)*len(self.ord_services)

        mutants = []
        for candidate in candidates:        
            if random.random() < 0.5:    
                numchanges = random.randint(1,3)
                for k in range(numchanges):
                    mutant = copy.copy(candidate)
                    pos = random.randint(0,len(candidate)-1)
                    s = pos%len(self.ord_services)
                    current = mutant[pos]    
                    
                    if pos < max_assig: 
                        minv = 0
                        maxv = self.number_servers[s] -1
                    else: 
                        minv = 1
                        maxv = self.maxw
                    
                    f = random.random()
                    if f > 0.5:
                        if current == maxv: mutant[pos] = minv
                        else: mutant[pos] = current + 1
                    else:
                        if current == minv:
                            mutant[pos] = maxv
                        else: mutant[pos] = current - 1
                mutants.append(mutant)    
            else:
                mutants.append(candidate)
        return mutants


    def single_inteligent_mut(self, random, candidates, args):
        import copy

        maxpos = len(self.ord_users)*len(self.ord_services)  
        mutants = []
        for candidate in candidates:        
            if random.random() < args.get("local_opt_rate", 0.2): 
                numtries = random.randint(1,50)
                mutant = copy.copy(candidate)
                # compute fitness of original candidate
                if self.opt_rout_weig:
                        assig_dic = self.decode_serv_assig(candidate[:maxpos])
                        w = self.decode_weights(candidate[maxpos:])
                        cur_fit = self.composite.of_normalized_penalty(assig_dic, False, 
                                                                       self.mincost, sp_weights = w)
                else:
                        assig_dic = self.decode_serv_assig(candidate)
                        cur_fit = self.composite.of_normalized_penalty(assig_dic, False, self.mincost)
                        
                for i in range (numtries): 
                    #pos = random.randint(0,maxpos-1)
                    pos = random.randint(0, len(mutant)-1)
                    current = mutant[pos]
                    
                    if pos < maxpos:
                        s = pos%len(self.ord_services)
                        alternatives = list(range(self.number_servers[s]))
                        alternatives.remove(current)
 
                    else:
                        #alternatives = list(range(1,self.maxw+1))
                        alternatives = []
                        if current == self.maxw: 
                            alternatives.append(1)
                            alternatives.append(2)
                        else:
                            alternatives.append(current + 1)
                            if current == self.maxw-1:
                                alternatives.append(1)
                            else:
                                alternatives.append(current + 2)
                            
                        if current == 1: 
                            alternatives.append(self.maxw)
                            alternatives.append(self.maxw-1)
                        else: 
                            alternatives.append(current-1)
                            if current == 2:
                                alternatives.append(self.maxw)
                            else:
                                alternatives.append(current-2)
                    
                    #alternatives.remove(current)
                    if len(alternatives) <= 1: 
                        mutants.append(candidate)
                        break
                    a = random.choice(alternatives)
                    mutant[pos] = a
                    
                    if self.opt_rout_weig:
                        if pos >= maxpos:
                            w = self.decode_weights(mutant[maxpos:])
                        assig_dic_mut = self.decode_serv_assig(mutant[:maxpos])
                        mut_fit = self.composite.of_normalized_penalty(assig_dic_mut, False, 
                                                                       self.mincost, sp_weights = w)
                    else:
                        assig_dic_mut = self.decode_serv_assig(mutant)
                        mut_fit = self.composite.of_normalized_penalty(assig_dic_mut, False, 
                                                                       self.mincost)
                                    
                    if mut_fit >= cur_fit:
                        mutant[pos] = current
                    else:
                        cur_fit = mut_fit
                        
                mutants.append(mutant)
            else:
                mutants.append(candidate)
        return mutants
 

    def mo_inteligent_mut(self, random, candidates, args):
        import copy

        if self.composite.congestion_cost: num_objectives = 3
        else: num_objectives= 2
        maxpos = len(self.ord_users)*len(self.ord_services)  
        mutants = []
        
        for candidate in candidates:        
            if random.random() < args.get("local_opt_rate", 0.2): 
                numtries = random.randint(10,20)
                mutant = copy.copy(candidate)
                # compute fitness of original candidate
                if self.opt_rout_weig:
                        assig_dic = self.decode_serv_assig(candidate[:maxpos])
                        w = self.decode_weights(candidate[maxpos:])
                        cur_fit = self.composite.of_normalized_penalty(assig_dic, False, self.mincost, 
                                                                       sp_weights = w, return_dic = True)
                else:
                        assig_dic = self.decode_serv_assig(candidate)
                        cur_fit = self.composite.of_normalized_penalty(assig_dic, False, self.mincost,
                                                                       return_dic = True)
                        
                for i in range (numtries):
                     # select one of the objectives
                    objective = random.randint(0, num_objectives -1)
                    
                    if objective == 0:
                        cur_fit_obj = (cur_fit["fh"] + cur_fit["e2e"]) / 2.0
                    elif objective == 1:
                        cur_fit_obj = cur_fit["cost"]
                    else: cur_fit_obj = cur_fit["cong"]
                   
                    pos = random.randint(0, len(mutant)-1)
                    current = mutant[pos]
                    
                    if pos < maxpos:
                        s = pos%len(self.ord_services)
                        alternatives = list(range(self.number_servers[s])) 
                    else:
                        alternatives = list(range(1,self.maxw+1))
                    
                    alternatives.remove(current)
                    a = random.choice(alternatives)
                    if len(alternatives) <= 1: 
                        mutants.append(candidate)
                        break
                    mutant[pos] = a
                    
                    if self.opt_rout_weig:
                        if pos >= maxpos:
                            w = self.decode_weights(mutant[maxpos:])
                        assig_dic_mut = self.decode_serv_assig(mutant[:maxpos])
                        mut_fit = self.composite.of_normalized_penalty(assig_dic_mut, False, 
                                                                       self.mincost, sp_weights = w,
                                                                       return_dic = True)
                    else:
                        assig_dic_mut = self.decode_serv_assig(mutant)
                        mut_fit = self.composite.of_normalized_penalty(assig_dic_mut, False, 
                                                                       self.mincost,
                                                                       return_dic = True)
                    
                    if objective == 0:
                        mut_fit_obj = (mut_fit["fh"] + mut_fit["e2e"]) / 2.0
                    elif objective == 1:
                        mut_fit_obj = mut_fit["cost"]
                    else: mut_fit_obj = mut_fit["cong"]
                    
                    if mut_fit_obj >= cur_fit_obj:
                        mutant[pos] = current
                    else:
                        cur_fit_obj = mut_fit_obj
                        
                mutants.append(mutant)
            else:
                mutants.append(candidate)
        return mutants
 

    
    def improve_user_assig(self, random, candidates, args):
        import copy
        
        num_users = len(self.ord_users)
        num_services = len(self.ord_services)

        maxpos = num_users*num_services

        mutants = []
        for candidate in candidates:        
            if random.random() < 0.05:
                mutant = copy.copy(candidate)
                
                if self.opt_rout_weig:
                        w = self.decode_weights(candidate[maxpos:])
                
                u = random.randint(0,num_users-1)
                pos= u*num_services
                
                # for each possible assignment of servers to services (try all for this user)
                nxt_assig = [0]*num_services
                opt_assig = None
                opt_fit = None
                
                while nxt_assig is not None:
                                   
                    for i in range(num_services):
                        mutant[pos+i] = nxt_assig[i]
                    
                    if self.opt_rout_weig:
                        assig_dic_mut = self.decode_serv_assig(mutant[:maxpos])
                        mut_fit = self.composite.of_normalized_penalty(assig_dic_mut, False, 
                                                                       self.mincost, sp_weights = w)
                    else:
                        assig_dic_mut = self.decode_serv_assig(mutant)
                        mut_fit = self.composite.of_normalized_penalty(assig_dic_mut, False, 
                                                                       self.mincost)
                
                    if opt_assig is None or mut_fit < opt_fit:
                        opt_assig = nxt_assig
                        opt_fit = mut_fit
                
                    nxt_assig = self.next_assig(nxt_assig, num_services, self.servers_per_service, self.ord_services)  
            
                for i in range(num_services):
                    mutant[pos+i] = opt_assig[i]
                
                mutants.append(mutant)
            else:
                mutants.append(candidate)
        
        return mutants
                
    
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

    
    def run_evol_alg(self, parallel = False, max_cpus = 4, ea_pars = {},
                     display = True, save_file = None):   
                
        popsize = ea_pars.get("pop_size", 100)
        maxevals = ea_pars.get("max_evaluations", 10000)
        numselected = ea_pars.get("num_selected", 80)
        mutationrate = ea_pars.get("mutation_rate", 0.05)
        numelites = ea_pars.get("num_elites", 20)
        local_opt_rate = ea_pars.get("local_opt_rate", 0.2)
        
        if display:
            print("Population size: ", popsize)
            print("Number evaluations: ", maxevals)
            print("Num selected: ", numselected)
            print("Num elites: ", numelites)
            print("Mutation rate: ", mutationrate)
            print("Local opt rate: ", local_opt_rate)
            if save_file is not None:
                print("Saving results to files with prefix: ", save_file)
        
        lower_limits = [0]*(len(self.ord_users)*len(self.ord_services))
        upper_limits = []
        for u in range(len(self.ord_users)):
            for k in range(len(self.ord_services)):
                upper_limits.append(self.number_servers[k]-1)
        
        if self.opt_rout_weig:
            lower_limits.extend ( [0]*self.composite.network.number_edges() )    
            upper_limits.extend ( [self.maxw] * self.composite.network.number_edges() )

        rand = Random()
        rand.seed(int(time()))
        
        if parallel:
            my_ec = inspyred.ec.DEA(rand)
        else:
            my_ec = inspyred.ec.EvolutionaryComputation(rand)
        
        my_ec.selector = inspyred.ec.selectors.rank_selection
  
        if self.opt_rout_weig:
            my_ec.variator = [inspyred.ec.variators.n_point_crossover,
                              inspyred.ec.variators.random_reset_mutation,
                              self.single_inteligent_mut,
                              self.increment_mut
                              ]
        else:
            my_ec.variator = [inspyred.ec.variators.n_point_crossover,
                              inspyred.ec.variators.random_reset_mutation,
                              self.single_inteligent_mut,
                              self.increment_mut
#                              self.improve_user_assig
                              ]
        #my_ec.replacer = inspyred.ec.replacers.steady_state_replacement#
        my_ec.replacer = inspyred.ec.replacers.generational_replacement
        
        my_ec.terminator = inspyred.ec.terminators.evaluation_termination
        
        stat_file = None
        #ind_file = None
        
        if save_file is not None:
            my_ec.observer = inspyred.ec.observers.file_observer
            stat_file = open(save_file + "-stats.txt", "w")
            #ind_file = open(save_file + "-pop.txt", "w")
        elif display:
            my_ec.observer = inspyred.ec.observers.stats_observer



        if parallel:
            final_pop = my_ec.evolve(generator=self.generate_solution_random,
                                     evaluator=inspyred.ec.evaluators.parallel_evaluation_mp,
                                     mp_evaluator=self.evaluate_serv_assig, 
                                     mp_num_cpus= max_cpus,
                                     maximize = False,   ### set to True if maximizing utility
                                     pop_size=popsize,
                                     bounder=inspyred.ec.Bounder(lower_limits, upper_limits),
                                     max_evaluations=maxevals,
                                     num_selected=numselected,
                                     mutation_rate = mutationrate,
                                     num_elites = numelites,
                                     num_crossover_points = 3,
                                     local_opt_rate = local_opt_rate,
                                     statistics_file=stat_file,
                                     #individuals_file=ind_file
                                     )
        else:
            final_pop = my_ec.evolve(generator=self.generate_solution_random,
                                     evaluator=self.evaluate_serv_assig,
                                     maximize = False,   ### set to True if maximizing utility
                                     pop_size=popsize,
                                     bounder=inspyred.ec.Bounder(lower_limits, upper_limits),
                                     max_evaluations=maxevals,
                                     num_selected=numselected,
                                     mutation_rate = mutationrate,
                                     num_elites = numelites,
                                     num_crossover_points = 3,
                                     local_opt_rate = local_opt_rate,
                                     statistics_file=stat_file,
                                     #individuals_file=ind_file
                                     )

        print('Terminated due to {0}.'.format(my_ec.termination_cause))

        best_sol = max(final_pop).candidate

        res = {}
        res["popsize"] = popsize
        res["evals"] = maxevals
        res["selected"] = numselected
        res["elites"] = numelites
        res["mutation_rate"] = mutationrate
        res["local_rate"] = local_opt_rate

        if self.opt_rout_weig:
            size_assig = len(self.ord_users)*len(self.ord_services)
            assig = self.decode_serv_assig(best_sol[:size_assig])
            w = self.decode_weights(best_sol[size_assig:])
            res["of_value"] = self.composite.of_normalized_penalty(assig, True, self.mincost, 
                                                      sp_weights = w)
            of = self.composite.of_normalized_penalty(assig, False, self.mincost, 
                                                      sp_weights = w, return_dic = True)
            res["of_fh"] = of["fh"]
            res["of_e2e"] = of["e2e"]
            res["of_cost"] = of["cost"]
            res["of_cong"] = of["cong"]

        else:
            assig = self.decode_serv_assig(best_sol)
            res["of_value"] = self.composite.of_normalized_penalty(assig, True, self.mincost)
            of = self.composite.of_normalized_penalty(assig, False, self.mincost,
                                                      return_dic = True)
            res["of_fh"] = of["fh"]
            res["of_e2e"] = of["e2e"]
            res["of_cost"] = of["cost"]
         
            if not self.composite.congestion_cost: ## reporting congestion even if not used in the optimization
                dem = self.composite.generate_e2e_demands(assig.dic_assig)
                l = Loads(self.composite.network)
                l.add_loads_from_paths(self.composite.del_paths, dem)
                if self.composite.cong_of == "mlu": cong = l.mlu()[0]
                elif self.composite.cong_of == "alu": cong = l.alu()
                elif self.composite.cong_of == "fortz": 
                    co = CongestionOptimization(self.composite.network,dem)
                    phiu = co.phi_uncap()
                    cong = l.fortz_of(phiu) - 1.0
                print("Congestion (not optimized):", cong)
                res["of_cong"] = cong
            else:
                res["of_cong"] = of["cong"]
        
        print("Objective function value: ", res["of_value"])

        if save_file is not None:
            stat_file.close()
            #ind_file.close()

        return assig, res


    def run_mo(self, ea_pars = {}, display = True, plot = False, save_file = None):
        
        popsize = ea_pars.get("pop_size", 100)
        maxevals = ea_pars.get("max_evaluations", 10000)
        mutationrate = ea_pars.get("mutation_rate", 0.05)
        local_opt_rate = ea_pars.get("local_opt_rate", 0.2)
        if self.composite.congestion_cost:
            num_objectives = 3
        else:
            num_objectives= 2
        
        if display:
            print("Population size: ", popsize)
            print("Number evaluations: ", maxevals)
            print("Local opt rate: ", local_opt_rate)
        
        lower_limits = [0]*(len(self.ord_users)*len(self.ord_services))
        upper_limits = []
        for u in range(len(self.ord_users)):
            for k in range(len(self.ord_services)):
                upper_limits.append(self.number_servers[k]-1)
        
        if self.opt_rout_weig:
            lower_limits.extend ( [0]*self.composite.network.number_edges() )    
            upper_limits.extend ( [self.maxw] * self.composite.network.number_edges() )

        rand = Random()
        rand.seed(int(time()))
        
        my_ec = inspyred.ec.emo.NSGA2(rand)
          
        if self.opt_rout_weig:
            my_ec.variator = [inspyred.ec.variators.n_point_crossover,
                              inspyred.ec.variators.random_reset_mutation,
                              self.single_inteligent_mut,
                              self.increment_mut,
                              self.mo_inteligent_mut
                              ]
        else:
            my_ec.variator = [inspyred.ec.variators.n_point_crossover,
                              inspyred.ec.variators.random_reset_mutation,
                              self.single_inteligent_mut,
                              self.increment_mut,
                              self.mo_inteligent_mut
#                              self.improve_user_assig
                              ]
        
        my_ec.terminator = inspyred.ec.terminators.evaluation_termination
        
        if display:
            my_ec.observer = inspyred.ec.observers.archive_observer

        my_ec.evolve(generator=self.generate_solution_random,
                     evaluator=self.evaluate_serv_mo,
                     maximize = False,   ### set to True if maximizing utility
                     pop_size=popsize,
                     max_archive_size=popsize,
                     bounder=inspyred.ec.Bounder(lower_limits, upper_limits),
                     max_evaluations=maxevals,
                     mutation_rate = mutationrate,
                     num_crossover_points = 3,
                     local_opt_rate = local_opt_rate
                     )
        
        final_arc = my_ec.archive
        
        res = {}
        res["popsize"] = popsize
        res["evals"] = maxevals
        res["mutation_rate"] = mutationrate
        res["local_rate"] = local_opt_rate
        
        if save_file is not None:
            f = open(save_file + "-archive.txt", "w")
            f.write("Delays" + "\t")
            f.write("Cost")
            if num_objectives > 2: f.write("\tCongestion")
            f.write("\n")
            for sol in final_arc: 
                f.write(str(sol.fitness[0]) + "\t")
                f.write(str(sol.fitness[1]))
                if num_objectives > 2: 
                    f.write("\t" + str(sol.fitness[2]) )
                f.write("\n")
            f.close()
        elif display:
            print(final_arc)
            if plot: 
                x = []
                y = []
                z = []
                for f in final_arc:
                    x.append(f.fitness[0])
                    y.append(f.fitness[1])
                    if num_objectives > 2: 
                        z.append(f.fitness[2])
                plt.plot(x, y, 'bo')
                plt.xlabel("Latency penalties")
                plt.ylabel("Cost penalties")
                plt.show()
                plt.clf()
                if num_objectives > 2:
                    plt.plot(x, z, 'ro')
                    plt.xlabel("Latency penalties")
                    plt.ylabel("Congestion penalty")
                    plt.show()
                    plt.clf()
                    
                    plt.plot(y, z, 'go')
                    plt.ylabel("Congestion penalty")
                    plt.xlabel("Cost penalties")
                    plt.show()
                    
        return res


#### RUN SCRIPT ####
## for command line usage ###

def run():
    ## FORMAT: type_optimization network_file services_tree instance_file results_file
    ## type_optimization:
    ##      nc - no congestion
    ##      d - congestion costs; shortest path delays
    ##      sp - congestion costs; EA optimizing weights
    ##      oc - congestion costs; MILP optimizaing congestion
    ## lnc, ld, lsp, loc - the same as before but with loops on the service tree
    
    
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
    ## -w weights - weights for the OF - fh, e2e, cost, congestion (split by ,)
    
    network_file = sys.argv[2]
    n = Network(network_file, "sndlib")#, engine = "igraph")
    
    filename_tree = sys.argv[3]
    if sys.argv[1][0] == "l":
        loops = True
    else:
        loops = False
    t = ServicesTree(loops, filename_tree)
    
    servers_file = sys.argv[4] + "-costs.txt"
    s = Servers(t, n, servers_file)

    users_dem_file = sys.argv[4] + "-users.txt"
    users_top_file = sys.argv[4] + "-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)

    optimize_routing_weig = False
    if sys.argv[1] == "nc" or sys.argv[1] == "lnc":
        cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = False, 
                               cong_of = "fortz")
    elif sys.argv[1] == "d" or sys.argv[1] == "ld":
        cs = CompositeServices(n, t, s, u, opt_cong = False, congestion_cost = True,
                               cong_of = "fortz")
    elif sys.argv[1] == "oc" or sys.argv[1] == "loc":
        cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True,
                               cong_opt_method = "milp", cong_of = "fortz")
    elif sys.argv[1] == "sp" or sys.argv[1] == "lsp": 
        cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True,
                               cong_opt_method = "sp", cong_of = "fortz")
        optimize_routing_weig = True

    ## options 
    par = False
    maxcpus = 1
    multiobj = False
    numruns = 1
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
            elif sys.argv[i] == "-ev":
                eapars["max_evaluations"] = int(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == "-mr":
                eapars["mutation_rate"] = float(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == "-lr":
                eapars["local_opt_rate"] = float(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == "-r":
                numruns = int(sys.argv[i+1])
                i += 2
            elif sys.argv[i] == "-w":
                wstr = sys.argv[i+1]
                tokens = wstr.split(",")
                w = {}
                w["fh"] = float(tokens[0])
                w["e2e"] = float(tokens[1])
                w["cost"] = float(tokens[2])
                if cs.congestion_cost and len(tokens) > 3: 
                    w["congestion"] = float(tokens[3])
                cs.set_weights(w)
                print(cs.weights)
                i += 2
            else:
                print("Invalid option")
                sys.exit(1)
    
    res = {}
    
    if multiobj:
        res_keys = ["type", "network", "tree", "instance",
                    "popsize", "evals", "mutation_rate", "local_rate"]
    else:
        res_keys = ["type", "network", "tree", "instance", 
                    "popsize", "evals", "selected", "elites", "mutation_rate", "local_rate",
                    "of_value", "of_cost", "of_e2e", "of_fh", "of_cong"]
        
    for k in res_keys:
        res[k] = []

    network_name = sys.argv[2].split("/").pop()
    tree_name = sys.argv[3].split("/").pop()
    instance_name = sys.argv[4].split("/").pop()
      
    for r in range(numruns):
        
        start = timeit.default_timer()
        
        ea = EACompositeServices(cs,optimize_routing_weights = optimize_routing_weig)
    
        res["type"].append(sys.argv[1])
        res["network"].append(network_name)
        res["tree"].append(tree_name)
        res["instance"].append(instance_name)
    
        if multiobj:
            file_run = sys.argv[5] + "-run" + str(r)
            res_ea = ea.run_mo(ea_pars = eapars, display = False, save_file = file_run)
            
            #res["popsize"].append(res_ea["popsize"])
            #res["evals"].append(res_ea["evals"])
            #res["mutation_rate"].append(res_ea["mutation_rate"])
            #res["local_rate"].append(res_ea["local_rate"])
            
            #res_pd = pd.DataFrame(data = res)
            #res_pd.to_csv(sys.argv[5] + "-results.csv")
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
                res["selected"].append(res_ea["selected"])
                res["elites"].append(res_ea["elites"])
                res["mutation_rate"].append(res_ea["mutation_rate"])
                res["local_rate"].append(res_ea["local_rate"])
                
                res_pd = pd.DataFrame(data = res)
                res_pd.to_csv(sys.argv[5] + "-results.csv")

        stop = timeit.default_timer()
        print('Time EA: ', stop - start) 

if __name__ == '__main__': 
    run()