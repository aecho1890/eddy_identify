# -*- coding: utf-8 -*-
# %run make_eddy_tracker_list_obj.py

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


make_eddy_tracker_list_obj.py

Version 1.4.1


===========================================================================


"""

import haversine_distmat_py as hav 
from py_eddy_tracker_classes import *


def haversine_distance_vector(lon1, lat1, lon2, lat2):
    '''
    Haversine formula to calculate distance between two points
    Uses mean earth radius in metres (from scalars.h) = 6371315.0
    '''
    #print ('haversine_distance_vector')用到了
    dist=hav.haversine_distvec(lon1, lat1, lon2, lat2)
    return dist



def nearest(lon_pt, lat_pt, lon2d, lat2d):
    """
    Return the nearest i, j point to a given lon, lat point
    in a lat/lon grid
    """
    #print ('nearest')用到了
    lon2d, lat2d = lon2d.copy(), lat2d.copy()
    lon2d -= lon_pt
    lat2d -= lat_pt
    d = np.hypot(lon2d, lat2d)
    j, i = np.unravel_index(d.argmin(), d.shape)
    return i, j
    

def uniform_resample(x, y, num_fac=4, kind='linear'):
    '''
    Resample contours to have (nearly) equal spacing
    '''
    #print ('uniform_resample')用到了
    # Get distances
    d = np.r_[0, np.cumsum(haversine_distance_vector(x[:-1],y[:-1], x[1:],y[1:]))]
    # Get uniform distances
    d_uniform = np.linspace(0, d.max(), num=d.size * num_fac, endpoint=True)
    # Do 1d interpolations
    xfunc = interpolate.interp1d(d, x, kind=kind)
    yfunc = interpolate.interp1d(d, y, kind=kind)
    xnew = xfunc(d_uniform)
    ynew = yfunc(d_uniform)
    #plt.plot(xnew, ynew, '.-r', lw=2)
    #plt.axis('image')
    #plt.show()
    return xnew, ynew

class eddy(object):
    
    def __init__(self,eddy_core,eddy_Uavg_contour,eddy_Uavg_contour_index_i,eddy_Uavg_contour_index_j,
                     eddy_Uavg,eddy_Uavg_max,eddy_radius,eddy_amp,eddy_flag,eddy_inout):
        '''
        Initialise the list 'eddy'
    涡心：涡心经纬度、sla值
    最大地转流等高线：数组
    最大地转流速度：u，v
    涡旋半径
    涡旋振幅
        '''        
        self.eddy_core = eddy_core
        self.eddy_Uavg_contour = eddy_Uavg_contour
        self.eddy_Uavg_contour_index_i=eddy_Uavg_contour_index_i  #等高线在某级的位置
        self.eddy_Uavg_contour_index_j=eddy_Uavg_contour_index_j  #等高线在某级的位置
        self.eddy_Uavg = eddy_Uavg
        self.eddy_Uavg_max = eddy_Uavg_max
        self.eddy_radius = eddy_radius
        self.eddy_amp    =eddy_amp
        self.eddy_flag    =eddy_flag
        self.eddy_inout    =eddy_inout
#    def append_eddy_Uavg_contour(self,eddy_Uavg_contour):
#        self.eddy_Uavg_contour = eddy_Uavg_contour
#        return self.eddy_Uavg_contour
#        
#    def append_eddy_Uavg(self,eddy_Uavg):
#        self.eddy_Uavg = eddy_Uavg
#        return self.eddy_Uavg
#        
#    def append_eddy_radius(self,eddy_radius):
#        self.eddy_radius = eddy_radius  
#        return self.eddy_radius
#
#    def append_eddy_Uavg_contour_index(self,eddy_Uavg_contour_index):
#        self.eddy_Uavg_contour_index = eddy_Uavg_contour_index
#        return self.eddy_Uavg_contour_index
#        
#    def append_eddy_amp(self,eddy_amp):
#        self.eddy_amp = eddy_amp
#        return self.eddy_amp


class eddy_list (object):
    '''
    Class that holds list of eddy information:
    '''
    def __init__(self):
        '''
        Initialise the list
        '''
#        self.eddy_list={}#[]
        self.PAD = 2
     

#    def append_list(self, eddy_core,eddy_Uavg_contour,eddy_Uavg_contour_index_i,eddy_Uavg_contour_index_j,
#                     eddy_Uavg,eddy_Uavg_max,eddy_radius,eddy_amp,eddy_flag,eddy_inout):
#        '''
#        Append a new 'eddy' object to the list
#        '''
#        
#        self.eddy_list.append(eddy(eddy_core,eddy_Uavg_contour,eddy_Uavg_contour_index_i,eddy_Uavg_contour_index_j,
#                     eddy_Uavg,eddy_Uavg_max,eddy_radius,eddy_amp,eddy_flag,eddy_inout))
                                    
                                    
                                    
                                    
#    def reset_holding_variables(self):
#        '''
#        Reset temporary holding variables to empty arrays
#        '''
#        #print ('reset_holding_variables')
#        self.eddy_Uavg_contour =np.array([])
#        self.eddy_Uavg = []
#        self.eddy_Uavg_contour_index_i=0 
#        self.eddy_Uavg_contour_index_j=0 
#        self.eddy_Uavg_max=0.0
#        self.eddy_radius =0.0
#        self.eddy_amp    =0.0
#        self.eddy_flag  =False
#        
#        return self

        
    
    def set_bounds(self, contlon, contlat, grd):
        """
        Get indices to a bounding box around the eddy
        WARNING won't work for a rotated grid
        """
        #print ('set_bounds')用到了
        lonmin, lonmax = contlon.min(), contlon.max()
        latmin, latmax = contlat.min(), contlat.max()
        bl_i, bl_j = nearest(lonmin, latmin, grd.lon(), grd.lat())
        tl_i, tl_j = nearest(lonmin, latmax, grd.lon(), grd.lat())
        br_i, br_j = nearest(lonmax, latmin, grd.lon(), grd.lat())
        tr_i, tr_j = nearest(lonmax, latmax, grd.lon(), grd.lat())
											        
        iarr = np.array([bl_i, tl_i, br_i, tr_i])
        jarr = np.array([bl_j, tl_j, br_j, tr_j])
        self.imin, self.imax = iarr.min(), iarr.max()
        self.jmin, self.jmax = jarr.min(), jarr.max()
        # For indexing the mins must not be less than zero
        self.imin = np.maximum(self.imin - self.PAD, 0)
        self.jmin = np.maximum(self.jmin - self.PAD, 0)
        self.imax += self.PAD + 1
        self.jmax += self.PAD + 1
        return self
    





