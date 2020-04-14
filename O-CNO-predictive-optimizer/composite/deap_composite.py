#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

import sys
import numpy

sys.path.append('..')
from netcore.topology import Network
from netcore.loads import Loads
from congopt.congoptim import CongestionOptimization
from users import Users
from services import ServicesTree
from servers import Servers
from composite import CompositeServices
from solution_comp import ServicesAssignment

import random

class DeapComposite:
    
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
    
    
    def generate_solution_random(self):
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
    
    def evaluate_serv_assig(self, individual):       
        if self.opt_rout_weig:
            size_assig = len(self.ord_users)*len(self.ord_services)
            assig = self.decode_serv_assig(individual[:size_assig])
            w = self.decode_weights(individual[size_assig:])
            fit = self.composite.of_normalized_penalty(assig, False, self.mincost, sp_weights = w)
        else:
            assig = self.decode_serv_assig(individual)
            fit = self.composite.of_normalized_penalty(assig, False, self.mincost)
        
        return fit,


    def evaluate_serv_mo(self, individual):
        if self.opt_rout_weig:
            size_assig = len(self.ord_users)*len(self.ord_services)
            assig = self.decode_serv_assig(individual[:size_assig])
            w = self.decode_weights(individual[size_assig:])
            fo = self.composite.of_normalized_penalty(assig, False, self.mincost, 
                                                       sp_weights = w, return_dic = True)
        else:
            assig = self.decode_serv_assig(individual)
            fo = self.composite.of_normalized_penalty(assig, False, self.mincost,
                                                       return_dic = True)
        del_pen = (fo["fh"] + fo["e2e"])/ 2.0
        if self.composite.congestion_cost:
            return del_pen, fo["cost"], fo["cong"]
        else:
            return del_pen, fo["cost"]


    def single_inteligent_mut(self, individual, localrate = 0.2, maxtries = 50):
        import copy

        maxpos = len(self.ord_users)*len(self.ord_services)  
        if random.random() < localrate: 
            numtries = random.randint(1,maxtries)
            mutant = copy.copy(individual)
            # compute fitness of original candidate
            if self.opt_rout_weig:
                    assig_dic = self.decode_serv_assig(individual[:maxpos])
                    w = self.decode_weights(individual[maxpos:])
                    cur_fit = self.composite.of_normalized_penalty(assig_dic, False, 
                                                                   self.mincost, sp_weights = w)
            else:
                    assig_dic = self.decode_serv_assig(individual)
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
                a = random.choice(alternatives)
                if len(alternatives) <= 1: 
                    return individual,
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
        else:
            max_assig = len(self.ord_users)*len(self.ord_services)
            #return individual,
            if random.random() < 0.5:
                numchanges = random.randint(1,3)
                for k in range(numchanges):
                    mutant = copy.copy(individual)
                    pos = random.randint(0,len(individual)-1)
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
            else:
                mutant = copy.copy(individual)
                pos = random.randint(0,len(individual)-1)
                if pos < max_assig:
                    s = pos%len(self.ord_services)
                    mutant[pos] = random.randint(0,self.number_servers[s] -1)
                else:
                    mutant[pos] = random.randint(0,self.maxw)
        return mutant,


    def run_evol_alg(self, ea_pars = {}, of = "mlu", parallel = None, max_cpus = 1, save_file = None): 
        
        ## parallel & max_cpus - being ignored for now !!!!
        ## save_file as well 
        
        self.of = of

        popsize = ea_pars.get("pop_size", 100)
        maxevals = ea_pars.get("max_evaluations", 10000)
        localrate = ea_pars.get("local_opt_rate", 0.2)

        numgen = int(maxevals / popsize) + 1
        
        indsize = len(self.ord_users)*len(self.ord_services)
        if self.opt_rout_weig:
            indsize += self.composite.network.number_edges()

        #lower_limits = [0]*(len(self.ord_users)*len(self.ord_services))
        upper_limits = []
        for u in range(len(self.ord_users)):
            for k in range(len(self.ord_services)):
                upper_limits.append(self.number_servers[k]-1)
        
        if self.opt_rout_weig:
            #lower_limits.extend ( [0]*self.composite.network.number_edges() )    
            upper_limits.extend ( [self.maxw] * self.composite.network.number_edges() )

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        
        toolbox = base.Toolbox()
        
        toolbox.register("individual", tools.initIterate, creator.Individual, self.generate_solution_random)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
        toolbox.register("evaluate", self.evaluate_serv_assig)
#        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mate", tools.cxUniform, indpb = 0.05)
        toolbox.register("mutate", self.single_inteligent_mut, localrate=localrate, maxtries = 50)
#        toolbox.register("mutate", tools.mutUniformInt, low = 1, up = upper_limits, indpb=0.05)

        toolbox.register("select", tools.selTournament, tournsize=3)
        
        pop = toolbox.population(n=popsize)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)
        
        pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=1.0, ngen=numgen, 
                                       stats=stats, halloffame=hof, verbose=True)
        
        #print(pop)
        #print(log)
        best_sol = hof[0]
        
        res = {}
        res["popsize"] = popsize
        res["evals"] = maxevals
        
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

