# -*- coding: utf-8 -*-
"""
Created on Fri May  6 11:00:30 2016

@author: Leo
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jul  1 10:30:46 2015
读取生成的涡旋识别json数据，生成栅格的jpg文件
@author: Leo
"""

import json,glob,os,time
from osgeo import gdal
#from  matplotlib import colors
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import pdb
#from PIL import ImageFont
#from PIL import ImageDraw
from mpl_toolkits.axes_grid1 import make_axes_locatable 
from scipy import ndimage



def getdatamin(slacopy):
    datamin=9999
    for n in range(len(slacopy[0])):
           for m in range(len(slacopy)):
               if (slacopy[m][n]>-10):
                   if slacopy[m][n]<datamin:
                       datamin=slacopy[m][n]
    return datamin


def find_close(arr, e):
    
    size = len(arr)
    idx = 0
    val = abs(e - arr[idx])

    for i in range(1, size):
        val1 = abs(e - arr[i])
        if val1 < val:
            idx = i
            val = val1

    return idx    


if __name__ == '__main__':

    st='2.4'
    location='dep'
    directory = 'D:\\2\\'    #涡旋识别结果路径
    tifdirectory='D:\\2\\'
#    if location=='depth':
#        dep='true'
#        outjpgdirectory='I:\\彭琳数据修改\\3.0_tian\\19930101\\'  #输出jpg路径
#    else:
    dep='tru'
    outjpgdirectory='D:\\'#'I:\\彭琳数据修改\\3.0_tian\\19930101\\' 
#    area='South China Sea' West Pacific
    area=''
#    area="#" 
    if st=='1.0':
        version=1.0
    elif st=='2.4':
        version=2.4
    
        
#*************************************************************************#  
  #初始化为全球海洋区域 未规定识别范围
    linewidth,seedsize,dpi=0.2,0.15,1000#0.5,5,800
    lonmin, lonmax, latmin, latmax=0,360,-90,90  #3,6,42,44    #
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
#        lonmin, lonmax, latmin, latmax=95,165,-15,45#100,200,-20,50
        '''test_error'''
        lonmin, lonmax, latmin, latmax=265,270,-42,-40#100,200,-20,50
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
    #pdb.set_trace()
    AVISO_files =glob.glob(directory+'*.json') 
    tif_files =glob.glob(tifdirectory+'*.tif') 

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

    for i in range(len(AVISO_files)):   #212  206,213  len(AVISO_files)
#     if i>=7274:
        eddy_file=AVISO_files[i]
        print(eddy_file)
        date=str(eddy_file.split('\\')[-1][15:23])
        #if int(date)==19930101:
#        pdb.set_trace()
        f1=open(eddy_file,'r')    #读取涡旋文件 
        eddy_dic_origin1= json.load(f1)  
        
        fig=plt.figure(250,figsize=figsize) #12, 7
        ax1=fig.add_axes(ax1)#[0.1, 0.15, 0.75, 0.7] #起始坐标的位置
        #设置投影 方法
        m = Basemap(projection='gall', llcrnrlon = lonmin, urcrnrlon = lonmax, \
                    llcrnrlat = latmin, urcrnrlat =  latmax, \
                     lat_ts = 0.5 * ( latmin + latmax), resolution = 'h',ax=ax1)#merc
        xpcol, ypcol = m(lon_grid[:], lat_grid[:])
    
    #读取tif文件作为底图
        tiff_file=tif_files[i] #open the tiff file   -90
        ds1 = gdal.Open(tiff_file)
        band1 = ds1.GetRasterBand(1) 
        data1 = band1.ReadAsArray()[::-1][jmin:jmax,imin:imax]
        mask=data1<-100
        sla_mask=np.ma.array(data1,mask=mask)
        np.place(data1, sla_mask == False, 0.)
        
        data1 -= ndimage.gaussian_filter(data1, [5, 10])
        sla = np.ma.masked_where(sla_mask == False, data1) # Expand the landmask
        
        slaparameter = np.arange(-1,1.01,0.0025)  #固定的最值
        
#        #绘制涡旋有效边界、涡旋最大地转流边界、涡心
        Anti_eddys_num=0
        cyc_eddys_num=0
        Southsea_Anti_eddys_num=0
        Southsea_cyc_eddys_num=0
        Global_Anti_eddys_num=0
        Global_cyc_eddys_num=0

        j=0
        eddy_num=0
        seed_num=0
        #pdb.set_trace()
        for i in range(len(eddy_dic_origin1)):
            eddy_dic_origin=eddy_dic_origin1[i]
            for seedname2 in eddy_dic_origin.keys():
                point_type=seedname2.split('_')[0]  
                if point_type=='eddy':
