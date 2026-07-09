import numpy as np
from math import *
# import pdb
#import haversine_distmat as hav_c

def  haversine(lon1,lat1,lon2,lat2):  
    d2r = atan2(0.0,-1.0)/ 180.0
    dlat = d2r * (lat2 - lat1)
    dlon = d2r * (lon2 - lon1)
    lt1 = d2r * lat1
    lt2 = d2r * lat2
    a= sin(0.5 * dlon) * sin(0.5 * dlon)
    a = a * cos(lt1) * cos(lt2)
    a = a + (sin(0.5 * dlat) * sin(0.5 * dlat))
    thedist = 2 * atan2(sqrt(a), sqrt(1 - a))
    #print 'myhaversine'
#    thedist= hav_c.haversine(lon1,lat1,lon2,lat2)
    return thedist
    
 
  
#def waypoint(lonin,latin,anglein,distin): #
##    erad = 6371315.0
##    d2r = atan2(0.0,-1.0)/ 180.0
##    d_r = distin / erad
##    thelon = d2r * lonin
##    thelat = d2r * latin
##    angle = d2r * anglein
##    lt1 = asin(sin(thelat) * cos(d_r) + cos(thelat) * sin(d_r) * cos(angle))
##    ln1 = atan2(sin(angle) * sin(d_r) * cos(thelat), cos(d_r) - sin(thelat) * sin(lt1))
##    ln1 = ln1 + thelon
##    lat=lt1 / d2r
##    lon=ln1 / d2r
#    lat= hav_c.waypoint_lat(lonin,latin,anglein,distin)
#    lon= hav_c.waypoint_lon(lonin,latin,anglein,distin)
#    #print 'mywaypoint'
#    return lon, lat
    
   
    
def haversine_distvec(lon1,lat1,lon2,lat2):  #
    erad = 6371315.0
    dist= np.empty(len(lon1))
    for i in range(len(lon1)):
        thedist=haversine(lon1[i], lat1[i], lon2[i], lat2[i])
        dist[i]= thedist* erad
    #print 'myhaversine_distvec'
    return dist
   
       
#def waypoint_vec(lonin,latin,anglein,distin):#
#    point_lon= np.empty(len(lonin))
#    point_lat= np.empty(len(lonin))
#    for i in range(len(lonin)):
#        thelon,thelat=waypoint(lonin[i],latin[i],anglein[i],distin[i])
#        point_lon[i]=thelon
#        point_lat[i]=thelat
#    #print 'mywaypoint_vec'
#    return point_lon,point_lat
	
    
#def haversine_dist(lon1,lat1,lon2,lat2):  #not use
##    pdb.set_trace()
##    erad = 6371315.0
##    thedist=haversine(lon1, lat1, lon2, lat2)
##    thedist = thedist * erad
#    thedist=hav_c.haversine_dist(lon1,lat1,lon2,lat2)
#    #print 'haversine_dist'
#    return thedist    
#    
#def  haversine_distmat(xa,xb): #not use
##    pdb.set_trace()
#    erad = 6371315.0
#    dist= np.empty((len(xa[0]),len(xb[0])))
#    for j in range(len(xa[0])):
#        for i in range(len(xb[0])):
#            thedist=haversine(xa[j][0], xa[j][1], xb[i][0], xb[i][1])
#            dist[j][i] = thedist* erad
#    #print 'haversine_distmat'
#    return dist      
#    
    
    
    
    
    
    
    
    
  
  