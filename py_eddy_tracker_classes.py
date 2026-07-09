# -*- coding: utf-8 -*-
# %run py_eddy_tracker_classes.py

"""
===========================================================================
This file is part of py-eddy-tracker.

    py-eddy-tracker is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    py-eddy-tracker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with py-eddy-tracker.  If not, see <http://www.gnu.org/licenses/>.

Copyright (c) 2014 by Evan Mason
Email: emason@imedea.uib-csic.es
===========================================================================

py_eddy_tracker_classes.py

Version 1.4.1
===========================================================================


"""
# External modules
#import matplotlib
#matplotlib.use("TkAgg")  # or whichever backend you wish to use

import json
import pdb
# import geojson as gj
# from osgeo import ogr  #将涡旋相关数据导出到shp文件中
import matplotlib.pyplot as plt
import numpy as np
import numexpr as ne 
import time,os
import matplotlib.dates as dt
from scipy import ndimage
from scipy import interpolate
from scipy import spatial
from scipy import io
# import matplotlib.path as path
# import matplotlib.patches as patch
import scipy.ndimage.filters as filters
import scipy.ndimage.morphology as morphology
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import generate_binary_structure, binary_erosion
import ogr
from make_eddy_tracker_list_obj import *
from collections import OrderedDict


#import haversine_distmat_py as hav # needs compiling with f2py

def DelLastChar(str):
	str_list=list(str)
	str_list.pop()
	return "".join(str_list)
def getdatamin(slalocal):
    datamin=9999
    for n in range(len(slalocal[0])):
           for m in range(len(slalocal)):
               if (slalocal[m][n]>-5):
                   if slalocal[m][n]<datamin:
                       datamin=slalocal[m][n]
    return datamin

def datestr2datetime(datestr):
    '''
    Take strings with format YYYYMMDD and convert to datetime instance
    '''
    assert len(datestr) == 8, "'datestr' must have length 8"
    assert datestr[0] in ('1', '2'), "first character of 'datestr' should be '1' or '2'"
    return dt.datetime.datetime(np.int(datestr[:4]),
                                np.int(datestr[4:6]),
                                np.int(datestr[6:]))

def gaussian_resolution(res, zwl, mwl):
    '''
    Get parameters for ndimage.gaussian_filter
    See http://stackoverflow.com/questions/14531072/how-to-count-bugs-in-an-image
    Input: res : grid resolution in degrees
           zwl : zonal distance in degrees
           mwl : meridional distance in degrees
    '''
    #print ('gaussian_resolution')
    zres = np.copy(zwl)
    mres = np.copy(mwl)
    zres *= 0.125
    mres *= 0.125
    zres /= res
    mres /= res
    return zres, mres

def detect_local_minima(arr):
    """
    Takes an array and detects the troughs using the local maximum filter.
    Returns a boolean mask of the troughs (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)
    http://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array/3689710#3689710
    """
    #print ('detect_local_minima')用到了
#    pdb.set_trace()
#    neighborhood = morphology.generate_binary_structure(len(arr.shape), 2)
    neighborhood=np.array([[ True,  True,  True,True,True],
       [ True,  True,  True,True,True],
       [  True,  True,  True,True,True],
       [True,  True,  True,True,True],
       [ True,  True,  True,True,True]], dtype=bool)   
    local_min = (filters.minimum_filter(arr, footprint=neighborhood) == arr)
    background = (arr == 0)
    eroded_background = morphology.binary_erosion(
        background, structure=neighborhood, border_value=1)
    detected_minima = local_min - eroded_background
    return detected_minima
  
def half_interp(h1, h2):
    '''
    Speed up for frequent operations
    '''
    #print ('half_interp')
    return ne.evaluate('0.5 * (h1 + h2)')

