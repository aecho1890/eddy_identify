# -*- coding: utf-8 -*-
"""
Created on Wed Dec 30 15:04:44 2015

@author: HXM
"""

import numpy as np
import scipy.ndimage.filters as filters
import scipy.ndimage.morphology as morphology
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import generate_binary_structure, binary_erosion
from scipy import ndimage
def detect_local_minima(arr):
    """
    Takes an array and detects the troughs using the local maximum filter.
    Returns a boolean mask of the troughs (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)
    http://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array/3689710#3689710
    """
    #print ('detect_local_minima')用到了
    neighborhood = morphology.generate_binary_structure(len(arr.shape), 2)
    local_min = (filters.minimum_filter(arr, footprint=neighborhood) == arr)
    background = (arr == 0)
    eroded_background = morphology.binary_erosion(
        background, structure=neighborhood, border_value=1)
    detected_minima = local_min - eroded_background
    return detected_minima
    
#a=np.random.random((3,3)) 
#print('aa',a)
#b=a-ndimage.gaussian_filter(a, [-50, 50.0])
#local_extrema1 = np.ma.copy(a)
#local_extrema1 = np.reshape(local_extrema1, (a.shape))
#local_extrema_ac1= detect_local_minima(-local_extrema1)
#print('local_extrema_ac1',local_extrema_ac1)
##inner_ac_seed_j1, inner_ac_seed_i1 = np.where(local_extrema_ac1)
#local_extrema2= np.ma.copy(b)
#local_extrema2= np.reshape(local_extrema2, (b.shape))
#local_extrema_ac2= detect_local_minima(-local_extrema2)
#print('bb',b)
#print('local_extrema_ac2',local_extrema_ac2)

#for n in range(len(inner_ac_seed_j)):
#        lmi = inner_ac_seed_i[n] 
#        lmj = inner_ac_seed_j[n]
#        seed_sla=a[lmj][lmi]
#        print('seed_sla',seed_sla)
