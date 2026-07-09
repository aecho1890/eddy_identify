# -*- coding: utf-8 -*-
"""
Created on Wed Jul  1 10:30:46 2015
读取生成的涡旋识别json数据，生成栅格的jpg文件
论文出图代码，勿随意改动——2016.05.20 lyj
@author: Lyj

"""

import json,glob,os,time
from osgeo import gdal
#from  matplotlib import colors
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
#import matplotlib
from scipy import ndimage
import scipy.ndimage.filters as filters
import scipy.ndimage.morphology as morphology

import pdb
    
if __name__ == '__main__':
#def putjpg(directory,dpi,area,tifdirectory):
    
    color1=['red','blue','yellow','green','pink','black','white',\
                '#8c531b','#bb505d','#ef5b9c','#deab8a','#faa755',\
                 '#b7ba6b','#4e72b8','#1a2933','#6a6da9','#689CD2','#BF9E30']
#*************************************************************************#
    #参数设置区域
    directory = 'H:\\Aviso\\woxuan\\涡旋识别老数据\\2015\\'    #涡旋识别结果路径'E:\\vvodata\\2004.8.8\\json\\'#
    tifdirectory='H:\\Aviso\\woxuan\\涡旋识别老数据\\h\\'#directory#'E:\\vvodata\\nanhai\\h\\'     #msla文件路径
                 
#    directory = 'E:\\vvodata\\2014\\json\\'#E:\\vvodata\\analyze\\2014\\'    #涡旋识别结果路径
#    tifdirectory='E:\\vvodata\\2014\\h\\'#directory#'E:\\vvodata\\nanhai\\h\\'     #msla文件路径
    outjpgdirectory='H:\\Aviso\\woxuan\\涡旋识别老数据\\h\\'#'E:\\vvodata\\nanhai\\jpg\\'  #输出jpg路径
    area='NorthWest Pacific'#'block2'#'block1'#'Global Ocean'#####'West Pacific'#设置识别区域
#    title='eddy'#'seed'
#*************************************************************************#  
 
  #初始化为全球海洋区域
    linewidth,seedsize,dpi=0.8,10,800#0.5,5,800
    lonmin, lonmax, latmin, latmax=0,360,-90,90  
    figsize=(17.8, 9.5)
    cb_ax=[0.97,0.05, 0.005, 0.9]
    ax1=[0.03, 0.05,0.93,0.9]
    if area=='North Indian Ocean':
        lonmin, lonmax, latmin, latmax=30,135,-15,30
        linewidth,seedsize,dpi=1,20,500
        figsize=(17, 8)
        cb_ax=[0.96,0.05, 0.015, 0.89]
    elif area=='West Pacific':
        linewidth,seedsize,dpi=1,20,500
        lonmin, lonmax, latmin, latmax=100,165,-15,45#100,200,-20,50
        figsize=(17, 9)
        cb_ax=[0.90,0.05, 0.015, 0.9]
    elif area=='South China Sea':
        linewidth,seedsize,dpi=1,20,800
        lonmin, lonmax, latmin, latmax=105,125,5,25
        figsize=(11.5, 9)
#        ax1=[0.03, 0.05,0.93,0.9]
        cb_ax=[0.92,0.05, 0.02, 0.9]  #原来的设置

    elif area=='South Atlantic Ocean': #南大西洋
        linewidth,seedsize,dpi=1,20,500
        lonmin, lonmax, latmin, latmax=290,360,-50,-15
        figsize=(16, 8)
        cb_ax=[0.955,0.05, 0.015, 0.89]  
    elif area=='NorthWest Pacific':
        linewidth,seedsize,dpi=1,20,500
#        lonmin, lonmax, latmin, latmax=105,125,5,25
        lonmin, lonmax, latmin, latmax=165,210,40,55
        figsize=(17.5, 10)
        cb_ax=[0.98,0.2, 0.015, 0.60]        
    elif area=='block2':
        linewidth,seedsize,dpi=1,20,500
        lonmin = 324.     # Canary
        lonmax = 354.5
        latmin = 18.
        latmax = 35.5
        figsize=(12, 9)
        cb_ax=[0.96,0.05, 0.015, 0.90]  
    
    start_time=time.time() 
    gdal.AllRegister()
    #获取涡旋数据路径 
    AVISO_files =glob.glob(directory+'*.json') 
    tif_files =glob.glob(tifdirectory+'*.tif') 
