#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  5 16:39:59 2018

@author: miguelrocha
"""

import model_delay.test as mtest
import networkx as nx
import igraph as ig
import xml.etree.ElementTree as ET

class Network:
    
    def __init__(self, filename = None, format_file="brite", sep="\t", engine = "igraph"):
        if filename is None:
            self.nodes = {}
            self.edges = {}
        else:
            if format_file == "brite":
                self.read_network_brite(filename, sep)
            elif format_file == "sndlib":
                self.read_sndlib(filename)
            else:
                print("Wrong format")
                self.nodes = {}
                self.edges = {}
        
        self.engine = engine
        if engine == "nx": self.G = self.to_networkx()
        else: 
            if engine == "igraph": self.igr = self.to_igraph()
    
    def read_network_brite(self, filename, sep = "\t"):
        fnodes = open(filename+".nodes")
        nnodes = int(fnodes.readline().strip())
        self.nodes = {}
        for i in range(nnodes):
            line = fnodes.readline().strip()
            tokens = line.split(sep)
            id_node = str(tokens[0])
            x_pos = float(tokens[1])
            y_pos = float(tokens[2])
            self.nodes[id_node] = (x_pos, y_pos)
        fnodes.close()
        
        fedges = open(filename+".edges")
        nedges = int(fedges.readline().strip())
        self.edges = {}
        for i in range(nedges):
            line = fedges.readline().strip()
            tokens = line.split(sep)
            src_node = tokens[1]
            dst_node = tokens[2]
            delay = float(tokens[4]) * 100.0
            bandwidth = float(tokens[5])
            self.edges[str(i)] = (src_node, dst_node, delay, bandwidth, 1.0) # cost set to 1.0
            self.edges[str(i+nedges)] = (dst_node, src_node, delay, bandwidth, 1.0) # cost set to 1.0
        fedges.close()

    def read_sndlib(self, filename):
        self.nodes = {}
        self.edges = {}
        f = open(filename)
        while not f.readline().strip().startswith("NODES"): 
            pass
        line = f.readline().strip()
        while not line.startswith(")"):
            tokens = line.split(" ")
            id_node= str(tokens[0])
            x_pos = float(tokens[2])
            y_pos = float(tokens[3]) 
            self.nodes[id_node] = (x_pos, y_pos)
            line = f.readline().strip()
        while not f.readline().strip().startswith("LINKS"): 
            pass
        line = f.readline().strip()
        while not line.startswith(")"):
            tokens = line.split(" ")
            id_link = str(tokens[0])
            src_node = tokens[2]
            dst_node = tokens[3]
            lat1, lon1 = self.nodes[src_node]
            lat2, lon2 = self.nodes[dst_node]
            delay = mtest.compute_latency(lat1, lon1, lat2, lon2)/1000 
            bandwidth = float(tokens[10])
            self.edges[id_link] = (src_node, dst_node, delay, bandwidth, 1.0) # cost set to 1.0
            self.edges[id_link+"-r"] = (dst_node, src_node, delay, bandwidth, 1.0) # cost set to 1.0
            line = f.readline().strip()
        f.close()

    def solution(self,solution_filename):
        f = open(solution_filename)
        while not f.readline().strip().startswith("LINK-CONFIGURATIONS"):
            pass
        line = f.readline()
        while not line.startswith(")"):
            tokens = line.split()
            id_link = tokens[0]
            link = self.edges[id_link]
            link_r = self.edges[id_link+"-r"]

            if len(tokens) < 5:
                print("Link {} has null capacity. Adding 20 Mbps.".format(id_link))
                capacity = 20
            else:
                capacity = float(tokens[2])*float(tokens[3])
            self.edges[id_link] = (link[0],link[1],link[2],capacity,link[4])
            self.edges[id_link+"-r"] = (link_r[0],link_r[1],link_r[2],capacity,link_r[4])
            line = f.readline()

    def read_xml_uhlig(self, filename, capacities_filename):
        self.nodes = {}
        self.edges = {}
        tree = ET.parse(filename)
        root = tree.getroot()
        nodes = root[1][0]
        links = root[1][1]
        link_capacities = root[2][0]
        node_ip = {}
        srcdst2link_id = {}

        for node in nodes:
            id_node = node.attrib['id']
            ip_addr = node[0].text
            node_ip[ip_addr] = id_node
            coord = node[1]
            lat = float(coord.attrib['latitude'])
            lon = float(coord.attrib['longitude'])
            self.nodes[id_node] = (lat,lon)

        for link in links:
            id_link = link.attrib['id']
            src_node = link[0].attrib['node']
            dst_node = link[1].attrib['node']
            lat1, lon1 = self.nodes[src_node]
            lat2, lon2 = self.nodes[dst_node]
            delay = mtest.compute_latency(lat1, lon1, lat2, lon2)/1000 
            bandwidth = 0
            srcdst2link_id[src_node,dst_node] = id_link
            self.edges[id_link] = [src_node,dst_node,delay,bandwidth,1]

        
        f = open(capacities_filename, "r")
        lines = f.readlines()
        for line in lines:
            line = line.split()
            src_last_digits = line[0][-5:-3] if line[0][-5] !='0' else line[0][-4]
            dst_last_digits = line[1][-5:-3] if line[1][-5] !='0' else line[1][-4]
            src = '62.40.102.'+ src_last_digits
            dst = '62.40.102.'+ dst_last_digits

            if src in node_ip and dst in node_ip:
                src_node = node_ip[src]
                dst_node = node_ip[dst]
                if (src_node, dst_node) in srcdst2link_id:                   
                    id_link = srcdst2link_id[src_node,dst_node]
                    bandwidth = float(line[4])
                    self.edges[id_link][3] = bandwidth if bandwidth !=0 else 10000
                    self.edges[id_link] = tuple(self.edges[id_link])

        if self.engine == "nx": self.G = self.to_networkx()
        else: 
            if self.engine == "igraph": self.igr = self.to_igraph()

        
        f.close()

    def __str__(self):
        res = "Network:\n"
        res += "Nodes\n"
        for k in self.nodes.keys():
            res += str(k) + "->" + str(self.nodes[k]) + "\n"
        res += "\nLinks\n"
        for k in self.edges.keys():
            res += str(k) + "->" + str(self.edges[k]) + "\n"
        return res

    def to_networkx(self):
        netx = nx.DiGraph()
        netx.add_nodes_from(list(self.nodes.keys()))
        netx.add_edges_from(self.list_edges())
        return netx

    def to_igraph(self):
        igr = ig.Graph(directed = True)
        for node in self.nodes.keys():
            igr.add_vertex(node)
        E = self.link_ids()
        for edge in E:
            e = self.edges[edge]
            igr.add_edge(e[0], e[1])
        igr.es["name"] = E
        return igr

    def number_nodes(self):
        return len(self.nodes)
    
    def number_edges(self):
        return len(self.edges)

    def list_nodes(self):
        return list(self.nodes.keys())

    def link_ids(self):
        return list(self.edges.keys())

    def list_edges(self):
        res = [(e[0],e[1]) for e in self.edges.values()]
        return res
    
    def link_capacity(self, e):
        li = self.edges.get(e, None)
        if li is not None: 
            return li[3]
        else: return None

    def avg_delays(self):
        sum_delays = 0
        for k in self.link_ids(): sum_delays += self.get_link_delay(k)
        return sum_delays/self.number_edges()

    def avg_capacities(self):
        sum_cap = 0
        for k in self.link_ids(): sum_cap += self.link_capacity(k)
        return sum_cap/self.number_edges()
        
    def get_link_delay(self, link):
        return self.edges[link][2]
    
    def in_edges(self, node):
        res = []
        for k in self.edges.keys():
            if self.edges[k][1] == node: 
                res.append(k)
        return res

    def out_edges(self, node):
        res = []
        for k in self.edges.keys():
            if self.edges[k][0] == node: 
                res.append(k)
        return res

    def all_out_edges(self):
        res = {}
        for node in self.nodes.keys():
            res[node] = []
        for e in self.edges.keys():
            res[self.edges[e][0]].append(e)
        return res

    def get_link_from_nodes(self, src, dest):
        for e in self.edges.keys():
            if self.edges[e][0] == src and self.edges[e][1] == dest:
                return e
        return None
    
    def get_links_from_path(self, path):
        res = []
        for i in range(len(path)-1):
            res.append(self.get_link_from_nodes(path[i], path[i+1]))
        return res

    def valid_path(self, src, dest, path):
        cur_node = src
        while cur_node != dest:
            out_links = self.out_edges(cur_node)
            inters = [e for e in out_links if e in path]
            if len(inters) == 1:
                cur_node = self.edges[inters[0]][1]
                if cur_node == src: return False
            else: return False
        return True

    ## shortest path between src and dest nodes
    ## uses delays as weights by defaults
    ## parameter weights allows to specify dictionary with weights per link
    def dijkstra(self, src, dest = None, weights = "delays"):
        if self.engine == "nx":
            for e in self.edges.keys():
                if weights == "delays":
                    w = self.get_link_delay(e)
                else: w = weights[e]
                self.G[self.edges[e][0]][self.edges[e][1]]['weight'] = w
    
            if dest is None:
                return nx.single_source_dijkstra(self.G, src)
            else: 
                return nx.dijkstra_path_length(self.G, src, dest), nx.dijkstra_path(self.G, src, dest) 

        elif self.engine == "igraph":
            W = []
            for e in self.edges.keys():
                if weights == "delays":    
                    W.append(self.get_link_delay(e))
                else: W.append(weights[e])
            self.igr.es['weight'] = W
            
            if dest is None:
                dic_d = {}
                dists = self.igr.shortest_paths(src, weights = "weight")[0]
                for (i,d) in enumerate(dists):
                    dic_d[self.igr.vs['name'][i]] = d
                paths = self.igr.get_shortest_paths(src, weights = "weight")
                dic_p = {}
                for (i,path) in enumerate(paths):
                    pnames = []
                    for p in path:
                        pnames.append(self.igr.vs['name'][p])
                    dic_p[self.igr.vs['name'][i]] = pnames
                return dic_d, dic_p
            else:
                path = self.igr.get_shortest_paths(src, dest, weights = "weight")[0]
                pnames = []
                for p in path:
                    pnames.append(self.igr.vs['name'][p])
                return self.igr.shortest_paths(src, dest, weights = "weight")[0][0], pnames
    

    def calculate_sp_delays(self):
        res_delays= {}
        res_paths = {}
        for node in self.nodes.keys():
            res_delays[(node,node)] = 0.0
            del_node, pnodes = self.dijkstra(node, None, "delays")
            for dst in del_node.keys():
                if node != dst:
                    res_delays[(node, dst)] = del_node[dst]
                    res_paths[(node, dst)] = self.get_links_from_path(pnodes[dst])
        return res_delays, res_paths
    

    def dist_unit_weights(self, src, dst):
        from collections import defaultdict
        w = defaultdict(lambda:1)
        d, _ = self.dijkstra(src, dst, w)
        return d

    def all_shortest_paths(self, weights):
        if self.engine == "nx":
            for e in self.edges.keys():
                w = weights[e]
                self.G[self.edges[e][0]][self.edges[e][1]]['weight'] = w
            paths = nx.all_pairs_dijkstra_path(self.G)
            return paths
        elif self.engine == "igraph":
            W = []
            for e in self.edges.keys():
                if weights == "delays":    
                    W.append(self.get_link_delay(e))
                else: W.append(weights[e])
            self.igr.es['weight'] = W
            res = []
            for node in self.nodes.keys():
                pnode = self.igr.get_shortest_paths(node, weights = "weight")
                dic_node = {}
                for (i, path) in enumerate(pnode):
                    pnames = []
                    for p in path:
                        pnames.append(self.igr.vs['name'][p])
                    dic_node[self.igr.vs['name'][i]] = pnames
                res.append( (node, dic_node) )
            return res


    def all_shortest_paths_with_ties(self, weights):
        if self.engine == "nx":
            if self.G is None: self.G = self.to_networkx()
            for e in self.edges.keys():
                w = weights[e]
                self.G[self.edges[e][0]][self.edges[e][1]]['weight'] = w
            dic_paths = {}
            for n in self.nodes.keys():
                for n1 in self.nodes.keys():
                    if n != n1:
                        dic_paths[(n, n1)] = list(nx.all_shortest_paths(self.G, n, n1, "weight"))
            return dic_paths
        elif self.engine == "igraph":
            W = []
            for e in self.edges.keys():
                if weights == "delays":    
                    W.append(self.get_link_delay(e))
                else: W.append(weights[e])
            self.igr.es['weight'] = W      
            dic_paths = {}
            for node in self.nodes.keys():
                pnode = self.igr.get_all_shortest_paths(node, weights = "weight")
                for path in pnode:
                    pnames = []
                    for p in path:
                        pnames.append(self.igr.vs['name'][p])
                    if pnames != []: 
                        dst = pnames[-1]
                        if (node, dst) in dic_paths:
                            dic_paths[(node, dst)].append(pnames)
                        else: dic_paths[(node, dst)] = [pnames]
            return dic_paths
        

### Testing ###


def test1():
    n = Network("../Networks/germany50.txt", "sndlib")
    print(n)
    print(n.list_nodes())
    print(n.list_edges())
    print( n.number_nodes(), n.number_edges() )

def test2():
    n = Network("../Networks/isno_30_2")
    print(n)
    print(n.list_nodes())
    print(n.list_edges())
    
def test3():
    n = Network("../Networks/isno_5_2")
    d, p = n.dijkstra("0")
    print(d)
    print(p)


def test4():
    #from collections import defaultdict
    n = Network("../Networks/isno_5_2")
    #w = defaultdict(lambda:1)
    #d, p = n.dijkstra("0", None, w)
    #print(d)
    #print(p)
    p = n.shortest_path_from_dijkstra("0","3")
    print(p)
    pl = n.get_links_from_path(p[0])
    print(pl)

    print(n.valid_path("0", "1", pl))
    #print(n.calculate_sp_delays())
    
    #print(n.dist_unit_weights("0","2"))
    
def test5():    
    from collections import defaultdict
    n = Network("../Networks/isno_30_4")
    #print(n)
    #netx = n.to_networkx()
    #print(netx.number_of_nodes())
    #print(netx.number_of_edges())
    #nx.draw(netx, with_labels = True, font_wieght = "bold")
    import timeit
    w = defaultdict(lambda:1)
    
    start = timeit.default_timer()
    n.all_shortest_paths_with_ties(w)
    #for x in p: print(x)    
    stop = timeit.default_timer()
    print('Time: ', stop - start) 


def test6():
    n = Network("../Networks/geant.txt", "sndlib")
    print(n)
    print( n.number_nodes(), n.number_edges() )

def test7():
    from collections import defaultdict
    n = Network("../Networks/isno_5_2", engine = "igraph")
    #n = Network("../Networks/isno_30_4")
    #print(n.igr)
    #print(n.igr.shortest_paths("0","2"))
    #print(n.igr.get_shortest_paths("0","2"))
    #print(n.igr.get_all_shortest_paths("0", "2"))

    #print(n.igr.vs[0].attributes())
    #print(n.igr.es[1].attributes())

    #import timeit
    
    W = []
    for e in n.edges.keys():
        W.append(1)
#        W.append(n.get_link_delay(e))
    n.igr.es['weight'] = W
    
    #start = timeit.default_timer()

    #print(n.igr.es[1].attributes())

    #print(n.dijkstra("0"))
    print( n.all_shortest_paths_with_ties(defaultdict(lambda:1)))

    #print(n.igr.shortest_paths("0", weights = "weight"))
    #print(n.igr.get_shortest_paths("0", weights = "weight"))
    #print(n.igr.get_all_shortest_paths("0", weights = "weight"))
    
    #for node in n.nodes.keys():
    #    n.igr.get_all_shortest_paths(node, weights = "weight")
        
    #stop = timeit.default_timer()
    #print('Time: ', stop - start)

def test8():
    n = Network()
    n.read_xml_uhlig("../Networks/geant_uhlig.xml", "../Networks/geant_dm_uhlig/geant_bandwidth.txt")
    print(n)
    print(n.list_nodes())
    print(n.list_edges())

def test9():
    n = Network("../Networks/nobelgermany.txt", "sndlib")
    n.solution("../Networks/solution_nobelgermany_db.txt")
    print(n)
    print(n.list_edges()) 

if __name__ == '__main__':   
    #test1()
    #print()
    #test2()
    #test4()
    #test5()
    #test6()
    #test7()
    test8()
    test9()