def pcol_2dxy(x, y):
    '''
    Function to shift x, y for subsequent use with pcolor
    by Jeroen Molemaker UCLA 2008
    '''
    #print ('pcol_2dxy')
    Mp, Lp = x.shape
    M = Mp - 1
    L = Lp - 1
    x_pcol = np.zeros((Mp, Lp))
    y_pcol = np.zeros((Mp, Lp))
    x_tmp = half_interp(x[:,:L], x[:,1:Lp])
    x_pcol[1:Mp,1:Lp] = half_interp(x_tmp[0:M,:], x_tmp[1:Mp,:])
    x_pcol[0,:] = 2. * x_pcol[1,:] - x_pcol[2,:]
    x_pcol[:,0] = 2. * x_pcol[:,1] - x_pcol[:,2]
    y_tmp = half_interp(y[:,0:L], y[:,1:Lp]    )
    y_pcol[1:Mp,1:Lp] = half_interp(y_tmp[0:M,:], y_tmp[1:Mp,:])
    y_pcol[0,:] = 2. * y_pcol[1,:] - y_pcol[2,:]
    y_pcol[:,0] = 2. * y_pcol[:,1] - y_pcol[:,2]
    return x_pcol, y_pcol

def fit_circle(xvec, yvec):
    '''
    Fit the circle
    Adapted from ETRACK (KCCMC11)
    '''
    #print ('fit_circle') 用到了
    #
    
    xvec, yvec = xvec.copy(), yvec.copy()
    if xvec.ndim == 1:
        xvec = xvec[np.newaxis]
    if yvec.ndim == 1:
        yvec = yvec[np.newaxis]
    if xvec.shape[1] != 1:
        xvec = xvec.T
    if yvec.shape[1] != 1:
        yvec = yvec.T
    
    npts = xvec.size
    xmean = np.mean(xvec)
    ymean = np.mean(yvec)
    xsc = ne.evaluate('xvec - xmean')
    ysc = ne.evaluate('yvec - ymean')
    scale = np.max((np.hypot(xsc, ysc).max(), np.finfo(float).eps))
    xsc /= scale
    ysc /= scale

    # Form matrix equation to be solved and solve it
    xyz  = np.linalg.lstsq(
             np.concatenate((2. * xsc, 2. * ysc, np.ones((npts, 1))), axis=1),
             np.hypot(xsc, ysc)**2)
    # Unscale data and get circle variables
    p = np.array([xmean, ymean, 0.]) +  \
        np.concatenate((xyz[0][0], xyz[0][1],
                        np.sqrt(xyz[0][2] + np.hypot(xyz[0][0], xyz[0][1])**2))) * scale

    ccx = p[0] # center X-position of fitted circle
    ccy = p[1] # center Y-position of fitted circle
    r = p[2] # radius of fitted circle
    carea = np.pi       
    carea = ne.evaluate('carea * r**2') # area of fitted circle
    
    # Shape test
    # Area and centroid of closed contour/polygon
    tmp = (xvec[:npts-1] * yvec[1:npts]) - (xvec[1:npts] * yvec[:npts-1])
    polar = ne.evaluate('sum(tmp, axis=None)')
    polar = ne.evaluate('0.5 * polar')
    parea = ne.evaluate('abs(polar)')
    
    # Find distance between circle center and contour points_inside_poly
    dist_poly = np.hypot(xvec - ccx, yvec - ccy)

    sintheta = ne.evaluate('(yvec - ccy) / dist_poly')
    ptmp_y = ne.evaluate('ccy + ( r * sintheta )')
    ptmp_x = ne.evaluate('ccx - (ccx - xvec) * ((ccy - ptmp_y) / (ccy - yvec))')

    pout_id = np.nonzero(dist_poly > r) # indices of polygon points outside circle
                                        # p_inon_? : polygon x or y points inside & on the circle
    p_inon_x = xvec # init 
    p_inon_y = yvec # init 
    p_inon_x[pout_id] = ptmp_x[pout_id]
    p_inon_y[pout_id] = ptmp_y[pout_id]

    # Area of closed contour/polygon enclosed by the circle
    tmp = (p_inon_x[0:npts-1] * p_inon_y[1:npts])  -    \
          (p_inon_x[1:npts]   * p_inon_y[0:npts-1])
    
    parea_incirc = ne.evaluate('sum(tmp, axis=None)')
    parea_incirc = ne.evaluate('0.5 * abs(parea_incirc)')
    aerr = ne.evaluate('100.0 * ((1 - parea_incirc / carea) + (parea - parea_incirc) / carea)')
    return ccx, ccy, r, aerr, npts

