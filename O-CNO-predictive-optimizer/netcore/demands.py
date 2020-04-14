#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  5 23:29:26 2018

@author: miguelrocha
"""

from netcore.topology import Network
import xml.etree.ElementTree as ET

class Demands:
    
    def __init__(self, network, filename = None, format_file="sndlib"):
        self.network= network
        self.demands = {}
        if filename is not None:
            if format_file == "sndlib":
                self.read_demands_sndlib(filename)
            elif format_file == "csv":
                self.read_demands_csv(filename)
        
    def read_demands_sndlib(self, filename):
        f = open(filename)
        while not f.readline().strip().startswith("DEMANDS"): 
            pass
        line = f.readline().strip()
        while not line.startswith(")"):
            tokens = line.split(" ")
            src_node = tokens[2]
            dst_node = tokens[3]
            dem = float(tokens[6])
            self.demands[(str(src_node), str(dst_node))] = dem
            line = f.readline().strip()
        f.close()
     
    def read_demands_csv(self, filename, sep = " "):
        f = open(filename)
        for s in self.network.nodes.keys():
           line = f.readline().strip()
           tokens = line.split(sep)
           i = 0
           for d in self.network.nodes.keys():
               dem = float(tokens[i])
               if dem > 0 and s != d: self.demands[(s,d)] = dem
               i += 1
        f.close()

    def read_demands_xml_uhlig(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        DM = root[1]
        for src in DM:
            src_id = src.attrib['id']
            for dst in src:
                dst_id = dst.attrib['id']
                demand = float(dst.text) * 1000/1000000 * 8# / (15*60) # Converting bytes (with 1/1000 sampling) to Mb(ps)
                self.demands[(src_id,dst_id)] = demand
        
    def __str__(self):
        res = "Demands:\n"
        for k in self.demands.keys():
            res += str(k) + "->" + str(self.demands[k]) + "\n"
        return res
    
    def __len__(self):
        return len(self.demands)
    
    def get_demands(self, src, dest):
        return self.demands.get((src, dest), None)
    
    def list_e2e_demands(self):
        return self.demands.keys()
    
    def total_demands(self):
        return sum(self.demands.values())
    
    def add_demands(self, src, dest, value):
        if (src, dest) in self.demands:
            self.demands[(src, dest)] += value
        else:
            self.demands[(src, dest)] = value
    
    def multiply_demands(self, multiplier):
        for k in self.demands.keys():
            self.demands[k] *= multiplier
    
### testing ###
    
def test1():
    n = Network("../Networks/germany50.txt", "sndlib")
    print(n)
    print(n.list_nodes())
    print(n.list_edges())
    d = Demands(n, "../Networks/germany50.txt")
    print(d)
    print(len(d))

def test2():
    n = Network("../Networks/isno_30_4")
    print(n)
    d = Demands(n, "../Networks/isno_30_4-D0.1.dem", "csv")
    print(d)

if __name__ == '__main__':     
    #test1()
    test2()