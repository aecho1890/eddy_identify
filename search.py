# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 15:30:47 2016

@author: Redouanelg
"""

import os

import shutil
import pdb
pdb.set_trace()
path="H:\\aviso_eddy"

path2=('H:\\aviso_eddy\\5')
if os.path.exists(path2)==False:
    os.mkdir(path2)

for root,dirs,files in os.walk(path):
    for file in files:
        try:
            if str(file).split("_")[2][0:5]=="merge":
                #pdb.set_trace() 
                path3=str(root)+"/"+str(file)
                shutil.copy(path3,path2)
        except:
            print(file)
        

  