#                            pdb.set_trace()
                    eddy_num=eddy_num+1
                    U_max=eddy_dic_origin[seedname2]['eddy_Uavg_max']
                    if U_max<1000:
                                
                        seedsize=0.3
                        if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                            eddy_cont=eddy_dic_origin[seedname2]['eddy_Uavg_contour']
                        else:
                            if eddy_dic_origin[seedname2]['eddy_shape_radius']!=0:
                                eddy_cont=eddy_dic_origin[seedname2]['eddy_shape_contour']
                            else:
                                eddy_cont=eddy_dic_origin[seedname2]['eddy_effect_contour']
#                                if eddy_dic_origin[seedname2]['eddy_inner_contour_index_i']!=0:
                        eddy_inner_cont=eddy_dic_origin[seedname2]['eddy_inner_contour']
                        if eddy_dic_origin[seedname2]['eddy_shape_radius']!=0    :
                            eddy_shape_cont=eddy_dic_origin[seedname2]['eddy_shape_contour']
                        eddy_cont_e=eddy_dic_origin[seedname2]['eddy_effect_contour']
                        
                        eddy_contlon_e, eddy_contlat_e =np.array(eddy_cont_e[0]),np.array(eddy_cont_e[1])
#                                if eddy_dic_origin[seedname2]['eddy_inner_contour_index_i']!=0: 
                        eddy_innerlon,eddy_innerlat=np.array(eddy_inner_cont[0]),np.array(eddy_inner_cont[1])
                        if eddy_dic_origin[seedname2]['eddy_shape_radius']!=0    :                                
                            eddy_shapelon,eddy_shapelat=np.array(eddy_shape_cont[0]),np.array(eddy_shape_cont[1])
                        
                        '''
                        2.3
                        '''
                        if version==2.4:
 
                            core_lon= eddy_dic_origin[seedname2]['eddy_core'][0]
                            core_lat=eddy_dic_origin[seedname2]['eddy_core'][1]   #'eddy_core'
                            slamaxmin=eddy_dic_origin[seedname2]['eddy_core'][2]
#                                    if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                            if eddy_cont!=0:
                                
                                eddy_contlon_s, eddy_contlat_s = np.array(eddy_cont[0]),np.array(eddy_cont[1])
                      

                        if U_max<=20:
                            Ucolor='#FFCCFF'#'pink'#'#00FF00'
                        elif U_max<=40:
                            Ucolor='#FF66FF'#'#FF00FF'#'#00FFFF'
                        elif U_max>40:
                            Ucolor='#990099'#'purple'
                        Ucolor='#FF66FF'
                        if (eddy_dic_origin[seedname2]['sign_type']=='Cyclonic'):
                            ecolor='#3a4cc0'
#                                    ecolor='r'
                            cc_legend_lats=eddy_cont[0]
                            cc_legend_lons=eddy_cont[1]
                            cc_color='#3a4cc0'
                            ucolor='#627de6'
                            shcolor='#95c45c'
                            
                        else:
                            ecolor='#b30326'
#                                    ecolor='b'
                            ac_legend_lats=eddy_cont[0]
                            ac_legend_lons=eddy_cont[1]
                            ac_color='#b30326'
                            ucolor='#e9755c'
                            shcolor='#c1822f'
                            
                            
                        cx_e, cy_e = m(eddy_contlon_e, eddy_contlat_e)
                        m.plot(cx_e, cy_e,color =ecolor,linewidth=0.5,)
#                                m.plot(cx_e, cy_e,color =ecolor,linewidth=0.3,)
#                               
#                                if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                        if eddy_cont!=0:
                            cx, cy = m(eddy_contlon_s, eddy_contlat_s) 
                            
#                                    m.plot(cx, cy,color =ucolor,linewidth=0.1,)   #linewidth'b'label='eddy_Uavg_border',画涡旋最大地转流速度等高线     
#                                    m.plot(cx, cy,'r.',)
                            m.scatter(cx, cy,s=0.02,c=ucolor,linewidths=0.3)
#                                    m.plot(cx, cy,'1',markersize=0.08)
                           
                        cx1, cy1 = m(eddy_innerlon,eddy_innerlat)
                        m.plot(cx1,cy1,color=ecolor,linewidth=0.5)
#                                m.plot(cx1,cy1,color=ecolor,linewidth=0.5)
                        
                        if eddy_dic_origin[seedname2]['eddy_shape_radius']!=0 :
                              
                            cx2, cy2 = m(eddy_shapelon,eddy_shapelat)
                            m.plot(cx2,cy2,color=shcolor,linewidth=0.5)
#                                    m.plot(cx2, cy2,'b|',markersize=0.15)
#                                    m.scatter(cx2, cy2,s=0.05,c=ecolor,linewidths=0.0001)
                        
                        centx, centy=m(core_lon, core_lat)    
                        m.scatter(centx, centy,s=seedsize,c=ecolor,linewidths=0.3)    
                            
                        """
                        暂时注掉
                        """
