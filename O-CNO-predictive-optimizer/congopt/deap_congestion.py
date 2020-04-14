#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  6 12:27:07 2018

@author: miguelrocha
"""

import random
import timeit
#import array
import numpy

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

from netcore.topology import Network
from congopt.congoptim import CongestionOptimization
from netcore.demands import Demands

class DeapCongestion:

    def __init__(self, network, demands, max_weight = 20, ecmp = True):
        self.network = network
        self.demands = demands
        self.max_weight= max_weight
        self.congestion = CongestionOptimization(self.network, self.demands)
        self.allow_ecmp = ecmp
    
    def decode_solution(self, sol):
        L = self.network.link_ids()
        w = {}
        for i, e in enumerate(L):
            w[e] = sol[i]
        return w
    
    def evaluate_solution(self, individual):
        w = self.decode_solution(individual)
        if self.allow_ecmp:
            fit = self.congestion.sp_congestion_ties(w, self.of, False)[0]
        else:
            fit = self.congestion.sp_congestion(w, self.of, False)[0]
        
        return fit,

    def run_evol_alg(self, ea_pars = {}, of = "mlu", display = True): 
        
        self.of = of

        popsize = ea_pars.get("pop_size", 100)

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        
        toolbox = base.Toolbox()
        # Attribute generator 
        toolbox.register("attr_int", random.randint, 1, self.max_weight)
        # Structure initializers
        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_int, 
                         self.network.number_edges())
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
        toolbox.register("evaluate", self.evaluate_solution)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutUniformInt, low = 1, up = self.max_weight, indpb=0.05)
        toolbox.register("select", tools.selTournament, tournsize=3)
        
        pop = toolbox.population(n=popsize)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)
        
        pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=200, 
                                       stats=stats, halloffame=hof, verbose=True)
        
        return pop, log, hof
    
def test1():
    n = Network("../Networks/isno_30_4")
    #print(n)
    d = Demands(n, "../Networks/isno_30_4-D0.2.dem", "csv")
    ea = DeapCongestion(n, d, ecmp = True)
    print("Starting EA")
    start = timeit.default_timer()
    ea.run_evol_alg(of = "fortz")
    stop = timeit.default_timer()
    print('Time EA: ', stop - start) 
    
test1()