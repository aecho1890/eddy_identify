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
    #directory = 'C:\\Users\\Leo\\Desktop\\20141201\\json\\'    #涡旋识别结果路径
    directory = 'D:\\data&py\\data\\AVISO\\msla\\dt\\test\\json5\\json\\'
    #G:\yisuodata\005\pic\json
    #E:\Pdata\ncdata\data\tif\00a\test2\pic\json
    '''sla'''
    tifdirectory='D:\\data&py\\data\\AVISO\\msla\\dt\\test\\h\\'  
    if location=='depth':
        dep='true'
        #outjpgdirectory='C:\\Users\\Leo\\Desktop\\20141201\\jpg\\'  #输出jpg路径
        outjpgdirectory='D:\\data&py\\data\\AVISO\\msla\\dt\\test\\json5\\jpg\\'  #输出jpg路径
    else:
        dep='tru'
        outjpgdirectory='D:\\data&py\\data\\AVISO\\msla\\dt\\test\\json5\\jpg\\' 
    #area='South China Sea'
#    area='West Pacific'
    #area="#"
    area="South China Sea"
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
        lonmin, lonmax, latmin, latmax=95,165,-15,45#100,200,-20,50
#        lonmin, lonmax, latmin, latmax=108,126,12,27#100,200,-20,50
        figsize=(9,12)
        cb_ax=[0.90,0.05, 0.015, 0.9]
    elif area=='South China Sea':
        linewidth,seedsize,dpi=1,40,500
#        lonmin, lonmax, latmin, latmax=84.125,138.125,53,89 #100,120,5,30#105,120,10,25#
        #lonmin, lonmax, latmin, latmax=104.5,134.5,4.5,34.5
        '''于老师需要范围'''
        #lonmin, lonmax, latmin, latmax=105,135,5,25
        lonmin, lonmax, latmin, latmax=105,125,5,25
        figsize=(10, 10)
#        figsize=(16, 16)  #尽量同实际经纬度相同
        cb_ax=[0.93,0.05, 0.02, 0.90]
    elif area=='South Atlantic Ocean': #南大西洋
        linewidth,seedsize,dpi=1,10,500
        lonmin, lonmax, latmin, latmax=290,360,-50,-15
        figsize=(16, 8)
        cb_ax=[0.955,0.05, 0.015, 0.89]    
        
    start_time=time.time()  #获取当前时间
    gdal.AllRegister()  #注册gdal 安装数据驱动
    #pdb.set_trace()
    AVISO_files =glob.glob(directory+'*.json') 
    #pdb.set_trace()
    tif_files =glob.glob(tifdirectory+'*.tif') 

   #获取特定区域的索引值
    #pdb.set_trace()   
    jmin=int((latmin+89.875)/0.25)
    jmax=int((latmax+89.875)/0.25)
    imin=int((lonmin-0.125)/0.25)
    imax=int((lonmax-0.125)/0.25)
#    jmin=int((latmin+90)/0.1)
#    jmax=int((latmax+90)/0.1)
#    imin=int((lonmin)/0.1)
#    imax=int((lonmax)/0.1)
    if area!='Global Ocean':
        imin-=4
        imax+=4
        jmin-=4
        jmax+=4
#    lon_grid = np.arange(0,360,0.1)[imin:imax]
#    lat_grid  = np.arange(-90,90,0.1)[jmin:jmax]
#    lon_grid = np.arange(105,125,0.1)
#    lat_grid  = np.arange(5,25,0.1)
#    lon_grid = np.arange(105,125,0.25)
#    lat_grid  = np.arange(5,25,0.25)
    lon_grid = np.arange(0.125,360,0.25)[imin:imax]
    lat_grid  = np.arange(-89.875,90,0.25)[jmin:jmax]
    lon_grid, lat_grid= np.meshgrid(lon_grid, lat_grid)  

    for i in range(len(AVISO_files)):   #212  206,213  len(AVISO_files)
        eddy_file=AVISO_files[i]
        f1=open(eddy_file,'r')    #读取涡旋文件 
        eddy_dic_origin1= json.load(f1)
        #eddy_origin= json.load(f1)
        
        fig=plt.figure(250,figsize=figsize) #12, 7
        ax1=fig.add_axes(ax1)#[0.1, 0.15, 0.75, 0.7] #起始坐标的位置
        #设置投影 方法
        m = Basemap(projection='gall', llcrnrlon = lonmin, urcrnrlon = lonmax, \
                    llcrnrlat = latmin, urcrnrlat =  latmax, \
                     lat_ts = 0.5 * ( latmin + latmax), resolution = 'h',ax=ax1)#merc
        xpcol, ypcol = m(lon_grid[:], lat_grid[:])
        
