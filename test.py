# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 21:59:13 2016

@author: LHS
"""
import json
import pdb
import gdal
import os
import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import copy




#blue_line = mlines.Line2D([], [], color='blue', marker='o',
#                          markersize=15, label='Blue stars')
#plt.legend(handles=[blue_line])
#
#plt.show()
#a="adsf_sdf"
#a=a.replace("adsf","seed")
#print(a)
    

#import copy
#a=[1,2,3,4]
#b=a
#c=copy.copy(a)
#c.append(7)
#b.append(6)
#print(a)
#print(b)
#print(c)

#now=datetime.datetime.now()
#print(now.strftime('%Y-%m-%d %H:%M:%S')  )
##判断边界点最多
#"""
#读取信息
#"""
#file="H:\\Aviso\\woxuan\\1993\\json\\19930102\\eddy_info_merge19930102.json"
#fi=open(file)
#f=json.load(fi)
##tulp={}
##number=0
##number2=0
#fi.close()
#for key in f.keys():
#    if key[:8]=="eddy_368":
##    if key[:8]=="eddy_112":
#    #if key=="118.25_14.25":
#        print(key)
##    
#        print('sign_type:',f[key]['sign_type'])
#        print('eddy_inout:',f[key]['eddy_inout'])
#        print('eddy_flag:',f[key]['eddy_flag'])
#        print('eddy_core:',f[key]['eddy_core'])
#        print('eddy_Uavg_radius:',f[key]['eddy_Uavg_radius'])
#        print('eddy_Uavg_eke:',f[key]['eddy_Uavg_eke'])
#        print('eddy_Uavg_amp:',f[key]['eddy_Uavg_amp'])
#        print('eddy_Uavg_uv_speed:',f[key]['eddy_Uavg_uv_speed'])
#        print('eddy_Uavg_contour_index_i:',f[key]['eddy_Uavg_contour_index_i'])
#        print('eddy_Uavg_contour_index_j:',f[key]['eddy_Uavg_contour_index_j'])
#        print('eddy_Uavg_relative_vorticity:',f[key]['eddy_Uavg_relative_vorticity'])
#        print('eddy_Uavg_divergence:',f[key]['eddy_Uavg_divergence'])
#        print('eddy_Uavg_max:',f[key]['eddy_Uavg_max'])
#        print('eddy_Uavg_SHD:',f[key]['eddy_Uavg_SHD'])
#        print('eddy_Uavg_STD:',f[key]['eddy_Uavg_STD'])
#        print('Uavg_contain_pixel_num:',f[key]['Uavg_contain_pixel_num'])
#        print('eddy_Uavg_contour:',f[key]['eddy_Uavg_contour'])
#        print('eddy_effect_radius:',f[key]['eddy_effect_radius'])
#        print('eddy_effect_contour_j:',f[key]['eddy_effect_contour_j'])
#        print('eddy_effect_contour_i:',f[key]['eddy_effect_contour_i'])
#        print('eddy_effect_STD:',f[key]['eddy_effect_STD'])
#        print('eddy_effect_SHD:',f[key]['eddy_effect_SHD'])
#        print('eddy_effect_eke:',f[key]['eddy_effect_eke'])
#        print('eddy_effect_amp:',f[key]['eddy_effect_amp'])
#        print('eddy_effect_uv_speedv:',f[key]['eddy_effect_uv_speed'])
#        print('eddy_effect_relative_vorticity:',f[key]['eddy_effect_relative_vorticity'])
#        print('eddy_effect_divergence:',f[key]['eddy_effect_divergence'])
#        print('effect_contain_pixel_num:',f[key]['effect_contain_pixel_num'])
#        print('eddy_effect_contour:',f[key]['eddy_effect_contour'])
#        print('eddy_inner_contour_index_j:',f[key]['eddy_inner_contour_index_j'])
#        print('eddy_inner_contour_index_i:',f[key]['eddy_inner_contour_index_i'])
#        print('eddy_inner_contour_sla:',f[key]['eddy_inner_contour_sla'])
#        print('eddy_inner_contour:',f[key]['eddy_inner_contour'])
#        print('eddy_centroid_core:',f[key]['eddy_centroid_core'])
#        print('eddy_circle_core:',f[key]['eddy_circle_core'])
##        
#        
#        
#        print('eddy_shape_contour',f[key]['eddy_shape_contour'])
#        print('eddy_shape_contour_i',f[key]['eddy_shape_contour_i'])
#        print('eddy_shape_contour_j',f[key]['eddy_shape_contour_j'])
#        print('eddy_effect_radius',f[key]['eddy_effect_radius'])
#        print('eddy_shape_amp',f[key]['eddy_shape_amp'])
#        print('eddy_shape_eke',f[key]['eddy_shape_eke'])
#        print('eddy_shape_uv_speed',f[key]['eddy_shape_uv_speed'])
#        print('eddy_shape_relative_vorticity',f[key]['eddy_shape_relative_vorticity'])
#        print('eddy_shape_divergence',f[key]['eddy_shape_divergence'])
#        print('eddy_shape_SHD',f[key]['eddy_shape_SHD'])
#        print('eddy_shape_STD',f[key]['eddy_shape_STD'])
#        print('shape_contain_pixel_num',f[key]['shape_contain_pixel_num'])  
      
        