#                           
                        '''涡旋个数统计 '''
                        if  eddy_dic_origin[seedname2]['sign_type']=='Anticyclonic':   #'''''''''''''''''''''''''''#
                            
#                                    if 105<=core_lon<=115 and 12<=core_lat<=25:
                            if 265<=core_lon<=270 and -42<=core_lat<=-40:    
                                Southsea_Anti_eddys_num=Southsea_Anti_eddys_num+1
#                                        Global_Anti_eddys_num=Global_Anti_eddys_num+1
            
                        else:
                            cyc_eddys_num=cyc_eddys_num+1
#                                    if 105<=core_lon<=115 and 12<=core_lat<=25:
                            if 265<=core_lon<=270 and -42<=core_lat<=-40:  
                                Southsea_cyc_eddys_num=Southsea_cyc_eddys_num+1
#                                        Global_cyc_eddys_num=Global_cyc_eddys_num+1 
                       
                    #        
                                    
            print("seed_num",seed_num) 
            print("eddy_num",eddy_num)                  
            #总的涡旋数  
            
            cc_lon,cc_lat=m(cc_legend_lons,cc_legend_lats)
            ac_lon,ac_lat=m(ac_legend_lons,ac_legend_lats)
            
            #左上角的标注
            m.plot(cc_lon,cc_lat,color =cc_color,linewidth=3,label='CE     '+str(Southsea_cyc_eddys_num)) 
            m.plot(ac_lon,ac_lat,color =ac_color,linewidth=3,label='AE     '+str(Southsea_Anti_eddys_num)) 

            ''''''
    #         ##等高线颜色-深度图
            if dep=='true':
                CS =m.contour(xpcol, ypcol,sla,slaparameter,colors='gray')#,cmap=plt.cm.jet)
            else:#普通等高线图
                CS =m.contour(xpcol, ypcol,sla,slaparameter,cmap=plt.cm.jet,linewidths=0.3)
            
            
            legend=plt.legend(loc = 'upper left')
            ltext = plt.gca().get_legend().get_texts()
            plt.setp(ltext[0], fontsize=10, color='w')
            plt.setp(ltext[1], fontsize=10, color='w')
    #        plt.setp(ltext[2], fontsize=10, color='w')
    #        plt.setp(ltext[3], fontsize=10, color='w')
    #        plt.setp(ltext[4], fontsize=10, color='w')
    #        
    #        
    
            
           
            frame = legend.get_frame()
            frame.set_color('k')
            
            font = {'family' : 'serif',
                      'color'  : 'k',
                      'weight' : 'normal',
                      'size'   : 16,
                      }
                      
                      
    #        title = str(os.path.split(eddy_file)[1][0:7])+' '+' Eddies'   #'  
            title = date+' '+' Eddies'   #'  
    
            #加title
            plt.title(title, fontdict=font)
            divider = make_axes_locatable(ax1)
            location='right'
            size="3%"
            pad='3%'
            cax = divider.append_axes(location, size=size, pad=pad)
            
            ax2=fig.add_axes(cax) #0.89
            '''
            等高线修改'''
            if dep=='true':
                cb=fig.colorbar(cf ,ax2)#cf CS 
            else:
                cb=fig.colorbar(CS ,ax2)
            cb.ax.set_title('m')
            
            m.drawmapboundary()# fill_color='gray' '#689CD2'#填充海洋的颜色
            #pdb.set_trace()
            m.drawparallels(np.arange(latmin,latmax+1,0.5),labels=[1,0,0,0],fontsize=10)#+1+4
            m.drawmeridians(np.arange(lonmin,lonmax+1,0.5),labels=[0,0,0,1],fontsize=10)#+1+4
    #        m.drawparallels(np.arange(latmin,latmax,float((latmax-latmin)/8)),labels=[1,0,0,0],fontsize=10)#+1+4
    #        m.drawmeridians(np.arange(lonmin,lonmax,float((lonmax-lonmin)/8)),labels=[0,0,0,1],fontsize=10)#+1+4
    #        m.drawparallels(np.arange(latmin,latmax,1))#+1+4
    #        m.drawmeridians(np.arange(lonmin,lonmax,1))#+1+4
            m.drawcoastlines()
            m.fillcontinents(color='k',lake_color='#689CD2',zorder=0)  #'#BF9E30'  #填充大陆颜色，湖泊颜色       
            savefilename=outjpgdirectory+title+st+location+'new_detect.jpg'
            plt.savefig(savefilename,bbox_inches='tight',pad_inches = 0,dpi=dpi)
            plt.show()
            #plt.clf()
            print('success')
        
    print ('Duration', str((time.time() - start_time) ), 'seconds!')
    
    
    
    
  