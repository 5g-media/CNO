#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 17:15:27 2018

@author: miguelrocha
"""

import pandas as pd
import matplotlib.pyplot as plt

runstats = pd.read_csv("../Results-paperIFIPNetw/nc-geant-treesyn-alu30-del08-run0-stats.txt", sep = ",")

print(runstats.shape)

#print(runstats.values[:, 4])

plt.clf()

plt.plot(runstats.values[:,0], runstats.values[:,3], 'b', label='Best solution')
plt.plot(runstats.values[:,0], runstats.values[:,4], 'r', label='Mean')
plt.title('NC - tree topology')
plt.xlabel('Generations')
plt.ylabel('Fitness')
plt.legend()
plt.savefig("../Results-paperIFIPNetw/nc-geant-loops-alu30-del08.jpg")
plt.show()