"""
多进程
"""

#from multiprocessing import Pool,Process
#import time
#
#def func(msg):
#    print("msg:",msg)
#    time.sleep(3)
#    print("end")
#if __name__ == '__main__':
#    
#    
#        
#    
#    
#    
#    
#    
#    pool=Pool(processes=2)
#    for i in range(4):
#        msg="hello %d" %(i)
#        pool.apply_async(func,(msg,))
#    pool.close()
#    pool.join()
#
#
#
#    print("done")    
    




    
#        进程池，可根据用户需求设置进程数
#        print(Blockdic)
#        pool = Pool(processes=pool_size)
#        for block_i in Blockdic:
#           #print('processes')
#           result = pool.apply_async(eddy_main,(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info,))
#           result = eddy_main(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info)
#           #print('block_i',block_i)      
#        pool.close()
#        pool.join()
#        
#        outjsons=[]
#        if result.successful():
    
    
    
    
    
#        #plist=[]
#        for block_i in Blockdic: 
#            #pdb.set_trace()
#            #proc = Process(target=eddy_main, args=(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info,))
#            eddy_main(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info)
#            #plist.append(proc)
#        #for proc in plist: proc.start() 
#        #for proc in plist: proc.join()
#        
        
        
#        outjsons=[]
#        for block_i in Blockdic:
#             outjsons.append(Blockdic[block_i]['outfnj'])
#        mergejson=eddyjson_merge(outjsons,lon,lat,outer_range,outdir,filedate,eddy_select_info,sladata)
#            
#        reject(mergejson,seedjson)
#        print("success")
#        print ('Duration', str((time.time() - start_time) ), 'seconds!')
        
        
        
        
        
import numpy as np        

from collections import OrderedDict
import json

import pdb  
import glob
def Block(lat,lon): 
        Blockdic=OrderedDict()   
        for j in range(len(lon)):
            for i in range(len(lat)):
                location=lon[j]+lat[i]        
                Blockdic.setdefault(str(j)+'_'+str(i),location) 
        return Blockdic 
#        
#def Block(lat,lon): 
#        
#        Blockdic=['0_0']   
#        
#        for i in range(1,lat):
#            for j in range(1,lon):
#                       
#                Blockdic.append(str(j)+'_'+str(i))
#        return Blockdic 



        
def process(Block_i,grid,filetem):

#    pdb.set_trace()
    eddys={}
    dicc=[]
    for key in filetem:
        #对所有涡旋进行遍历，查看是否在当下的分块中
        if key[:4]=="eddy" :
#            pdb.set_trace()
#            if Block_i=="24_44" and key=="eddy_72.875_-46.375":
#                pdb.set_trace()
#                print(1)
#            x=int(filetem[key]["eddy_centroid_core"][0]/3)%120
#            y=int((filetem[key]["eddy_centroid_core"][1]+90)/3)
            
          
            
            x=int(float(key.split("_")[1])/3)%120
            y=int((float(key.split("_")[2])+90)/3)
            if x==120:
                x=119
            if y==60:
                y=59
            if y==int(Block_i.split("_")[1]) and x==int(Block_i.split("_")[0]):
                a=filetem[key]
                eddys.setdefault(key,a)
                
                
                
                
                
                
    #当分块存在涡旋时   
    if len(eddys)!=0:
#        pdb.set_trace()
#        pdb.set_trace()              
        lonmin,lonmax,latmin,latmax=grid[0],grid[1],grid[2],grid[3]
#        latmin,latmax,lonmin,lonmax=grid[0],grid[1],grid[2],grid[3]
        centerx=(lonmin+lonmax)/2
        centery=(latmin+latmax)/2
        #网格内所有涡旋遍历
        for i in eddys:   
            #将经度大于360的移到左边
