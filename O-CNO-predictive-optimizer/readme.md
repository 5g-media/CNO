# O-CNO-predictive-optimizer
As part of the 5G-MEDIA project, O-CNO-predictive-optimizer has been designed by a genetic algorithm which tries to optimally allocate resources to services based on their predicted resource consumption/demand. The results of this algorithm has been published in the conference IFIP Networking 2019 (https://ieeexplore.ieee.org/abstract/document/8816840).
## Prerequisites  
- python3
- networkx
- igraph
- inspyred
## Running
```
$ python3 run_ea_composite.py type_optimization network_file services_tree instance_file results_file
```
where:
- type_optimization: with/without congestion
- network file: assuming sndlib format
- services tree: file with "tree" of services
- instance_file: defines "name" of instance
- results_file: prefix of the files for results