#    pdb.set_trace() 
   #获取特定区域的索引值   
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
    
    for i in range(len(AVISO_files)):   #,,97,137
        eddy_file=AVISO_files[i]
    #for eddy_file in AVISO_files:
#        eddy_date=os.path.split(eddy_file)[1] 
        f1=open(eddy_file,'r')    #读取涡旋文件
        eddy_dic = json.load(f1)   
    
        fig=plt.figure(250,figsize=figsize) #12, 7  
        ax1=fig.add_axes(ax1)#[0.1, 0.15, 0.75, 0.7]
        m = Basemap(projection='gall', llcrnrlon = lonmin, urcrnrlon = lonmax, \
                    llcrnrlat = latmin, urcrnrlat =  latmax, \
                     lat_ts = 0.5 * ( latmin + latmax), resolution = 'h',ax=ax1)#merc  
                     
            
        #读取tif文件作为底图
        tiff_file=tif_files[i] #open the tiff file
        ds1 = gdal.Open(tiff_file)
        band1 = ds1.GetRasterBand(1) 
        data1 = band1.ReadAsArray()[::-1][jmin:jmax,imin:imax]
#        sla=data1
        print ('start smoothing')
        mask=data1<-100
        sla_mask=np.ma.array(data1,mask=mask)
        np.place(data1, sla_mask == False, 0.)
        data1 -= ndimage.gaussian_filter(data1, [10.0, 5.0])
        sla = np.ma.masked_where(sla_mask == False, data1) # Expand the landmask
        sla_step=0.01  #0.0025   0.05#
        slaparameter = np.arange(-0.5,0.5+sla_step,sla_step)
        xpcol, ypcol = m(lon_grid[:], lat_grid[:]) 
        
#***************************************************************************************************#
#        datamax=np.max(sla)
#        datamin=getdatamin(sla)
#        print (datamin,datamax)
#        slaparameter = np.arange(round(datamin,2),round(datamax,2),0.0025)
#        Idata=np.ones((108,108),np.float32)
        cmap=plt.cm.jet #plt.cm.RdBu_r  #
#        CS = m.contour(xpcol, ypcol,sla,slaparameter,cmap=cmap)#colors=color1[17],linestyles='--') #'k'colors='k',, 
        CS1 = m.contour(xpcol, ypcol,sla,slaparameter,linewidths=0.5,colors='k',animated=True)
        CS = m.contourf(xpcol, ypcol,sla,slaparameter,cmap=cmap)#,norm=normplt.cm.bwr,shading='faceted'##cmap= 
#        pcol200 = m.pcolormesh(xpcol, ypcol, data1,cmap=plt.cm.RdBu_r, shading='faceted')
#        pcol200.set_clim(-0.1, 0.1)
 #***************************************************************************************************#           
        
        
#***************************************************************************************************#        
#    
            
        
#***************************************************************************************************#      
       #绘制涡旋有效边界、涡旋最大地转流边界、涡心 
        cc_n=0
        ac_n=0    
#        x1=172.125
#        y1=46.0873
        x1=[171.5,172.8,172.8,171.5,171.5]
        y1=[45.5,45.5,46.8,46.8,45.5]
        centx1,centy1=m(x1,y1)
        m.plot(centx1, centy1,c='k')
#        pdb.set_trace()
        for seedname2 in eddy_dic:
          if seedname2[:4]=="eddy":  
#            lon=eddy_dic[seedname2]['eddy_core'][0]
#            lat=eddy_dic[seedname2]['eddy_core'][1]
            lon=eddy_dic[seedname2]['eddy_centroid_core'][0]
            lat=eddy_dic[seedname2]['eddy_centroid_core'][1]
#            lon, lat=lon-0.125, lat-0.125   #1.0    
            lon, lat=lon, lat
            centx, centy=m(lon,lat)
            if eddy_dic[seedname2]['eddy_Uavg_radius']!=0:
                eddy_cont=eddy_dic[seedname2]['eddy_Uavg_contour']
                eddy_contlon_s, eddy_contlat_s = np.array(eddy_cont[0]),np.array(eddy_cont[1])
#                eddy_contlon_s, eddy_contlat_s =eddy_contlon_s-0.125, eddy_contlat_s -0.125
                eddy_contlon_s, eddy_contlat_s =eddy_contlon_s, eddy_contlat_s
                cx, cy = m(eddy_contlon_s, eddy_contlat_s)  
            if eddy_dic[seedname2]['eddy_effect_radius']!=0:
                eddy_cont_e=eddy_dic[seedname2]['eddy_effect_contour']
                eddy_contlon_e, eddy_contlat_e = np.array(eddy_cont_e[0]),np.array( eddy_cont_e[1])
