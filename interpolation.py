# -*- coding: utf-8 -*-
"""
Created on Wed Sep  7 19:46:24 2016

@author: LYJ
"""

import json
import pdb
import gdal
import os
from scipy import interpolate 
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import math
import numpy as np

#
file="H:\\Aviso\\woxuan\\涡旋识别老数据\\2015\\eddy_info_merge20151231.json"
fi=open(file)
#print(help(json))
f=json.load(fi)
#print(f)
tulp={}
number=0
number2=0
l1=[]
fi.close()

def polyfit(x,y,degree):
    results={}
    coeffs=np.polyfit(x,y,degree)
    results['polynomial']=coeffs.tolist()
    
    p=np.poly1d(coeffs)
    yhat=p(x)
    ybar=np.sum(y)/len(y)
    ssreg=np.sum((yhat-ybar)**2)
    sstot=np.sum((y-ybar)**2)
    results['determination']=ssreg/sstot

    a=results['polynomial'][0]
    print(a)
    return results
    
    
for key in f.keys():

    if key=="eddy_118.625_19.125":

        pdb.set_trace()
        f[key].keys()=="eddy_effect_contour"
        print(len(f[key]['eddy_effect_contour']))
        m=f[key]['eddy_effect_contour']

        print('eddy_centroid_core:',f[key]['eddy_centroid_core'])
        x0,y0=f[key]['eddy_centroid_core']
        print(x0,y0)

        fig1=plt.figure()
        ax=fig1.add_axes([0.05,0.05,0.9,0.9])
       
        
        x=m[0]
        y=m[1]
        plt.plot(x,y,'o')
        plt.plot(x0,y0,'o',color='r')
        plt.show()
        
        #转换为以涡旋质心为原点的坐标
        pdb.set_trace()
        derty=[]
        dertx=[]
        for i in range(len(x)):
            derty.append(y[i]-y0)
            dertx.append(x[i]-x0)

        
        rn=[]         #用于存储极径
        Bn=[]         #用于存储极角
        thta=[]
        pdb.set_trace()
        #将以质心为直角坐标转换为以质心为极点的极坐标
        for i in range(len(x)):
            rn.append(np.sqrt(dertx[i]**2+derty[i]**2))
            
        for i in range(len(x)):
            if derty[i]>0:
                if dertx[i]==0:
                    Bn.append(np.pi/2)
                else:
                    Bn.append(np.arctan(derty[i]/dertx[i]))
            elif derty[i]<0:
                if dertx[i]==0: 
                    Bn.append(3/2*np.pi)
                else:
                    Bn.append(np.arctan(derty[i]/dertx[i]))
                
        #将极角的弧度转换为角度
        for i in range(len(x)):
            thta.append(180*Bn[i]/np.pi)
     

        pdb.set_trace()

        item={}
        
        #将极角和极径一一对应添加到字典中存储
        """
        """
        for i in range(len(x)):
            if dertx[i]>0:
                if derty[i]>0:
                    item.setdefault(thta[i],rn[i])
                       
                else:
                    item.setdefault(thta[i]+360,rn[i])
                           
            else:
                item.setdefault(thta[i]+180,rn[i])
                
       
        #对极角和极径进行排序，分别存到it和rr
        pdb.set_trace()
        it_s=sorted(item)
        r_st=[]
#        
        for i in range(len(item)):
            r_st.append(item[it_s[i]])

#        
        #定义函数求指定极角对应的极径
        def f(r0,t0,k,bb):
            return((r0*np.sin(t0)-k*r0*np.cos(t0))/(np.sin(bb)-k*np.cos(bb)))
#       
        
        ind=[]     #存储下标
       
        ri=[]      #存储所求极径
        
        
        
        """
        插值核心
        """
        pdb.set_trace() 
        #获取插值点的下标
        for j in range(36):
            for i in range(len(item)):
                 
                if i<len(item)-1:
                    if it_s[i]<=(10*(j+1)):
                        if it_s[i+1]>=(10*(j+1)):
                            ind.append(i)
                            if i!=len(item)-1:
                                ind.append(i+1)
                            else:
                                ind.append(0)
                else:
                    ind.append(i)
                    ind.append(0)
            pdb.set_trace()    
            #获取待插值两点的极角和极径
            tm=it_s[ind[0]]*np.pi/180
            rm=item[it_s[ind[0]]]
            tn=it_s[ind[1]]*np.pi/180
            rn=item[it_s[ind[1]]]
            #定义待插值两点所在直线的斜率
            k=(rm*np.sin(tm)-rn*np.sin(tn))/(rm*np.cos(tm)-rn*np.cos(tn))
            #定义插值的角度值，并转换为弧度
            ti=10*(j+1)*np.pi/180
            #调用函数求极径
            ri.append(f(rm,tm,k,ti))
            
            j+=1
            ind.clear()
        #存储插值后的各角度
        pdb.set_trace()    
        tb=[]
        for j in range(36):
            tb.append(10*(j+1))
        print(tb)

#       #将极坐标转换为以涡旋质心为原点的直角坐标
        xx=[]
        yy=[]
        for i in range(len(ri)):
            xx.append(ri[i]*np.cos(tb[i]*np.pi/180))
            yy.append(ri[i]*np.sin(tb[i]*np.pi/180))
        #将直角坐标转换为以（0,0）为原点的直角坐标      
        pdb.set_trace()    
        XX=[]
        YY=[]
        for i in range(len(ri)):
            XX.append(xx[i]+x0)
            YY.append(yy[i]+y0)
        pdb.set_trace()    
            
            
            
#        print(XX)
#        print(YY)
        fig2=plt.figure()
        ax=fig2.add_axes([0.05,0.05,0.9,0.9])
        plt.plot(XX,YY,'o')
        plt.plot(x0,y0,'o',color='r')
        plt.show()
        
        
        
            
      
        