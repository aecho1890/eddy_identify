# -*- coding: utf-8 -*-
"""
Created on Sat Dec  3 15:17:20 2016

@author: Redouanelg
"""

import json,glob,os,time
from osgeo import gdal
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import pdb
from mpl_toolkits.axes_grid1 import make_axes_locatable 
from scipy import ndimage
from collections import OrderedDict


def Block(lat,lon): 
    Blockdic=OrderedDict()   
    for j in range(len(lon)):
        for i in range(len(lat)):
            location=lon[j]+lat[i]        
            Blockdic.setdefault(str(j)+'_'+str(i),location) 
    return Blockdic 



if __name__ == '__main__':

    st='2.4'
    location='dep'
    directory = 'H:\\Aviso\\woxuan\\涡旋识别老数据\\陈老师\\20-31\\shapeall.json'    #涡旋识别结果路径

    if location=='depth':
        dep='true'
        outjpgdirectory='C:\\Users\\Redouanelg\\Desktop\\16json\\20160911\\seedjson\\'  #输出jpg路径
    else:
        dep='tru'
        outjpgdirectory='H:\\Aviso\\woxuan\\涡旋识别老数据\\2015\\shape\\' 

    area="#" 
    if st=='1.0':
        version=1.0
    elif st=='2.4':
        version=2.4

#    pdb.set_trace()    
#*************************************************************************#  
  #初始化为全球海洋区域 未规定识别范围
    linewidth,seedsize,dpi=0.2,0.15,1000#0.5,5,800
    lonmin, lonmax, latmin, latmax=0.125,360.125,-90,90  #3,6,42,44    #
    figsize=(17.8, 9)
    cb_ax=[0.92,0.05, 0.015, 0.9]
    ax1=[0.03, 0.05,0.93,0.9]

#    纬度：  4.5°N -  34.833°N
    if area=='North Indian Ocean':
        lonmin, lonmax, latmin, latmax=30,135,-15,30
        linewidth,seedsize,dpi=1,20,500
        figsize=(17, 8)
        cb_ax=[0.96,0.05, 0.015, 0.89]
    elif area=='West Pacific':
        linewidth,seedsize,dpi=1,20,500
        lonmin, lonmax, latmin, latmax=95,165,-15,45#100,200,-20,50
#        lonmin, lonmax, latmin, latmax=108,126,12,27#100,200,-20,50
        figsize=(9,12)
        cb_ax=[0.90,0.05, 0.015, 0.9]
    elif area=='South China Sea':
        linewidth,seedsize,dpi=1,40,500
#        lonmin, lonmax, latmin, latmax=84.125,138.125,53,89 #100,120,5,30#105,120,10,25#
        lonmin, lonmax, latmin, latmax=104.5,134.5,4.5,34.5
        '''于老师需要范围'''
#        lonmin, lonmax, latmin, latmax=105,135,5,25
        figsize=(10, 10)
#        figsize=(16, 16)  #尽量同实际经纬度相同
        cb_ax=[0.93,0.05, 0.02, 0.90]
    elif area=='South Atlantic Ocean': #南大西洋
        linewidth,seedsize,dpi=1,20,500
        lonmin, lonmax, latmin, latmax=290,360,-50,-15
        figsize=(16, 8)
        cb_ax=[0.955,0.05, 0.015, 0.89]    
        
    start_time=time.time()  #获取当前时间
    gdal.AllRegister()  #注册gdal 安装数据驱动
#    AVISO_files =glob.glob(directory+'*.json') 
    
    

   #获取特定区域的索引值
    #pdb.set_trace()   
    jmin=int((latmin+89.875)/0.25)
    jmax=int((latmax+89.875)/0.25)
    imin=int((lonmin-0.125)/0.25)
    imax=int((lonmax-0.125)/0.25)
    if area!='Global Ocean':
        imin-=4
        imax+=4
        jmin-=4
        jmax+=4
        
    lon_grid = np.arange(0.125,360,0.25)[imin:imax]
    lat_grid  = np.arange(-89.875,90,0.25)[jmin:jmax]
    lon_grid, lat_grid= np.meshgrid(lon_grid, lat_grid)  
    
    lat_grid2=np.arange(0.125,181.125,3)
    lon_grid2=np.arange(0.125,361.125,3)
    
    lat=[[lat_grid2[0],lat_grid2[1]]]
    lon=[[lon_grid2[0],lon_grid2[1]]]

    for i in range(1,len(lat_grid2)-1):
        lat.append([lat_grid2[i],lat_grid2[i+1]])
    for i in range(1,len(lon_grid2)-1):
        lon.append([lon_grid2[i],lon_grid2[i+1]])  
