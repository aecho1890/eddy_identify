# -*- coding: utf-8 -*-
# %run make_eddy_track_AVISO.py

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

make_eddy_track_AVISO.py

Version 1.4.1


Scroll down to line ~640 to get started
===========================================================================
"""

from multiprocessing import Pool,Process
import os
import glob as glob
from py_eddy_tracker_classes import *
from make_eddy_tracker_list_obj import *
from dateutil import parser
from mpl_toolkits.basemap import Basemap
import numpy as np 
from NeighborsSearch import rangesearch
from matplotlib.path import Path
import gdal  
from gdalconst import * 
import json
from collections import OrderedDict
import pdb


class PyEddyTracker (object):
    '''
    Base object
    
    Methods defined here are grouped into categories based on input data source,
    i.e., AVISO, ROMS, etc.  To introduce a new data source new methods can be
    introduced here.
    
    METHODS:
      Common: set_initial_indices
              set_index_padding
              haversine_dist
              half_interp
      AVISO:  get_AVISO_f_pm_pn
      ROMS:   get_ROMS_f_pm_pn
    
    '''
    #print ('PyEddyTracker')用到
    def __init__(self):
        '''
        Set some constants
        '''
        self.gravity = 9.81
        self.earth_radius = 6371315.0
        self.zero_crossing = False
        self.pad = 2
    def read_nc_att(self, varfile, varname, att):
        '''
        Read data attribute from nectdf file
          varname : variable ('temp', 'mask_rho', etc) to read
          att : string of attribute, eg. 'valid_range'
        '''
        with netcdf.Dataset(varfile) as nc:
            return eval(''.join(("nc.variables[varname].", att)))
            
    def set_initial_indices(self, lonmin, lonmax, latmin, latmax):
        '''
        Get indices for desired domain
        '''
        #print ('Setting initial indices')用到
#        pdb.set_trace()
        self.i0, junk = self.nearest_point(lonmin, latmin + 0.5 * (latmax - latmin))
        self.i1, junk = self.nearest_point(lonmax, latmin + 0.5 * (latmax - latmin))
        junk, self.j0 = self.nearest_point(lonmin + 0.5 * (lonmax - lonmin), latmin)
        junk, self.j1 = self.nearest_point(lonmin + 0.5 * (lonmax - lonmin), latmax)

        def kdt(lon, lat, limits, k=4):
            ppoints = np.array([lon.ravel(), lat.ravel()]).T
            ptree = spatial.cKDTree(ppoints)
            pindices = ptree.query(limits, k=k)[1]
            iind, jind = np.array([], dtype=int), np.array([], dtype=int)
            for pind in pindices.ravel():
                j, i = np.unravel_index(pind, lon.shape)
                iind = np.r_[iind, i]
                jind = np.r_[jind, j]
            return iind, jind

        if 'AvisoGrid' in self.__class__.__name__:
            if self.zero_crossing is True:
                '''
                Used for a zero crossing, e.g., across Agulhas region
                '''
                def half_limits(lon, lat):
                    return np.array([np.array([lon.min(), lon.max(),
                                               lon.max(), lon.min()]),
                                     np.array([lat.min(), lat.min(),
                                               lat.max(), lat.max()])]).T
                # Get bounds for right part of grid
                lat = self._lat[self._lon >= 360 + lonmin - 0.5]
                lon = self._lon[self._lon >= 360 + lonmin - 0.5]
                limits = half_limits(lon, lat)
                iind, jind = kdt(self._lon, self._lat, limits)
                self.i1 = iind.min()
                # Get bounds for left part of grid
                lat = self._lat[self._lon <= lonmax + 0.5]
                lon = self._lon[self._lon <= lonmax + 0.5]
                limits = half_limits(lon, lat)
                iind, jind = kdt(self._lon, self._lat, limits)
                self.i0 = iind.max()
        return self


    def set_index_padding(self, pad=2):
        '''
        Set start and end indices for temporary padding and later unpadding
        around 2d variables.
        Padded matrices are needed only for geostrophic velocity computation.
        '''
        #print ('set_index_padding=%s' %pad)用到
        
        def get_str(thestr, pad):
            '''
            Get start indices for pad
            Returns:
              pad_str   - index to add pad
              unpad_str - index for later unpadding
            '''
            pad_str = np.max([0, thestr - pad])
            if pad > 0:
                unpad_str = np.max([0, np.diff([pad_str, thestr])])
                return pad_str, unpad_str
            else:
                unpad_str = np.min([0, np.diff([pad_str, thestr])])
                return pad_str, -1 * unpad_str
    
        def get_end(theend, shape, pad):
            '''lat_block_num,lon_block_num,lat_inner,lon_inner,outer_range=3,6,52,50,12
            Get end indices for pad
            Returns:
              pad_end   - index to add pad
              unpad_end - index for later unpadding
            '''
            if theend is None:
                pad_end = None
                unpad_end = None
            else:
                pad_end = np.minimum(shape, theend + pad)
                if shape == theend + pad:
                    unpad_end = -pad
                elif shape == theend + pad - 1:
                    unpad_end = -1
                elif shape == pad_end:
                    unpad_end = None
                else:
                    unpad_end = -pad
            if pad > 0:
                return pad_end, unpad_end
            else:
                return pad_end, -1 * unpad_end
        
        #pdb.set_trace()
        self.jp0, self.jup0 = get_str(self.j0, pad)
        self.jp1, self.jup1 = get_end(self.j1, self._lon.shape[0], pad)
        if self.zero_crossing:
            pad = -pad
        self.ip0, self.iup0 = get_str(self.i0, pad)
        self.ip1, self.iup1 = get_end(self.i1, self._lon.shape[1], pad)
        return self



    def haversine_dist(self, lon1, lat1, lon2, lat2):
        #pdb.set_trace()
        '''
        TO DO: change to use f2py version
        Haversine formula to calculate distance between two lon/lat points
        Uses mean earth radius in metres (from ROMS scalars.h) = 6371315.0
        Input:
          lon1, lat1, lon2, lat2
        Return:
          distance (m)
        '''
        #print ('haversine_dist')用到
        lon1, lat1, lon2, lat2 = lon1.copy(), lat1.copy(), lon2.copy(), lat2.copy()
        dlat = np.deg2rad(lat2 - lat1)
        dlon = np.deg2rad(lon2 - lon1)
        np.deg2rad(lat1, out=lat1)
        np.deg2rad(lat2, out=lat2)
        a = ne.evaluate('sin(0.5 * dlon) * sin(0.5 * dlon)')
        a = ne.evaluate('a * cos(lat1) * cos(lat2)')
        a = ne.evaluate('a + (sin(0.5 * dlat) * sin(0.5 * dlat))')
        c = ne.evaluate('2 * arctan2(sqrt(a), sqrt(1 - a))')
        return ne.evaluate('6371315.0 * c') # Return the distance



    def nearest_point(self, lon, lat):
        '''
        Get indices to a point (lon, lat) in the grid
        '''
        #print ('nearest_point')用到
#        pdb.set_trace()
        i, j = nearest(lon, lat, self._lon, self._lat)
        return i, j
    
    
    
    def half_interp(self, h_one, h_two):
        '''
        Speed up frequent operations of type 0.5 * (arr[:-1] + arr[1:])
        '''
        #print ('half_interp')用到
        h_one += h_two
        h_one *= 0.5
        return h_one
        #return ne.evaluate('0.5 * (h_one + h_two)')


    def get_AVISO_f_pm_pn(self):      
        '''
        Padded matrices are used here because Coriolis (f), pm and pn
        are needed for the geostrophic velocity computation in 
        method getSurfGeostrVel()
        NOTE: this should serve for ROMS too
        '''
        #print ('get_AVISO_f_pm_pn')用到
        # Get gravity / Coriolis
        self._gof = np.sin(np.deg2rad(self.latpad()))
        self._gof *= 4.
        self._gof *= np.pi
        self._gof /= 86400.
        self._gof = self.gravity / self._gof
        
        lonu = self.half_interp(self.lonpad()[:,:-1], self.lonpad()[:,1:])
        latu = self.half_interp(self.latpad()[:,:-1], self.latpad()[:,1:])
        lonv = self.half_interp(self.lonpad()[:-1], self.lonpad()[1:])
        latv = self.half_interp(self.latpad()[:-1], self.latpad()[1:])

        # Get pm and pn
        pm = np.zeros_like(self.lonpad())
        pm[:,1:-1] = self.haversine_dist(lonu[:,:-1], latu[:,:-1],
                                         lonu[:,1:],  latu[:,1:])
        pm[:,0] = pm[:,1]
        pm[:,-1] = pm[:,-2]
        self._dx = pm
        self._pm = np.reciprocal(pm)
                
        pn = np.zeros_like(self.lonpad())
        pn[1:-1] = self.haversine_dist(lonv[:-1], latv[:-1],
                                       lonv[1:],  latv[1:])
        pn[0] = pn[1]
        pn[-1] = pn[-2]
        self._dy = pn
        self._pn = np.reciprocal(pn)
        return self


    def u2rho_2d(self, uu_in):
        '''
        Convert a 2D field at u points to a field at rho points
        '''
       # print ('u2rho_2d')用到
        def uu2ur(uu_in, Mp, Lp):
            L = Lp - 1
            Lm = L  - 1
            u_out = np.zeros((Mp, Lp))
            u_out[:, 1:L] = self.half_interp(uu_in[:, 0:Lm], uu_in[:, 1:L])
            u_out[:, 0] = u_out[:, 1]
            u_out[:, L] = u_out[:, Lm]
            return (u_out.squeeze())
        Mshp, Lshp = uu_in.shape
        return uu2ur(uu_in, Mshp, Lshp )



    def v2rho_2d(self, vv_in):
        # Convert a 2D field at v points to a field at rho points
        #print ('v2rho_2d')用到
        def vv2vr(vv_in, Mp, Lp):
            M = Mp - 1
            Mm = M  - 1
            v_out = np.zeros((Mp, Lp))
            v_out[1:M] = self.half_interp(vv_in[:Mm], vv_in[1:M])
            v_out[0] = v_out[1]
            v_out[M] = v_out[Mm]
            return (v_out.squeeze())
        Mshp, Lshp = vv_in.shape
        return vv2vr(vv_in, Mshp , Lshp)


    def uvmask(self):
        '''
        Get mask at U and V points
        '''
        #print ('uvmask')用到
        Mp, Lp = self.mask.shape
        M = Mp - 1
        L = Lp - 1
        self._umask = self.mask[:,:L] * self.mask[:,1:Lp]
        self._vmask = self.mask[:M] * self.mask[1:Mp]
        return self


    def make_gridmask(self, with_pad=True, use_maskoceans=False):   #False
        '''
        Use Basemap to make a landmask        
        '''
       
        self.M = Basemap(projection='gall', llcrnrlon = self.lonmin, \
                                            urcrnrlon = self.lonmax, \
                                            llcrnrlat = self.latmin, \
                                            urcrnrlat = self.latmax, \
                                            lat_ts = 0.5 * (self.latmin + self.latmax), \
                                            resolution = 'h') # 'h'-high, 'l'-low  
                                            
        
        self.M.proj4string                                  
        if with_pad:
            x, y = self.M(self.lonpad(), self.latpad())
            #x, y = (self.lonpad(), self.latpad())
        else:
            x, y = self.M(self.lon(), self.lat())
            #x, y = (self.lon(), self.lat())
        print ('--- Computing Basemap mask')
        self.mask = np.ones_like(x, dtype=bool) 
#        use_maskoceans=True 
#        if use_maskoceans:
#            print ("------ using Basemap *maskoceans*: this is fast but may be")
#            print ("------ marginally less accurate than Basemap's *is_land* method...")
#            from mpl_toolkits.basemap import maskoceans
#            if with_pad:
#                self.mask = maskoceans(self.lonpad(), self.latpad(), self.mask,
#                                       inlands=False, resolution='f', grid=1.25)
#            else:
#                self.mask = maskoceans(self.lon(), self.lat())
#            self.mask = self.mask.mask.astype(int)
#        else:
#            print ("------ using Basemap *is_land*: this is slow for larger domains")
#            print ("------ but can be speeded up once Basemap's *maskoceans* method is introduced")
#            print ("------ (currently longitude wrapping behaviour is unclear...)")
#            it = np.nditer([x, y], flags=['multi_index'])
#            
#            int_num=0
#            while not it.finished:
#                int_num=int_num+1
#                self.mask[it.multi_index] = self.M.is_land(x[it.multi_index],
#                                                           y[it.multi_index])
#                it.iternext()
#            self.mask = np.atleast_2d(-self.mask).astype(int)
        self.Mx, self.My = x, y 
        return self

    def get_geostrophic_velocity(self, zeta):    #科氏力计算uv值
        '''
        Returns u and v geostrophic velocity at
        surface from variables f, zeta, pm, pn...
        Note: output at rho points
        '''
        #print ('get_geostrophic_velocity')用到
#        
        self.upad[:] = -self.gof() * self.v2rho_2d(self.vmask() * (zeta.data[1:] - zeta.data[:-1]) \
                                        * 0.5 * (self.pn()[1:] + self.pn()[:-1]))
        
        self.vpad[:] =  self.gof() * self.u2rho_2d(self.umask() * (zeta.data[:, 1:] - zeta.data[:, :-1]) \
                                        * 0.5 * (self.pm()[:, 1:] + self.pm()[:, :-1]))
        return self

    def get_AVISO_uvdata(self, udata,vdata):    #直接读取AVISO的uv值
        '''
        Returns u and v geostrophic velocity at
        surface from variables f, zeta, pm, pn...
        Note: output at rho points
        '''
        #print ('get_geostrophic_velocity')用到
#        
        print('upad',len(self.upad[:]),len(self.upad[:][0]))
        print('udata',len(udata),len(udata[0]))
        self.upad[:] = udata
        print('vpad',len(self.vpad[:]),len(self.vpad[:][0]))
        print('vdata',len(vdata),len(udata[0]))
        self.vpad[:] = vdata
        return self
    
    def set_u_v_eke(self, pad=2):
        '''
        '''
        #double_pad = pad * 2
        #print ('set_u_v_eke')用到
        if self.zero_crossing:
            u1 = np.empty((self.jp1 - self.jp0, self.ip0))
            u0 = np.empty((self.jp1 - self.jp0, self._lon.shape[1] - self.ip1))
            self.upad = np.ma.concatenate((u0, u1), axis=1)
        else:
            self.upad = np.empty((self.jp1 - self.jp0, self.ip1 - self.ip0))
        self.vpad = np.empty_like(self.upad)
        self.eke = np.empty_like(self.upad[self.jup0:self.jup1, self.iup0:self.iup1])
        self.u = np.empty_like(self.eke)
        self.v = np.empty_like(self.eke)
        return self
        
    def getEKE(self):
        '''
        '''
        self.u[:] = self.upad[self.jup0:self.jup1, self.iup0:self.iup1]
        self.v[:] = self.vpad[self.jup0:self.jup1, self.iup0:self.iup1]
        np.add(self.u**2, self.v**2, out=self.eke)
        self.eke *= 0.5
        return self    

class AvisoGrid (PyEddyTracker):
    '''
    Class to satisfy the need of the ROMS eddy tracker
    to have a grid class
    '''
    #print ('AvisoGrid')用到
    def __init__(self, sladata, lonmin, lonmax, latmin, latmax, Origin_GetGeoTransform , with_pad=True, use_maskoceans=False):
        '''
        Initialise the grid object
        '''
        super(AvisoGrid, self).__init__()
        #print ('\nInitialising the AVISO_grid')用到
        self.i0, self.j0 = 0, 0
        self.i1, self.j1 = None, None
        self.lonmin = lonmin
        self.lonmax = lonmax
        self.latmin = latmin
        self.latmax = latmax
        
        #Origin_GetGeoTransform=[originX,end_X,pixelwidth,originY,end_Y,pixelheigh]
        originX    = Origin_GetGeoTransform[0]
        #print('AA_originx',originX)
        end_X      = Origin_GetGeoTransform[1]
        pixelwidth = Origin_GetGeoTransform[2]
        originY    = Origin_GetGeoTransform[3]
        end_Y      = Origin_GetGeoTransform[4]
        pixelheigh=Origin_GetGeoTransform[5]
        out_range=Origin_GetGeoTransform[6]
#        self._lon = np.arange(originX,end_X+out_range+0.5,pixelwidth)
#        self._lat = np.arange(originY,end_Y+0.5,-pixelheigh)
        self._lon = np.arange(0.125,out_range+360,0.25)
        self._lat = np.arange(-89.875,90,0.25)
#        print('originY,end_Y,pixelheigh',originY,end_Y,pixelheigh)
        self.fillval = -2147483647
        base_date =  'days since 1950-01-01 00:00:00 UTC'
        self.base_date = dt.date2num(parser.parse(base_date.split(' ')[2:4][0]))
 
        if np.logical_and(lonmin < 0, lonmax <=0):
            self._lon -= 360.
        self._lon, self._lat = np.meshgrid(self._lon, self._lat)
#        print('self._lon, self._lat ',self._lon, self._lat )
        self._angle = np.zeros_like(self._lon)
        # To be used for handling a longitude range that crosses 0 degree meridian
        if np.logical_and(lonmin < 0, lonmax >= 0):
            self.zero_crossing = True
        #不用管
        self.set_initial_indices(lonmin, lonmax, latmin, latmax)
        self.set_index_padding()
        self.make_gridmask(with_pad, use_maskoceans).uvmask()
        self.get_AVISO_f_pm_pn()
        self.set_u_v_eke()
        #print('set_u_v_eke()',self.set_u_v_eke())



    def get_AVISO_data(self, sladata):
        '''
        Read tif data from AVISO file
        '''
        #print ('get_AVISO_data')用到
#        gdal.AllRegister()        
#        ds = gdal.Open(AVISO_file)
#        band = ds.GetRasterBand(1)
#        data = band.ReadAsArray()[::-1]#sla值
        data=sladata
        #pdb.set_trace()
        if self.zero_crossing:
         # new AVISO (2014) 
            ssh1 = data[self.jp0:self.jp1, :self.ip0]
            ssh0 = data[self.jp0:self.jp1, self.ip1:]
            #print('ssh0',ssh0)
            ssh0, ssh1 = ssh0.squeeze(), ssh1.squeeze()
            ssh0 *= 100. # m to cm
            ssh1 *= 100. # m to cm 
            zeta = np.ma.concatenate((ssh0, ssh1), axis=1)
        else:# new AVISO (2014)
            zeta = data[self.jp0:self.jp1, self.ip0:self.ip1]
            zeta = zeta.squeeze()
            #print('zeta',zeta)
            zeta *= 100. # m to cm
        try: # Extrapolate over land points with fillmask
            #print ('Extrapolate over land points with fillmask')
            zeta = fillmask(zeta, self.mask == 1)
            #zeta = fillmask(zeta, 1 + (-1 * zeta.mask))
        except Exception: # In case no landpoints
            zeta = np.ma.masked_array(zeta)
            
        return zeta.astype(np.float64)
    


    def lon(self):
        #print ('lon')
        if self.zero_crossing:
            # TO DO: These concatenations are possibly expensive, they shouldn't need
            # to happen with every call to self.lon()
            lon0 = self._lon[self.j0:self.j1,  self.i1:]
            lon1 = self._lon[self.j0:self.j1, :self.i0]
            return np.concatenate((lon0 - 360., lon1), axis=1)
        else:
            lon =self._lon[self.j0:self.j1, self.i0:self.i1]-0.125
            #print('LON',lon)
            return lon
    
    def lat(self):
        #print ('lat')
        if self.zero_crossing:
            lat0 = self._lat[self.j0:self.j1,  self.i1:]
            lat1 = self._lat[self.j0:self.j1, :self.i0]
            return np.concatenate((lat0, lat1), axis=1)
        else:
            lat=self._lat[self.j0:self.j1, self.i0:self.i1]-0.125       
            return lat

    def lonpad(self):
        #print ('lonpad')
        if self.zero_crossing:
            lon0 = self._lon[self.jp0:self.jp1,  self.ip1:]
            lon1 = self._lon[self.jp0:self.jp1, :self.ip0]
            return np.concatenate((lon0 - 360., lon1), axis=1)
        else:
            return self._lon[self.jp0:self.jp1, self.ip0:self.ip1]
    
    def latpad(self):
        #print ('latpad')
        if self.zero_crossing:
            lat0 = self._lat[self.jp0:self.jp1,  self.ip1:]
            lat1 = self._lat[self.jp0:self.jp1, :self.ip0]
            return np.concatenate((lat0, lat1), axis=1)
        else:            
            return self._lat[self.jp0:self.jp1, self.ip0:self.ip1]

    def angle(self):
        #print ('angle')
        return self._angle[self.j0:self.j1, self.i0:self.i1]
 
    def umask(self): # Mask at U points
        #print ('umask')
        return self._umask
    
    def vmask(self): # Mask at V points
        #print ('vmask')
        return self._vmask
    
    def gof(self): # Gravity / Coriolis
        #print ('gof')
        return self._gof

    def dx(self): # Grid spacing along X direction
        #print ('dx')
        return self._dx
    
    def dy(self): # Grid spacing along Y direction
        return self._dy
        
    def pm(self): # Reciprocal of dx
        #print ('pm')
        return self._pm
    
    def pn(self): # Reciprocal of dy
        return self._pn


    def get_resolution(self):
        #print ('get_resolution')用到
        return np.mean(np.sqrt(np.diff(self.lon()[1:], axis=1) *
                               np.diff(self.lat()[:,1:], axis=0)))
 
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#计算涡度
def vorticity(u, v, pm, pn,grd):
        """
        Returns vorticity calculated using np.gradient
        """
        def vort(u, v, dx, dy,grd):
            dx = ne.evaluate('1 / dx')
            dy = ne.evaluate('1 / dy')
#            print('grd.v2rho_2d(v)',len(grd.v2rho_2d(v)),len(grd.v2rho_2d(v)[0]))
#            print('dx',len(dx),len(dx[0]))
#            print('dy',len(dy),len(dy[0]))
            uy, ux = np.gradient(grd.u2rho_2d(u), dx, dy)
            vy, vx = np.gradient(grd.v2rho_2d(v), dx, dy)
            xi = ne.evaluate('vx - uy')
            return xi
        return vort(u, v, pm, pn,grd)
#计算散度        
def Divergence(u, v, dx, dy,grd):

    dx = ne.evaluate('1 / dx')
    dy = ne.evaluate('1 / dy')
#            print('grd.v2rho_2d(v)',len(grd.v2rho_2d(v)),len(grd.v2rho_2d(v)[0]))
#            print('dx',len(dx),len(dx[0]))
#            print('dy',len(dy),len(dy[0]))
    uy, ux = np.gradient(grd.u2rho_2d(u), dx, dy)
    vy, vx = np.gradient(grd.v2rho_2d(v), dx, dy)
    di = ne.evaluate('ux + vy')
    return di
#计算剪切变形率
def shear_deformation_rate (u, v, dx, dy,grd):

    dx = ne.evaluate('1 / dx')
    dy = ne.evaluate('1 / dy')
#            print('grd.v2rho_2d(v)',len(grd.v2rho_2d(v)),len(grd.v2rho_2d(v)[0]))
#            print('dx',len(dx),len(dx[0]))
#            print('dy',len(dy),len(dy[0]))
    uy, ux = np.gradient(grd.u2rho_2d(u), dx, dy)
    vy, vx = np.gradient(grd.v2rho_2d(v), dx, dy)
    shd = ne.evaluate('vx + uy')
    return shd
#计算延伸变形率
def stretching_deformation_rate  (u, v, dx, dy,grd):

    dx = ne.evaluate('1 / dx')
    dy = ne.evaluate('1 / dy')
#            print('grd.v2rho_2d(v)',len(grd.v2rho_2d(v)),len(grd.v2rho_2d(v)[0]))
#            print('dx',len(dx),len(dx[0]))
#            print('dy',len(dy),len(dy[0]))
    uy, ux = np.gradient(grd.u2rho_2d(u), dx, dy)
    vy, vx = np.gradient(grd.v2rho_2d(v), dx, dy)
    std = ne.evaluate('ux - vy')
    return std
    
def eddy_main(sladata,udata,vdata,filedate,Block,outer_range,eddy_pixel_num_range,Origin_Data_info): 
    
#    start_time = time.time()
#
    plt.close('all')
    #----------------------------------------------------------------------------         
    #
    lonmin, lonmax, latmin, latmax=Block['location'][0],Block['location'][1],Block['location'][2],Block['location'][3]
 # apply Gaussian filter
#    zwl = 20. # degrees, zonal wavelength (see Chelton etal 2011)
#    mwl = 10. # degrees, meridional wavelength

    # - profiles of swirl velocity from effective contour inwards
    verbose =False #  True 
    
    # Loop through the AVISO files...
    print ('\nStart detecting')   
    
    #获取文件日期
    thedate = dt.date2num(datestr2datetime(str(filedate)))
    rtime = thedate
    try:
        thedate = dt.num2date(rtime)[0]
    except:
        thedate = dt.num2date(rtime)
            
    #初始化保存涡旋属性信息
    A_eddy = eddy_list()
    
    A_eddy.year = thedate.year
    A_eddy.month = thedate.month
    A_eddy.day = thedate.day   
    #
    # Set up a grid object using first AVISO file in the list
    pixelwidth=Origin_Data_info['pixelwidth']
    pixelheigh=Origin_Data_info['pixelheigh']
    originX=Origin_Data_info['originX']
    originY=Origin_Data_info['originY']
    end_X=Origin_Data_info['end_X']
    end_Y=Origin_Data_info['end_Y']
    #print('pixelwidth',pixelwidth)
    Origin_GetGeoTransform=[originX,end_X,pixelwidth,originY,end_Y,pixelheigh,outer_range]
    #print('Origin_GetGeoTransform',Origin_GetGeoTransform)
    sla_grd = AvisoGrid(sladata, lonmin, lonmax, latmin, latmax,Origin_GetGeoTransform)
    #pdb.set_trace()
    #print('sladata',sladata)
    # Get parameters for ndimage.gaussian_filter
    #zres, mres = gaussian_resolution(sla_grd.get_resolution(), zwl, mwl)
      
    sla = sla_grd.get_AVISO_data(sladata)  #获取该区域的sla数据
    
    u=sla_grd.get_AVISO_data(udata)  #获取该区域的u数据
    v=sla_grd.get_AVISO_data(vdata)  #获取该区域的v数据
    pm_value=sla_grd.pm()
    pn_value=sla_grd.pn()
    
    # Set landpoints to zero
#    mask=sla<-100
#    sla_grd.mask=np.ma.array(sla,mask=mask)
#    np.place(sla, sla_grd.mask == False, 0.)
#    print ('start smoothing')
#    sla -= ndimage.gaussian_filter(sla, [mres, zres])   
#         # Expand the landmask
#    sla = np.ma.masked_where(sla_grd.mask == False, sla)
    # Multiply by 0.01 for m
#    sla_grd.get_geostrophic_velocity(sla * 0.01)  
    sla_grd.get_AVISO_uvdata(u,v)      #直接用AVISO的uv产品  
    #pdb.set_trace()        
    # Remove padded boundary
    sla = sla[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1]  
    sla_grd.getEKE()
    pmvalue=pm_value[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1]
    pnvalue=pn_value[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1] 
    uvalue=u[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1] 
    vvalue=v[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1]
   # pdb.set_trace()
#    print('uvalue',len(uvalue),len(uvalue[0]))
#    print('uvalue',len(vvalue),len(vvalue[0]))
#    print('pmvalue',len(pmvalue),len(pmvalue[0]))
#    print('pnvalue',len(pnvalue),len(pnvalue[0]))
    eddy_relative_vorticity=vorticity(uvalue/100, vvalue/100, pmvalue, pnvalue,sla_grd)
    eddy_divergence = Divergence(uvalue/100, vvalue/100, pmvalue, pnvalue,sla_grd)
    eddy_shd = shear_deformation_rate(uvalue/100, vvalue/100, pmvalue, pnvalue,sla_grd)
    eddy_std = stretching_deformation_rate(uvalue/100, vvalue/100, pmvalue, pnvalue,sla_grd)
   
     # Get scalar speed
    Uspd = np.hypot(sla_grd.u, sla_grd.v)
    Uspd = np.ma.masked_where(sla_grd.mask[sla_grd.jup0:sla_grd.jup1,
                                                   sla_grd.iup0:sla_grd.iup1] == False, Uspd)
     
    #初始化每个涡旋的信息    
    
    eddy_Uavg_max=0    #最大地转流速度
    eddy_radius =0 #涡旋半径
    eddy_amp    =0 #涡旋振幅
    eddy_Uavg_amp=0#最大地转流振幅
    eddy_flag  =False    #涡旋是否已被识别标志
    A_eddy.M = sla_grd.M     
    
    contfig = plt.figure(99)
    ax = contfig.add_subplot(111)
#    
#        print ('before seed %s seconds'% str(time.time() - start_time), 'seconds!')    
#--------------------------------------------------------------------------------------#      
#        seedtime=time.time()
    
    #识别反气旋涡种子点
    local_extrema = np.ma.copy(sla)
    local_extrema = np.reshape(local_extrema, (sla.shape))
    local_extrema_ac= detect_local_minima(-local_extrema)
    inner_ac_seed_j, inner_ac_seed_i = np.where(local_extrema_ac)  #涡旋种子点的索引值
    
#    print('sla',local_extrema)
  
    
    outer_range=outer_range/pixelwidth    #outer的像素个数 1度4个像素
#    =outer_range2/pixelheigh   #pay attention
#    lon=np.arange(originX,end_X,pixelwidth)
#    lat=np.arange(originY,end_Y,pixelheigh)
    
    #创建反气旋（暖涡）种子点数组
    A_eddy_dic=OrderedDict()
    seed_sla_max=-100  #初始化反气旋涡旋种子点极大值
     #将种子点索引值转换为经纬度值
    for n in range(len(inner_ac_seed_j)):
        lmi = inner_ac_seed_i[n] 
        lmj = inner_ac_seed_j[n]
        seed_lon, seed_lat = sla_grd.lon()[lmj, lmi], sla_grd.lat()[lmj, lmi]
        seed_sla=sla[lmj][lmi]
         #种子点的sla值不能为无效值  
        if abs(seed_sla)<100:
            #检索种子点极大值
            if seed_sla>seed_sla_max: 
                seed_sla_max=seed_sla  
            #区分inner和outer
            if (outer_range+20)<=lmj<= (len(sla)-outer_range-20) and (outer_range+20)<=lmi<= (len(sla[0])-outer_range-20): 
                eddy_inout='inner'
            else:
                 eddy_inout='outer'
            #初始化涡旋结构
            eddyk = OrderedDict([('sign_type','Anticyclonic'),
                                 ('eddy_inout',eddy_inout),
                                 ('eddy_flag',eddy_flag), 
                                 ('eddy_core',[seed_lon,seed_lat,seed_sla]), 
                                  #最大地转流边界相关的参数
                                 ('eddy_Uavg_contour',0),
                                 ('eddy_Uavg_contour_index_i',0),
                                 ('eddy_Uavg_contour_index_j',0),
                                 ('eddy_Uavg_max',eddy_Uavg_max), 
                                 ('eddy_Uavg_radius',eddy_Uavg_max), 
                                 ('eddy_Uavg_amp',eddy_Uavg_amp), 
                                 ('eddy_Uavg_eke',0),
                                 ('eddy_Uavg_uv_speed',0),
                                 ('eddy_Uavg_relative_vorticity',0),
                                 ('eddy_Uavg_divergence',0),
                                 ('eddy_Uavg_SHD',0),
                                 ('eddy_Uavg_STD',0),
                                 ('Uavg_contain_pixel_num',0),
                                 #有效边界相关的参数
                                 ('eddy_effect_contour',0),
                                 ('eddy_effect_contour_i',0),
                                 ('eddy_effect_contour_j',0),
                                 ('eddy_effect_radius',eddy_radius),
                                 ('eddy_effect_amp',eddy_amp),
                                 ('eddy_effect_eke',0),
                                 ('eddy_effect_uv_speed',0),
                                 ('eddy_effect_relative_vorticity',0),
                                 ('eddy_effect_divergence',0),
                                 ('eddy_effect_SHD',0),
                                 ('eddy_effect_STD',0),
                                 ('effect_contain_pixel_num',0),
                                 
                                 
                                 ('eddy_shape_contour',0),
                                 ('eddy_shape_contour_i',0),
                                 ('eddy_shape_contour_j',0),
                                 ('eddy_shape_radius',0),
                                 ('eddy_shape_amp',0),
                                 ('eddy_shape_eke',0),
                                 ('eddy_shape_uv_speed',0),
                                 ('eddy_shape_relative_vorticity',0),
                                 ('eddy_shape_divergence',0),
                                 ('eddy_shape_SHD',0),
                                 ('eddy_shape_STD',0),
                                 ('shape_contain_pixel_num',0),
                                 
                                 
                                 
                                 
                                 
                                 
                                 
                                 
                                 
                                 #最里层的等高线相关的参数
                                 ('eddy_inner_contour',0),
                                 ('eddy_inner_contour_index_i',0),
                                 ('eddy_inner_contour_index_j',0),
                                 ('eddy_inner_contour_sla',-500),
                                 ('eddy_centroid_core',[]),
                                 ('eddy_circle_core',[])#最近等高线拟合圆的圆心
                                ])
                                

            #根据涡旋种子点的经纬度位置命名涡旋
            eddy_name='eddy'+'_'+ str(seed_lon)+'_'+str(seed_lat) 
            A_eddy_dic.setdefault(eddy_name,eddyk) 
#                A_eddy.append_list([seed_lon, seed_lat,seed_sla],eddy_Uavg_contour,
#                               eddy_Uavg_contour_index_i,eddy_Uavg_contour_index_j,
#                               eddy_Uavg,eddy_Uavg_max,eddy_radius,eddy_amp,eddy_flag,eddy_inout)
            
    #识别气旋涡种子点
    local_extrema_cc= detect_local_minima(local_extrema)
    inner_cc_seed_j, inner_cc_seed_i= np.where(local_extrema_cc)  
    seed_sla_min=100 #初始化气旋涡旋种子点极小值
    #将种子点索引值转换为经纬度值
    for n in range(len(inner_cc_seed_j)):
        lmi = inner_cc_seed_i[n] 
        lmj = inner_cc_seed_j[n]
        seed_lon, seed_lat = sla_grd.lon()[lmj, lmi], sla_grd.lat()[lmj, lmi]
        seed_sla=sla[lmj][lmi] 
        if abs(seed_sla)<100:  #种子点的sla值不能为无效值 
             #检索种子点极小值
            if seed_sla<seed_sla_min:
                seed_sla_min=seed_sla 
            #区分inner和outer
            if outer_range+20<=lmj<= len(sla)-outer_range-20 and outer_range+20<=lmi<= len(sla[0])-outer_range-20: 
                eddy_inout='inner'
            else:
                eddy_inout='outer' 
            
            eddyk = OrderedDict([('sign_type','Cyclonic'),
                                 ('eddy_inout',eddy_inout),
                                 ('eddy_flag',eddy_flag), 
                                 ('eddy_core',[seed_lon,seed_lat,seed_sla]), 
                                  #最大地转流边界相关的参数
                                 ('eddy_Uavg_contour',0),
                                 ('eddy_Uavg_contour_index_i',0),
                                 ('eddy_Uavg_contour_index_j',0),
                                 ('eddy_Uavg_max',eddy_Uavg_max), 
                                 ('eddy_Uavg_radius',eddy_Uavg_max), 
                                 ('eddy_Uavg_amp',eddy_Uavg_amp), 
                                 ('eddy_Uavg_eke',0),
                                 ('eddy_Uavg_uv_speed',0),
                                 ('eddy_Uavg_relative_vorticity',0),
                                 ('eddy_Uavg_divergence',0),
                                 ('eddy_Uavg_SHD',0),
                                 ('eddy_Uavg_STD',0),
                                 ('Uavg_contain_pixel_num',0),
                                 #有效边界相关的参数
                                 ('eddy_effect_contour',0),
                                 ('eddy_effect_contour_i',0),
                                 ('eddy_effect_contour_j',0),
                                 ('eddy_effect_radius',eddy_radius),
                                 ('eddy_effect_amp',eddy_amp),
                                 ('eddy_effect_eke',0),
                                 ('eddy_effect_uv_speed',0),
                                 ('eddy_effect_relative_vorticity',0),
                                 ('eddy_effect_divergence',0),
                                 ('eddy_effect_SHD',0),
                                 ('eddy_effect_STD',0),
                                 ('effect_contain_pixel_num',0),




                                 ('eddy_shape_contour',0),
                                 ('eddy_shape_contour_i',0),
                                 ('eddy_shape_contour_j',0),
                                 ('eddy_shape_radius',0),
                                 ('eddy_shape_amp',0),
                                 ('eddy_shape_eke',0),
                                 ('eddy_shape_uv_speed',0),
                                 ('eddy_shape_relative_vorticity',0),
                                 ('eddy_shape_divergence',0),
                                 ('eddy_shape_SHD',0),
                                 ('eddy_shape_STD',0),
                                 ('shape_contain_pixel_num',0),


                                 #最里层的等高线相关的参数
                                 ('eddy_inner_contour',0),
                                 ('eddy_inner_contour_index_i',0),
                                 ('eddy_inner_contour_index_j',0),
                                 ('eddy_inner_contour_sla',500),
                                 ('eddy_centroid_core',[]),
                                 ('eddy_circle_core',[])#最近等高线拟合圆的圆心
                                ])
            #涡旋名字
            eddy_name='eddy'+'_'+ str(seed_lon)+'_'+str(seed_lat)
            A_eddy_dic.setdefault(eddy_name,eddyk)
 
 
      
    A_eddy.sla = np.ma.copy(sla)
    A_eddy.slacopy = np.ma.copy(sla) 
    A_eddy.Uspd = np.ma.copy(Uspd) 
    A_eddy.M = sla_grd.M
    #
    A_eddy.points = np.array([sla_grd.lon().ravel(),
                              sla_grd.lat().ravel()]).T  
    A_eddy.i0, A_eddy.i1 = sla_grd.i0, sla_grd.i1
    A_eddy.j0, A_eddy.j1 = sla_grd.j0, sla_grd.j1 
    A_eddy.lonmin, A_eddy.lonmax = np.float(lonmin), np.float(lonmax)
    A_eddy.latmin, A_eddy.latmax = np.float(latmin), np.float(latmax) 
    A_eddy.ampmin = np.float(1)
    A_eddy.ampmax = np.float(150) 
    A_eddy.verbose = verbose 
    A_eddy.u_speed=np.ma.copy(uvalue)
    A_eddy.v_speed=np.ma.copy(vvalue)
    A_eddy.eddy_relative_vorticity=np.ma.copy(eddy_relative_vorticity)
    A_eddy.eddy_divergence=np.ma.copy(eddy_divergence)
    A_eddy.eddy_shd=np.ma.copy(eddy_shd)
    A_eddy.eddy_std=np.ma.copy(eddy_std)
    # See Chelton section B2 (0.4 degree radius)
    # These should give 8 and 1000 for 0.25 deg resolution 
    #A_eddy.pixel_threshold = [8, 1000]

       # Get contours of sla parameter   
    print ('------ getting SLA contours')
    #
#    contfig = plt.figure(99)
#    ax = contfig.add_subplot(111)
#    print ('seed_sla_min,seed_sla_max',seed_sla_min,seed_sla_max)
    # Define contours
    #0.25cm
    slaparameter = np.arange(seed_sla_min,seed_sla_max,0.25) # cm Set SLA contour spacing 
    shape_err = 55. * np.ones(slaparameter.size)
    A_eddy.shape_err = shape_err 
#   print ('before loop %s seconds'% str(time.time() - eddytime), 'seconds!')
    
#    try:
#       A_CS = ax.contour(sla_grd.lon(),sla_grd.lat(), A_eddy.sla, slaparameter[::-1])  #slaparameter
#    except:
#        print(A_eddy.sla)
#        print(slaparameter[::-1]) 
    A_CS = ax.contour(sla_grd.lon(),sla_grd.lat(), A_eddy.sla, slaparameter[::-1])    
    oudatajson=OrderedDict()  #初始化涡旋输出结构
    #Now we loop over the CS collection  
#    sign_type= 'Anticyclonic' 
    block_json_name=Block['outfnj'].split('\\')[-1]
    Block_i=block_json_name.split('_')[2]
    Block_j=block_json_name.split('_')[3].split('.')[0]
#    print('Block',Block_i,Block_j)
    Block_name='Block_'+str(Block_i)+'_'+str(Block_j)
#    try:
#        oudatajson=collection_loop(A_CS,sla_grd,A_eddy_dic,eddy_pixel_num_range,Block_name,list_obj=A_eddy)#,sign_type=sign_type, verbose=verbose
#    except:
#        print("此分区无值")
    
    
    oudatajson=collection_loop(A_CS,sla_grd,A_eddy_dic,eddy_pixel_num_range,Block_name,list_obj=A_eddy)#,sign_type=sign_type, verbose=verbose   
#    jsonwrite=time.time()
    #print('Block[outfnj]',Block['outfnj'])
    json.dump(oudatajson,open(Block['outfnj'],'w'))  

    return Block['outfnj']




#剔除合并区域的重复涡旋  （待改进）
def eddyjson_outer(tulp1,tulp2,eddy_dic_outer_union):

     for block1 in tulp1.keys():
         for eddy1 in tulp1[block1].keys():
#            print('eddy1',eddy1)
            for block2 in tulp2.keys(): 
                for eddy2 in tulp2[block2].keys():
                    #
                    lon1=float(eddy1.split('_')[1])
                    lat1=float(eddy1.split('_')[2])
                    lon2=float(eddy2.split('_')[1])
                    lat2=float(eddy2.split('_')[2])
                    if lon1>=360:
                        lon1=lon1-360
                    if lon2>=360:
                        lon2=lon2-360
                    difer=abs(lon1-lon2)+abs(lat1-lat2)
                    if tulp1[block1][eddy1]['eddy_flag'] and tulp2[block2][eddy2]['eddy_flag']:
                            if lon1==lon2 and lat1==lat2:
#                                if eddy1==eddy2:
                                    if tulp1[block1][eddy1]['eddy_effect_amp']>=tulp2[block2][eddy2]['eddy_effect_amp'] :
                                            if  eddy2 in eddy_dic_outer_union[block2]  and eddy1 in eddy_dic_outer_union[block1]: 
                                                del eddy_dic_outer_union[block2][eddy2]
                                    elif tulp1[block1][eddy1]['eddy_effect_amp']<=tulp2[block2][eddy2]['eddy_effect_amp'] and eddy1 in eddy_dic_outer_union[block1] :
                                            if  eddy2 in eddy_dic_outer_union[block2]  and eddy1 in eddy_dic_outer_union[block1]: 
                                                del eddy_dic_outer_union[block1][eddy1]

                            elif 0<difer<=0.5:    #0.75
                               if tulp1[block1][eddy1]['eddy_effect_amp']>tulp2[block2][eddy2]['eddy_effect_amp']:
                                   if  eddy2 in eddy_dic_outer_union[block2]  and eddy1 in eddy_dic_outer_union[block1]: 
#                                       print('del eddy_dic_outer_union[block2][eddy2]_1')
                                       del eddy_dic_outer_union[block2][eddy2]
                               else:
                                   if  eddy2 in eddy_dic_outer_union[block2]  and eddy1 in eddy_dic_outer_union[block1]: 
#                                       print('del eddy_dic_outer_union[block1][eddy1]_1')
                                       del eddy_dic_outer_union[block1][eddy1]


          
     return eddy_dic_outer_union
    
def getdatamin(slalocal):
    datamin=9999
    for n in range(len(slalocal[0])):
           for m in range(len(slalocal)):
               if (slalocal[m][n]>-5):
                   if slalocal[m][n]<datamin:
                       datamin=slalocal[m][n]
    return datamin


def eddy_fig(outdir,lon_block,lat_block,eddy_select_info,filedate,sladata,eddy_dic):
#    lonmin, lonmax, latmin, latmax=0,360,-89,89  #
    lonmin, lonmax, latmin, latmax=lon_block[0][0],lon_block[-1][-1],lat_block[0][0],lat_block[-1][-1] #
    print('lonmin, lonmax, latmin, latmax',lonmin, lonmax, latmin, latmax)
    #初始化全球的画布大小和colorbar位置
    figsize=(17.8, 9)
    cb_ax=[0.94,0.05, 0.015, 0.9]
    ax=[0.05, 0.05,0.9,0.9]
#    ax=[0.1, 0.05,0.8, 0.8]
    if eddy_select_info['eddy_location']=='South China Sea': #105,125,5,25
        figsize=(11.5, 9)
        cb_ax=[0.93,0.05, 0.015, 0.9]
    elif eddy_select_info['eddy_location']=='West Pacific': #100,200，-20,50
        figsize=(17, 9)
        cb_ax=[0.90,0.05, 0.015, 0.9]
    elif eddy_select_info['eddy_location']=='North Indian Ocean': #100,200，-20,50
        figsize=(17.8, 8)
        ax=[0.05, 0.05,0.88,0.9]
        cb_ax=[0.94,0.05, 0.015, 0.89]
    elif eddy_select_info['eddy_location']=='Specific area': #100,200，-20,50
        figsize=(11.5, 9)
        cb_ax=[0.93,0.05, 0.015, 0.9]
    elif eddy_select_info['eddy_location']=='Kuroshio Current': #100,200，-20,50
        figsize=(17.8, 8)
        cb_ax=[0.95,0.05, 0.015, 0.89]
    if lonmax>=360:
        lonmax=360
#    print (ax,cb_ax)
    #画合并后的涡旋识别效果图
    fig=plt.figure(250,figsize=figsize) 
    ax1=fig.add_axes(ax)
    #
    m = Basemap(projection='gall', llcrnrlon = lonmin, urcrnrlon = lonmax, \
                 llcrnrlat = latmin, urcrnrlat =  latmax, \
                 lat_ts = 0.5 * ( latmin + latmax), resolution = 'h',ax=ax1)#merc

    title = str(filedate)+' '+eddy_select_info['eddy_location']+' '+'Eddies'
    plt.title(title)
    #是否加sla背景
    
    if eddy_select_info['if_add_slabg']=='yes':
#        print ('add')
        jmin=int((latmin+89.875)/0.25)
        jmax=int((latmax+89.875)/0.25)
        imin=int((lonmin-0.125)/0.25)
        imax=int((lonmax-0.125)/0.25)
        if eddy_select_info['eddy_location']!='Global Ocean':
            imin-=4
            imax+=4
            jmin-=4
            jmax+=4
        
        lon_grid = np.arange(0.125,360,0.25)[imin:imax]
        lat_grid  = np.arange(-89.875,90,0.25)[jmin:jmax]
        lon_grid, lat_grid= np.meshgrid(lon_grid, lat_grid)  
        xpcol, ypcol = m(lon_grid[:], lat_grid[:])      
#    pcol200 = m.pcolormesh(xpcol, ypcol, slacopy[:],cmap=my_cmap, shading='faceted',alpha=0.7) 
        
        
        slalocal= sladata[jmin:jmax,imin:imax]
        datamax=np.max(slalocal)
        datamin=getdatamin(slalocal)
##        slaparameter = np.arange(round(datamin,2),round(datamax,2),0.01)
#        print (datamin,datamax)
        slaparameter = np.arange(datamin,datamax,0.1)  #固定值
#        m.pcolormesh(lon_grid, lat_grid,slacopy,shading='flat',cmap=plt.cm.jet,latlon=True)        
#        m.contour(xpcol, ypcol,slalocal,slaparameter,cmap=plt.cm.jet)
        
        CS=m.contour(xpcol, ypcol,slalocal,slaparameter,cmap=plt.cm.jet)
        ax2=fig.add_axes(cb_ax)
        cb=fig.colorbar(CS,ax2)
        cb.ax.set_title('m')

    for key1 in eddy_dic.keys():
            eddy_inout=eddy_dic[key1]
#            print('eddy_inout',eddy_inout)
            i=0
            j=0
            for key2 in eddy_inout.keys():
                block_eddy=eddy_inout[key2]
                for seedname2 in block_eddy:
                     point_type=seedname2.split('_')[0]
                     if point_type=='seed':
                        core= block_eddy[seedname2]['eddy_core']
                        core_x_lon,core_y_lat=core[0],core[1]
                        i=i+1
                        if core_x_lon>360:
                            core_x_lon=core_x_lon-360
                        core_x_lon,core_y_lat=m(core_x_lon,core_y_lat)    
                        m.scatter(core_x_lon,core_y_lat,s=eddy_select_info['seed_size'],c='#8B008B',linewidths=0.0001)
                     if point_type=='eddy':
                        j=j+1
                        if block_eddy[seedname2]['sign_type']=='Cyclonic':
                            ecolor=eddy_select_info['cc_effect_edge_color']
                            seed_color=eddy_select_info['cc_seed_color']
                            ucolor=eddy_select_info['cc_eddy_edge_color']
                        else:
                            ecolor=eddy_select_info['ac_effect_edge_color']
                            seed_color=eddy_select_info['ac_seed_color']
                            ucolor=eddy_select_info['ac_eddy_edge_color']
                        eddy_cont_e=block_eddy[seedname2]['eddy_effect_contour']
                        eddy_contlon_e, eddy_contlat_e =np.array(eddy_cont_e[0]),np.array(eddy_cont_e[1])
                        
                        eddy_cont_Uavg=block_eddy[seedname2]['eddy_Uavg_contour']
                        eddy_contlon_Uavg, eddy_contlat_Uavg =np.array(eddy_cont_Uavg[0]),np.array(eddy_cont_Uavg[1])

                        
                        eddy_core=block_eddy[seedname2]['eddy_core']
                        
                        eddy_core_lon,eddy_core_lat = eddy_core[0],eddy_core[1]
                          
#                        exstra_flag=True
                        if eddy_core_lon>360:
                                eddy_core_lon=eddy_core_lon-360
                        eddy_core_lon,eddy_core_lat=m(eddy_core_lon,eddy_core_lat)
                        m.scatter(eddy_core_lon,eddy_core_lat,s=eddy_select_info['seed_size'],c=seed_color,linewidths=0.0001)
                        exstra_flag=True
                        for i in eddy_contlon_e:
                            if i>360:
                                  exstra_flag=False
                        if not exstra_flag:
                               cx_e, cy_e = m(eddy_contlon_e, eddy_contlat_e)
                               m.plot(cx_e, cy_e ,color =ecolor,linewidth=eddy_select_info['line_width']) 
                               
                               cx_Uavg, cy_Uavg = m(eddy_contlon_Uavg, eddy_contlat_Uavg)
                               m.plot(cx_e, cy_e ,color =ecolor,linewidth=eddy_select_info['line_width'])
                               m.plot(cx_Uavg, cy_Uavg ,color =ucolor,linewidth=eddy_select_info['line_width']) 
                               eddy_contlon=[]
                               for i in eddy_contlon_e:
                                    eddy_contlon.append(i-360)
                               eddy_contlon_e=eddy_contlon
                               
                        cx_e, cy_e  = m(eddy_contlon_e, eddy_contlat_e)
                        m.plot(cx_e, cy_e,color =ecolor,linewidth=eddy_select_info['line_width']) 
                        
                        cx_Uavg, cy_Uavg = m(eddy_contlon_Uavg, eddy_contlat_Uavg)
                        m.plot(cx_Uavg, cy_Uavg ,color =ucolor,linewidth=eddy_select_info['line_width']) 
        
    m.drawmapboundary()#fill_color='#689CD2'
    m.drawparallels(np.arange(latmin,latmax,int((latmax-latmin)/5)),labels=[1,0,0,0],linewidth=0,fontsize=10)#+1+4
    m.drawmeridians(np.arange(lonmin,lonmax,int((latmax-latmin)/5)),labels=[0,0,0,1],linewidth=0,fontsize=10)#+1+4
    m.drawcoastlines()
    m.fillcontinents(color='k')#color='#BF9E30',lake_color='#689CD2',zorder=0
    
#    plt.show()  
    savefilename=outdir+'\\'+title+'.jpg'
    plt.savefig(savefilename,dpi=eddy_select_info['dpi']) #600
    plt.close(250)
#    plt.clf()
    

def eddy_mask(outdir,lon_block,lat_block,eddy_select_info,filedate,sladata,eddy_dic):    
    lonmin, lonmax, latmin, latmax=lon_block[0][0],lon_block[-1][-1],lat_block[0][0],lat_block[-1][-1] #
   
    jmin=int((latmin+89.875)/0.25)
    jmax=int((latmax+89.875)/0.25)
    imin=int((lonmin-0.125)/0.25)
    imax=int((lonmax-0.125)/0.25)
    print('jmin,jmax,imin,imax',jmin,jmax,imin,imax)
    
    lon_grid=np.arange(0.125,372,0.25)#[imin:imax]
    lat_grid= np.arange(-89.875,90,0.25)[jmin:jmax]
    
    height=len(lat_grid)
    width=len(lon_grid)
    mask_list=np.zeros((height,width),np.byte)
    lon_grid, lat_grid= np.meshgrid(lon_grid, lat_grid)  
    
#    eddy_json_dict={}
#    for seedname2 in eddy_dic:
#            #获取涡心经纬度
#        
#            eddy_core_lon=eddy_dic[seedname2]['eddy_core'][0] 
#            eddy_core_lat=eddy_dic[seedname2]['eddy_core'][1]
#            #获取最大地转流边界数据
#            eddy_Uag_cont=eddy_dic[seedname2]['eddy_Uavg_contour']
#            eddy_contlon_Uag, eddy_contlat_Uag = eddy_Uag_cont[0], eddy_Uag_cont[1]
#             #获取有效边界数据
#            eddy_effect_cont=eddy_dic[seedname2]['eddy_effect_contour']
#            eddy_contlon_effect, eddy_contlat_effect = eddy_effect_cont[0], eddy_effect_cont[1]
#            
#            
    
    eddy_json_dict = OrderedDict()
    for key1 in eddy_dic.keys():
            eddy_inout=eddy_dic[key1]
            for key2 in eddy_inout.keys():
                block_eddy=eddy_inout[key2]
                for seedname2 in block_eddy:
                     point_type=seedname2.split('_')[0]
                     if point_type=='eddy':
                            eddy_core_lon=block_eddy[seedname2]['eddy_core'][0] 
                            
                            eddy_core_lat=block_eddy[seedname2]['eddy_core'][1]
                            #获取最大地转流边界数据
                            eddy_Uag_cont=block_eddy[seedname2]['eddy_Uavg_contour']
                            eddy_contlon_Uag, eddy_contlat_Uag = eddy_Uag_cont[0], eddy_Uag_cont[1]
                             #获取有效边界数据
                            eddy_effect_cont=block_eddy[seedname2]['eddy_effect_contour']
                            eddy_contlon_effect, eddy_contlat_effect = eddy_effect_cont[0], eddy_effect_cont[1]
                            
                            #对最大地转流边界进行处理
                            Uag_cont=zip(eddy_contlon_Uag, eddy_contlat_Uag)
                            Uag_cont=list(Uag_cont)
                            Uag_cont = Path(Uag_cont)
                            #求经度的最大值最小值
                            Uag_cont_lonmin=np.min(eddy_contlon_Uag)
                            Uag_cont_lonmax=np.max(eddy_contlon_Uag)
                            #求经度的最大值最小值的index
                            Uag_imin_index=int((Uag_cont_lonmin-lonmin)/0.25)
                            Uag_imax_index=int((Uag_cont_lonmax-lonmin)/0.25)
                            #求纬度的最大值最小值
                            Uag_cont_latmin=np.min(eddy_contlat_Uag)
                            Uag_cont_latmax=np.max(eddy_contlat_Uag)
                            #求纬度的最大值最小值的index
                            Uag_jmin_index=int((Uag_cont_latmin+latmin)/0.25)
                            Uag_jmax_index=int((Uag_cont_latmax+latmin)/0.25)
                            if Uag_imin_index-4>=0:
                                Uag_imin_index=Uag_imin_index-4
                            if Uag_imax_index+4<width:
                                Uag_imax_index=Uag_imax_index+4
                            if Uag_jmin_index-4>=0:
                                Uag_jmin_index=Uag_jmin_index-4
                            if Uag_jmax_index+4<height:
                                Uag_jmax_index=Uag_jmax_index+4 
                                
                                
                            #对有效边界的值进行处理
                            Effect_cont=zip(eddy_contlon_effect, eddy_contlat_effect)
                            Effect_cont=list(Effect_cont)
                            Effect_cont = Path(Effect_cont)
                            #求有效边界经度度的最大值最小值
                            cont_lonmin=np.min(eddy_contlon_effect)
                            cont_lonmax=np.max(eddy_contlon_effect)
                            #求有效边界经度的最大值最小值的index
                            imin_index=int((cont_lonmin-lonmin)/0.25)
                            imax_index=int((cont_lonmax-lonmin)/0.25)
                #            if cont_lonmax>360:
                #                print('cont_lonmax',cont_lonmax)
                            #求有效边界纬度的最大值最小值
                            cont_latmin=np.min(eddy_contlat_effect)
                            cont_latmax=np.max(eddy_contlat_effect)
                             #求有效边界纬度的最大值最小值的index
                            jmin_index=int((cont_latmin+latmin)/0.25)
                            jmax_index=int((cont_latmax+latmin)/0.25)
                            if imin_index-4>=0:
                                imin_index=imin_index-4
                            if imax_index+4<width:
                                imax_index=imax_index+4
                            if jmin_index-4>=0:
                                jmin_index=jmin_index-4
                            if jmax_index+4<height:
                                jmax_index=jmax_index+4 
                            mask_effect_point=[]
                            mask_Uag_point=[]   
                            eddy_core=[]
                            for i in range(jmin_index, jmax_index+1):
                                for j in range(imin_index,imax_index+1):
                                    #mask_list[i][j]=0.5
                #                    if j>1439:
                #                        j=j-1439
                                    point=[lon_grid[i][j],lat_grid[i][j]]
                                    if (lon_grid[i][j]==eddy_core_lon or (lon_grid[i][j]-360)==eddy_core_lon)and lat_grid[i][j]==eddy_core_lat:
                                          if (block_eddy[seedname2]['sign_type']=='Cyclonic'):   
                                                   mask_list[i][j]=-50
                                                   eddy_core.append([i,j,-50])
                                          elif (block_eddy[seedname2]['sign_type']=='Anticyclonic'):   
                                                   mask_list[i][j]=50
                                                   eddy_core.append([i,j,50])
                                    elif Effect_cont.contains_point(point) and not Uag_cont.contains_point(point):
                                            #mask_list[i][j]=255
                                            if (block_eddy[seedname2]['sign_type']=='Cyclonic'):   
                                                   mask_list[i][j]=-10
                                                   mask_effect_point.append([i,j,-10])
                                            elif (block_eddy[seedname2]['sign_type']=='Anticyclonic'):   
                                                   mask_list[i][j]=10
                                                   mask_effect_point.append([i,j,10])
                                    elif Uag_cont.contains_point(point):
                                           if (block_eddy[seedname2]['sign_type']=='Cyclonic'):   
                                                   mask_list[i][j]=-30
                                                   mask_Uag_point.append([i,j,-30])
                                           elif (block_eddy[seedname2]['sign_type']=='Anticyclonic'):   
                                                   mask_list[i][j]=30
                                                   mask_Uag_point.append([i,j,30])
                            for i in range(len(mask_list)):
                                for j in range(len(mask_list[0])):
                                    if j >1439 and mask_list[i][j]!=0 and mask_list[i][j-1439]==0:
                                        mask_list[i][j-1439]=mask_list[i][j]
                            mask=mask_list[:,0:1440]        
                            eddy_info={
                            'sign_type':block_eddy[seedname2]['sign_type'],
                            'eddy_core_latlonindex_mask':eddy_core,
                            'mask_effect_latlonindex_mask':mask_effect_point,
                            'mask_Uag_latlonindex_mask':mask_Uag_point
                            }
                            eddy_name='eddy'+str(eddy_core_lon)+'_'+str(eddy_core_lat)
                            eddy_json_dict.setdefault(eddy_name,eddy_info)
    eddy_json_outname=outdir+'\\'+str(filedate)+eddy_select_info['eddy_location']+'Eddies'+'mask.json'
    json.dump(eddy_json_dict,open(eddy_json_outname,'w'))
           

    mask=mask[::-1]
    #print('mask_list',mask_list)
    driver = gdal.GetDriverByName('GTiff') #注册
    driver.Register()
    ##创建tif文件GDT_Byte
    outname=outdir+'\\'+str(filedate)+eddy_select_info['eddy_location']+'Eddies'+'mask.tif'
    outDataset=driver.Create(outname,1440,height,1,GDT_Byte,options=["INTERLEAVE=PIXEL","PIXELTYPE=SIGNEDBYTE"])#options=["INTERLEAVE=PIXEL","COMPRESS=JPEG","PHOTOMETRIC="])
    outBand=outDataset.GetRasterBand(1) 
    outBand.WriteArray(mask,0,0)
    outBand.WriteRaster(0,0,1440,height,mask.tostring())
    outDataset = None
    
    print('success')

    
def eddyjson_merge(outjsons,lon_block,lat_block,outer_range,outdir,filedate,eddy_select_info,sladata): 
    #
    eddy_dic=OrderedDict()
    eddy_dic_inner = OrderedDict()  #保存全球inner涡旋信息
    eddy_dic_outer = OrderedDict()
    #
#    eddy_dic_inner=OrderedDict()
#    eddy_dic_outer=OrderedDict()
    if outer_range==0:  #只有一块
        
        f = open(outjsons[0],'r')#
            
        tulp = json.load(f) 
        print('tulp',tulp)
        for key in  tulp:
          # print('key',key)
           eddy_dic_inner = tulp['inner']#所有里面的先合并
#        print('eddy_dic_inner',eddy_dic_inner)
    else: #多块

        eddy_dic_outer_union = OrderedDict()   #保存全球outer涡旋信息
    
        for i in range(len(outjsons)):
            try:
                f = open(outjsons[i],'r')#
                tulp = json.load(f) 
                for key in tulp['inner']:
                    eddy_dic_inner.setdefault(key,tulp['inner'][key])
                    eddy_dic_outer_union.update(OrderedDict(tulp['outer']))  # 
            except:
                print(outjsons[i],"此块全为无效值")
            
  
#       =================================    
        #
        block_i_j_list=[]
        for i in range(len(lat_block)):
                 for j in range(len(lon_block)+1):
                        block_i_j_list.append([i,j])
        
        
        range_indexs=rangesearch(np.array(block_i_j_list),np.sqrt(2))
        for i in range(len(block_i_j_list)):
            if block_i_j_list[i][1]==len(lon_block):
                    block_i_j_list[i][1]=0

        
        for i in range(len(range_indexs)):
                curr_block_file=outdir+'\\eddy_info'+'_'+str(block_i_j_list[i][0])+'_'+str(block_i_j_list[i][1])+'.json'
                try:
                    curr_tulp=json.load(open(curr_block_file,'r'))                 
                    for j in range(len(range_indexs[i])):
                        neighbor_index=range_indexs[i][j]
                        if range_indexs[i][j]!=i:
                            neighbor_block_file=outdir+'\\eddy_info'+'_'+str(block_i_j_list[neighbor_index][0])+'_'+str(block_i_j_list[neighbor_index][1])+'.json'
                            neighbor_tulp=json.load(open(neighbor_block_file,'r')) 
                            eddy_dic_outer_union=eddyjson_outer(curr_tulp['outer'],neighbor_tulp['outer'],eddy_dic_outer_union)
                        
                                
                except:
                    print("这里报过错")
                     
        eddy_dic_outer.update(eddy_dic_outer_union)  #所有的涡旋信息
        
        for i in range(len(lat_block)):
            try:
             curr_block=outdir+'\\eddy_info'+'_'+str(i)+'_'+str(0)+'.json'
             next_block=outdir+'\\eddy_info'+'_'+str(i)+'_'+str(len(lon_block)-1)+'.json'
             #print('curr_block',str(i)+'_'+str(0),str(i)+'_'+str(len(lon_block)-1))
             curr_block_tulp=json.load(open(curr_block,'r'))   
             next_block_tulp=json.load(open(next_block,'r'))
             eddy_dic_outer_union=eddyjson_outer(curr_block_tulp['outer'],next_block_tulp['outer'],eddy_dic_outer_union)
            except:
                print("这里也报过错")
        eddy_dic_outer.update(eddy_dic_outer_union)
    eddy_dic.setdefault('outer',eddy_dic_outer)
    eddy_dic.setdefault('inner',eddy_dic_inner)
  
    mergejson=outdir+'\\eddy_info_merge'+filedate+'.json'   #合并的涡旋文件名
    eddy_len=0
    
    for key in eddy_dic:
        for key2 in eddy_dic[key]:
            eddy_len=eddy_len+len(eddy_dic[key][key2])
    print ('涡旋个数',eddy_len)   #涡旋个数
    
    
    

    json.dump(eddy_dic,open(mergejson,'w'))
    return mergejson
    
    
       
       
"""
new add
"""        
def reject(outjson,seedjson):
            #
            eddy={}  
            file1=outjson
            file2=seedjson
            f1 = open(file1,'r')#
            tulp1 = json.load(f1) 
            f1.close()
            for key1 in tulp1.keys():
               for key2 in tulp1[key1].keys():
                    #for key3 in tulp1[key1][key2].keys():
                    
                
                        eddy=dict(eddy,**tulp1[key1][key2])   
            #
            f2=open(file2,'r')
            tulp2=json.load(f2)
            f2.close()
            
#            tulp3=tulp2.keys()
            tulp3={}
            tulp3=dict(tulp3, **tulp2) 
            for key1 in eddy.keys():
                for key2 in tulp2.keys():
                    if abs(float(key1.split("_")[1])-float(key2.split("_")[1]))<0.25 and abs(float(key1.split("_")[2])-float(key2.split("_")[2]))<0.25:
                        if key2 in  tulp3:  
                           #
                           del tulp3[key2] 
  

            eddy=dict(eddy, **tulp3)
            json.dump(eddy,open(file1,'w'))
            #print(str(time.time()-start))   
            
            
            
            
            
            

#获取不同分块的经纬度
def lon_lat_block(lon1,lat1,lat_block_num,lon_block_num,lon_inner,lat_inner,outer_range):
     #初始化第一块的经度范围
#    pdb.set_trace()
    lon2=lon1+lon_inner+outer_range
    lon=[[lon1,lon2]]
    for i in range(lon_block_num-1):
        if i==0:  #经度方向的第二块
            lon1+=lon_inner
            if lon_block_num-1>1:
                lon2+=lon_inner+outer_range
            else:
                lon2+=lon_inner
        elif i==lon_block_num-2:      #经度方向的最后一块
            lon1+=lon_inner+outer_range
            lon2+=lon_inner+outer_range
        else:
            lon1+=lon_inner+outer_range
            lon2+=lon_inner+outer_range
        
        lon.append([lon1,lon2])
    #print (lon)
      #初始化第一块的经度范围
#    lat1=-90
    lat2=lat1+lat_inner+outer_range
    latinit=lat1
    if latinit==-90:
        latinit=latinit+1
    lat=[[latinit,lat2]]
    for i in range(lat_block_num-1):
        if i==0:  #
            lat1+=lat_inner
            if lat_block_num-1>1:
                lat2+=lat_inner+outer_range
            else:
                lat2+=lat_inner
        elif i==lat_block_num-2:      #边界的区域块
            lat1+=lat_inner+outer_range
            lat2+=lat_inner
            if lat2==90:   #纬度到89度
                lat2=lat2-1
        else:
            lat1+=lat_inner+outer_range
            lat2+=lat_inner+outer_range
        
        lat.append([lat1,lat2])  
    print ('lat',lat)
    print('lon',lon)
    #pdb.set_trace()
    return lon,lat
#存储涡旋识别参数json
def eddy_detect_parameter(eddy_select_info,outdir):
    json.dump(eddy_select_info,open(outdir,'w')) 
    
#读取所有年份的数据并进行涡旋识别
def readdir_gloabal_eddy_multi_detect(eddy_select_info):
    
    inputdirectory=eddy_select_info['inputfile'] 

    filelist=os.listdir(inputdirectory)
    for f in filelist:
      filepath = os.path.join(inputdirectory, f )
      #判断所识别的数据是一年的数据
      if os.path.isdir(filepath) and f=='h':
          
         eddy_select_info['outfile']=inputdirectory+'json/'
         outfile=inputdirectory+'json/'
         if not os.path.exists(outfile): #判断该路径是否存在
            os.makedirs(outfile)
            
         gloabal_eddy_multi_detect(eddy_select_info,filepath+'/')
      #判断所识别的数据是多年数据
      elif os.path.isdir(filepath) and f!='h' and f!='uv':
          ChildrenDir=filepath+'/'
          ChildrenfileList=os.listdir(ChildrenDir)
          for childrenf in ChildrenfileList:
               childrenfilepath=os.path.join( ChildrenDir,childrenf)
               if os.path.isdir(childrenfilepath) and childrenf=='h':
                   #定义输出路径
                   eddy_select_info['outfile']=ChildrenDir+'json/'
                   outfile=ChildrenDir+'json/'
                   if not os.path.exists(outfile): #判断该路径是否存在
                       os.makedirs(outfile)
                   gloabal_eddy_multi_detect(eddy_select_info,childrenfilepath+'/')
#    
#进行一年内多时间点的涡旋识别
def gloabal_eddy_multi_detect(eddy_select_info):
#    #默认全球
    inputdirectory=eddy_select_info['inputfile'] 
    lat_block_num=eddy_select_info["z_block_num"]
    lon_block_num=eddy_select_info["m_block_num"]
    outer_range=eddy_select_info["out_range"]
    lat_inner=round((180-(lat_block_num-1)*outer_range)/lat_block_num,2)
    lon_inner=round((360-(lon_block_num-1)*outer_range)/lon_block_num,2)
    print(lat_inner)
    print(lon_inner)

    lon1,lat1=0.125,-90
    
#    pdb.set_trace()
    m_kernel=eddy_select_info['m_kernel'] 
    z_kernel=eddy_select_info['z_kernel'] 
    pool_size=int(eddy_select_info['pool_size']) 
    eddy_pixel_num_range=eddy_select_info['eddy_pixel_num_range']
    
    start_time=time.time()        
    #获取不同分块的经纬度范围
#    
    AVISO_files =glob.glob(inputdirectory+'*.tif')  
    #识别不同时间的涡旋
    for AVISO_file in AVISO_files: 
        filename=os.path.split(AVISO_file)[1]  #tif文件名
        filename_split=filename.split('_')
        filedate=filename_split[5]#获得数据的时间
        gdal.AllRegister()        #注册gdal
        ds = gdal.Open(AVISO_file)  #读取tif数据中的数据集
        band = ds.GetRasterBand(1) #获取数据集中的通道1中的数据
        
        GT=ds.GetGeoTransform()
        XSize=ds.RasterXSize
        YSize=ds.RasterYSize 
        pixelwidth=round(GT[1],2)
        pixelheigh=round(GT[5],2)
        originX=GT[0]+180+0.25+0.125
        originY=GT[3]
        end_X=originX + pixelwidth*XSize
        end_Y=originY - pixelheigh*YSize
        
        print('XSize,YSize,pixelwidth,pixelheigh,originX,originY,end_X,end_Y',XSize,YSize,pixelwidth,pixelheigh,originX,originY,end_X,end_Y)
        
        
        #对数据进行分块
         #默认全球
#        lat_block_num = eddy_select_info['z_block_num'] 
#        lon_block_num =eddy_select_info['m_block_num'] 
#        outer_range = eddy_select_info['out_range'] 
#        lat_inner = ((end_Y-originY)- outer_range*(lat_block_num-1))/lat_block_num
#        lon_inner =((end_X+outer_range-originX)- outer_range*(lon_block_num))/lon_block_num
        #print('lat_block_num,lon_block_num,outer_range,lat_inner,lon_inner',[lat_block_num,lon_block_num,outer_range,lat_inner,lon_inner])
        Origin_Data_info={
                       'XSize':XSize,
                       'YSize':YSize,
                       'pixelwidth':pixelwidth,
                       'pixelheigh':pixelheigh,
                       'originX':originX,
                       'originY':originY,
                       'end_X':end_X,
                       'end_Y':end_Y,
                       'outer_range':outer_range
                     
                       
                         }
      #  print('lat_inner,lon_inner',lat_inner,lon_inner)
#        lon1,lat1=originX,originY
#        if eddy_select_info['eddy_location']=='South China Sea': #105,125,5,25
#            lat_block_num,lon_block_num,lat_inner,lon_inner,outer_range=1,1,25,20,0
#            lon1,lat1=104.875,-0.125
        if eddy_select_info['eddy_location']=='South China Sea': #105,125,5,25
#        lonmin, lonmax, latmin, latmax=104.5,134.5,4.5,34.5
            lat_block_num,lon_block_num,lat_inner,lon_inner,outer_range=1,1,20,20,0
            lon1,lat1=105,5
        elif eddy_select_info['eddy_location']=='West Pacific': #100,200，-20,50
            lat_block_num,lon_block_num,lat_inner,lon_inner,outer_range=2,2,30,45,10
            lon1,lat1=90,-20
        elif eddy_select_info['eddy_location']=='North Indian Ocean': #100,200，-20,50
            lat_block_num,lon_block_num,lat_inner,lon_inner,outer_range=1,3,30,25,15
            lon1,lat1=30,-15
    #    elif eddy_select_info['eddy_location']=='Specific area': #100,200，-20,50
    #        lat_block_num,lon_block_num,lat_inner,lon_inner,outer_range=1,1,18,20,0#1,1,10,10,0
    #        lon1,lat1=270,-20#120,15
        elif eddy_select_info['eddy_location']=='Specific area': #100,200，-20,50
            lat_block_num,lon_block_num,lat_inner,lon_inner,outer_range=1,1,12,12,0#1,1,10,10,0
            lon1,lat1=174,26#120,15
        elif eddy_select_info['eddy_location']=='Kuroshio Current':
            lat_block_num,lon_block_num,lat_inner,lon_inner,outer_range=1,1,10,20,0
            lon1,lat1=140,30
        #pdb.set_trace()
        lon,lat=lon_lat_block(lon1,lat1,lat_block_num,lon_block_num,lon_inner,lat_inner,outer_range)
        #print('lon,lat',lon,lat)
        
        sladata = band.ReadAsArray()[::-1]#获得sla值
        sladata_copy=np.ma.copy(sladata)
        exstra_range=int(outer_range/pixelwidth)
        #将经度方向靠近0度位置部分数据复制到360度左边
        sladata=np.hstack((sladata,sladata[:,0:exstra_range]))
        #将经度方向靠近360度位置部分数据复制到0度右边
        end_exstra_sladata=sladata_copy[:,len(sladata_copy[0])-1-exstra_range:len(sladata_copy[0])-1]
        sladata=np.hstack((end_exstra_sladata,sladata))
        
        #对无效值进行处理
        mask=abs(sladata)>100
        sladatamask=np.ma.array(sladata,mask=mask)
        np.place(sladata, sladatamask == False, 0.)
        
        #对数据进行滤波
        print ('start smoothing')
        #m_kernel,z_kernel表示经向、纬向的高斯滤波的核大小
        sladata -= ndimage.gaussian_filter(sladata, [z_kernel,m_kernel]) 
#        sladata -= ndimage.gaussian_filter(sladata, [m_kernel,z_kernel]) 
        #滤波后的数据无效值进行处理
        sladata = np.ma.masked_where(sladatamask == False, sladata)
        
        #删除掉复制到靠近经度为0右边处的数据，只留360左边的数据来对边界处涡旋数据进行识别       
        sladata = sladata[:,exstra_range:len(sladata[0])]
        dire = os.path.split(AVISO_file)[0]  #sla文件夹路径
        #AVISO
        #uvfile = filename_split[0]+'_'+filename_split[1]+'_'+filename_split[2]+'_'+filename_split[3]+'_uv_'+filename_split[5]+'_'+filename_split[6]#+'_u_v_1.tif'#uv的文件名
        #NEW_AVISO
        uvfile = filename_split[0]+'_'+filename_split[1]+'_'+filename_split[2]+'_'+filename_split[3]+'_'+filename_split[4]+'_'+filename_split[5]+'_'+filename_split[6][:8]+'_u_v_1.tif'#uv的文件名
#        if len(filename_split)>7:
#            #AVISO
#            uvfile=uvfile+'_u_v_1.tif'
            #NEW_AVISO
#            uvfile=uvfile+'_ugosa_vgosa_1.tif'
        print (uvfile)
        uvAVISO_file= os.path.split(AVISO_file)[0]+ '\\uv\\'+uvfile
        #pdb.set_trace()
        uvds=gdal.Open(uvAVISO_file)
        uband = uvds.GetRasterBand(1) #获取数据集中的通道1中的数据
        udata = uband.ReadAsArray()[::-1]#获得u值
        udata=np.hstack((udata,udata[:,0:exstra_range]))
        vband = uvds.GetRasterBand(2) #获取数据集中的通道2中的数据
        vdata = vband.ReadAsArray()[::-1]#获得v值
        vdata=np.hstack((vdata,vdata[:,0:exstra_range]))
        outdir=eddy_select_info['outfile']  +str(filedate)  #创建json文件保存路径
        if not os.path.exists(outdir): #判断该路径是否存在
            os.makedirs(outdir)
        outfile_temp=outdir+'\\eddy_info'    #+'.'+str(lat_block_num)+'.'+str(lon_block_num)+'.'+str(outer_range)    
        eddy_detect_parameter_outjson=outdir+'\\eddy_detect_parameter_'+filedate+'.json'
        eddy_detect_parameter(eddy_select_info,eddy_detect_parameter_outjson)
        #
        
        
        
        
        
        """
        新添加直接识别全球种子点
        """
        #
        A_eddy_dic=OrderedDict()
        area=eddy_select_info['eddy_location']
        lonmin, lonmax, latmin, latmax=0,360,-90,90#3,6,42,44 #
       #获取特定区域的索引值   
        jmin=int((latmin+90)/0.25)
        jmax=int((latmax+90)/0.25)
        imin=int((lonmin-0.125)/0.25)
        imax=int((lonmax+outer_range)/0.25)
        if area!='Global Ocean':
            imin-=4
            imax+=4
            jmin-=4
            jmax+=4
        lon_grid=np.arange(lonmin,lonmax)    
        #lon_grid = np.arange(0.125,360,0.25)[imin:imax]+0.125
        lon_grid = np.arange(lonmin,lonmax+outer_range,0.25)[imin:imax]+0.125
        lat_grid  = np.arange(-89.875,90,0.25)[jmin:jmax]+0.125
        lon_grid, lat_grid= np.meshgrid(lon_grid, lat_grid)  
        xpcol, ypcol = lon_grid[:], lat_grid[:]
        
        #反气旋
        local_extrema = np.ma.copy(sladata)
        local_extrema = np.reshape(local_extrema, (sladata.shape))
        local_extrema_ac= detect_local_minima(-local_extrema)
        inner_ac_seed_j, inner_ac_seed_i = np.where(local_extrema_ac) 
        
        for n in range(len(inner_ac_seed_j)):
            lmi = inner_ac_seed_i[n] 
            lmj = inner_ac_seed_j[n]
            seed_lon, seed_lat = xpcol[lmj, lmi], ypcol[lmj, lmi]
            seed_sla=round(float(sladata[lmj][lmi]),6) 
            eddy_flag="false"
            if abs(seed_sla)<100: 
                
#                if outer_range+20<=lmj<= len(sladata)-outer_range-20 and outer_range+20<=lmi<= len(sladata[0])-outer_range-20: 
#                    
#                    eddy_inout='inner'
#                else:
                eddy_inout='outer'   
                eddyk=OrderedDict()
                
                eddyk = OrderedDict([('sign_type','Anticyclonic'),
                                     ('eddy_inout',eddy_inout),
                                     ('eddy_flag',eddy_flag), 
                                     ('eddy_core',[seed_lon,seed_lat,seed_sla])])

                eddy_name='seed'+'_'+ str(seed_lon)+'_'+str(seed_lat)
                A_eddy_dic.setdefault(eddy_name,eddyk)                     
        local_extrema = np.ma.copy(sladata)
        local_extrema = np.reshape(local_extrema, (sladata.shape))
        local_extrema_ac= detect_local_minima(local_extrema)
        inner_ac_seed_j, inner_ac_seed_i = np.where(local_extrema_ac) 
        for n in range(len(inner_ac_seed_j)):
            lmi = inner_ac_seed_i[n] 
            lmj = inner_ac_seed_j[n]
            seed_lon, seed_lat = xpcol[lmj, lmi], ypcol[lmj, lmi]
            seed_sla=round(float(sladata[lmj, lmi]),6)
            if abs(seed_sla)<100:
#              if outer_range+20<=lmj<= len(sladata)-outer_range-20 and outer_range+20<=lmi<= len(sladata[0])-outer_range-20: 
#                eddy_inout='inner'
#              else:
              eddy_inout='outer' 
              
              eddyk = OrderedDict([('sign_type','Cyclonic'),
                                 ('eddy_inout',eddy_inout),
                                 ('eddy_flag',eddy_flag), 
                                 ('eddy_core',[seed_lon,seed_lat,seed_sla])])
                    
              eddy_name='seed'+'_'+ str(seed_lon)+'_'+str(seed_lat)
              
              A_eddy_dic.setdefault(eddy_name,eddyk)
        num=0      
        for w in A_eddy_dic.keys():
            num+=1
        print(num)
        #
        seedjsondir=eddy_select_info['outfile'] +str(filedate)+'/'+"seedjson"+'/'
        
        if not os.path.exists(seedjsondir): #判断该路径是否存在
            os.makedirs(seedjsondir)
        seedjson=seedjsondir+str(filedate)+'_seed'+'.json'     
        #mergejson='H:\\1993_twosat\\json\\19930101\\eddy_info_merge'+'19930101'+'.json'   #合并的涡旋文件名
        json.dump(A_eddy_dic,open(seedjson,'w'))
        #        
        print("成功建种子点json")
        """
        全球种子点识别完毕
        """
        #创建每块的空间范围及json文件名的字典
#        
#        pdb.set_trace()
        Blockdic=OrderedDict()   
        
        for i in range(len(lat)):
            for j in range(len(lon)):
                location=lon[j]+lat[i]
                outfnj=outfile_temp+'_'+str(i)+'_'+str(j)+'.json'
                Block={'location':location,
                   'outfnj':outfnj}
                   
                Blockdic.setdefault(str(i)+'_'+str(j),Block)               
        

#        pool = Pool(processes=6)
        #不并行
        pool = Pool(processes=8)
        for block_i in Blockdic:
       
           pool.apply_async(eddy_main,(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info,))
#           eddy_main(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info)
#             
        pool.close()
        pool.join()
#        

    
    
    
    
    
#        #plist=[]
#        for block_i in Blockdic: 
#            #
#            #proc = Process(target=eddy_main, args=(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info,))
#            eddy_main(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info)
#            #plist.append(proc)
#        #for proc in plist: proc.start() 
#        #for proc in plist: proc.join()
        
        
        
        outjsons=[]
        for block_i in Blockdic:
             outjsons.append(Blockdic[block_i]['outfnj'])
        mergejson=eddyjson_merge(outjsons,lon,lat,outer_range,outdir,filedate,eddy_select_info,sladata)
            
        reject(mergejson,seedjson)
        print("success")
        print ('Duration', str((time.time() - start_time) ), 'seconds!')