#            pdb.set_trace()
            if eddys[i]["eddy_centroid_core"][0]>360.125:
                eddys[i]["eddy_centroid_core"][0]=eddys[i]["eddy_centroid_core"][0]-360
                for eddy_lon in range(len(eddys[i]["eddy_effect_contour"][0])):
                    eddys[i]["eddy_effect_contour"][0][eddy_lon]=eddys[i]["eddy_effect_contour"][0][eddy_lon]-360
                
            #对纬度加90度处理    
            eddys[i]["eddy_centroid_core"][1]=eddys[i]["eddy_centroid_core"][1]+90 
            for j in range(len(eddys[i]["eddy_effect_contour"][1])): 
                eddys[i]["eddy_effect_contour"][1][j]=eddys[i]["eddy_effect_contour"][1][j]+90
            
            
            
            
            
            
            
            #涡旋质心点距网格中间点的位置
            diffx=eddys[i]["eddy_centroid_core"][0]-centerx
            diffy=eddys[i]["eddy_centroid_core"][1]-centery
            #将所有涡旋转到同一个点上
            for m in range(len(eddys[i]["eddy_effect_contour"][0])):
                eddys[i]["eddy_effect_contour"][0][m]=eddys[i]["eddy_effect_contour"][0][m]-diffx
                eddys[i]["eddy_effect_contour"][1][m]=eddys[i]["eddy_effect_contour"][1][m]-diffy
             
    
    
        #开始对涡旋的边界进行处理
        
        for m in eddys:
#            pdb.set_trace()
            derty=[]
            dertx=[]
            y=eddys[m]["eddy_effect_contour"][1]
            x=eddys[m]["eddy_effect_contour"][0]
 
            for j in range(len(x)):
                derty.append(y[j]-centery)
                dertx.append(x[j]-centerx)
                
            rn=[]         #用于存储极径
            Bn=[]         #用于存储极角
            thta=[]
        
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
                
            item={}
            
        #将极角和极径一一对应添加到字典中存储
            for i in range(len(x)):
                if dertx[i]>0:
                    if derty[i]>0:
                        item.setdefault(thta[i],rn[i])
                           
                    else:
                        item.setdefault(thta[i]+360,rn[i])
                               
                else:
                    item.setdefault(thta[i]+180,rn[i])
                    
           
            #对极角和极径进行排序，分别存到it和rr
            
            it_s=sorted(item)
            r_st=[]
            for ir in range(len(item)):
                r_st.append(item[it_s[ir]])
                
            #定义函数求指定极角对应的极径
            def f(r0,t0,k,bb):
                return((r0*np.sin(t0)-k*r0*np.cos(t0))/(np.sin(bb)-k*np.cos(bb)))
    #       
            
            ind=[]     #存储下标
            ri=[]      #存储所求极径
            
            
            
            """
            插值核心
            """
            
            #获取插值点的下标
            for je in range(36):
                for ie in range(len(item)):
                     
                    if ie<len(item)-1:
                        if it_s[ie]<=(10*(je+1)):
                            if it_s[ie+1]>=(10*(je+1)):
                                ind.append(ie)
                                if ie!=len(item)-1:
                                    ind.append(ie+1)
                                else:
                                    ind.append(0)
                    else:
                        ind.append(ie)
                        ind.append(0)
#                    
                #获取待插值两点的极角和极径
                tm=it_s[ind[0]]*np.pi/180
                rm=item[it_s[ind[0]]]
                tn=it_s[ind[1]]*np.pi/180
                rn=item[it_s[ind[1]]]
                #定义待插值两点所在直线的斜率
                k=(rm*np.sin(tm)-rn*np.sin(tn))/(rm*np.cos(tm)-rn*np.cos(tn))
                #定义插值的角度值，并转换为弧度
                ti=10*(je+1)*np.pi/180
                #调用函数求极径
                ri.append(f(rm,tm,k,ti))
                
                je+=1
                ind.clear()
            #存储插值后的各角度
                
            tb=[]
            for jw in range(36):
                tb.append(10*(jw+1))
#            print(tb)
                
            dicc.append(ri)
            
    #       #将极坐标转换为以涡旋质心为原点的直角坐标
            

#            pdb.set_trace()
        #对极坐标下所有形状进行插值 
#        pdb.set_trace()
        
        
        for iq in range(len(dicc)):
            if iq+1<len(dicc):
                for jq in range(len(dicc[0])):
                    dicc[iq+1][jq]=(dicc[iq][jq]+dicc[iq+1][jq])/2
                   
#                if i<len(dicc):
#                    dicc[i+1][j]=(dicc[i][j]+dicc[i+1][j])/2              
        ri=dicc[-1]
        return ri            
