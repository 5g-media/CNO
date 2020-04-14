#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 11:00:25 2018

@author: miguelrocha
"""

class Loads:
    
    def __init__(self, network):
        self.network = network
        self.loads = {}
        
    def __getitem__(self, i):
        return self.loads.get(i, 0)
    
    def get_link_load (self, link):
        return self.loads.get(link, 0.0)
        
    def add_load(self, link, value):
        if link in self.loads:
            self.loads[link] += value
        else:
            self.loads[link] = value
            
    def subtract_load(self, link, value):
        if link in self.loads:
            if self.loads[link] > value:
                self.loads[link] -= value
            else: # remove the entry from the loads
                self.loads.pop(link)

    # path - list links
    def add_loads_path(self, path, demand):
        for e in path:
            self.add_load(e, demand)
    
    def sub_loads_path(self, path, demand):
        for e in path:
            self.subtract_load(e, demand)
    
    def add_loads_from_paths(self, paths, demands):
        for (s,d) in demands.list_e2e_demands():
            demand = demands.get_demands(s,d)
            p = paths[(s,d)]
            self.add_loads_path(p, demand)          
    
    def loads_from_link_fvars(self, links, demands):
        for (e, i, j) in links.keys():
            v = demands.get_demands(i, j) * links[(e,i,j)]
            self.add_load(e, v)
    
    def link_utilization(self, link_id):
        if link_id in self.loads:
            return self.loads[link_id] / self.network.link_capacity(link_id)
        else: return 0.0
    
    def as_list(self):
        res = []
        E = self.network.link_ids()
        for e in E:
            res.append(self[e])
        return res
    
    def mlu(self):
        mlu = 0.0
        mlu_link = None
        for e in self.loads:
            u = self.link_utilization(e)
            if u > mlu: 
                mlu = u
                mlu_link = e
        return mlu, mlu_link
    
    def alu(self):
        sum_lu = 0.0
        for e in self.network.link_ids():
            u = self.link_utilization(e)
            sum_lu += u
        return sum_lu / self.network.number_edges()
    
    def fortz_of(self, phi_uncap = 1.0):
        sum_p = 0.0
        for e in self.network.link_ids():
            u = self.link_utilization(e)
            l = self.get_link_load(e)
            if u < 1.0/3.0: 
                sum_p += l
            elif u < 2.0 / 3.0: 
                sum_p += 3.0*l-2.0/3.0*self.network.link_capacity(e)
            elif u < 0.9:
                sum_p += 10.0*l-16.0/3.0*self.network.link_capacity(e)
            elif u < 1.0:
                sum_p += 70.0*l-178.0/3.0*self.network.link_capacity(e)
            elif u < 1.1:
                sum_p += 500.0*l-1468.0/3.0*self.network.link_capacity(e)
            else:
                sum_p += 5000.0*l-16318.0/3.0*self.network.link_capacity(e)
        return sum_p / phi_uncap
    