def get_circle(x0, y0, r, npts):
    '''
    Return points on a circle, with specified (x0,y0) center and radius
                    (and optional number of points too!).
  
    Input     : 1  - x0, scalar, center X of circle
                2  - y0, scalar, center Y of circle
                3  - r,  scalar, radius
                4  - npts, scalar, number of points (optional)

    Output    : 1  - cx, circle x-points
                2  - cy, circle y-points

    Example   :  [cx cy] = func_get_circle (5, 5, 3, 256)
                plot (cx, cy, '-')

    Written By : UCLA ROMS Team (jaison@atmos.ucla.edu) 
    Written On : June/05/2008
    Tool       : Eddy Tracker
    '''
    theta = np.arange(npts)
    theta = ne.evaluate('theta * 2. * (4. * arctan(1.)) / npts')
    cx  = ne.evaluate('x0 + r * cos(theta)')
    cy  = ne.evaluate('y0 + r * sin(theta)')
    return cx, cy 

def get_eddy_Uavg(Eddy,poly_e, grd):
    '''
    Calculate geostrophic speed around successive contours
    Returns the average
    
    If save_all_uavg == True we want Uavg for every contour
    '''
    #print ('get_Uavg')
    def calc_uavg(points, uspd, lon, lat):
        '''
        TO DO: IT SHOULD BE QUICKER, AND POSSIBLY BETTER, TO DO THIS BY CALCULATING
        WEIGHTS AND THEN USING np.average()...
        '''
        uavg = interpolate.griddata(points, uspd.ravel(), (lon, lat), 'linear')
#        print 'uavg',uavg
        return np.mean(uavg[np.isfinite(uavg)])
    #istr, iend, jstr, jend = Eddy.i0, Eddy.i1, Eddy.j0, Eddy.j1
    imin, imax, jmin, jmax = Eddy.imin, Eddy.imax, Eddy.jmin, Eddy.jmax
#    print 'imin, imax, jmin, jmax',imin, imax, jmin, jmax   #每次都是一样的 
    points = np.array([grd.lon()[jmin:jmax,imin:imax].ravel(),
                       grd.lat()[jmin:jmax,imin:imax].ravel()]).T
#    print 'points',points
    # First contour is the outer one (effective)
    theseglon, theseglat = poly_e.vertices[:,0].copy(), poly_e.vertices[:,1].copy()
#    print 'poly_e',poly_e
#    theseglon, theseglat =uniform_resample(theseglon, theseglat)
    #计算该区域的平均地转流速度
#    print imin, imax, jmin, jmax,Eddy.Uspd[jmin:jmax,imin:imax]
#    print '------------------------------------------------------------'
#    
    Uavg = calc_uavg(points, Eddy.Uspd[jmin:jmax,imin:imax], theseglon[:-1], theseglat[:-1])
#    print 'Uavg',Uavg
    return Uavg   

