# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 22:05:26 2016

@author: Redouanelg
"""
import pdb
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import json
from mpl_toolkits.basemap import Basemap

directory = 'H:\\Aviso\\woxuan\\涡旋识别老数据\\2015\\eddy_info_merge20151231.json'    #涡旋识别结果路径
eddy_file=directory
f1=open(eddy_file,'r')    #读取涡旋文件 
eddy_dic_origin= json.load(f1)  
#pdb.set_trace()

for i in eddy_dic_origin:
#    if int(i.split("_")[1])>40 and int(i.split("_")[0])>20 and int(i.split("_")[0])>30 and int(i.split("_")[1])>50:
    if i=="eddy_72.875_-46.375" :   
        pdb.set_trace()
        print(11)











          