#                eddy_contlon_e, eddy_contlat_e =eddy_contlon_e-0.125, eddy_contlat_e -0.125
                eddy_contlon_e, eddy_contlat_e =eddy_contlon_e, eddy_contlat_e#1.0
                cx_e, cy_e = m(eddy_contlon_e, eddy_contlat_e)
            
#            if lonmin<lon<lonmax and latmin<lat<latmax:
            sign_type=eddy_dic[seedname2]['sign_type']
            
            if (sign_type=='Cyclonic'):
                seed_color='k'
                Ucolor='b' #color1[15]#'b'
                Ecolor='b'
                cc_n+=1
            else:
                seed_color='k'
                Ucolor='r' #color1[9]#'r'
                Ecolor='r'
                ac_n+=1

            if cc_n==1 and sign_type=='Cyclonic':
                m.plot(cx, cy,color =Ucolor,label='CE $C_{Umax}$',linewidth=linewidth)   #linewidth'b'label='eddy_Uavg_border',画涡旋最大地转流速度等高线     
                m.plot(cx_e, cy_e,color =Ecolor,label='CE $C_{eff}$',linewidth=2)
                m.scatter(centx, centy,s=seedsize,c=Ecolor,label='CE Core')
            elif ac_n==1 and sign_type=='Anticyclonic': #and cc_n<=1
                m.plot(cx, cy,color =Ucolor,label='AE $C_{Umax}$',linewidth=linewidth)
                m.plot(cx_e, cy_e,color =Ecolor,label='AE $C_{eff}$',linewidth=2)
                m.scatter(centx, centy,s=seedsize,c=Ecolor,label='AE Core')
            else:
                m.plot(cx, cy,color =Ucolor,linewidth=linewidth)
                m.plot(cx_e, cy_e,color =Ecolor,linewidth=2)
                
                m.scatter(centx, centy,s=seedsize,c=Ecolor)
 
#***************************************************************************************************#            
            
        plt.legend(loc = 'upper left',fontsize=12)  #centerright
#        font = {'family' : 'serif',
#                  'color'  : 'k',
#                  'weight' : 'normal',
#                  'size'   : 20,
#                  }
                              
        title = str(os.path.split(eddy_file)[1][15:23])+' '+area+' Eddies'   #' 
#        plt.title(title, fontdict=font)
#        norm = matplotlib.colors.Normalize(vmin=-1, vmax=1)
        ax2=fig.add_axes(cb_ax) #0.89   #ax2,
#        cb = m.colorbar(CS,"bottom",size="3%", pad="2%",ticks=[-0.5,-0.4,-0.3,-0.2,-0.1,0,0.1,0.2,0.3,0.4,0.5])
        cb=fig.colorbar(CS,ax2,ticks=[-0.5,-0.4,-0.3,-0.2,-0.1,0,0.1,0.2,0.3,0.4,0.5] ) #[-1,-0.8,-0.6,-0.4,-0.2,0,0.2,0.4,0.6,0.8,1]
        cb.ax.set_title('m')
        for t in cb.ax.get_yticklabels():
            t.set_fontsize(16) 
# 
        
        m.drawmapboundary()# fill_color='gray' '#689CD2'#填充海洋的颜色
        m.drawparallels(np.arange(latmin,latmax+1,5),labels=[1,0,0,0],fontsize=15)#float((latmax-latmin)/9)+1+4#linewidth=0,
        m.drawmeridians(np.arange(lonmin,lonmax+1,5),labels=[0,0,0,1],fontsize=15)#float((lonmax-lonmin)/8))+1+4#linewidth=0,
        m.drawcoastlines()
        m.fillcontinents(color='gray',lake_color='#689CD2',zorder=0)  # '#BF9E30' #填充大陆颜色，湖泊颜色
        
        
        savefilename=outjpgdirectory+title+str(sla_step)+'.jpg' #slafilter  contour
        print (savefilename)
#        extent = ax1.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
#        plt.savefig(savefilename, dpi = dpi, bbox_inches = extent)
        plt.savefig(savefilename,dpi=dpi,bbox_inches='tight',pad_inches = 0) #,transparent=False,dpi=dpi, bbox_inches = extent,dpi=800
        plt.clf()
        
#    plt.close(250)
    print ('Duration', str((time.time() - start_time) ), 'seconds!')
    
    