def collection_loop(CS, grd, eddy_dic,eddy_pixel_num_range,Block_name,list_obj,
                    xi=None, CSxi=None, sign_type='None'):  #, verbose=False
    '''
    Loop over each collection of contours
    '''
    # Loop over each collection

    for collind, coll in enumerate(CS.collections):   #迭代等高线
        lineValue=CS.cvalues[collind]
        for cont_index in range(len(coll.get_paths())): 
            cont=coll.get_paths()[cont_index]             
            #print ('cont',cont)
            #得到等高线的经纬度数组
            
            contlon_e, contlat_e = cont.vertices[:,0].copy(), \
                                   cont.vertices[:,1].copy()        
            # Filter for closed contours如果是闭合的等高线
            if np.alltrue([contlon_e[0] == contlon_e[-1],contlat_e[0] == contlat_e[-1],contlon_e.ptp(),contlat_e.ptp()]):
                contain_num=0  #初始化的等高线包含的种子点个数
                seed_index=''   #初始化种子点索引序列 
                ##判断等高线是否只包含一个种子点
                for seedname in eddy_dic: 
                    if cont.contains_point(eddy_dic[seedname]['eddy_core'][0:2]): 
                        contain_num=contain_num+1      #该等高线包含的种子点个数 
                        seed_index=seedname   #记录种子点的索引序列 
                    if contain_num>1:
                        break
                    
                seedname1=seed_index 
		#包含一个种子点
                if (contain_num==1): #  #and eddy_dic[seedname1]['eddy_flag']==False
                    proceed0 = True 
                else:

                    proceed0 = False
                    
                if proceed0:
                    list_obj.set_bounds(contlon_e, contlat_e, grd)# Get lon,lat of bounding box around list_obj
                    imin = list_obj.imin    #涡旋有效边界的经纬度下标
                    imax = list_obj.imax
                    jmin = list_obj.jmin
                    jmax = list_obj.jmax
                    U=list_obj.u_speed
                    V=list_obj.v_speed
                   
                    u= U[jmin:jmax,imin:imax]
                    v= V[jmin:jmax,imin:imax]
                    lon_eddy=grd.lon()[jmin:jmax,imin:imax]
                    lat_eddy=grd.lat()[jmin:jmax,imin:imax]
                    
                    Uavg=get_eddy_Uavg(list_obj,cont, grd) #计算等高线平均地转流速度 
                    uv_fillvalue_flag = True
                    for i in range(len(u)):
                       for j in range(len(u[0])):
                            point=np.array([[lon_eddy[i][j],lat_eddy[i][j]]])
                            if cont.contains_points(point):
                                if abs(u[i][j])>1000 or abs(v[i][j])>1000:
                                     uv_fillvalue_flag=False
                    if abs(Uavg)<1000:
                        if uv_fillvalue_flag:                 
                           points = np.array([grd.lon()[jmin:jmax,imin:imax].ravel(),
                                          grd.lat()[jmin:jmax,imin:imax].ravel()]).T
                           #               
                           mask_i = cont.contains_points(points)
                           # sum(mask) between 8 and 1000, CSS11 criterion 2 判断像素个数
                           #人为定义的涡旋
                           if np.logical_and(np.sum(mask_i) >= 2,
                                                  np.sum(mask_i) <= 10000):
                              proceed1 = True
                           else:
                              proceed1 = False              
                           if  proceed1:    
                             # Prepare for shape test and get list_obj_radius_e
                            #cx, cy =(contlon_e, contlat_e)   #等高线 