#        ''''''
#        深度图
#        ''''''
        if dep=='true':
            #print('aa')
            height_ds1 = gdal.Open("a.tif")
            height_band1 = height_ds1.GetRasterBand(1)
            height_data = height_band1.ReadAsArray()[::-1]
            levels = MaxNLocator(nbins=100).tick_values(-9000,0)
            height_lon = np.arange(lonmin,lonmax,0.01667)
            height_lat = np.arange(latmin,latmax,0.01667)       
            height_lon_grid, height_lat_grid= np.meshgrid(height_lon, height_lat)  
            height_xpcol, height_ypcol = m(height_lon_grid[:], height_lat_grid[:])
            
            height_mask=height_data>0
            height_mask=np.ma.array(height_data,mask=height_mask)
            np.place(height_data, height_mask == False, 0.)
            height_data1 = np.ma.masked_where(height_mask == False, height_data) # Expand the landmask
            
            cf=m.contourf(height_xpcol, height_ypcol,height_data1,levels =levels, cmap=plt.cm.ocean)#jet
#        #
#    
        
        
        #读取tif文件作为底图
        tiff_file=tif_files[i] #open the tiff file   -90
        ds1 = gdal.Open(tiff_file)
        band1 = ds1.GetRasterBand(1) 
        #data1 = band1.ReadAsArray()[::-1][jmin:jmax,imin:imax]
        data1 = band1.ReadAsArray()[::-1]#[jmin:jmax,imin:imax]
        mask=data1<-100
        sla_mask=np.ma.array(data1,mask=mask)
        np.place(data1, sla_mask == False, 0.)
        
        
        data1 -= ndimage.gaussian_filter(data1, [5, 10.0])
        sla = np.ma.masked_where(sla_mask == False, data1) # Expand the landmask
        '''先滤波再获取局部数据'''
        sla=sla[jmin:jmax,imin:imax]
        slaparameter = np.arange(-1,1.01,0.025)  #固定的最值
        
#        #绘制涡旋有效边界、涡旋最大地转流边界、涡心
        Anti_eddys_num=0
        cyc_eddys_num=0
#        Southsea_Anti_eddys_num=0
#        Southsea_cyc_eddys_num=0
        Global_Anti_eddys_num=0
        Global_cyc_eddys_num=0

        j=0
        eddy_num=0
        seed_num=0
        
        #Block_dic=innr_dic["Block_0_0"]
        #pdb.set_trace()
        for i in range(len(eddy_dic_origin1)):
            eddy_dic_origin=eddy_dic_origin1[i]
            for seedname2 in eddy_dic_origin.keys():
#        for key1 in eddy_origin.keys():
#            if key1=="inner":
#                innr_dic=eddy_origin["inner"]
#                for key2 in innr_dic.keys():
#                    if key2=="Block_0_0":
#                        eddy_dic_origin=innr_dic["Block_0_0"]
#                        for seedname2 in eddy_dic_origin.keys():
                
