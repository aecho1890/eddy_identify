# -*- coding: utf-8 -*-
"""
Created on Thu Aug 31 04:12:11 2017

@author: Administrator
"""

import json
import glob
import pdb
from collections import OrderedDict



jsonfile_path='I:\\彭琳数据修改\\3.0_tian\\19930104test\\json\\new\\'
out_jsonfile_path='I:\\彭琳数据修改\\3.0_tian\\19930104test\\json\\new\\'
files=glob.glob(jsonfile_path + '*.json')

for i in range(len(files)):
    
        
        eddy_filename=files[i]
        date=int(eddy_filename.split('\\')[-1][-13:-5])
        print(date)
        json_file=open(eddy_filename,'r')
#        json_data=json.load(json_file)
        json_0=json.load(json_file)
    #    pdb.set_trace()
    #    print(len(json_data))
#        json_0=json_data[0]
#        print(len(json_0))
    #    eddy_seed=[]
    #    pdb.set_trace()
        eddy_later_arr=[]
        
        for key in json_0.keys():
             eddy_later_dic=OrderedDict()
    #         eddy_seed.append(key)
    #         pdb.set_trace()
             eddy_later_dic.setdefault(key,json_0[key])
             eddy_later_arr.append(eddy_later_dic)
    #    print(eddy_later_arr)
    #    pdb.set_trace()     
        print(len(eddy_later_arr))
        out_json=out_jsonfile_path+str(date)+'.json'
        json.dump(eddy_later_arr,open(out_json,'w'))