#    pdb.set_trace()    
    Blockdi_c=Block(lat,lon)
#    lonmin,lonmax,latmin,latmax=0.125,360.125,0.125,180.125
    
#    for i in range(len(AVISO_files)):   #212  206,213  len(AVISO_files)
    eddy_file=directory
    f1=open(eddy_file,'r')    #读取涡旋文件 
    eddy_dic_origin= json.load(f1)  
    
    fig=plt.figure(250,figsize=figsize) #12, 7
    ax1=fig.add_axes(ax1)#[0.1, 0.15, 0.75, 0.7] #起始坐标的位置
    #设置投影 方法
    m = Basemap(projection='gall', llcrnrlon = lonmin, urcrnrlon = lonmax, \
                llcrnrlat = latmin, urcrnrlat =  latmax, \
                 lat_ts = 0.5 * ( latmin + latmax), resolution = 'h',ax=ax1)#merc
   
    
#        #绘制涡旋有效边界、涡旋最大地转流边界、涡心
#    ycter=[]
    
#    pdb.set_trace()
#    x,y=m([109,115],[18,12])
#    m.plot(x,y,'r-',lw=1.5)

    
    
    
    
#    pdb.set_trace()
    for seedname2 in eddy_dic_origin.keys():
#        if int(seedname2.split('_')[1])>40 and int(seedname2.split('_')[1])<50 and int(seedname2.split('_')[0])>20  and int(seedname2.split('_')[0])<30:
#            pdb.set_trace()
            zcounter=[]
            lonmin,lonmax,latmin,latmax=Blockdi_c[seedname2]
            #求快的中间点
            centerx=(lonmin+lonmax)/2
            centery=(latmin+latmax)/2-90
            centerx2,centery2=m(centerx,centery)
#            m.scatter(centerx2, centery2,s=1.0,c='b',linewidths=0.0001) 
    #        pdb.set_trace()
            
            
            
    #        pdb.set_trace()  
            xcounter=eddy_dic_origin[seedname2][0]
            ycounter=eddy_dic_origin[seedname2][1]
            xcounter2=[]
            ycounter2=[]
            #剔除有错误的点
            for i in range(len(xcounter)):
                if xcounter[i]<lonmax+3 and xcounter[i]>lonmin-3 and ycounter[i]>latmin-3 and ycounter[i]<latmax+3:
    #                pdb.set_trace()                
                    xcounter2.append(xcounter[i])
                    ycounter2.append(ycounter[i])
            #纬度的值减去90度        
            for i in range(len(ycounter2)):
                zcounter.append(ycounter2[i]-90)    
            #给数组添加一个点使数组闭合    
            if len(xcounter2)!=0:
                xcounter2.append(xcounter2[0])
                zcounter.append(zcounter[0])    
            cx_e, cy_e = m(xcounter2, zcounter)   
               
            m.plot(cx_e, cy_e,color ='r',linewidth=0.5)
#            break

    title = 'shape_Eddies'   #'  

    #加title
    plt.title(title)
    
    
#    divider = make_axes_locatable(ax1)
#    location='right'
#    size="3%"
#    pad='3%'
#    cax = divider.append_axes(location, size=size, pad=pad)
#    
#    ax2=fig.add_axes(cax) #0.89
    '''
    等高线修改'''
#        if dep=='true':
#            cb=fig.colorbar(cf ,ax2)#cf CS 
#        else:
#            cb=fig.colorbar(CS ,ax2)
#        cb.ax.set_title('m')
    
    m.drawmapboundary()# fill_color='gray' '#689CD2'#填充海洋的颜色
    #pdb.set_trace()
#    m.drawparallels(np.arange(-89.875,90.125,3),labels=[1,0,0,0],fontsize=10)#+1+4
#    m.drawmeridians(np.arange(0.125,360.125,3),labels=[0,0,0,1],fontsize=10)#+1+4
    m.drawcoastlines()
    
    m.fillcontinents(color='k',lake_color='#689CD2',zorder=0)  #'#BF9E30'  #填充大陆颜色，湖泊颜色       
    savefilename=outjpgdirectory+title+st+location+'.jpg'
    plt.savefig(savefilename,bbox_inches='tight',pad_inches = 0,dpi=dpi)
    plt.show()
#        plt.clf()
    print('success')
        
    print ('Duration', str((time.time() - start_time) ), 'seconds!')
    
    
    
    
  