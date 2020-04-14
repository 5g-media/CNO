#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 23 16:22:44 2018

@author: miguelrocha
"""

from random import Random
from time import time
import inspyred

from netcore.topology import Network
from congopt.congoptim import CongestionOptimization
from netcore.demands import Demands

import timeit

class EACongestion:
    
    def __init__(self, network, demands, max_weight = 20, ecmp = True):
        self.network = network
        self.demands = demands
        self.max_weight= max_weight
        self.congestion = CongestionOptimization(self.network, self.demands)
        self.allow_ecmp = ecmp
        self.stop = timeit.default_timer()
        
    def generate_solution_random(self, random, args):
        from random import randint
         
        res = []    
        for i in range(self.network.number_edges()):
            res.append(randint(1, self.max_weight))
                
        return res
    
    def decode_solution(self, sol):
        L = self.network.link_ids()
        w = {}
        for i, e in enumerate(L):
            w[e] = sol[i]
        return w
    
    def evaluate_solutions(self, candidates, args):
        fitness = []
        for cs in candidates:
            w = self.decode_solution(cs)
            if self.allow_ecmp:
                self.start = timeit.default_timer()
                #print('Time else: ', self.start - self.stop) 
                fit = self.congestion.sp_congestion_ties(w, self.of, False)[0]
                self.stop = timeit.default_timer()
                #print('Time eval: ', self.stop - self.start) 
            else:
                fit = self.congestion.sp_congestion(w, self.of, False)[0]
            fitness.append(fit)
        
        return fitness
    
    def increment_mut(self, random, candidates, args):
        import copy

        mutants = []
        for candidate in candidates:        
            if random.random() < 0.5:    
                numchanges = random.randint(1,4)
                for k in range(numchanges):
                    mutant = copy.copy(candidate)
                    pos = random.randint(0,len(candidate)-1)
                    current = mutant[pos]    
                    
                    f = random.random()
                    if f > 0.5:
                        if current == self.max_weight:
                            mutant[pos] = 1
                        else: mutant[pos] = current + 1
                    else:
                        if current == 1:
                            mutant[pos] = self.max_weight
                        else: mutant[pos] = current - 1
                mutants.append(mutant)    
            else:
                mutants.append(candidate)
        return mutants
    
    def run_evol_alg(self, ea_pars = {}, of = "mlu", display = True): 
        
        self.of = of
        
        popsize = ea_pars.get("pop_size", 100)
        maxevals = ea_pars.get("max_evaluations", 20000)
#        tournamentsize = ea_pars.get("tournament_size", 20)
        numselected = ea_pars.get("num_selected", 50)
        mutationrate = ea_pars.get("mutation_rate", 0.002)
        numelites = ea_pars.get("num_elites", 20)
        
        lower_limits = [1]* self.network.number_edges()
        upper_limits = [self.max_weight] * self.network.number_edges() 
    
        rand = Random()
        rand.seed(int(time()))
        my_ec = inspyred.ec.EvolutionaryComputation(rand)
        #my_ec.selector = inspyred.ec.selectors.tournament_selection
        my_ec.selector = inspyred.ec.selectors.rank_selection
        my_ec.variator = [inspyred.ec.variators.uniform_crossover, 
                          inspyred.ec.variators.random_reset_mutation,
                          self.increment_mut
                          ]
        #my_ec.replacer = inspyred.ec.replacers.steady_state_replacement
        my_ec.replacer = inspyred.ec.replacers.generational_replacement
        my_ec.terminator = inspyred.ec.terminators.evaluation_termination
        if display:
            my_ec.observer = inspyred.ec.observers.stats_observer
            
        final_pop = my_ec.evolve(generator=self.generate_solution_random,
                                     evaluator=self.evaluate_solutions,
                                     maximize = False,   ### set to True if maximizing utility
                                     pop_size=popsize,
                                     bounder=inspyred.ec.Bounder(lower_limits, upper_limits),
                                     max_evaluations=maxevals,
                                     num_selected=numselected, 
                                     mutation_rate = mutationrate,
#                                     tournament_size= tournamentsize,
                                     num_elites = numelites
                                     )

        print('Terminated due to {0}.'.format(my_ec.termination_cause))
        best_sol = max(final_pop).candidate
        print(best_sol)


def test1():
    network_file = "../Networks/isno_5_2"
    n = Network(network_file)

    dem = Demands(n)
    dem.add_demands("0","1",1000)
    dem.add_demands("0","2",1000)
    dem.add_demands("0","3",1000)
    dem.add_demands("0","4",1000)
    dem.add_demands("1","0",1000)
    dem.add_demands("1","2",1000)
    dem.add_demands("1","3",1000)
    dem.add_demands("1","4",1000)
    dem.add_demands("2","0",1000)
    dem.add_demands("2","1",1000)
    dem.add_demands("2","3",1000)
    dem.add_demands("2","4",1000)    
    dem.add_demands("3","0",1000)    
    dem.add_demands("3","1",1000)
    dem.add_demands("3","2",1000)
    dem.add_demands("3","4",1000)
    dem.add_demands("4","0",1000)
    dem.add_demands("4","1",1000)
    dem.add_demands("4","2",1000)
    dem.add_demands("4","3",1000)
    
    ea = EACongestion(n, dem)

    ea.run_evol_alg()

def test2():
    n = Network("../Networks/germany50.txt", "sndlib")
    d = Demands(n, "../Networks/germany50.txt")
    ea = EACongestion(n, d)
    print("Starting EA")
    ea.run_evol_alg()
    
def test3():
    n = Network("../Networks/isno_30_4", engine = "igraph")
    #print(n)
    d = Demands(n, "../Networks/isno_30_4-D0.2.dem", "csv")
    
    start = timeit.default_timer()
    
    ea = EACongestion(n, d, ecmp = True)
    
    print("Starting EA")
    ea_pars = {}
    ea_pars["max_evaluations"] = 10000
    ea.run_evol_alg(ea_pars, of = "fortz")
    stop = timeit.default_timer()
    print('Time EA: ', stop - start) 
    #ea.run_evol_alg()

def test4():
    ### incomplete 
    
    sol = [2, 3, 6, 19, 19, 2, 14, 1, 19, 14, 15, 17, 10, 13, 3, 14, 11, 12, 9, 5, 4, 6, 5, 7, 19, 5, 2, 7, 10, 3, 1, 15, 10, 14, 1, 1, 4, 11, 0, 3, 14, 0, 4, 4, 12, 9, 4, 13, 14, 4, 12, 10, 8, 9, 8, 19, 7, 14, 2, 13, 11, 3, 4, 18, 16, 14, 11, 4, 5, 11, 9, 13, 13, 3, 19, 8, 4, 6, 6, 11, 11, 2, 17, 13, 7, 11, 10, 15, 19, 19, 5, 6, 18, 5, 6, 6, 16, 3, 9, 4, 0, 11, 19, 19, 11, 10, 8, 3, 3, 1, 2, 15, 4, 1, 19, 16, 7, 18, 6, 15, 8, 18, 2, 19, 5, 7, 9, 13, 13, 15, 3, 19, 11, 11, 10, 16, 8, 11, 14, 8, 16, 7, 12, 10, 2, 1, 0, 14, 6, 0, 19, 12, 4, 0, 7, 13, 10, 17, 11, 14, 15, 9, 11, 14, 8, 13, 7, 12, 8, 16, 8, 11, 11, 14, 12, 11, 2, 16, 15, 5, 15, 19, 15, 14, 15, 19, 5, 3, 11, 1, 2, 11, 2, 8, 4, 10, 2, 13, 2, 3, 15, 2, 10, 9, 8, 11, 5, 5, 18, 19, 15, 16, 12, 7, 2, 2, 1, 4, 9, 7] 
    print(len(sol))
    for i in range(len(sol)):
        sol[i] += 1
    n = Network("Networks/isno_30_4")
    print(n.number_edges())
    d = Demands(n, "Networks/isno_30_4-D0.1.dem", "csv")
    ea = EACongestion(n, d)
    
    #w = {}
    #for 
    #    w[e] = sol[i]
    
    w = ea.decode_solution(sol)
    fit = ea.congestion.sp_congestion_ties(w, "fortz", False)[0]
    print(fit)
    
test3()    