#        xx=[]
#        yy=[]
#        for i in range(len(ri)):
#            xx.append(ri[i]*np.cos(tb[i]*np.pi/180))
#            yy.append(ri[i]*np.sin(tb[i]*np.pi/180))
#        #将直角坐标转换为以（0,0）为原点的直角坐标
#            
#            
#            
#            
##            pdb.set_trace()    
#        XX=[]
#        YY=[]
#        for i in range(len(ri)):
#            XX.append(xx[i]+centerx)
#            YY.append(yy[i]+centery) 
            
    
    else:
      return []
    

        
        
        
        
        
        
        
if __name__ == '__main__':
    #对单个文件进行处理
    lat_grid=np.arange(0.125,181.125,3)
    lon_grid=np.arange(0.125,361.125,3)
    lat=[[lat_grid[0],lat_grid[1]]]
    lon=[[lon_grid[0],lon_grid[1]]]

    for i in range(1,len(lat_grid)-1):
        lat.append([lat_grid[i],lat_grid[i+1]])
    for i in range(1,len(lon_grid)-1):
        lon.append([lon_grid[i],lon_grid[i+1]])  
        
    Blockdi_c=Block(lat,lon)
    floder="H:\\Aviso\\woxuan\\涡旋识别老数据\\2015\\" 
    outputfile="H:\\Aviso\\woxuan\\涡旋识别老数据\\2015\\"
#    pdb.set_trace()
    jsonfils=glob.glob(floder+'*.json')
    for i in jsonfils: 
#        pdb.set_trace()
        outputname=i[:29]+"shape\\"+"shape_"+i[-13:-5]+".json"#输出文件、路径
        temporaryfile=open(i)
        file=json.load(temporaryfile)
        temporaryfile.close()
#        pdb.set_trace()
        newjson={}
        for block_i in Blockdi_c:
#            fi=copy.copy(file)
#            pdb.set_trace()
            listt=[]
            listt=process(block_i,Blockdi_c[block_i],file)
            newjson.setdefault(block_i,listt)

#            newjson.setdefault(Blockdi_c[block_i],process(block_i,Blockdi_c[block_i],file))
#        pdb.set_trace()    
        json.dump(newjson,open(outputname,'w'))    
    
    
    
    
    
    
#    pdb.set_trace()
    newfiles=glob.glob("H:\\Aviso\\woxuan\\涡旋识别老数据\\2015\\shape\\"+'*.json')
#    pdb.set_trace()
    #将所有数据与第一个形状json进行叠加。重叠完毕后得到最终的数据为第一个文件
    fileall=newfiles[0]
    temporaryall=open(fileall)
    filall=json.load(temporaryall)
    temporaryall.close()
    for j in range(1,len(newfiles)):
#        outputname2=newfiles[j][:29]+"shape\\"+"shape_"+newfiles[j][-13:-5]+".json"
        temporaryfile=open(newfiles[j])
        file2=json.load(temporaryfile)
        temporaryfile.close()
#        pdb.set_trace()
        for i in filall:
#            pdb.set_trace()
            for w in file2:
                
                if i==w:
#                    pdb.set_trace()
                    print(11)
                    if len(filall[i])!=0 and len(file2[i])!=0:
                        for z in range(len(filall[i])):
#                        pdb.set_trace()
                            filall[i][z]=(file2[i][z]+filall[i][z])/2
    
    
    
    
#    pdb.set_trace()
    #对叠加后的极坐标进行坐标转换
    tb=[]
    for j in range(36):
        tb.append(10*(j+1))
#    pdb.set_trace()
    end={}
    for b in filall:
        xx=[]
        yy=[]
        XX=[]
        YY=[]
        lonmin,lonmax,latmin,latmax=Blockdi_c[b]
          
        centerx=(lonmin+lonmax)/2
        centery=(latmin+latmax)/2
        for i in range(len(filall[b])):
            #将极坐标转为平面坐标
            xx.append(filall[b][i]*np.cos(tb[i]*np.pi/180))
            yy.append(filall[b][i]*np.sin(tb[i]*np.pi/180))
            
            #将直角坐标转换为以（0,0）为原点的直角坐标    
            XX.append(xx[i]+centerx)
            YY.append(yy[i]+centery) 
            
        end.setdefault(b,[XX,YY])
#    pdb.set_trace()    
    json.dump(end,open(fileall[:35]+"shapeall"+'.json','w'))    
    
    
#    lon_grid2, lat_grid2= np.meshgrid(lon_grid, lat_grid)  
#    xpcol, ypcol = lon_grid2[:], lat_grid2[:]
     
    
         