#            if seedname2=='inner':
#                for 

                    
                            point_type=seedname2.split('_')[0]
                            
                            if point_type=='seed':
                                #pdb.set_trace()
                                seed_num+=1
                                if eddy_dic_origin[seedname2]["sign_type"]=="Cyclonic":
                                    
                                    core_lon1=eddy_dic_origin[seedname2]["eddy_core"][0]
                                    core_lat1=eddy_dic_origin[seedname2]["eddy_core"][1]
                                    centx1, centy1=m(core_lon1, core_lat1)
                                    m.scatter(centx1, centy1,s=seedsize,c='#2a6819',linewidths=0.0001)    
                                elif eddy_dic_origin[seedname2]["sign_type"]=="Anticyclonic":
                                    core_lon2=eddy_dic_origin[seedname2]["eddy_core"][0]
                                    core_lat2=eddy_dic_origin[seedname2]["eddy_core"][1]
         
                                    centx2, centy2=m(core_lon2, core_lat2)
                                
                                    m.scatter(centx2, centy2,s=seedsize,c='#960558',linewidths=0.0001)
                                
                                
                            elif point_type=='eddy':
                                #pdb.set_trace()
                                if eddy_dic_origin[seedname2]['eddy_effect_radius']!=0:
                                    eddy_num=eddy_num+1
                                else:
                                    seed_num+=1
                                #if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                                
                                
                                U_max=eddy_dic_origin[seedname2]['eddy_Uavg_max']
                               
                                #pdb.set_trace()   
                                if U_max<1000:
                                            
                                    seedsize=10
                                    if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                                        eddy_cont=eddy_dic_origin[seedname2]['eddy_Uavg_contour']
    #                                if eddy_dic_origin[seedname2]['eddy_inner_contour_index_i']!=0:
                                    if eddy_dic_origin[seedname2]['eddy_inner_contour']!=0:
                                        eddy_inner_cont=eddy_dic_origin[seedname2]['eddy_inner_contour']
                                    if eddy_dic_origin[seedname2]['eddy_shape_radius']!=0:
                                        eddy_shape_cont=eddy_dic_origin[seedname2]['eddy_shape_contour']
                                    if eddy_dic_origin[seedname2]['eddy_effect_radius']!=0:
                                        eddy_cont_e=eddy_dic_origin[seedname2]['eddy_effect_contour']
                                        #if eddy_shape_cont=eddy_dic_origin[seedname2]['eddy_effect_contour']!=0:
                                        eddy_contlon_e, eddy_contlat_e =np.array(eddy_cont_e[0]),np.array(eddy_cont_e[1])
    #                                if eddy_dic_origin[seedname2]['eddy_inner_contour_index_i']!=0: 
                                    if eddy_dic_origin[seedname2]['eddy_inner_contour']!=0:
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
                                        if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                                            eddy_contlon_s, eddy_contlat_s = np.array(eddy_cont[0]),np.array(eddy_cont[1])
                                  
        
                                    if U_max<=20:
                                        Ucolor='#FFCCFF'#'pink'#'#00FF00'
                                    elif U_max<=40:
                                        Ucolor='#FF66FF'#'#FF00FF'#'#00FFFF'
                                    elif U_max>40:
                                        Ucolor='#990099'#'purple'
                                    Ucolor='#FF66FF'
                                    if (eddy_dic_origin[seedname2]['sign_type']=='Cyclonic'):
                                        #ecolor='#3a4cc0'
                                        ecolor='b'
                                        if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                                            cc_legend_lats=eddy_cont[0]
                                            cc_legend_lons=eddy_cont[1]
                                        cc_color='#3a4cc0'
                                        
                                        
                                        
                                        
                                            
                                    else:
                                        #ecolor='#b30326'
                                        ecolor='r'
                                        if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                                            ac_legend_lats=eddy_cont[0]
                                            ac_legend_lons=eddy_cont[1]
                                        ac_color='#b30326'
                                        
                                    if eddy_dic_origin[seedname2]['eddy_effect_radius']!=0:    
                                        cx_e, cy_e = m(eddy_contlon_e, eddy_contlat_e)
                                    #m.plot(cx_e, cy_e,color =ecolor,linewidth=0.05,)
                                        m.plot(cx_e, cy_e,color =ecolor,linewidth=1,)
    #                               
                                    if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
                                        cx, cy = m(eddy_contlon_s, eddy_contlat_s) 
                                        
    #                                    m.plot(cx, cy,color =ecolor,linewidth=0.1,linestyle='^')   #linewidth'b'label='eddy_Uavg_border',画涡旋最大地转流速度等高线     
    #                                    m.plot(cx, cy,'r.',)
    #                                    m.scatter(cx, cy,s=0.02,c=ecolor,linewidths=0.0001)
                                        #m.plot(cx, cy,'o',markersize=0.008)
                                        m.plot(cx, cy,'o',markersize=0.2,color=ecolor,linewidth=0.4)
                                    if eddy_dic_origin[seedname2]['eddy_inner_contour']!=0:
                                        cx1, cy1 = m(eddy_innerlon,eddy_innerlat)
                                    #m.plot(cx1,cy1,color=ecolor,linewidth=0.1)
                                        m.plot(cx1,cy1,color=ecolor,linewidth=0.5)
                                    
                                    if eddy_dic_origin[seedname2]['eddy_shape_radius']!=0 :
                                          
                                        cx2, cy2 = m(eddy_shapelon,eddy_shapelat)
                                        #m.plot(cx2,cy2,':',markersize=0.08,color=ecolor,linewidth=0.3)
                                        m.plot(cx2,cy2,'*',markersize=1.1,color='black',linewidth=1.2)
                                        #m.plot(cx2, cy2,'b|',markersize=0.15)
                                        #m.scatter(cx2, cy2,s=0.05,c=ecolor,linewidths=0.0001)
                                        #m.scatter(cx2, cy2,s=0.05,c=ecolor,linewidths=0.4)
                                            
                                    
                                    centx, centy=m(core_lon, core_lat)    
                                    m.scatter(centx, centy,s=seedsize,c=ecolor,linewidths=0.5)    
                                        
                                        
    
                                        
                                    """
                                    暂时注掉
                                    """
    #                           
                                    '''涡旋个数统计 '''
                                    if  eddy_dic_origin[seedname2]['sign_type']=='Anticyclonic':   #'''''''''''''''''''''''''''#
                                        
                                        #if 105<=core_lon<=115 and 12<=core_lat<=25:
    #                                    if 95<=core_lon<=165 and -15<=core_lat<=45:    
                                       
    #                                    Global_Anti_eddys_num=Global_Anti_eddys_num+1
                                        if 105<=core_lon<=125 and 5<=core_lat<=25:
                                            #pdb.set_trace()
                                            if eddy_dic_origin[seedname2]['eddy_effect_radius']!=0:
                                                Global_Anti_eddys_num=Global_Anti_eddys_num+1
                                            
                        
                                    else:
                                        cyc_eddys_num=cyc_eddys_num+1
                                        #if 105<=core_lon<=115 and 12<=core_lat<=25:
    #                                    if 95<=core_lon<=165 and -15<=core_lat<=45:  
                                        #Global_cyc_eddys_num=Global_cyc_eddys_num+1
                                        if 105<=core_lon<=125 and 5<=core_lat<=25:
                                            if eddy_dic_origin[seedname2]['eddy_effect_radius']!=0:
                                                Global_cyc_eddys_num=Global_cyc_eddys_num+1
                   
                #        
                                
        print("seed_num",seed_num) 
        print("eddy_num",eddy_num)
        print("Global_Anti_eddys_num",Global_Anti_eddys_num) 
        print("Global_cyc_eddys_num",Global_cyc_eddys_num)                 
        #总的涡旋数  
        #if eddy_dic_origin[seedname2]['eddy_Uavg_radius']!=0:
