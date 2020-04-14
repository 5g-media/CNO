#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 27 17:31:48 2018

@author: miguelrocha
"""

## Class to keep solutions for service assignment

## Keeps a dictionary of user_ids (keys) -> dictionary with service assingment 
## which is a dictionary of service ids (keys) -> servers

class ServicesAssignment:
    
    def __init__(self, composite, dic_assig = None):
        self.composite = composite
        self.dic_assig = dic_assig
        
    def __str__(self):
        res = ""
        for u in self.dic_assig.keys():
            res += str(u) + " : "
            res += str(self.dic_assig[u])
            res += "\n"
        return res

    def __getitem__(self, ij):
        if len(ij) == 1:
            return self.user_assig(ij)
        else:
            if len(ij) == 2:
                return self.dic_assig[ij[0]][ij[1]]
            else: 
                return None

    def user_assig(self, user_id):
        return self.dic_assig[user_id]