#   NEED TO CHECK HOW TO SAVE Logbook to file
#        if (save_file is not None):
#            f = open(save_file, "w")
#            f.write(log)
#            f.close()

        return assig, res
        #return pop, log, hof
    
    
    def run_mo(self, ea_pars = {}, display = True):
        
        popsize = ea_pars.get("pop_size", 100)
        maxevals = ea_pars.get("max_evaluations", 10000)

#        mutprob = ea_pars.get("mut_rate", 0.05)
        localrate = ea_pars.get("local_opt_rate", 0.2)
        algorithm = ea_pars.get("algorithm", "eaMuPlusLambda")
        
        numgen = int(maxevals / popsize) + 1
        
        indsize = len(self.ord_users)*len(self.ord_services)
        if self.opt_rout_weig:
            indsize += self.composite.network.number_edges()
            
               #lower_limits = [0]*(len(self.ord_users)*len(self.ord_services))
        upper_limits = []
        for u in range(len(self.ord_users)):
            for k in range(len(self.ord_services)):
                upper_limits.append(self.number_servers[k]-1)
        
        if self.opt_rout_weig:
            #lower_limits.extend ( [0]*self.composite.network.number_edges() )    
            upper_limits.extend ( [self.maxw] * self.composite.network.number_edges() )

        if self.composite.congestion_cost:
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,-1.0,-1.0))
        else:
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,-1.0))    
            
        creator.create("Individual", list, fitness=creator.FitnessMin)
                
        toolbox = base.Toolbox()
        
        toolbox.register("individual", tools.initIterate, creator.Individual, self.generate_solution_random)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
        toolbox.register("evaluate", self.evaluate_serv_mo)
        toolbox.register("mate", tools.cxTwoPoint)
        
        toolbox.register("mutate", self.single_inteligent_mut, localrate=localrate, maxtries = 50)
#        toolbox.register("mutate", tools.mutUniformInt, low = 1, up = upper_limits, indpb=mutprob)

        toolbox.register("select", tools.selNSGA2)
        if algorithm == "spea":
            toolbox.register("select", tools.selSPEA2)
    
        pop = toolbox.population(n=popsize)
        
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean, axis=0)
#        stats.register("std", numpy.std, axis = 0)
        stats.register("min", numpy.min, axis=0)
#        stats.register("max", numpy.max, axis = 0)
        
        if algorithm == "eaMuPlusLambda" or algorithm == "spea":
            pop = toolbox.select(pop, len(pop))
            hof = tools.ParetoFront()

            algorithms.eaMuPlusLambda(pop, toolbox, mu=popsize, 
                                         lambda_= popsize, 
                                         cxpb=0.5,
                                         mutpb=0.5, 
                                         stats=stats, 
                                         ngen=numgen, 
                                         halloffame=hof,
                                         verbose=display)
            
            front = numpy.array([ind.fitness.values for ind in hof])
            
        elif algorithm == "nsga":
            invalid_ind = [ind for ind in pop if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            pop = toolbox.select(pop, len(pop))
            
            logbook = tools.Logbook()
            logbook.header = "gen", "evals", "avg", "min"
            record = stats.compile(pop)
            logbook.record(gen=0, evals=len(invalid_ind), **record)
            print(logbook.stream)
                      
            for gen in range(1, numgen):
                offspring = tools.selTournamentDCD(pop, len(pop))
                offspring = [toolbox.clone(ind) for ind in offspring]
        
                for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
                    if random.random() <= 0.9:
                        toolbox.mate(ind1, ind2)
        
                    toolbox.mutate(ind1)
                    toolbox.mutate(ind2)
                    del ind1.fitness.values, ind2.fitness.values
        
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit
        
                pop = toolbox.select(pop + offspring, len(pop))
        
                record = stats.compile(pop)
                logbook.record(gen=gen, evals=len(invalid_ind), **record)
                print(logbook.stream)
        
            front = numpy.array([ind.fitness.values for ind in pop])
        
        print(front)
        
        return pop, stats, front

def test1():
    #network_file = "../Networks/isno_30_4"
    network_file = "../Networks/geant.txt"
    n = Network(network_file, "sndlib")
    
    filename_tree = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename_tree)
    
#    servers_file = "../DataComposite/isno_30_4-t1-costs.txt"
    servers_file = "../DataComposite/geant-t3-costs.txt"
    s = Servers(t, n, servers_file)

    users_dem_file = "../DataComposite/geant-t3-users.txt"
#    users_dem_file = "../DataComposite/isno_30_4-t1-users.txt"
    users_top_file = "../DataComposite/geant-t3-user_topo.txt"
#    users_top_file = "../DataComposite/isno_30_4-t1-user_topo.txt"
    u = Users(n, users_dem_file, users_top_file)
    
    cs = CompositeServices(n, t, s, u, opt_cong = True, congestion_cost = True,
                           cong_opt_method = "sp", cong_of = "fortz")    
    
    print("Starting EA:")
    ea = DeapComposite(cs,optimize_routing_weights = True)
    
    #ea.run_evol_alg({"num_gens": 100})
    
    _, _, f = ea.run_mo({"max_evaluations": 10000, "algorithm": "spea"})
    
    numpy.savetxt("front.csv", f)

if __name__ == '__main__': 
    test1()