#        cc_lon,cc_lat=m(cc_legend_lons,cc_legend_lats)
#        ac_lon,ac_lat=m(ac_legend_lons,ac_legend_lats)
        
        #左上角的标注
#        m.plot(cc_lon,cc_lat,color =cc_color,linewidth=3,label='CE     '+str(Global_cyc_eddys_num)) 
#        m.plot(ac_lon,ac_lat,color =ac_color,linewidth=3,label='AE     '+str(Global_Anti_eddys_num))
        m.plot([],[],color ='b',linewidth=3,label='CE     '+str(Global_cyc_eddys_num)) 
        m.plot([],[],color ='r',linewidth=3,label='AE     '+str(Global_Anti_eddys_num))
#        m.plot([],[],color ='#3a4cc0',linewidth=3,label='CE     '+str(Global_cyc_eddys_num)) 
#        m.plot([],[],color ='#b30326',linewidth=3,label='AE     '+str(Global_Anti_eddys_num))
#        m.plot([],[],color='#FFCCFF',lw=3,label='U_max<=20 cm/s') 

        m.plot([],[],color='#960558',label='AE_SEED')
        m.plot([],[],color='#2a6819',label='CE_SEED')
        
        

        ''''''
         ##等高线颜色-深度图
        if dep=='true':
            CS =m.contour(xpcol, ypcol,sla,slaparameter,colors='gray')#,cmap=plt.cm.jet)
        else:#普通等高线图
            CS =m.contour(xpcol, ypcol,sla,slaparameter,cmap=plt.cm.jet,linewidths=0.3)
        
        
        '''画框'''
        #画直线i
#        x,y=m([109,115],[18,12])
#        m.plot(x,y,'r-',lw=1.5)
        
#        #画圆
#        theta=np.linspace(0,2*np.pi,100)
#        x_circle=6*np.sin(theta)+109
#        y_circle=6*np.cos(theta)+18
#        x_circle,y_circle= m(x_circle,y_circle)
#        m.plot(x_circle,y_circle,'k-',lw=1.5)
        #化有效边界
                
        #画方框