#                            pdb.set_trace()
                            cx, cy = list_obj.M(contlon_e, contlat_e)
                            
                            #获取aerr  (获取等高线的图心，半径)
                            
                            centlon_e, centlat_e, eddy_radius_e, aerr, junk = fit_circle(cx, cy)    
                            aerr = np.atleast_1d(aerr)
                            lonmin= contlon_e.min()
                            latmin= contlat_e.min()
                            
                            relative_vorticity=list_obj.eddy_relative_vorticity[jmin:jmax,imin:imax]
                            divergence = list_obj.eddy_divergence[jmin:jmax,imin:imax]
                            shd = list_obj.eddy_shd[jmin:jmax,imin:imax]
                            std = list_obj.eddy_std[jmin:jmax,imin:imax]
                           # print('pm_pn_value',pn_pm_value)
                            
                            
                            
                            eke =0
                            uv_spe=0
                            num=0
                            ed_vorticity=0
                            ed_divergence=0
                            ed_shd=0
                            ed_std=0
                            #
                            for i in range(len(u)):
                                for j in range(len(u[0])):
                                    point=np.array([[lon_eddy[i][j],lat_eddy[i][j]]])
                                    if cont.contains_points(point):
                                        uv=pow(u[i][j],2)+pow(v[i][j],2)
                                        eke=uv*0.5+eke
    #                                            uv_spe= np.sqrt(uv)+uv_spe
    #                                            eddy_vorticity=relative_vorticity[i][j]+eddy_vorticity
                                        uv_spe = np.sqrt(uv)+uv_spe
                                        ed_vorticity = relative_vorticity[i][j]+ed_vorticity
                                        ed_divergence = divergence[i][j]+ed_divergence                                        
                                        ed_shd = shd[i][j]+ed_shd 
                                        ed_std = std[i][j]+ed_std
                                        num=num+1
                            uvspeed=uv_spe/num
                            eddy_r_vorticity=ed_vorticity/num
                            eddy_avg_eke=eke
                            eddy_avg_shd=ed_shd/num
                            eddy_avg_std=ed_std/num
                            eddy_avg_divergence=ed_divergence/num
    #                        #判断对于该种子点seedname1是否计算地转流
    #                        #1，对于反气旋若得到Le则不再计算地转流
    #                        #2，对于气旋，在获得Le后再计算地转流   
                            if (eddy_dic[seedname1]['sign_type']=='Cyclonic' and eddy_dic[seedname1]['eddy_flag']) or eddy_dic[seedname1]['sign_type']=='Anticyclonic':  #得到气旋的Le
                                
                                Uavg_amplitude=abs(eddy_dic[seedname1]['eddy_core'][2]-CS.cvalues[collind])                         
                               #[-1]更新最大地转流速度等高线及地转流速度
                                if  Uavg> eddy_dic[seedname1]['eddy_Uavg_max'] :
                                    eddy_dic[seedname1]['eddy_Uavg_max']= Uavg   
                                    eddy_dic[seedname1]['eddy_Uavg_contour']=np.array([contlon_e, contlat_e]).tolist()
                                    eddy_dic[seedname1]['eddy_Uavg_amp']= Uavg_amplitude   
                                    
                                    eddy_dic[seedname1]['eddy_Uavg_radius']= eddy_radius_e/1000   #涡旋半径单位为km
                                    eddy_dic[seedname1]['eddy_Uavg_contour_index_i']=collind
                                    eddy_dic[seedname1]['eddy_Uavg_contour_index_j']=cont_index  #等高线在某级的位置某级的位置
                                    eddy_dic[seedname1]['eddy_Uavg_eke']=eddy_avg_eke 
                                    eddy_dic[seedname1]['eddy_Uavg_uv_speed']=uvspeed #涡旋的平均速度
                                    eddy_dic[seedname1]['eddy_Uavg_relative_vorticity']=eddy_r_vorticity
                                    eddy_dic[seedname1]['eddy_Uavg_divergence']=eddy_avg_divergence
                                    eddy_dic[seedname1]['eddy_Uavg_SHD']=eddy_avg_shd
                                    eddy_dic[seedname1]['eddy_Uavg_STD']=eddy_avg_std
                                    eddy_dic[seedname1]['Uavg_contain_pixel_num']=num#等高线在某级的位置某级的位置
                                    
                            #找到最里的等高线
                            if eddy_dic[seedname1]['sign_type']=='Cyclonic':
                                  if lineValue<eddy_dic[seedname1]['eddy_inner_contour_sla']:
                                    eddy_dic[seedname1]['eddy_inner_contour_sla']=lineValue
                                    eddy_dic[seedname1]['eddy_inner_contour_index_i']=collind
                                    eddy_dic[seedname1]['eddy_inner_contour_index_j']=cont_index
                                    eddy_dic[seedname1]['eddy_inner_contour']=np.array([contlon_e, contlat_e]).tolist()
                                   #求质心
                                    point= np.array([contlon_e.ravel(), contlat_e.ravel()]).T
                                    new_point='POLYGON(('                 
                                    for i in point:
                                          new_point=new_point+str(i[0])+' '+str(i[1])+','
                                    new_point=DelLastChar(new_point)
                                    new_point=new_point+'))'
                    
                                    geom_poly = ogr.CreateGeometryFromWkt(new_point)
                                    Centroid_geometry=str(geom_poly.Centroid())
                                      
                                    Centroid_lon=float(Centroid_geometry.split(' ')[1].split('(')[1])
                                    Centroid_lat=float(Centroid_geometry.split(' ')[2].split(')')[0])
                                    eddy_dic[seedname1]['eddy_centroid_core']=[Centroid_lon,Centroid_lat]
                                    #求最里层等高线的拟合圆心
                                    
                                    circle_centlon_e, circle_centlat_e, eddy_radius_e_inner, aerr, junk = fit_circle(contlon_e, contlat_e) 
                                    eddy_dic[seedname1]['eddy_circle_core']=[centlon_e, centlat_e]
                            elif  eddy_dic[seedname1]['sign_type']=='Anticyclonic':
                                  if lineValue>eddy_dic[seedname1]['eddy_inner_contour_sla']:
                                    eddy_dic[seedname1]['eddy_inner_contour_sla']=lineValue
                                    eddy_dic[seedname1]['eddy_inner_contour_index_i']=collind
                                    eddy_dic[seedname1]['eddy_inner_contour_index_j']=cont_index
                                    eddy_dic[seedname1]['eddy_inner_contour']=np.array([contlon_e, contlat_e]).tolist()
                                   #求质心
                                    point= np.array([contlon_e.ravel(), contlat_e.ravel()]).T
                                    new_point='POLYGON(('                 
                                    for i in point:
                                          new_point=new_point+str(i[0])+' '+str(i[1])+','
                                    new_point=DelLastChar(new_point)
                                    new_point=new_point+'))'
                    
                                    geom_poly = ogr.CreateGeometryFromWkt(new_point)
                                    Centroid_geometry=str(geom_poly.Centroid())
                                      
                                    Centroid_lon=float(Centroid_geometry.split(' ')[1].split('(')[1])
                                    Centroid_lat=float(Centroid_geometry.split(' ')[2].split(')')[0])
                                    eddy_dic[seedname1]['eddy_centroid_core']=[Centroid_lon,Centroid_lat]
                                    #求最里层等高线的拟合圆心
                                    
                                    circle_centlon_e, circle_centlat_e, eddy_radius_e_inner, aerr, junk = fit_circle(contlon_e, contlat_e) 
                                    eddy_dic[seedname1]['eddy_circle_core']=[centlon_e, centlat_e]
                           
                            amplitude=abs(eddy_dic[seedname1]['eddy_core'][2]-CS.cvalues[collind])
