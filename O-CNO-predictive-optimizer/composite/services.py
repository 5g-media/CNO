#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  6 13:49:06 2018

@author: miguelrocha
"""

class ServicesTree:
    
    def __init__(self, loops = False, filename = None, sep = ":", sep2 = ","):
        self.tree = {}
        self.loops = loops
        if filename is not None: 
            self.read_service_tree(filename, sep, sep2)
    
    ## reads file with tree defining services
    def read_service_tree(self, filename, sep = ":", sep2 = ","):
        f = open(filename)
        self.tree = {}
        self.root = None
        for lines in f:
            if not lines.startswith("#"):
                tokens = lines.split(sep)
                key = tokens[0].strip()
                if self.root is None: self.root = key
                values = tokens[1].strip()
                l = []
                if len(values) > 0:
                    tokens2 = values.split(sep2)
                    for t in tokens2:
                        l.append(t.strip())
                self.tree[key] = l
        f.close()
    
    def tree(self):
        return self.tree
    
    def root(self):
        return self.root
    
    def root_service(self):
        if self.loops: 
            return remove_index_fromid(self.root)
        else: 
            return self.root
    
    def __str__(self):
        res = "Service tree:\n"
        res += "Root: " + str(self.root) + "\n"
        res += "Tree\n"
        for (k,v) in self.tree.items():
            res += (str(k) + " -> " + str(v) + "\n")
        return res
    
    def __len__(self):
        return len(self.services_list_from_tree())
    
    def has_loops(self):
        return self.loops

    def branches(self, node):
        return self.tree[node]
       
    def services_list_from_tree(self):
        res = []
        current = [self.root]
        while current != []:
            node = current.pop()
            if self.loops: 
                node_without_id = remove_index_fromid(node)
                if node_without_id not in res:
                    res.append(node_without_id)
            else: 
                if node not in res: res.append(node)
            neigs = self.tree[node]
            for n in neigs:
                current.append(n)
        return res

    def predecessor_in_tree(self, s):
        if self.loops: 
            print("Warning !! Tree has loops - use all_predecessors_in_tree")
            return None
        for k in self.tree.keys():
            if s in self.tree[k]: 
                return k
        return None

    def get_all_edges_fromtree(self):
        res = []
        for k in self.tree.keys():
            for d in self.tree[k]:
                if self.loops:
                    res.append( (remove_index_fromid(d), remove_index_fromid(k)) )
                else:
                    res.append((d,k))
        return res

    def all_predecessors_in_tree(self, s): ## trees with loops
        res = []
        if self.loops:
            for k in self.tree.keys():
                for suc in self.tree[k]:
                    if remove_index_fromid(suc) == s:
                        res.append(k)
        else: res.append(self.predecessor_in_tree(s))
        return res
    
def remove_index_fromid(idnode):
    tokens = idnode.split("-")
    return tokens[0]

## Testing ##

def test1():
    filename = "../DataComposite/linear_structure.txt"
    loops = False
    t = ServicesTree(loops, filename)
    print(t)
    print(t.services_list_from_tree())
    
def test2():
    filename = "../DataComposite/linear_structure_loops.txt"
    loops = True
    t = ServicesTree(loops, filename)
    print(t)
    print(t.services_list_from_tree())

def test3():
    filename = "../DataComposite/tree_structure.txt"
    loops = False
    t = ServicesTree(loops, filename)
    print(t)
    print(t.services_list_from_tree())    

def test4():
    filename = "../DataComposite/tree_structure_loops.txt"
    loops = True
    t = ServicesTree(loops, filename)
    print(t)
    print(t.services_list_from_tree())   

if __name__ == '__main__': 
    test1()
    print()
    test2()
    print()
    test3()
    print()
    test4()