#        southsealons,southsealats=m([105,105,115,115,105],[12,24,24,12,12])
#        m.plot(southsealons,southsealats,'k-',lw=1.5)  ##框框的名称,label='Trading limit'

    
        
#          #画九段线
#        x,y=m([109.27,109.67],[16.24,15.67])
#        m.plot(x,y,'k--',lw=1.5)
#        
#        x,y=m([109.67,109.92],[15.67,15.17])
#        m.plot(x,y,'k--',lw=1.5)
#        
#        x,y=m([109.92,110.16],[15.17,14.17])
#        m.plot(x,y,'k--',lw=1.5)
#        
#        x,y=m([110.16,110.28],[14.17,13.17])
#        m.plot(x,y,'k--',lw=1.5)
#        
#        x,y=m([110.28,110.31],[13.17,12.25])
#        m.plot(x,y,'k--',lw=1.5)
#        
#                
#        x,y=m([110.31,110.26],[12.25,11.67])
#        m.plot(x,y,'k--',lw=1.5)
#        
#        x,y=m([110.26,109.93],[11.67,11.16])
#        m.plot(x,y,'k--',lw=1.5)
#        
        
        #画200海里 1海里=1.852公里 200海里=370400=3.4度
#        x,y=m([111.42,111.82],[16.13,15.63])
#        m.plot(x,y,'r--',lw=1.5)
#        
#        x,y=m([111.82,112.17],[15.63,15.13])
#        m.plot(x,y,'r--',lw=1.5)
#        
#        x,y=m([112.17,112.56],[15.13,14.13])        
#        m.plot(x,y,'r--',lw=1.5)
#        
#        x,y=m([112.56,112.60],[14.13,13.63])        
#        m.plot(x,y,'r--',lw=1.5)
#        
#        x,y=m([112.60,112.66],[13.63,13.13])
#        m.plot(x,y,'r--',lw=1.5)
#        
#        x,y=m([112.66,112.66],[13.13,12.13])
#        m.plot(x,y,'r--',lw=1.5)
#        
#               
#        x,y=m([112.66,112.52],[12.13,11.63])
#        m.plot(x,y,'r--',lw=1.5)
#        
#        x,y=m([112.52,112.16],[11.63,11.13])        
#        m.plot(x,y,'r--',lw=1.5)
#    
#        x1,y1=m([111.04,115.34,115.34,111.04,111.04],[17.55,18.31,17.17,17.17,17.55])
#        m.plot(x1,y1,'k-',lw=1)
        '''
        center
        upper left
        lower center
        right
        center right
        best
        center left
        lower right
        upper center
        lower left
        upper right
         '''
        legend=plt.legend(loc = 'upper left')
        ltext = plt.gca().get_legend().get_texts()
        plt.setp(ltext[0], fontsize=10, color='w')
        plt.setp(ltext[1], fontsize=10, color='w')
        plt.setp(ltext[2], fontsize=10, color='w')
        plt.setp(ltext[3], fontsize=10, color='w')
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
                  
                  
        title = 'madt '+' '+str(os.path.split(eddy_file)[1][15:23])+' '+' Eddies'   #'  

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
#        x = [105,110,115,120,125]  
#        y = [5,10,15,20,25] 
        m.drawmapboundary()# fill_color='gray' '#689CD2'#填充海洋的颜色
        #pdb.set_trace()
        #m.drawparallels(np.arange(latmin,latmax,float((latmax-latmin)/8)),labels=[1,0,0,0],fontsize=10)#+1+4
        #m.drawmeridians(np.arange(lonmin,lonmax,float((lonmax-lonmin)/8)),labels=[0,0,0,1],fontsize=10)#+1+4
        m.drawparallels(np.arange(latmin,latmax,5),labels=[1,0,0,0],fontsize=10)#+1+4
        m.drawmeridians(np.arange(lonmin,lonmax,5),labels=[0,0,0,1],fontsize=10)#+1+4
#        plt.xticks(x, rotation=0)
#        plt.yticks(y, rotation=0)
        
        m.drawcoastlines()
        m.fillcontinents(color='k',lake_color='#689CD2',zorder=0)  #'#BF9E30'  #填充大陆颜色，湖泊颜色       
        savefilename=outjpgdirectory+title+st+location+'111.jpg'
        plt.savefig(savefilename,bbox_inches='tight',pad_inches = 0,dpi=dpi)
        plt.show()
        plt.clf()
        print('success')
        
    print ('Duration', str((time.time() - start_time) ), 'seconds!')
    
    
    
    
  