#                               
                            
                            
                            
                            """
                            添加形状测试
                            """       
                            if np.logical_and(aerr >= 0., aerr <= list_obj.shape_err[collind]):
                                                  
                                proceed2 = True
                            else:
                                proceed2 = False 
                            
                            if  proceed2: #振幅
                                amplitude=abs(eddy_dic[seedname1]['eddy_core'][2]-CS.cvalues[collind])
                            
                                if np.logical_and(amplitude >= list_obj.ampmin, amplitude <= list_obj.ampmax):
                                    #if eddy_dic[seedname1]['sign_type']=='Cyclonic' and not eddy_dic[seedname1]['eddy_flag']:
                                    if eddy_dic[seedname1]['sign_type']=='Cyclonic' and eddy_dic[seedname1]['eddy_shape_radius']==0:    
                                        eddy_dic[seedname1]['eddy_shape_radius']= eddy_radius_e/1000                                         
                                        eddy_dic[seedname1]['eddy_shape_amp']= amplitude 
                                        eddy_dic[seedname1]['eddy_shape_contour']=np.array([contlon_e, contlat_e]).tolist()
                                        eddy_dic[seedname1]['eddy_shape_contour_i']=collind
                                        eddy_dic[seedname1]['eddy_shape_contour_j']=cont_index
                                        eddy_dic[seedname1]['eddy_shape_eke']= eddy_avg_eke 
                                        eddy_dic[seedname1]['eddy_shape_uv_speed'] = uvspeed #涡旋的平均速度
                                        eddy_dic[seedname1]['eddy_shape_relative_vorticity'] = eddy_r_vorticity
                                        eddy_dic[seedname1]['eddy_shape_divergence'] = eddy_avg_divergence
                                        eddy_dic[seedname1]['eddy_shape_SHD'] = eddy_avg_shd
                                        eddy_dic[seedname1]['eddy_shape_STD'] = eddy_avg_std
                                        eddy_dic[seedname1]['shape_contain_pixel_num']=num
                                    elif  eddy_dic[seedname1]['sign_type']=='Anticyclonic':
                                        eddy_dic[seedname1]['eddy_shape_radius']= eddy_radius_e/1000 
                                        eddy_dic[seedname1]['eddy_shape_amp']= amplitude 
                                        eddy_dic[seedname1]['eddy_shape_contour']=np.array([contlon_e, contlat_e]).tolist()
                                        eddy_dic[seedname1]['eddy_shape_contour_i']=collind
                                        eddy_dic[seedname1]['eddy_shape_contour_j']=cont_index
                                        eddy_dic[seedname1]['eddy_shape_eke']= eddy_avg_eke 
                                        eddy_dic[seedname1]['eddy_shape_uv_speed'] = uvspeed #涡旋的平均速度
                                        eddy_dic[seedname1]['eddy_shape_relative_vorticity'] = eddy_r_vorticity
                                        eddy_dic[seedname1]['eddy_shape_divergence'] = eddy_avg_divergence
                                        eddy_dic[seedname1]['eddy_shape_SHD'] = eddy_avg_shd
                                        eddy_dic[seedname1]['eddy_shape_STD'] = eddy_avg_std
                                        eddy_dic[seedname1]['shape_contain_pixel_num']=num
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            if eddy_dic[seedname1]['sign_type']=='Cyclonic' and not eddy_dic[seedname1]['eddy_flag']:
                                    
                                    eddy_dic[seedname1]['eddy_effect_radius']= eddy_radius_e/1000   #涡旋半径单位为km
                                    eddy_dic[seedname1]['eddy_effect_amp']= amplitude 
                                    eddy_dic[seedname1]['eddy_effect_contour']=np.array([contlon_e, contlat_e]).tolist()
                                    eddy_dic[seedname1]['eddy_effect_contour_i'] = collind
                                    eddy_dic[seedname1]['eddy_effect_contour_j'] = cont_index
                                    eddy_dic[seedname1]['eddy_effect_eke']= eddy_avg_eke 
                                    eddy_dic[seedname1]['eddy_effect_uv_speed'] = uvspeed #涡旋的平均速度
                                    eddy_dic[seedname1]['eddy_effect_relative_vorticity'] = eddy_r_vorticity
                                    eddy_dic[seedname1]['eddy_effect_divergence'] = eddy_avg_divergence
                                    eddy_dic[seedname1]['eddy_effect_SHD'] = eddy_avg_shd
                                    eddy_dic[seedname1]['eddy_effect_STD'] = eddy_avg_std
                                    eddy_dic[seedname1]['effect_contain_pixel_num']=num
                            elif  eddy_dic[seedname1]['sign_type']=='Anticyclonic':
                                    
                                    eddy_dic[seedname1]['eddy_effect_radius']= eddy_radius_e/1000   #涡旋半径单位为km
                                    eddy_dic[seedname1]['eddy_effect_amp']= amplitude 
                                    eddy_dic[seedname1]['eddy_effect_contour']=np.array([contlon_e, contlat_e]).tolist()
                                    eddy_dic[seedname1]['eddy_effect_contour_i']=collind
                                    eddy_dic[seedname1]['eddy_effect_contour_j']=cont_index
                                    eddy_dic[seedname1]['eddy_effect_eke']=eddy_avg_eke 
                                    eddy_dic[seedname1]['eddy_effect_uv_speed']=uvspeed #涡旋的平均速度
                                    eddy_dic[seedname1]['eddy_effect_relative_vorticity']=eddy_r_vorticity
                                    eddy_dic[seedname1]['eddy_effect_divergence']=eddy_avg_divergence
                                    eddy_dic[seedname1]['eddy_effect_SHD']=eddy_avg_shd
                                    eddy_dic[seedname1]['eddy_effect_STD']=eddy_avg_std
                                    eddy_dic[seedname1]['effect_contain_pixel_num']=num
                            eddy_dic[seedname1]['eddy_flag']=True
                            
