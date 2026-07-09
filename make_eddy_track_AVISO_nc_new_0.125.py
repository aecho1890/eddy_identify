#!/usr/bin/env python
# coding: utf-8

# In[25]:


from multiprocessing import Pool,Process
import os,netCDF4
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
import time



# In[26]:


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
       
        self.M = Basemap(projection='gall', llcrnrlon = self.lonmin,                                             
                         urcrnrlon = self.lonmax,                                             
                         llcrnrlat = self.latmin,                                             
                         urcrnrlat = self.latmax,                                             
                         lat_ts = 0.5 * (self.latmin + self.latmax),                                            
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
        self.upad[:] = -self.gof() * self.v2rho_2d(self.vmask() * (zeta.data[1:] - zeta.data[:-1])                                         * 0.5 * (self.pn()[1:] + self.pn()[:-1]))
        
        self.vpad[:] =  self.gof() * self.u2rho_2d(self.umask() * (zeta.data[:, 1:] - zeta.data[:, :-1])                                         * 0.5 * (self.pm()[:, 1:] + self.pm()[:, :-1]))
        return self

    def get_AVISO_uvdata(self, udata,vdata):    #直接读取AVISO的uv值
        '''
        Returns u and v geostrophic velocity at
        surface from variables f, zeta, pm, pn...
        Note: output at rho points
        '''
        #print ('get_geostrophic_velocity')用到
#        
        #print('upad',len(self.upad[:]),len(self.upad[:][0]))
        #print('udata',len(udata),len(udata[0]))
        self.upad[:] = udata
        #print('vpad',len(self.vpad[:]),len(self.vpad[:][0]))
        #print('vdata',len(vdata),len(udata[0]))
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
#        originX    = Origin_GetGeoTransform[0]
#        #print('AA_originx',originX)
#        end_X      = Origin_GetGeoTransform[1]
#        pixelwidth = Origin_GetGeoTransform[2]
#        originY    = Origin_GetGeoTransform[3]
#        end_Y      = Origin_GetGeoTransform[4]
#        pixelheigh=Origin_GetGeoTransform[5]
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
    





# In[34]:


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


    


# In[36]:


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
        #print('tulp',tulp)
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


# In[38]:


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


# In[42]:


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
    
 
    sla_grd.get_AVISO_uvdata(u,v)      #直接用AVISO的uv产品   
    # Remove padded boundary
    sla = sla[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1]  
    sla_grd.getEKE()
    pmvalue=pm_value[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1]
    pnvalue=pn_value[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1] 
    uvalue=u[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1] 
    vvalue=v[sla_grd.jup0:sla_grd.jup1, sla_grd.iup0:sla_grd.iup1] 
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
    print ('local_extrema',local_extrema.shape)
    local_extrema_ac= detect_local_minima(-local_extrema)
    inner_ac_seed_j, inner_ac_seed_i = np.where(local_extrema_ac)  #涡旋种子点的索引值
    
#    print('sla',local_extrema)
  
    
    outer_range=outer_range/pixelwidth    #outer的像素个数 1度4个像素 
    
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


from skimage.measure import block_reduce

def downsample_array_simple(data, factor=2, method='mean'):
    """
    使用block_reduce进行下采样（更简单的方法）
    """
    if method == 'mean':
        func = np.mean
    elif method == 'max':
        func = np.max
    elif method == 'min':
        func = np.min
    else:
        func = np.mean
    
    # 对于掩码数组，需要特殊处理
    if isinstance(data, np.ma.MaskedArray):
        # 将掩码数组转换为普通数组，用NaN表示掩码值
        data_filled = data.filled(np.nan)
        result = block_reduce(data_filled, block_size=(factor, factor), func=func)
        # 将全为NaN的块标记为掩码
        mask = np.isnan(result)
        return np.ma.masked_array(result, mask=mask)
    else:
        return block_reduce(data, block_size=(factor, factor), func=func)

# 在循环中使用
#sladata_downsampled = downsample_array(sladata, factor=2, method='mean')



import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap

def plot_sla_data(data, title, vmin=-0.3, vmax=0.3, cmap='RdBu_r', save_path=None):
    """Visualize SLA data"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Subplot 1: Data visualization
    # Handle invalid values for display
    plot_data = np.ma.filled(data, fill_value=np.nan)
    im1 = ax1.imshow(plot_data, cmap=cmap, vmin=vmin, vmax=vmax, origin='lower')
    ax1.set_title('{} - Image Display'.format(title))
    ax1.set_xlabel('Longitude Index')
    ax1.set_ylabel('Latitude Index')
    plt.colorbar(im1, ax=ax1, label='SLA (m)')
    
    # Subplot 2: Data statistics
    # Safely get valid data
    if isinstance(data, np.ma.MaskedArray):
        valid_data = data.compressed()
    else:
        valid_data = data.ravel()
    
    # Filter out NaN and infinite values
    valid_data = valid_data[np.isfinite(valid_data)]
    
    if len(valid_data) > 0:
        # Calculate reasonable histogram range
        data_min = np.nanmin(valid_data)
        data_max = np.nanmax(valid_data)
        
        # If data range is too small, set reasonable bins
        if data_max - data_min < 1e-10:
            bins = 10
            data_range = (data_min - 0.1, data_max + 0.1)
        else:
            bins = 50
            data_range = (data_min, data_max)
        
        ax2.hist(valid_data, bins=bins, range=data_range, alpha=0.7, color='blue')
        ax2.set_title('{} - Data Distribution\nValid Data: {}/{}'.format(title, len(valid_data), data.size))
    else:
        ax2.text(0.5, 0.5, 'No Valid Data', transform=ax2.transAxes, 
                ha='center', va='center', fontsize=12)
        ax2.set_title('{} - Data Distribution\nNo Valid Data'.format(title))
    
    ax2.set_xlabel('SLA Value (m)')
    ax2.set_ylabel('Frequency')
    ax2.grid(True, alpha=0.3)
    
    # Add statistical information
    if len(valid_data) > 0:
        stats_text = """
        Min: {:.4f}
        Max: {:.4f}
        Mean: {:.4f}
        Std: {:.4f}
        """.format(np.nanmin(valid_data), np.nanmax(valid_data), 
                  np.nanmean(valid_data), np.nanstd(valid_data))
        
        if isinstance(data, np.ma.MaskedArray):
            mask_ratio = (data.mask.sum()/data.size)*100
            stats_text += "Mask Ratio: {:.2f}%".format(mask_ratio)
    else:
        stats_text = "No Valid Data"
    
    ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

def plot_global_map(data, lons, lats, title, vmin=-0.3, vmax=0.3, cmap='RdBu_r'):
    """Visualize data on global map"""
    fig = plt.figure(figsize=(12, 8))
    
    m = Basemap(projection='robin', lon_0=0, resolution='c')
    m.drawcoastlines()
    m.fillcontinents(color='lightgray', lake_color='white')
    m.drawparallels(np.arange(-90, 91, 30), labels=[1,0,0,0])
    m.drawmeridians(np.arange(-180, 181, 60), labels=[0,0,0,1])
    
    # Convert coordinates
    x, y = m(lons, lats)
    
    # Process data for display
    plot_data = np.ma.filled(data, fill_value=np.nan)
    
    # Plot data
    im = m.pcolormesh(x, y, plot_data, cmap=cmap, vmin=vmin, vmax=vmax, shading='auto')
    plt.colorbar(im, label='SLA (m)', shrink=0.8)
    plt.title(title)
    
    plt.show()

def safe_statistics(data):
    """Safely calculate statistics, handle invalid values"""
    if isinstance(data, np.ma.MaskedArray):
        valid_data = data.compressed()
    else:
        valid_data = data.ravel()
    
    valid_data = valid_data[np.isfinite(valid_data)]
    
    if len(valid_data) == 0:
        return {'min': np.nan, 'max': np.nan, 'mean': np.nan, 'std': np.nan}
    
    return {
        'min': np.min(valid_data),
        'max': np.max(valid_data),
        'mean': np.mean(valid_data),
        'std': np.std(valid_data)
    }

#if __name__ == '__main__':
#    start_time = time.time()
#    area='Global Ocean'
#    eddy_select_info={}
#    
#    eddy_select_info['outfile']='D:/DATA/SLA/eddy/2023/'
#    eddy_select_info['eddy_location']=area
#    lat_block_num=5
#    lon_block_num=8
#    outer_range=10
#    lat_inner=round((180-(lat_block_num-1)*outer_range)/lat_block_num,2)
#    lon_inner=round((360-(lon_block_num-1)*outer_range)/lon_block_num,2)
#
#    lon1,lat1=0.125,-90
#    
#    m_kernel=10
#    z_kernel=5
#    pool_size=20
#    eddy_pixel_num_range=[2, 100000]
#    
#    inputdirectory='E:/cmems_ssh/2023_0.25/'
#    AVISO_files =glob.glob(inputdirectory+'*.nc')  
#    
#    for k in range(1):  # Process only first file for debugging
#        AVISO_file=AVISO_files[k]
#        print("Processing file: {}".format(AVISO_file))
#        filename=os.path.split(AVISO_file)[1]
#        filename_split=filename.split('_')
#        filedate =filename_split[-1].split('.')[0]
#        print("Date: {}".format(filedate))
#         
#        # Step 1: Read original data
#        AVISO_data=netCDF4.Dataset(AVISO_file)
#        sladata_original = AVISO_data.variables['sla'][0]
#        print("Original data shape: {}".format(sladata_original.shape))
#        
#        # Check original data
#        print("Original data basic information:")
#        stats = safe_statistics(sladata_original)
#        print("  Min: {:.4f}".format(stats['min']))
#        print("  Max: {:.4f}".format(stats['max']))
#        print("  Mean: {:.4f}".format(stats['mean']))
#        print("  Std: {:.4f}".format(stats['std']))
#        
#        # Check for NaN/Inf values in original data
#        nan_count_original = (~np.isfinite(sladata_original)).sum()
#        print("  NaN/Inf values in original: {} ({:.2f}%)".format(
#            nan_count_original, nan_count_original/sladata_original.size*100))
#        
#        # Visualize original data
#        plot_sla_data(sladata_original, 'Step 1: Original SLA Data - {}'.format(filedate), 
#                     vmin=-0.5, vmax=0.5, save_path='step1_original_{}.png'.format(filedate))
#        
#        # Step 2: Data chunking and concatenation
#        data1 = sladata_original[:,:720]
#        data2 = sladata_original[:,720:]
#        sladata = np.hstack((data2, data1))
#        
#        print("Concatenated data shape: {}".format(sladata.shape))
#        stats = safe_statistics(sladata)
#        print("After concatenation statistics:", stats)
#        
#        plot_sla_data(sladata, 'Step 2: Longitude Rearranged Data - {}'.format(filedate), 
#                     vmin=-0.5, vmax=0.5, save_path='step2_rearranged_{}.png'.format(filedate))
#        
#        # Save copy for subsequent processing
#        sladata_copy = np.ma.copy(sladata)
#        
#        # Step 3: Boundary extension
#        XSize = len(sladata)
#        YSize = len(sladata[0])
#        pixelwidth = 0.25
#        exstra_range = int(outer_range/pixelwidth)
#        
#        print("Boundary extension range: {} pixels".format(exstra_range))
#        
#        # Extend to right (left of 360 degrees)
#        sladata_extended1 = np.hstack((sladata, sladata[:,0:exstra_range]))
#        print("After first extension shape: {}".format(sladata_extended1.shape))
#        stats = safe_statistics(sladata_extended1)
#        print("After first extension statistics:", stats)
#        
#        plot_sla_data(sladata_extended1, 'Step 3a: Right Boundary Extension - {}'.format(filedate), 
#                     vmin=-0.5, vmax=0.5, save_path='step3a_right_extend_{}.png'.format(filedate))
#        
#        # Extend to left (right of 0 degrees)
#        end_exstra_sladata = sladata_copy[:, len(sladata_copy[0])-1-exstra_range:len(sladata_copy[0])-1]
#        sladata_extended2 = np.hstack((end_exstra_sladata, sladata_extended1))
#        print("After second extension shape: {}".format(sladata_extended2.shape))
#        stats = safe_statistics(sladata_extended2)
#        print("After second extension statistics:", stats)
#        
#        plot_sla_data(sladata_extended2, 'Step 3b: Complete Boundary Extension - {}'.format(filedate), 
#                     vmin=-0.5, vmax=0.5, save_path='step3b_full_extend_{}.png'.format(filedate))
#        
#        sladata = sladata_extended2
#        
#        # Step 4: Invalid value processing
#        # Create comprehensive mask for all types of invalid values
#        nan_mask = ~np.isfinite(sladata)  # NaN and infinite values
#        extreme_mask = abs(sladata) > 100  # Extreme physical values
#        mask = nan_mask | extreme_mask
#
#        print("Invalid values analysis:")
#        print("  Total invalid values: {} ({:.2f}%)".format(mask.sum(), mask.sum()/mask.size*100))
#        print("  - NaN/Inf values: {} ({:.2f}%)".format(nan_mask.sum(), nan_mask.sum()/mask.size*100))
#        print("  - Extreme values (>100): {} ({:.2f}%)".format(extreme_mask.sum(), extreme_mask.sum()/mask.size*100))
#        print("  - Valid values: {} ({:.2f}%)".format((~mask).sum(), (~mask).sum()/mask.size*100))
#
#        # Apply mask and replace invalid values with 0
#        sladatamask = np.ma.array(sladata, mask=mask)
#        np.place(sladata, mask, 0.)  # Replace all masked values with 0
#
#        stats = safe_statistics(sladata)
#        print("After invalid value processing statistics:", stats)
#
#        plot_sla_data(sladata, 'Step 4: After Invalid Value Processing - {}'.format(filedate), 
#                     vmin=-0.5, vmax=0.5, save_path='step4_invalid_processed_{}.png'.format(filedate))
#        
#        # Step 5: Gaussian filtering with mask preservation
#        print('Starting Gaussian filtering...')
#        print("Filter kernel size: meridional={}, zonal={}".format(z_kernel, m_kernel))
#        
#        # Pre-filter statistics
#        pre_filter_stats = safe_statistics(sladata)
#        print("Pre-filter statistics:", pre_filter_stats)
#        
#        # Apply Gaussian filter with mask preservation
#        try:
#            # Save original mask state
#            original_mask = None
#            if isinstance(sladata, np.ma.MaskedArray):
#                original_mask = sladata.mask.copy()
#                print("Original mask count: {}".format(original_mask.sum()))
#            
#            # For filtering, we need to fill masked values temporarily
#            if isinstance(sladata, np.ma.MaskedArray):
#                # Fill masked areas with 0 for filtering
#                sladata_filled = sladata.filled(0)
#            else:
#                sladata_filled = sladata
#            
#            # Apply Gaussian filter to filled data
#            gaussian_filtered = ndimage.gaussian_filter(sladata_filled, [z_kernel, m_kernel])
#            
#            # Reapply original mask to filtered data
#            if original_mask is not None:
#                gaussian_filtered = np.ma.masked_array(gaussian_filtered, mask=original_mask)
#                print("Filtered data mask count: {}".format(gaussian_filtered.mask.sum()))
#            
#            stats = safe_statistics(gaussian_filtered)
#            print("Gaussian filter result statistics:", stats)
#            
#            plot_sla_data(gaussian_filtered, 'Step 5a: Gaussian Filter Result - {}'.format(filedate), 
#                         vmin=-0.1, vmax=0.1, save_path='step5a_gaussian_filtered_{}.png'.format(filedate))
#            
#            # Subtract filter result while preserving masks
#            if isinstance(sladata, np.ma.MaskedArray) and isinstance(gaussian_filtered, np.ma.MaskedArray):
#                # Ensure both arrays have the same mask
#                combined_mask = sladata.mask | gaussian_filtered.mask
#                sladata_result = sladata - gaussian_filtered
#                sladata_result = np.ma.masked_array(sladata_result, mask=combined_mask)
#            else:
#                sladata_result = sladata - gaussian_filtered
#            
#            sladata = sladata_result
#            
#            post_filter_stats = safe_statistics(sladata)
#            print("Post-filter statistics:", post_filter_stats)
#            if isinstance(sladata, np.ma.MaskedArray):
#                print("Post-filter mask count: {}".format(sladata.mask.sum()))
#            
#            plot_sla_data(sladata, 'Step 5b: After Filter Subtraction - {}'.format(filedate), 
#                         vmin=-0.3, vmax=0.3, save_path='step5b_after_subtraction_{}.png'.format(filedate))
#            
#        except Exception as e:
#            print("Gaussian filtering failed: {}".format(e))
#            # Skip this step if filtering fails
#            print("Skipping Gaussian filtering step")
#        
#        # Step 6: Reapply mask (this should now be redundant but kept for safety)
#        sladata = np.ma.masked_where(sladatamask == False, sladata)
#        stats = safe_statistics(sladata)
#        print("After reapplying mask statistics:", stats)
#        if isinstance(sladata, np.ma.MaskedArray):
#            print("Final mask count: {}".format(sladata.mask.sum()))
#        
#        plot_sla_data(sladata, 'Step 6: After Reapplying Mask - {}'.format(filedate), 
#                     vmin=-0.3, vmax=0.3, save_path='step6_remasked_{}.png'.format(filedate))
#        
#        # Step 7: Remove boundary extension
#        sladata_final = sladata[:, exstra_range:len(sladata[0])]
#        print("Final data shape: {}".format(sladata_final.shape))
#        final_stats = safe_statistics(sladata_final)
#        print("Final data statistics:", final_stats)
#        if isinstance(sladata_final, np.ma.MaskedArray):
#            print("Final data mask count: {}".format(sladata_final.mask.sum()))
#        
#        plot_sla_data(sladata_final, 'Step 7: Final Processing Result - {}'.format(filedate), 
#                     vmin=-0.3, vmax=0.3, save_path='step7_final_result_{}.png'.format(filedate))


if __name__ == '__main__':
    start_time = time.time()
    area='Global Ocean'
    eddy_select_info={}
    #filenamedir=os.getcwd()
    
    eddy_select_info['outfile']='E:/eddy/2025-2026/'  #D:\Data\SLA\eddy\2023
    eddy_select_info['eddy_location']=area
    lat_block_num=5
    lon_block_num=8
    outer_range=10
    lat_inner=round((180-(lat_block_num-1)*outer_range)/lat_block_num,2)
    lon_inner=round((360-(lon_block_num-1)*outer_range)/lon_block_num,2)
    #print(lat_inner)
    #print(lon_inner)

    lon1,lat1=0.125,-90
    
#    
    m_kernel=10
    z_kernel=5
    pool_size=20
    eddy_pixel_num_range=[2, 100000]
    
    start_time=time.time()   
#    mons=['10_1','11','12']      #'01','02','03','04','05','06','07','08','09',
#    #获取不同分块的经纬度范围
#    for mon in mons: E:\cmems_ssh\2023_0.25
    inputdirectory='E:/2025-2026-0.25/' #'D:\\Data\\SLA\\2022\\done\\'#'E:\\Data\\SLA\\all-sat-nc\\2022\\'#+mon+'\\'#'D:/SLA/04/'
    AVISO_files =glob.glob(inputdirectory+'*.nc')  
    #识别不同时间的涡旋
    #for AVISO_file in AVISO_files: 
    for k in range (len(AVISO_files)): #
        AVISO_file=AVISO_files[k]
        print (AVISO_file)
        filename=os.path.split(AVISO_file)[1]  #tif文件名
        filename_split=filename.split('_')
        #filedate=filename_split[5]#获得数据的时间  
        filedate =filename_split[-1].split('.')[0]
        print(filedate)  # 输出: 20230101
         
        AVISO_data=netCDF4.Dataset(AVISO_file)  # 
        sladata =AVISO_data.variables['sla'][0]#读取tif数据中的数据集  
        data1 =sladata[:,:720]
        data2 = sladata[:,720:]
        
        
#        data1 = AVISO_data.variables['sla'][0,:,:720]
#        data2 = AVISO_data.variables['sla'][0,:,720:]
        #sla=np.hstack((data2,data1))[jmin:jmax,imin:imax]
        sladata =np.hstack((data2,data1))#读取tif数据中的数据集     
        #sladata = band.ReadAsArray()[::-1]#获得sla值
        sladata_copy=np.ma.copy(sladata)
        XSize=len(sladata)
        YSize=len(sladata[0])
        pixelwidth=0.25#round(GT[1],2)
        pixelheigh=-0.25#round(GT[5],2)
        originX=180.5#GT[0]+180+0.25+0.125
        originY=-89.875#GT[3]
        end_X=540.5#originX + pixelwidth*XSize
        end_Y=90.125#originY - pixelheigh*YSize
        
        exstra_range=int(outer_range/pixelwidth)
        #将经度方向靠近0度位置部分数据复制到360度左边
        sladata=np.hstack((sladata,sladata[:,0:exstra_range]))
        #将经度方向靠近360度位置部分数据复制到0度右边
        end_exstra_sladata=sladata_copy[:,len(sladata_copy[0])-1-exstra_range:len(sladata_copy[0])-1]
        sladata=np.hstack((end_exstra_sladata,sladata))
 
        #pdb.set_trace()  
        udata =np.hstack((AVISO_data.variables['ugosa'][0,:,720:],AVISO_data.variables['ugosa'][0,:,:720]))#读取tif数据中的数据集      
        udata=np.hstack((udata,udata[:,0:exstra_range])) 
        vdata = np.hstack((AVISO_data.variables['vgosa'][0,:,720:],AVISO_data.variables['vgosa'][0,:,:720]))
        #AVISO_data.variables['vgosa'][0]#获得v值  
        vdata=np.hstack((vdata,vdata[:,0:exstra_range]))    

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

        lon,lat=lon_lat_block(lon1,lat1,lat_block_num,lon_block_num,lon_inner,lat_inner,outer_range)

        
        #对无效值进行处理
        #mask=abs(sladata)>100 
        nan_mask = ~np.isfinite(sladata)  # NaN and infinite values
        extreme_mask = abs(sladata) > 100  # Extreme physical values
        mask = nan_mask | extreme_mask
        
        
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
        
        

        outdir=eddy_select_info['outfile']  +str(filedate)  #创建json文件保存路径
        if not os.path.exists(outdir): #判断该路径是否存在
            os.makedirs(outdir)
        outfile_temp=outdir+'\\eddy_info'    #+'.'+str(lat_block_num)+'.'+str(lon_block_num)+'.'+str(outer_range)    
        #eddy_detect_parameter_outjson=outdir+'\\eddy_detect_parameter_'+filedate+'.json'
        #eddy_detect_parameter(eddy_select_info,eddy_detect_parameter_outjson)

        
        """
        新添加直接识别全球种子点
        """
        #
        A_eddy_dic=OrderedDict()
        
        lonmin, lonmax, latmin, latmax=0,360,-90,90#3,6,42,44 # 99,150,-12,35#
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
        #print (local_extrema.shape,local_extrema)
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
        json.dump(A_eddy_dic,open(seedjson,'w'))
        #        
        print("成功建种子点json")
        """
        全球种子点识别完毕
        """
 
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
#           if block_i=='3_3':
#               print (Blockdic[block_i])
               pool.apply_async(eddy_main,(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info,))
#           eddy_main(sladata,udata,vdata,filedate,Blockdic[block_i],outer_range,eddy_pixel_num_range,Origin_Data_info)
#             
        pool.close()
        pool.join()
#        

        end_time = time.time()

        elapsed_time = end_time - start_time
        print("程序运行时间: {:.6f} 秒".format(elapsed_time))

        
        outjsons=[]
        for block_i in Blockdic:
             outjsons.append(Blockdic[block_i]['outfnj'])
        mergejson=eddyjson_merge(outjsons,lon,lat,outer_range,outdir,filedate,eddy_select_info,sladata)
            
        reject(mergejson,seedjson)
        print("success")
        print ('Duration', str((time.time() - start_time) ), 'seconds!')


