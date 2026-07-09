# -*- coding: utf-8 -*-
"""
Created on Thu Dec 31 15:48:16 2015

@author: HXM
"""
import numpy as np
import scipy.spatial as spatial 
import pdb 
#a=np.random.random((3,3))
#c=np.where(a)
#print(c) 
#b=np.random.random((3,3)) 
#print('a',a)
#print('b',b)
def rangesearch(block, r):

    block_range_index=[]
    points=block.squeeze()
    centers=block.squeeze()
    point_tree= spatial.cKDTree(centers)  
    W=point_tree.query_ball_point(points, r)  #树上的哪些点是points的 r范围内
    for i in range(len(W)):
            block_range_index.append(W[i])
    return block_range_index
#a=[]
#for i in range(3):
#    for j in range(6):
#        a.append(np.array([i,j]))
#
#
#b=np.array(a)
##c=np.array(a) 
##print(b)
#index=rangesearch( b, np.sqrt(2))
#
#print(index)