#                               
                                
    Block_eddy_info=OrderedDict()
    eddy_info=OrderedDict()
    inner_eddy=OrderedDict()
    outer_eddy=OrderedDict()
    inner_block_eddy = OrderedDict()
    outer_block_eddy = OrderedDict()
    eddy_num=0
#    fig250 = plt.figure(250) 
    do_fig_250 = True                  
    if 'do_fig_250' in locals(): 
        if do_fig_250:
            for seedname2 in  eddy_dic:
                if eddy_dic[seedname2]['eddy_flag']:
#                    eddy_info.setdefault(seedname2,eddy_dic[seedname2]) 
                    eddy_num=eddy_num+1 
                    #判断最大地转流速度等高线是否在有效边界内 
                    
                    if eddy_dic[seedname2]['eddy_Uavg_contour']!=0: 
                     #判断经度是不是小于0
                       for i in range(len(eddy_dic[seedname2]['eddy_Uavg_contour'][0])): 
                           if eddy_dic[seedname2]['eddy_Uavg_contour'][0][i]<0:
                               eddy_dic[seedname2]['eddy_Uavg_contour'][0][i]=eddy_dic[seedname2]['eddy_Uavg_contour'][0][i]+360
                    if eddy_dic[seedname2]['eddy_effect_contour']!=0: 
                       for j in range(len(eddy_dic[seedname2]['eddy_effect_contour'][0])):
                           if eddy_dic[seedname2]['eddy_effect_contour'][0][j]<0:
                               eddy_dic[seedname2]['eddy_effect_contour'][0][j]=eddy_dic[seedname2]['eddy_effect_contour'][0][j]+360  
                    seedname3=seedname2
                    if float(seedname2.split('_')[1])<0:
                        lon_tran=float(seedname2.split('_')[1])+360 
                        eddy_dic[seedname2]['eddy_core'][0]=lon_tran
                        seedname3='eddy'+'_'+ str(lon_tran)+'_'+seedname2.split('_')[2] 
                        

                    if eddy_dic[seedname2]['eddy_inout']=='inner':
#                        del eddy_dic[seedname2]['eddy_inout']
                        inner_block_eddy.setdefault(seedname3,eddy_dic[seedname2])
                    else: 
#                        del eddy_dic[seedname2]['eddy_inout']
                        outer_block_eddy.setdefault(seedname3,eddy_dic[seedname2])
             
                            
                         
    inner_eddy.setdefault(Block_name,inner_block_eddy)
    outer_eddy.setdefault(Block_name,outer_block_eddy)
    eddy_info.setdefault('inner',inner_eddy)
    eddy_info.setdefault('outer',outer_eddy)
#    Block_eddy_info.setdefault(Block_name,eddy_info)
#    print ('eddy_info',eddy_info)
#    print ('Duration_Loop %s seconds'% str(time.time() - loop_time)) 
    return eddy_info


 

        
    