from matplotlib import rc
from streamlines import streamplot
from streamlines import fstreamplot
#rc('verbose', level='debug')
#rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## for Palatino and other serif fonts use:
#rc('font',**{'family':'serif','serif':['Palatino']})
#rc('mathtext',fontset='cm')
#rc('mathtext',rm='stix')
#rc('text', usetex=True)

#from pylab import figure, axes, plot, xlabel, ylabel, title, grid, savefig, show

import gc
import numpy as np
import array
#import scipy as sc
from scipy.interpolate import griddata
from scipy.interpolate import interp1d
#from scipy.interpolate import Rbf
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
from matplotlib import mpl
from matplotlib import cm
from numpy import ma
import matplotlib.colors as colors
import os,glob
import pylab
import sys
import streamlines
from matplotlib.patches import Ellipse

#from matplotlib.pyplot import *
#from numpy import *
#from mpl_toolkits.axisartist import *

#global rho, ug, vu, uu, B, CS
#global nx,ny,nz,_dx1,_dx2,_dx3,ti,tj,tk,x1,x2,x3,r,h,ph,gdet,conn,gn3,gv3,ck,dxdxp

def get2davg(usedefault=0,whichgroup=-1,whichgroups=-1,whichgroupe=-1,itemspergroup=20):
    if whichgroup >= 0:
        whichgroups = whichgroup
        whichgroupe = whichgroup + 1
    elif whichgroupe < 0:
        whichgroupe = whichgroups + 1
    #check values for sanity
    if usedefault == 0 and (whichgroups < 0 or whichgroupe < 0 or whichgroups >= whichgroupe or itemspergroup <= 0):
        print( "whichgroups = %d, whichgroupe = %d, itemspergroup = %d not allowed" 
               % (whichgroups, whichgroupe, itemspergroup) )
        return None
    #
    if usedefault:
        fname = "avg2d.npy"
    else:
        fname = "avg2d%02d_%04d_%04d.npy" % (itemspergroup, whichgroups, whichgroupe)
    if os.path.isfile( fname ):
        print( "File %s exists, loading from file..." % fname )
        avgtot=np.load( fname )
        return( avgtot )
    n2avg = 0
    nitems = 0
    myrange = np.arange(whichgroups,whichgroupe)
    numrange = myrange.shape[0]
    for (i,g) in enumerate(myrange):
        avgone=get2davgone( whichgroup = g, itemspergroup = itemspergroup )
        if avgone == None:
            continue
        if 0==i:
            avgtot = np.zeros_like(avgone)
            ts=avgone[0,0,0]
        tf=avgone[0,1,0]
        avgtot += avgone
        nitems += avgone[0,2,0]
        n2avg += 1
    avgtot[0,0,0] = ts
    avgtot[0,1,0] = tf
    avgtot[0,2,0] = nitems
    #get the average
    if n2avg == 0:
        print( "0 total files, so no data generated." )
        return( None )
    #avoid renormalizing the header
    avgtot[1:] /= n2avg
    #only save if more than 1 dump
    if n2avg > 1:
        print( "Saving data to file..." )
        np.save( fname, avgtot )
    return( avgtot )
    
def assignavg2dvars(avgmem):
    global avg_ts,avg_te,avg_nitems,avg_rho,avg_ug,avg_bsq,avg_unb,avg_uu,avg_bu,avg_ud,avg_bd,avg_B,avg_gdetB,avg_omegaf2,avg_rhouu,avg_rhobu,avg_rhoud,avg_rhobd,avg_uguu,avg_ugud,avg_Tud,avg_fdd,avg_rhouuud,avg_uguuud,avg_bsquuud,avg_bubd,avg_uuud
    global avg_TudEM, avg_TudMA, avg_mu, avg_sigma, avg_bsqorho, avg_absB, avg_absgdetB, avg_psisq
    global avg_gamma
    #avg defs
    i=0
    avg_ts=avgmem[i,0,:];
    avg_te=avgmem[i,1,:]; 
    avg_nitems=avgmem[i,2,:];i+=1
    #quantities
    avg_rho=avgmem[i,:,:,None];i+=1
    avg_ug=avgmem[i,:,:,None];i+=1
    avg_bsq=avgmem[i,:,:,None];i+=1
    avg_unb=avgmem[i,:,:,None];i+=1
    n=4
    avg_uu=avgmem[i:i+n,:,:,None];i+=n
    avg_bu=avgmem[i:i+n,:,:,None];i+=n
    avg_ud=avgmem[i:i+n,:,:,None];i+=n
    avg_bd=avgmem[i:i+n,:,:,None];i+=n
    #cell-centered magnetic field components
    n=3;
    avg_B=avgmem[i:i+n,:,:,None];i+=n
    avg_gdetB=avgmem[i:i+n,:,:,None];i+=n
    avg_omegaf2=avgmem[i,:,:,None];i+=1
    #
    n=4
    avg_rhouu=avgmem[i:i+n,:,:,None];i+=n
    avg_rhobu=avgmem[i:i+n,:,:,None];i+=n
    avg_rhoud=avgmem[i:i+n,:,:,None];i+=n
    avg_rhobd=avgmem[i:i+n,:,:,None];i+=n
    avg_uguu=avgmem[i:i+n,:,:,None];i+=n
    avg_ugud=avgmem[i:i+n,:,:,None];i+=n
    #
    n=16
    #energy fluxes and faraday
    avg_Tud=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
    avg_fdd=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
    # part1: rho u^m u_l
    avg_rhouuud=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
    # part2: u u^m u_l
    avg_uguuud=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
    # part3: b^2 u^m u_l
    avg_bsquuud=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
    # part6: b^m b_l
    avg_bubd=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
    # u^m u_l
    #print( "i = %d, avgmem.shape[0] = %d " % (i, avgmem.shape[0]) )
    #sys.stdout.flush()
    avg_uuud=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
    #new format, extra columns
    if( avgmem.shape[0] > 164 ):
        n=16
        #EM/MA
        avg_TudEM=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
        avg_TudMA=avgmem[i:i+n,:,:,None].reshape((4,4,nx,ny,1));i+=n
        #mu,sigma
        n=1
        avg_mu=avgmem[i,:,:,None];i+=n
        avg_sigma=avgmem[i,:,:,None];i+=n
        avg_bsqorho=avgmem[i,:,:,None];i+=n
        n=3
        avg_absB=avgmem[i:i+n,:,:,None];i+=n
        avg_absgdetB=avgmem[i:i+n,:,:,None];i+=n
        if( avgmem.shape[0] > 205 ):
            n=1
            avg_psisq=avgmem[i,:,:,None];i+=n
        else:
            n=1
            print( "Old-ish format: missing avg_psisq, filling it in with zeros." )
            avg_psisq=np.zeros_like(avg_mu);i+=n

    else:
        print( "Old format: missing avg_TudEM, avg_TudMA, avg_mu, avg_sigma, avg_bsqorho, etc." )
    #derived quantities
    avg_gamma=avg_uu[0]/(-gn3[0,0])**0.5


def get2davgone(whichgroup=-1,itemspergroup=20):
    """
    """
    global avg_ts,avg_te,avg_nitems,avg_rho,avg_ug,avg_bsq,avg_unb,avg_uu,avg_bu,avg_ud,avg_bd,avg_B,avg_gdetB,avg_omegaf2,avg_rhouu,avg_rhobu,avg_rhoud,avg_rhobd,avg_uguu,avg_ugud,avg_Tud,avg_fdd,avg_rhouuud,avg_uguuud,avg_bsquuud,avg_bubd,avg_uuud
    global avg_TudEM, avg_TudMA, avg_mu, avg_sigma, avg_bsqorho, avg_absB, avg_absgdetB, avg_psisq
    if whichgroup < 0 or itemspergroup <= 0:
        print( "whichgroup = %d, itemspergroup = %d not allowed" % (whichgroup, itemspergroup) )
        return None
    fname = "avg2d%02d_%02d.npy" % (itemspergroup, whichgroup)
    if os.path.isfile( fname ):
        print( "File %s exists, loading from file..." % fname )
        avgmem=np.load( fname )
        return( avgmem )
    tiny=np.finfo(rho.dtype).tiny
    flist = glob.glob( os.path.join("dumps/", "fieldline*.bin") )
    flist.sort()
    #
    #print "Number of time slices: %d" % flist.shape[0]
    #store 2D data
    navg=206
    avgmem=np.zeros((navg,nx,ny),dtype=np.float32)
    assignavg2dvars(avgmem)
    ##
    ######################################
    ##
    ## NEED TO ADD vmin/vmax VELOCITY COMPONENTS
    ##
    ######################################
    ##
    #print "Total number of quantities: %d" % (i)
    print "Doing %d-th group of %d items" % (whichgroup, itemspergroup)
    sys.stdout.flush()
    #end avg defs
    for fldindex, fldname in enumerate(flist):
        if( whichgroup >=0 and itemspergroup > 0 ):
            if( fldindex / itemspergroup != whichgroup ):
                continue
        print( "Reading " + fldname + " ..." )
        sys.stdout.flush()
        rfd("../"+fldname)
        print( "Computing " + fldname + " ..." )
        sys.stdout.flush()
        cvel()
        Tcalcud()
        faraday()
        #if first item in group
        if fldindex == itemspergroup * whichgroup:
            avg_ts[0]=t
        #if last item in group
        if fldindex == itemspergroup * whichgroup + (itemspergroup - 1):
            avg_te[0]=t
        avg_nitems[0]+=1
        #quantities
        avg_rho+=rho.sum(-1)[:,:,None]
        avg_ug+=ug.sum(-1)[:,:,None]
        avg_bsq+=bsq.sum(-1)[:,:,None]
        enth=1+ug*gam/rho
        avg_unb+=(enth*ud[0]).sum(-1)[:,:,None]
        avg_uu+=uu.sum(-1)[:,:,:,None]
        avg_bu+=bu.sum(-1)[:,:,:,None]
        avg_ud+=ud.sum(-1)[:,:,:,None]
        avg_bd+=bd.sum(-1)[:,:,:,None]
        #cell-centered magnetic field components
        n=3;
        avg_B+=B[1:4].sum(-1)[:,:,:,None]
        avg_gdetB+=gdetB[1:4].sum(-1)[:,:,:,None]
        #
        avg_omegaf2+=omegaf2.sum(-1)[:,:,None]
        #
        n=4
        avg_rhouu+=(rho*uu).sum(-1)[:,:,:,None]
        avg_rhobu+=(rho*bu).sum(-1)[:,:,:,None]
        avg_rhoud+=(rho*ud).sum(-1)[:,:,:,None]
        avg_rhobd+=(rho*bd).sum(-1)[:,:,:,None]
        avg_uguu+=(ug*uu).sum(-1)[:,:,:,None]
        avg_ugud+=(ug*ud).sum(-1)[:,:,:,None]
        #
        n=16
        #energy fluxes and faraday
        avg_Tud+=Tud.sum(-1)[:,:,:,:,None]
        avg_fdd+=fdd.sum(-1)[:,:,:,:,None]
        #
        uuud=odot(uu,ud).sum(-1)[:,:,:,:,None]
        # part1: rho u^m u_l
        avg_rhouuud+=rho.sum(-1)[:,:,None]*uuud
        # part2: u u^m u_l
        avg_uguuud+=ug.sum(-1)[:,:,None]*uuud
        # part3: b^2 u^m u_l
        avg_bsquuud+=bsq.sum(-1)[:,:,None]*uuud
        # part6: b^m b_l
        avg_bubd+=odot(bu,bd)[:,:,:,:,None].sum(-1)
        # u^m u_l
        avg_uuud+=uuud
        #EM/MA
        avg_TudEM+=TudEM.sum(-1)[:,:,:,:,None]
        avg_TudMA+=TudMA.sum(-1)[:,:,:,:,None]
        #mu,sigma
        avg_mu += (-Tud[1,0]/(rho*uu[1])).sum(-1)[:,:,None]
        avg_sigma += (-TudEM[1,0]/TudMA[1,0]).sum(-1)[:,:,None]
        avg_bsqorho += (bsq/rho).sum(-1)[:,:,None]
        n=3
        avg_absB += np.abs(B[1:4]).sum(-1)[:,:,:,None]
        avg_absgdetB += np.abs(gdetB[1:4]).sum(-1)[:,:,:,None]
        n=1
        aphi = fieldcalcface()
        avg_psisq += ((_dx3*aphi.sum(-1))**2)[:,:,None]
    if avg_nitems[0] == 0:
        print( "No files found" )
        return None
    #divide all lines but the header line [which holds (ts,te,nitems)]
    #by the number of elements to get time averages
    avgmem[1:]/=(np.float32(avg_nitems[0])*np.float32(nz))
    print( "Saving to file..." )
    np.save( fname, avgmem )
    print( "Done!" )
    return(avgmem)

def extractlena():
    #along field lines 0.5,0.8,0.99
    cvel()
    Tcalcud()
    faraday()
    psi=fieldcalctoth()/dxdxp[3][3][:,:,0]
    #
    Br = dxdxp[1,1]*B[1]+dxdxp[1,2]*B[2]
    Bh = dxdxp[2,1]*B[1]+dxdxp[2,2]*B[2]
    Bp = B[3]*dxdxp[3,3]
    #
    Brnorm=Br
    Bhnorm=Bh*np.abs(r)
    Bpnorm=Bp*np.abs(r*np.sin(h))
    #
    Bznorm=Brnorm*np.cos(h)-Bhnorm*np.sin(h)
    BRnorm=Brnorm*np.sin(h)+Bhnorm*np.cos(h)
    #
    eta=rho*uu[1]/B[1]
    #
    z = -r*np.cos(h)
    R = r*np.sin(h)
    #
    uur = dxdxp[1,1]*uu[1]+dxdxp[1,2]*uu[2]
    uuh = dxdxp[2,1]*uu[1]+dxdxp[2,2]*uu[2]
    uup = uu[3] * dxdxp[3,3]
    #
    uurnorm = uur
    uuhnorm=uuh*np.abs(r)
    uupnorm=uup*np.abs(r*np.sin(h))
    #
    #(cpsi, cr, ch, cR, cz, cBr, cBtheta, cBphi, ceta, crho, cuur, cuutheta, cuuphi, cgamma, comegaf, cmu, csigma, cbsq) = cvals

    vals = (psi, r, h, R, z, -Brnorm, -Bhnorm, -Bpnorm, -eta, rho, uurnorm, uuhnorm, uupnorm, gamma, omegaf2*dxdxp[3][3], mu, sigma, bsq)
    nu = 1.0
    om0 = 0.75

    for psi0 in (0.2, 0.4, 0.6, 0.8, 0.9, 0.99, 1.0):
        #FIELDLINE: psi = psi0
        fname = "fieldline_nu%0.3g_om%0.2g_psi%0.3g.dat" % (nu, om0, psi0)
        print( "Doing psi = %0.3g, fname = %s" % (psi0, fname) )
        sys.stdout.flush()
        cvals = findroot2d(psi-psi0, vals, axis = 0 )
        fp = open( fname, "wt" )
        fp.write( "#psi, r, \\theta, R, z, B^r, B^\\theta, B^\\phi, \\eta, rho, u^r, u^\\theta, u^\\phi, \\gamma, \\Omega_F, \\mu, \\sigma, b^2 = B^2-E^2\n" )
        fp.flush()
        os.fsync(fp.fileno())
        np.savetxt( fp, np.array(cvals,dtype=np.float64).transpose(), fmt='%21.15g' )
        fp.close()

    for z0 in (10, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 5e10):
        #FIELDLINE: psi = psi0
        fname = "fieldline_nu%0.3g_om%0.3g_z%0.3g.dat" % (nu, om0, z0)
        print( "Doing z0 = %0.3g, fname = %s" % (z0, fname) )
        sys.stdout.flush()
        cvals = findroot2d(z-z0, vals, axis = 1 )
        fp = open( fname, "wt" )
        fp.write( "#psi, r, \\theta, R, z, B^r, B^\\theta, B^\\phi, \\eta, rho, u^r, u^\\theta, u^\\phi, \\gamma, \\Omega_F, \\mu, \\sigma, b^2 = B^2-E^2\n" )
        fp.flush()
        os.fsync(fp.fileno())
        np.savetxt( fp, np.array(cvals,dtype=np.float64).transpose(), fmt='%21.15g' )
        fp.close()

def readlena(fname):
    global cpsi, cr, ch, cR, cz, cBr, cBtheta, cBphi, ceta, crho, cuur, cuutheta, cuuphi, cgamma, comegaf, cmu, csigma, cbsq
    cvals = np.loadtxt( fname, 
                      dtype=np.float64, 
                      skiprows=1, 
                      unpack = True )
    cpsi, cr, ch, cR, cz, cBr, cBtheta, cBphi, ceta, crho, cuur, cuutheta, cuuphi, cgamma, comegaf, cmu, csigma, cbsq = cvals    
    return(cvals)

def findroot2d( fin, xin, isleft=True, nbnd = 1, axis = 0, fallback = 0, fallbackval = 0 ):
    """ returns roots, y(x), so that f(x,y(x)) = 0 (here axis = 0)
        (axis selects independent variable)
    """
    if fin.ndim == 3:
        fin = fin[:,:,0]
    if fin.ndim != 2:
        raise( ValueError( "fin.ndim = %d, should be 2" % fin.ndim ) )
    if axis == 1:
        f = fin.transpose()
    else:
        f = fin
    if not isinstance(xin,tuple):
        xtuple = (xin,)
    else:
        xtuple = xin
    xout = ()
    for (j, x) in enumerate(xtuple):
        if x.ndim == 3:
            x = x[:,:,0]
        if x.ndim != 2:
            raise( ValueError( "x[%d].ndim = %d, should be 2" % (j, x.ndim) ) )
        n = f.shape[0]
        if axis == 1:
            x = x.transpose()
        if f.shape != x.shape:
            raise( ValueError( "f and x have different shapes" ) )
        xsol = np.empty((n),dtype=f.dtype)
        for i in np.arange(0,n):
            xsol[i] = findroot1d( f[i], x[i], isleft, nbnd, fallback, fallbackval )
        xout += (xsol,)
    if len(xout) == 1:
        return( xout[0] )
    else:
        return( xout )
        
    
def findroot1d( f, x, isleft=True, nbnd = 1, fallback = 0, fallbackval = 0 ):
    """ find a 1-D root """
    #fallback=1
    if isleft==True:
        ind=0
        dir=1
    else:
        ind=-1
        dir=-1
    if f[ind] > 0:
        coef = 1
    else:
        coef = -1
    #multiplies the final function so f is increasing
    #otherwise scipy gives an error
    if isleft == False:
        interpcoef = coef
    else:
        interpcoef = -coef
    n = x.shape[0]
    ilist = np.arange(0,n)
    indexlist = f*coef<0
    if( not indexlist.any() ):
        if not fallback:
            return( float('nan') )
        else:
            return( fallbackval )
    i0 = ilist[indexlist][ind]
    if f[i0]*f[i0-dir] > 0:
        raise( ValueError("Could not bracket root") )
    ir = i0 + nbnd*dir
    il = i0 - (nbnd+1)*dir
    #limit il, ir to be between 0 and n-1:
    ir = max(0,min(ir,n-1))
    il = max(0,min(il,n-1))
    #order them
    istart = min(il,ir)
    iend = max(il,ir)
    kind = 'linear'
    x2interp = x[istart:iend+1]
    f2interp = interpcoef*f[istart:iend+1]
    #
    if f2interp.shape[0] < 4 or (f2interp[:-1]>=f2interp[1:]).any():
        #too few elements or non-monotonic behavior
        ir = i0 
        il = i0 - dir
        #limit il, ir to be between 0 and n-1:
        ir = max(0,min(ir,n-1))
        il = max(0,min(il,n-1))
        #order them
        istart = min(il,ir)
        iend = max(il,ir)
        kind = 'linear'
        x2interp = x[istart:iend+1]
        f2interp = interpcoef*f[istart:iend+1]
    #
    if f2interp.shape[0]==1:
        #too few elements
        kind='nearest'
        raise( "Too few entries" )
        xinterp = interp1d( f2interp, x2interp, kind=kind, copy = False )
    else:
        xinterp = interp1d( f2interp, x2interp, kind=kind, copy = False )
    ans = xinterp(0.0)
    #if ans < min(x[i0],x[i0-dir]) or ans > max(x[i0],x[i0-dir]):
    #    raise( ValueError("ans = %g out of bounds, (%g,%g)" % (ans,x[i0-dir],x[i0])) )
    return( ans )

def plot2davg(dosq=True,whichplot=-1):
    global eout1, eout2, eout, avg_aphi,avg_aphi2,powjetwind,powjet,jminjet,jmaxjet,jminwind,jmaxwind,mymu,maxaphibh
    #use ratio of averages since more stable definition:
    #
    etad = np.zeros_like(uu)
    etad[0] = -1/(-gn3[0,0])**0.5
    avg_mu = -avg_Tud[1,0] / avg_rhouu[1]
    avg_bsqo2rho = avg_bsqorho*0.5
    avg_unb = avg_TudMA[1,0] / avg_rhouu[1]
    #sum away from theta = 0
    muminwind= 1. #1./(1.-0.1**2)**0.5
    muminjet=2.0
    unbcutoff=0 #1./(1.-0.1**2)**0.5-1
    rhor=1+(1-a**2)**0.5
    ihor=iofr(rhor)
    #
    qtymem=getqtyvstime(ihor,0.2)
    if avg_ts[0] != 0:
        fti = avg_ts[0]
    else:
        fti = 8000
    if avg_te[0] != 0:
        ftf = avg_te[0]
    else:
        ftf = 1e5
    print( "Using: ti = %g, tf = %g" % (fti,ftf) )
    md, ftot, fsqtot, f30, fsq30, pjemtot  = plotqtyvstime(qtymem,ihor=ihor,whichplot=-1,fti=fti,ftf=ftf)
    #
    avg_aphi = scaletofullwedge(nz*_dx3*fieldcalc(gdetB1=avg_gdetB[0]))
    avg_aphi2 = scaletofullwedge((nz*avg_psisq)**0.5)
    #aphi1 = scaletofullwedge(_dx3*_dx2*(avg_gdetB[0]).cumsum(1))
    #aphi2 = scaletofullwedge(-_dx3*_dx2*(avg_gdetB[0])[:,::-1].cumsum(1)[:,::-1])
    aphi = avg_aphi if dosq==True else avg_aphi
    aphi1 = aphi
    aphi2 = aphi
    maxaphibh = np.max(aphi[ihor])
    mdotden    = scaletofullwedge(nz*(-gdet*avg_rhouu[1]*_dx2*_dx3).sum(axis=2))
    mdottot       = mdotden.sum(-1)
    #
    eout1den   = scaletofullwedge(nz*(-gdet*avg_Tud[1,0]*_dx2*_dx3).sum(axis=2))
    eout1denEM = scaletofullwedge(nz*(-gdet*avg_TudEM[1,0]*_dx2*_dx3).sum(axis=2))
    eout1denMA = scaletofullwedge(nz*(-gdet*avg_TudMA[1,0]*_dx2*_dx3).sum(axis=2))
    #subtract off rest-energy flux
    eout1denKE = scaletofullwedge(nz*(gdet*(-avg_TudMA[1,0]-avg_rhouu[1])*_dx2*_dx3).sum(axis=2))
    #eout1den=eout1denEM+eout1denMA
    #eout1   = eout1den.cumsum(axis=1)
    eoutEM1 = eout1denEM.cumsum(axis=1)
    eoutEMtot = eout1denEM.sum(axis=1)[ihor]
    eoutMA1 = eout1denMA.cumsum(axis=1)
    eoutKE1 = eout1denKE.cumsum(axis=1)
    eout1 = eoutEM1+eoutMA1
    eouttot = eout1den.sum(axis=-1)
    #sum from from theta = pi
    eout2den   = scaletofullwedge(nz*(-gdet*avg_Tud[1,0]*_dx2*_dx3)[:,::-1].sum(axis=2))
    eout2denEM = scaletofullwedge(nz*(-gdet*avg_TudEM[1,0]*_dx2*_dx3)[:,::-1].sum(axis=2))
    eout2denMA = scaletofullwedge(nz*(-gdet*avg_TudMA[1,0]*_dx2*_dx3)[:,::-1].sum(axis=2))
    eout2denKE = scaletofullwedge(nz*(gdet*(-avg_TudMA[1,0]-avg_rhouu[1])*_dx2*_dx3).sum(axis=2))
    #eout2den=eout2denEM+eout2denMA
    #eout2   = eout2den.cumsum(axis=1)[:,::-1]
    eoutEM2 = eout2denEM.cumsum(axis=1)[:,::-1]
    eoutMA2 = eout2denMA.cumsum(axis=1)[:,::-1]
    eoutKE2 = eout2denKE.cumsum(axis=1)[:,::-1]
    eout2 = eoutEM2+eoutMA2
    eout = np.zeros_like(eout1)
    eout[tj[:,:,0]>ny/2] = eout2[tj[:,:,0]>ny/2]
    eout[tj[:,:,0]<=ny/2] = eout1[tj[:,:,0]<=ny/2]
    eoutden = np.zeros_like(eout1den)
    eoutden[tj[:,:,0]>ny/2] = eout2den[tj[:,:,0]>ny/2]
    eoutden[tj[:,:,0]<=ny/2] = eout1den[tj[:,:,0]<=ny/2]
    eoutdenEM = np.zeros_like(eout1denEM)
    eoutdenEM[tj[:,:,0]>ny/2] = eout2denEM[tj[:,:,0]>ny/2]
    eoutdenEM[tj[:,:,0]<=ny/2] = eout1denEM[tj[:,:,0]<=ny/2]
    aphip1 = np.zeros((aphi.shape[0],aphi.shape[1]+1,aphi.shape[2]))    
    aphip1[:,0:ny] = aphi
    daphi = np.zeros_like(ti)
    daphi[:,0:ny]=aphip1[:,1:ny+1]-aphip1[:,0:ny]
    mdot = scaletofullwedge(nz*(gdet*avg_rhouu[1]*_dx2*_dx3)).sum(-1).sum(-1)
    #
    mymu = np.copy(avg_mu)
    mymu[(tj[:,:,0] > ny-10)+(tj[:,:,0] < 10)]=50
    mymu[mymu<1]=50
    #
    #tot
    if False:
        #keep same sign in jet
        hjet1aphia = findroot2d( (aphi1[:,:,0]-maxaphibh)*daphi[:,:,0], h, isleft=True, fallback = 1, fallbackval = np.pi/2 )
        hjet2aphia = findroot2d( (aphi2[:,:,0]-maxaphibh)*daphi[:,:,0], h, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    else:
        #allow different signs in jet
        hjet1aphia = findroot2d( (aphi1[:,:,0]-1*maxaphibh), h, isleft=True, fallback = 1, fallbackval = np.pi/2 )
        hjet2aphia = findroot2d( (aphi2[:,:,0]-1*maxaphibh), h, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    #hjet1aphia*=3
    #hjet2aphia=np.pi-(np.pi-hjet2aphia)*3
    hjet1aphi = np.copy(hjet1aphia)
    hjet2aphi = np.copy(hjet2aphia)
    if False:
        rx=1
        hjet1aphi[r[:,0,0]>rx] = findroot2d( -mymu[:,:,0]+muminjet, h, isleft=True, fallback = 1, fallbackval = np.pi/2  )[r[:,0,0]>rx]
        hjet2aphi[r[:,0,0]>rx] = findroot2d( -mymu[:,:,0]+muminjet, h, isleft=False, fallback = 1, fallbackval = np.pi/2  )[r[:,0,0]>rx]
        hjet1aphi = amin(hjet1aphi,hjet1aphia)
        hjet2aphi = amax(hjet2aphi,hjet2aphia)
        hwind1aphi = findroot2d( -mymu[:,:,0]+muminwind, h, isleft=True, fallback = 1, fallbackval = np.pi/2  )
        hwind2aphi = findroot2d( -mymu[:,:,0]+muminwind, h, isleft=False, fallback = 1, fallbackval = np.pi/2  )
    else:
        hwind1aphi = findroot2d( -avg_uu[1,:,0:ny/2,0], h[:,0:ny/2], isleft=False, fallback = 1, fallbackval = np.pi/2  )
        hwind2aphi = findroot2d( -avg_uu[1,:,ny/2:ny,0], h[:,ny/2:ny], isleft=True, fallback = 1, fallbackval = np.pi/2  )
    ################
    #WIND
    ################
    #
    powwind1 = findroot2d( h[:,:,0] - hwind1aphi[:,None], eout1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powwind2 = findroot2d( h[:,:,0] - hwind2aphi[:,None], eout2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powwind = powwind1+powwind2
    powwindEM1 = findroot2d( h[:,:,0] - hwind1aphi[:,None], eoutEM1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powwindEM2 = findroot2d( h[:,:,0] - hwind2aphi[:,None], eoutEM2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powwindEM = powwindEM1+powwindEM2
    powwindMA1 = findroot2d( h[:,:,0] - hwind1aphi[:,None], eoutMA1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powwindMA2 = findroot2d( h[:,:,0] - hwind2aphi[:,None], eoutMA2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powwindMA = powwindMA1+powwindMA2
    powwindEMKE1 = findroot2d( h[:,:,0] - hwind1aphi[:,None], eoutEM1+eoutKE1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powwindEMKE2 = findroot2d( h[:,:,0] - hwind2aphi[:,None], eoutEM2+eoutKE2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powwindEMKE = powwindEMKE1+powwindEMKE2
    powtot1 = eout1[:,ny/2-1]
    powtot2 = eout2[:,ny/2]
    powtot = powtot1 + powtot2
    powtotEM1 = eoutEM1[:,ny/2-1]
    powtotEM2 = eoutEM2[:,ny/2]
    powtotEM = powtotEM1 + powtotEM2
    powtotMA1 = eoutMA1[:,ny/2-1]
    powtotMA2 = eoutMA2[:,ny/2]
    powtotMA = powtotMA1 + powtotMA2
    #
    ################
    # JET
    ################
    #
    #Tot
    #
    powjet1 = findroot2d( h[:,:,0] - hjet1aphi[:,None], eout1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powjet2 = findroot2d( h[:,:,0] - hjet2aphi[:,None], eout2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powjet = powjet1+powjet2
    #
    #EM
    #
    powjetEM1 = findroot2d( h[:,:,0] - hjet1aphi[:,None], eoutEM1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powjetEM2 = findroot2d( h[:,:,0] - hjet2aphi[:,None], eoutEM2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powjetEM = powjetEM1+powjetEM2
    #
    #KE
    #
    powjetKE1 = findroot2d( h[:,:,0] - hjet1aphi[:,None], eoutKE1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powjetKE2 = findroot2d( h[:,:,0] - hjet2aphi[:,None], eoutKE2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powjetKE = powjetKE1+powjetKE2
    powjetEMKE1 = findroot2d( h[:,:,0] - hjet1aphi[:,None], eoutEM1+eoutKE1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powjetEMKE2 = findroot2d( h[:,:,0] - hjet2aphi[:,None], eoutEM2+eoutKE2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powjetEMKE = powjetEMKE1+powjetEMKE2
    #
    #MA
    #
    powjetMA1 = findroot2d( h[:,:,0] - hjet1aphi[:,None], eoutMA1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powjetMA2 = findroot2d( h[:,:,0] - hjet2aphi[:,None], eoutMA2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powjetMA = powjetMA1+powjetMA2
    #
    #################
    #
    # powjetEM1aphi = findroot2d( aphi1[:,:,0]-maxaphibh, eoutEM1, isleft=True )
    # powjetEM2aphi = findroot2d( aphi2[:,:,0]-maxaphibh, eoutEM2, isleft=False )
    # powjetEM1 = powjetEM1aphi
    # powjetEM2 = powjetEM2aphi
    # powjetEM = powjetEM1+powjetEM2
    #
    #powjetwind1a = findroot2d( (-avg_unb[:,:,0]-(1.0+unbcutoff))*(avg_uu[1,:,:,0]), eout1, isleft=True )
    #powjetwind2a = findroot2d( (-avg_unb[:,:,0]-(1.0+unbcutoff))*(avg_uu[1,:,:,0]), eout2, isleft=False )
    hjetwind1a = findroot2d( (-avg_unb[:,:,0]-(1.0+unbcutoff)), h, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    hjetwind2a = findroot2d( (-avg_unb[:,:,0]-(1.0+unbcutoff)), h, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    hjetwind1b = findroot2d( daphi[:,:,0], h, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    hjetwind2b = findroot2d( daphi[:,:,0], h, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    #limit jet+wind power to be no smaller than jet power
    if False:
        hjetwind1 = amin(hjetwind1b, hjetwind1a) #amax(powjet1,powjetwind1a)
        hjetwind2 = amax(hjetwind2b, hjetwind2a) #amax(powjet2,powjetwind2a)
    else:
        hjetwind1 = hjetwind1a
        hjetwind2 = hjetwind2a
    powjetwind1 = findroot2d( h-hjetwind1[:,None,None], eout1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powjetwind2 = findroot2d( h-hjetwind2[:,None,None], eout2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powjetwind = powjetwind1 + powjetwind2
    powjetwindEMKE1 = findroot2d( h-hjetwind1[:,None,None], eoutEM1+eoutKE1, isleft=True, fallback = 1, fallbackval = np.pi/2 )
    powjetwindEMKE2 = findroot2d( h-hjetwind2[:,None,None], eoutEM2+eoutKE2, isleft=False, fallback = 1, fallbackval = np.pi/2 )
    powjetwindEMKE = powjetwindEMKE1 + powjetwindEMKE2
    #
    #Write out power
    #
    rprintout = 100.
    powjetatr = powjetEMKE[iofr(rprintout)]
    powjetwindatr = powjetwindEMKE[iofr(rprintout)]
    powwindatr = powwindEMKE[iofr(rprintout)]
    print( "r = %g: Mdot = %g, etajet = %g, Pjet = %g, etawind = %g, Pwind = %g, Ftot = %g, Fsqtot = %g, pjemtot = %g, eoutEMtot = %g" % ( rprintout, md, powjetatr/md, powjetatr, powjetwindatr/md, powjetwindatr, ftot, fsqtot, pjemtot, eoutEMtot ) )
    foutpower = open( "pjet_2davg_%s.txt" %  os.path.basename(os.getcwd()), "w" )
    # radius of jet power measurement
    rjet=100.
    #
    printjetwindpower(filehandle = foutpower, r = rjet, stage = 0, powjet = powjet, powwind = powwind, muminjet = muminjet, muminwind = muminwind, md=md, powjetEMKE=powjetEMKE, powjetwindEMKE=powjetwindEMKE, 
                      ftot=ftot, fsqtot=fsqtot, f30=f30, fsq30=fsq30, pjemtot=pjemtot, eoutEMtot=eoutEMtot)
    printjetwindpower(filehandle = foutpower, r = 200., stage = 1, powjet = powjet, powwind = powwind, muminjet = muminjet, muminwind = muminwind, md=md, powjetEMKE=powjetEMKE, powjetwindEMKE=powjetwindEMKE)
    printjetwindpower(filehandle = foutpower, r = 400., stage = 2, powjet = powjet, powwind = powwind, muminjet = muminjet, muminwind = muminwind, md=md, powjetEMKE=powjetEMKE, powjetwindEMKE=powjetwindEMKE)
    foutpower.close()
    #HHH
    if whichplot==1:
        #Plot jet, wind, disk powers vs. r
        plt.figure(1)
        plt.clf()
        rhor=1+(1-a**2)**0.5
        r1d=r[:,0,0]
        plt.plot(r1d, powjet, 'b', lw=3,label=r"$P_{\rm j,tot}$")
        plt.plot(r1d, powjetEM, 'b', lw=1,label=r"$P_{\rm j,EM}$")
        plt.plot(r1d, powjetMA, 'b--',lw=1,label=r"$P_{\rm j,MA}$")
        cond=(r1d>5)
        plt.plot(r1d[cond], (powwind-powjet)[cond], 'g', lw=3, label=r"$P_{\rm w,tot}$")
        plt.plot(r1d[cond], (powwindEM-powjetEM)[cond], 'g', lw=1, label=r"$P_{\rm w,EM}$")
        plt.plot(r1d[cond], (powwindMA-powjetMA)[cond], 'g--',lw=1, label=r"$P_{\rm w,MA}$")
        plt.plot(r1d[cond], (powtot-powwind)[cond], 'c', lw=3, label=r"$P_{\rm d,tot}$")
        plt.plot(r1d[cond], (powtotEM-powwindEM)[cond], 'c', lw=1, label=r"$P_{\rm d,EM}$")
        plt.plot(r1d[cond], (powtotMA-powwindMA)[cond], 'c--',lw=1, label=r"$P_{\rm d,MA}$")
        plt.plot(r1d, (powtot-powjet), 'm', lw=3, label=r"$P_{\rm d+w,tot}$")
        plt.plot(r1d, (powtotEM-powjetEM), 'm', lw=1, label=r"$P_{\rm d+w,EM}$")
        plt.plot(r1d, (powtotMA-powjetMA), 'm--',lw=1, label=r"$P_{\rm d+w,MA}$")
        plt.plot(r1d, powtot, 'r', lw=3, label=r"$P_{\rm tot}$")
        plt.plot(r1d, powtotEM, 'r', lw=1, label=r"$P_{\rm tot,EM}$")
        plt.plot(r1d, powtotMA, 'r--',lw=1, label=r"$P_{\rm tot,MA}$")
        plt.plot(r1d, mdot, 'y',lw=3, label=r"$\dot M$")
        plt.legend(ncol=6)
        #plt.plot(r1d, powwind-powjet, label=r"$P_{\rm jet,tot}$")
        plt.xlim(rhor,35)
        plt.ylim(-20,30)
        plt.xlabel(r"$r\ [r_g]$",fontsize=16)
        plt.ylabel("Fluxes",fontsize=16)
        plt.grid()
        #
        plt.figure(2)
        plt.clf()
        #plco(aphi,xcoord=r*np.sin(h),ycoord=r*np.cos(h),colors='k',nc=30)
        #plc(daphi,xcoord=r*np.sin(h),ycoord=r*np.cos(h),levels=(0,),colors='r')
        d=500
        plt.xlim(0,d/2.); plt.ylim(-d,d)
        plc(aphi-maxaphibh,levels=(0,),colors='b',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hjet1aphi[:,None,None],levels=(0,),colors='m',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hjet2aphi[:,None,None],levels=(0,),colors='m',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hwind1aphi[:,None,None],levels=(0,),colors='c',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hwind2aphi[:,None,None],levels=(0,),colors='c',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(avg_uu[1,:,:,0],levels=(0,),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        #plc(h-hjetwind1[:,None,None],levels=(0,),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        #plc(h-hjetwind2[:,None,None],levels=(0,),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
     #
    if whichplot==-1:
        #PLOT EVERYTHING
        ##################
        #
        # FIGURE 1
        #
        ##################
        plt.figure(1)
        plt.clf()
        #plco( np.log10(avg_rho), cb=True )
        #plco(choplo(chophi(avg_mu,40),2),cb=True,nc=39)
        plco(avg_mu,levels=np.concatenate(((1.01,),np.arange(2,120,1.))),cb=True)
        #plc(avg_aphi,nc=30,cmap=cm.bone)
        #plc(avg_gamma,levels=np.arange(1.,3.4,0.1),cb=True)
        #
        #plt.clf()
        r1 = 250
        r2 = 1000
        ############
        #
        # FIG 2
        #
        ############
        plt.figure(2)
        plt.clf()
        gs3 = GridSpec(3, 3)
        #gs3.update(left=0.05, right=0.95, top=0.30, bottom=0.03, wspace=0.01, hspace=0.04)
        #mdot
        ax31 = plt.subplot(gs3[-3,:])
        #ymax=ax31.get_ylim()[1]
        #ymax=2*(np.floor(np.floor(ymax+1.5)/2))
        #ax31.set_yticks((ymax/2.0,ymax))
        i=iofr(r1)
        plt.plot( aphi[i,:,0]/maxaphibh, eout[i,:],'g-' )
        i=iofr(r2)
        plt.plot( aphi[i,:,0]/maxaphibh, eout[i,:],'b-' )
        plt.xlim( 0, 2 )
        plt.ylim( 0, 20 )
        plt.ylabel(r"$P_{\rm j,enc}(\Psi)$")
        ax31.grid(True)
        ax32 = plt.subplot(gs3[-2,:])
        i=iofr(r1)
        print i
        plt.plot( aphi[i,:,0]/maxaphibh, avg_mu[i,:],'g-' )
        plt.plot( aphi[i,:,0]/maxaphibh, avg_gamma[i,:]*(avg_bsqorho[i,:]+1),'g--' )
        i=iofr(r2)
        plt.plot( aphi[i,:,0]/maxaphibh, avg_mu[i,:], 'b-' )
        #somehow don't show up on plot; maybe make use of avg_bsquuud, etc.
        plt.plot( aphi[i,:,0]/maxaphibh, avg_ud[0,i,:]*((gam*avg_ug/avg_rho+avg_bsqorho)[i,:]+1),'b--' )
        plt.plot( aphi[i,:,0]/maxaphibh, avg_ud[0,i,:]*(-avg_sigma[i,:]+1),'b-.' )
        plt.xlim( 0, 2 )
        plt.ylim( 0, 10 )
        plt.ylabel(r"$\mu(\Psi)$")
        ax32.grid(True)
        ax33 = plt.subplot(gs3[-1,:])
        myunb = np.copy(avg_unb)
        myunb[-myunb<=1.+unbcutoff]=myunb[-myunb<=1.0+unbcutoff]*0
        i=iofr(r1)
        #plt.plot( aphi[i,:,0]/maxaphibh, avg_B[0,i,:]/(avg_rhouu[1,i]),'g-' )
        plt.plot( aphi[i,:,0]/maxaphibh, -myunb[i,:],'g-' )
        plt.plot( aphi[i,:,0]/maxaphibh, (avg_uu[1]*dxdxp[1,1])[i,:],'g--' )
        i=iofr(r2)
        #plt.plot( aphi[i,:,0]/maxaphibh, avg_B[0,i,:]/(avg_rhouu[1,i]),'b-' )
        plt.plot( aphi[i,:,0]/maxaphibh, -myunb[i,:],'b-' )
        plt.plot( aphi[i,:,0]/maxaphibh, (avg_uu[1]*dxdxp[1,1])[i,:],'b--' )
        plt.xlim( 0, 2 )
        plt.ylim( -0.5,2)
        plt.ylabel(r"$(1+u/\rho) u_t$")
        ax33.grid(True)
        #print maxaphibh
        #FIG 3
        plt.figure(3)
        plt.clf()
        i=iofr(r1)
        plt.plot( aphi[i,:]/maxaphibh, 'g' )
        plt.plot( aphi[i,:]/maxaphibh, 'gx' )
        i=iofr(r2)
        plt.plot( aphi[i,:]/maxaphibh, 'b' )
        plt.plot( aphi[i,:]/maxaphibh, 'bx' )
        plt.grid()
        ##############
        #
        #  FIGURE 5
        #
        ##############
        plt.figure(5)
        plt.clf()
        plt.plot(r[:,0,0],powjet,'m:',label=r'$P_{jet,EM+MA}$')
        #plt.plot(r[:,0,0],mdottot,'r')
        #plt.plot(r[:,0,0],powjet,'bx')
        plt.ylim(0,20)
        plt.xlim(rhor,30)
        #plt.plot(findroot2d(aphix[:,:,0]-maxaphibh,eout)+findroot2d(aphix[:,:,0]-maxaphibh,eout,isleft=False),'y--')
        #plt.plot(powxjet,'b--')
        #plt.plot(r[:,0,0],powxjetEM,'b--')
        #plt.plot(r[:,0,0],powxjetwind,'g')
        plt.plot(r[:,0,0],eouttot,'r',label=r'$P_{tot}$')
        plt.plot(r[:,0,0],powjetEM,'m-.',label=r'$P_{jet,EM}$')
        plt.plot(r[:,0,0],powjetKE,'m--',label=r'$P_{jet,KE}$')
        plt.plot(r[:,0,0],powjetEMKE,'m',label=r'$P_{jet,EMKE}$')
        #xxx
        #plt.plot(r[iofr(16):,0,0],powjetwind[iofr(16):],'g',label=r'$P_{unbound}(-u_t(1+\Gamma u_g/\rho)>1)$')
        #plt.plot(r[iofr(rjet):,0,0],powwind[iofr(rjet):],'c',label=r'$P_{jetwind}(\mu>1.005)$')
        plt.plot(r[iofr(10):,0,0],powjetwindEMKE[iofr(10):],'c--',label=r'$P_{jetwindEMKE}$')
        plt.legend(loc='upper right',ncol=3)
        plt.ylabel(r'Energy fluxes in jet region, $\mu>2$')
        plt.xlabel(r'$r$')
        #plt.plot(r[:,0,0],powjetEM+powjetMA,'k')
        plt.grid()
        plt.figure(8)
        plt.clf()
        plt.plot(r[:,0,0],hjet1aphi,'k')
        plt.plot(r[:,0,0],h[:,ny/4,0],'g')
        plt.plot(r[:,0,0],np.pi-hjet2aphi,'k:')
        plt.xlim(0,1500)
        #xxx
        ##############
        #
        #  FIGURE 6
        #
        ##############
        #
        plt.figure(6)
        plco(aphi,xcoord=r*np.sin(h),ycoord=r*np.cos(h),colors='k',nc=30)
        #plc(daphi,xcoord=r*np.sin(h),ycoord=r*np.cos(h),levels=(0,),colors='r')
        d=500
        plt.xlim(0,d/2.); plt.ylim(-d,d)
        plc(aphi-maxaphibh,levels=(0,),colors='b',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hjet1aphi[:,None,None],levels=(0,),colors='m',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hjet2aphi[:,None,None],levels=(0,),colors='m',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hwind1aphi[:,None,None],levels=(0,),colors='c',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hwind2aphi[:,None,None],levels=(0,),colors='c',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hjetwind1[:,None,None],levels=(0,),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(h-hjetwind2[:,None,None],levels=(0,),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        #plc(chophi(choplo(-avg_unb[:,:,0]-(1.0),0),0.001),xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        #plc(avg_gamma,nc=50,xcoord=r*np.sin(h),ycoord=r*np.cos(h),cb=True)
        #
        #plc(chophi((r/rhor)**0.75*(1-np.abs(np.cos(h))),1),xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        #plc(avg_omegaf2*2*np.pi,xcoord=r*np.sin(h),ycoord=r*np.cos(h),cb=True)
        #plc(avg_uu[1]*dxdxp[1][1],xcoord=r*np.sin(h),ycoord=r*np.cos(h),levels=(0,))
        #plc(avg_uu[1]*dxdxp[1][1],xcoord=r*np.sin(h),ycoord=r*np.cos(h),levels=(0,),colors='g')
        #plc(-avg_unb[:,:,0]-(1.0),levels=(0,0.01,0.1),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        #plc(avg_mu[:,:,0]-(1.0),levels=(0,0.01,0.1),colors='r',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        if False:
            plc(chophi(choplo(-avg_unb[:,:,0]-(1.0),0),0.001),xcoord=r*np.sin(h),ycoord=r*np.cos(h))
            rfd("fieldline0000.bin")
            #plc(np.log10(avg_rho),xcoord=r*np.sin(h),ycoord=r*np.cos(h))
            plc(avg_uu[1],levels=(0,),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
            #plc(daphi,levels=(0,),colors='r',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
            #plc(h-hjet1aphia[:,None,None],levels=(0,),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
            plc(h-hjetwind1[:,None,None],levels=(0,),colors='c',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
            plc(h-hjetwind2[:,None,None],levels=(0,),colors='y',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
            plc(chophi(choplo(-avg_sigma,0.1),10),xcoord=r*np.sin(h),ycoord=r*np.cos(h))
            plc(chophi((r/rhor)**0.75*(1-np.abs(np.cos(h))),1),xcoord=r*np.sin(h),ycoord=r*np.cos(h))
    #xxx
    #plc(h,xcoord=r*np.sin(h),ycoord=r*np.cos(h))
    #plc(lrho,xcoord=r*np.sin(h),ycoord=r*np.cos(h))

def printjetwindpower(filehandle = None, r = None, stage = 0, powjet = 0, powwind = 0, muminjet = 0, muminwind = 0, md = 0, powjetEMKE=0, powjetwindEMKE=0, ftot=0, fsqtot=0, f30=0, fsq30=0, pjemtot=0, eoutEMtot = 0):
    if filehandle == None or r == None:
        raise( ValuseError("filehandle and r have to be specified") )
    #
    #foutpower.write( "#Name a Mdot   Pjet    Etajet  Psitot Psisqtot**0.5 Psijet Psisqjet**0.5 rstag Pjtotmax Pjtot1rstag Pjtot2rstag Pjtot4rstag Pjtot8rstag\n"  )
    #
    i = iofr(r)
    if stage == 0:
        #initial stage
        filehandle.write( "%s %f %f %f %f %f %f %f %f %f %f %f %f" % (os.path.basename(os.getcwd()), a, avg_ts[0], avg_te[0], muminjet, muminwind, md, ftot, fsqtot, f30, fsq30, pjemtot, eoutEMtot) )
    if stage == 0 or stage == 1:
        #intermediate stage
        filehandle.write( " %f %f %f %f %f" % (powjetEMKE[i], powjetwindEMKE[i], powjet[i], powwind[i], r) )
    if stage == 2:
        #final stage
        filehandle.write( " %f %f %f %f %f\n" % (powjetEMKE[i], powjetwindEMKE[i], powjet[i], powwind[i], r) )
    #flush to disk just in case to make sure all is written
    filehandle.flush()
    os.fsync(filehandle.fileno())
    
    
def horcalc(which=1):
    """
    Compute root mean square deviation of disk body from equatorial plane
    """
    tiny=np.finfo(rho.dtype).tiny
    up=(gdet*rho*(h-np.pi/2)*which).sum(axis=1)
    dn=(gdet*rho*which).sum(axis=1)
    thetamid2d=up/(dn+tiny)+np.pi/2
    thetamid3d=np.empty((nx,ny,nz),dtype=h.dtype)
    hoverr3d=np.empty((nx,ny,nz),dtype=h.dtype)
    for j in np.arange(0,ny):
        thetamid3d[:,j] = thetamid2d
    up=(gdet*rho*(h-thetamid3d)**2*which).sum(axis=1)
    dn=(gdet*rho*which).sum(axis=1)
    hoverr2d= (up/(dn+tiny))**0.5
    for j in np.arange(0,ny):
        hoverr3d[:,j] = hoverr2d
    return((hoverr3d,thetamid3d))

def intangle(qty,hoverr=None,thetamid=np.pi/2,minbsqorho=None,mumax=None,mumin=None,maxbeta=None,which=1):
    #somehow gives slightly different answer than when computed directly
    if hoverr == None:
        hoverr = np.pi/2
        thetamid = np.pi/2
    integrand = qty
    insidehor = np.abs(h-thetamid)<hoverr
    if minbsqorho != None:
        insidebsqorho = bsq/rho>=minbsqorho
    else:
        insidebsqorho = 1
    #
    #
    v4asq=bsq/(rho+ug+(gam-1)*ug)
    mum1fake=uu[0]*(1.0+v4asq)-1.0
    if mumax is None:
        insidemumax = 1
    else:
        insidemumax = 1
        insidemumax = insidemumax * (mum1fake<mumax)
        insidemumax = insidemumax * (isunbound==1)
        insidemumax = insidemumax * (uu[1]>0.0)
    #
    if mumin is None:
        insidemumin = 1
    else:
        insidemumin = 1
        insidemumin = insidemumin * (mum1fake>mumin)
        insidemumin = insidemumin * (isunbound==1)
        insidemumin = insidemumin * (uu[1]>0.0)
    #
    beta=((gam-1)*ug)/(bsq/2)
    if maxbeta is None:
        insidebeta = 1
    else:
        insidebeta = (beta>maxbeta)
    #
    integral=(integrand*insidehor*insidebsqorho*insidemumin*insidemumax*insidebeta*which).sum(axis=2).sum(axis=1)*_dx2*_dx3
    integral=scaletofullwedge(integral)
    return(integral)

# def inttheta(qty,dtheta=np.pi/2):
#     integrand = qty
#     insidedtheta = np.abs(h-np.pi/2)<=dtheta
#     integral=np.sum(np.sum(integrand*insidetheta,axis=2),axis=1)
#     return(integral)

    
def Qmri():
    """
    APPROXIMATELY Computes number of theta cells resolving one MRI wavelength
    """
    global bu,rho,uu,_dx2
    cvel()
    #corrected this expression to include both 2pi and dxdxp[3][3]
    #also corrected defition of va^2 to contain bsq+gam*ug term
    #need to figure out how to properly measure this in fluid frame
    vau2 = np.abs(bu[2])/np.sqrt(rho+bsq+gam*ug)
    omega = dxdxp[3][3]*uu[3]/uu[0]+1e-15
    lambdamriu2 = 2*np.pi * vau2 / omega
    res=lambdamriu2/_dx2
    return(res)

def plco(myvar,xcoord=None,ycoord=None,ax=None,**kwargs):
    plt.clf()
    plc(myvar,xcoord,ycoord,ax,**kwargs)

def plc(myvar,xcoord=None,ycoord=None,ax=None,**kwargs): #plc
    #xcoord = kwargs.pop('x1', None)
    #ycoord = kwargs.pop('x2', None)
    if(np.min(myvar)==np.max(myvar)):
        print("The quantity you are trying to plot is a constant = %g." % np.min(myvar))
        return
    cb = kwargs.pop('cb', False)
    nc = kwargs.pop('nc', 15)
    k = kwargs.pop('k',0)
    if None != xcoord and None != ycoord:
        xcoord = xcoord[:,:,None] if xcoord.ndim == 2 else xcoord[:,:,k:k+1]
        ycoord = ycoord[:,:,None] if ycoord.ndim == 2 else ycoord[:,:,k:k+1]
    myvar = myvar[:,:,None] if myvar.ndim == 2 else myvar[:,:,k:k+1]
    if ax is None:
        ax = plt.gca()
    if( xcoord == None or ycoord == None ):
        res = ax.contour(myvar[:,:,0].transpose(),nc,**kwargs)
    else:
        res = ax.contour(xcoord[:,:,0],ycoord[:,:,0],myvar[:,:,0],nc,**kwargs)
    if( cb == True): #use color bar
        plt.colorbar(res,ax=ax)

def reinterp(vartointerp,extent,ncell,domask=1,isasymmetric=False):
    global xi,yi,zi
    #grid3d("gdump")
    #rfd("fieldline0250.bin")
    xraw=r*np.sin(h)
    yraw=r*np.cos(h)
    x=xraw[:,:,0].view().reshape(-1)
    y=yraw[:,:,0].view().reshape(-1)
    var=vartointerp[:,:,0].view().reshape(-1)
    #mirror
    x=np.concatenate((-x,x))
    y=np.concatenate((y,y))
    kval=min(vartointerp.shape[2]-1,nz/2)
    varmirror = vartointerp[:,:,kval].view().reshape(-1)
    if isasymmetric:
        varmirror *= -1.
    var=np.concatenate((varmirror,var))
    # define grid.
    xi = np.linspace(extent[0], extent[1], ncell)
    yi = np.linspace(extent[2], extent[3], ncell)
    # grid the data.
    zi = griddata((x, y), var, (xi[None,:], yi[:,None]), method='cubic')
    #zi[interior] = np.ma.masked
    if domask!=0:
        interior = np.sqrt((xi[None,:]**2) + (yi[:,None]**2)) < (1+np.sqrt(1-a**2))*domask
        varinterpolated = ma.masked_where(interior, zi)
    else:
        varinterpolated = zi
    return(varinterpolated)

def reinterpxy(vartointerp,extent,ncell,domask=1):
    global xi,yi,zi
    #grid3d("gdump")
    #rfd("fieldline0250.bin")
    xraw=r*np.sin(h)*np.cos(ph)
    yraw=r*np.sin(h)*np.sin(ph)
    #2 cells below the midplane
    x=xraw[:,ny/2+1,:].view().reshape(-1)
    y=yraw[:,ny/2+1,:].view().reshape(-1)
    var=vartointerp[:,ny/2+1,:].view().reshape(-1)
    #mirror
    if nz*_dx3*dxdxp[3,3,0,0,0] < 0.99 * 2 * np.pi:
        x=np.concatenate((-x,x))
        y=np.concatenate((-y,y))
        var=np.concatenate((var,var))
    # define grid.
    xi = np.linspace(extent[0], extent[1], ncell)
    yi = np.linspace(extent[2], extent[3], ncell)
    # grid the data.
    zi = griddata((x, y), var, (xi[None,:], yi[:,None]), method='cubic')
    #zi[interior] = np.ma.masked
    if domask!=0:
        interior = np.sqrt((xi[None,:]**2) + (yi[:,None]**2)) < (1+np.sqrt(1-a**2))*domask
        varinterpolated = ma.masked_where(interior, zi)
    else:
        varinterpolated = zi
    return(varinterpolated)
    
def ftr(x,xb,xf):
    return( amax(0.0*x,amin(1.0+0.0*x,1.0*(x-xb)/(xf-xb))) )


# What Sasha uses for streamlines:
#    The new code is at http://www.atm.damtp.cam.ac.uk/people/tjf37/streamplot.py and 
#there are new sample plots at 
#http://www.atm.damtp.cam.ac.uk/people/tjf37/streamlines1.png and 
#http://www.atm.damtp.cam.ac.uk/people/tjf37/streamlines2.png .

# other stream line methods:
# http://github.enthought.com/mayavi/mayavi/mlab.html
# http://permalink.gmane.org/gmane.comp.python.matplotlib.general/26362
# http://comments.gmane.org/gmane.comp.python.matplotlib.general/26354
# http://mindseye.no/tag/python/
# http://scikits.appspot.com/vectorplot  (includes LIC)
# http://wiki.chem.vu.nl/dirac/index.php/How_to_plot_vector_fields_calculated_with_DIRAC11_as_streamline_plots_using_PyNGL


def mkframe(fname,ax=None,cb=True,vmin=None,vmax=None,len=20,ncell=800,pt=True,shrink=1,dostreamlines=True,downsample=4,density=2,dodiskfield=False,minlendiskfield=0.2,minlenbhfield=0.2,dorho=True,dovarylw=True,dobhfield=True,dsval=0.01,color='k',dorandomcolor=False,doarrows=True,lw=None,skipblankint=False,detectLoops=True,minindent=1,minlengthdefault=0.2,startatmidplane=True,showjet=False):
    extent=(-len,len,-len,len)
    palette=cm.jet
    palette.set_bad('k', 1.0)
    #palette.set_over('r', 1.0)
    #palette.set_under('g', 1.0)
    rhor=1+(1-a**2)**0.5
    ihor = iofr(rhor)
    ilrho = reinterp(np.log10(rho),extent,ncell,domask=1.0)
    if not dostreamlines:
        aphi = fieldcalc()
        iaphi = reinterp(aphi,extent,ncell,domask=0)
        #maxabsiaphi=np.max(np.abs(iaphi))
        maxabsiaphi = 100 #50
        ncont = 100 #30
        levs=np.linspace(-maxabsiaphi,maxabsiaphi,ncont)
    else:
        aphi = fieldcalc()
        iaphi = reinterp(aphi,extent,ncell,domask=0)
        Br = dxdxp[1,1]*B[1]+dxdxp[1,2]*B[2]
        Bh = dxdxp[2,1]*B[1]+dxdxp[2,2]*B[2]
        Bp = B[3]*dxdxp[3,3]
        #
        Brnorm=Br
        Bhnorm=Bh*np.abs(r)
        Bpnorm=Bp*np.abs(r*np.sin(h))
        #
        Bznorm=Brnorm*np.cos(h)-Bhnorm*np.sin(h)
        BRnorm=Brnorm*np.sin(h)+Bhnorm*np.cos(h)
        #
        iBz = reinterp(Bznorm,extent,ncell,domask=0.8)
        iBR = reinterp(BRnorm,extent,ncell,isasymmetric=True,domask=0.8) #isasymmetric = True tells to flip the sign across polar axis
        #
        if dorandomcolor:
            Ba=np.copy(B)
            cond = (B[1]<0)
            Ba[2,cond]*=-1
            Ba[3,cond]*=-1
            Ba[1,cond]*=-1
            Bar = dxdxp[1,1]*Ba[1]+dxdxp[1,2]*Ba[2]
            Bah = dxdxp[2,1]*Ba[1]+dxdxp[2,2]*Ba[2]
            Bap = Ba[3]*dxdxp[3,3]
            #
            Barnorm=Bar
            Bahnorm=Bah*np.abs(r)
            Bapnorm=Bap*np.abs(r*np.sin(h))
            #
            Baznorm=Barnorm*np.cos(h)-Bahnorm*np.sin(h)
            BaRnorm=Barnorm*np.sin(h)+Bahnorm*np.cos(h)
            #
            iBaz = reinterp(Baznorm,extent,ncell,domask=0.8)
            iBaR = reinterp(BaRnorm,extent,ncell,isasymmetric=True,domask=0.8) #isasymmetric = True tells to flip the sign across polar axis
        else:
            iBaz = None
            iBaR = None
        if showjet:
            imu = reinterp(mu,extent,ncell,domask=0.8)
        #
        if dovarylw:
            iibeta = reinterp(0.5*bsq/(gam-1)/ug,extent,ncell,domask=0)
            ibsqorho = reinterp(bsq/rho,extent,ncell,domask=0)
            ibsqo2rho = 0.5 * ibsqorho
        xi = np.linspace(extent[0], extent[1], ncell)
        yi = np.linspace(extent[2], extent[3], ncell)
        #myspeed=np.sqrt(iBR**2+iBz**2)
    #
    #myslines=streamplot(ti[:,0,0],tj[0,:,0],avg_gdetB[0,:,:,0].transpose(),avg_gdetB[1,:,:,0].transpose(),density=2,downsample=4,linewidth=1)
    #for c in cset2.collections:
    #    c.set_linestyle('solid')
    #CS = plt.contourf(xi,yi,zi,15,cmap=palette)
    if ax == None:
        ax = plt.gca()
        # CS = plt.imshow(ilrho, extent=extent, cmap = palette, norm = colors.Normalize(clip = False),origin='lower',vmin=vmin,vmax=vmax)
        # if not dostreamlines:
        #     cset2 = plt.contour(iaphi,linewidths=0.5,colors='k', extent=extent,hold='on',origin='lower',levels=levs)
        # else:
        #     lw = 0.5+1*ftr(np.log10(amax(ibsqo2rho,1e-6+0*ibsqorho)),np.log10(1),np.log10(2))
        #     lw += 1*ftr(np.log10(amax(iibeta,1e-6+0*ibsqorho)),np.log10(1),np.log10(2))
        #     lw *= ftr(np.log10(amax(iibeta,1e-6+0*iibeta)),-3.5,-3.4)
        #     # if t < 1500:
        #     #     lw *= ftr(ilrho,-2.,-1.9)
        #     fstreamplot(yi,xi,iBR,iBz,density=2,downsample=4,linewidth=lw,ax=ax,detectLoops=True,dodiskfield=False,dobhfield=True,startatmidplane=True,a=a)
        #     #streamplot(yi,xi,iBR,iBz,density=3,linewidth=1,ax=ax)
        # plt.xlim(extent[0],extent[1])
        # plt.ylim(extent[2],extent[3])
    if dorho:
        CS = ax.imshow(ilrho, extent=extent, cmap = palette, norm = colors.Normalize(clip = False),origin='lower',vmin=vmin,vmax=vmax)
    if showjet:
        ax.contour(imu,linewidths=0.5,colors='g', extent=extent,hold='on',origin='lower',levels=(2,))
        ax.contour(iaphi,linewidths=0.5,colors='b', extent=extent,hold='on',origin='lower',levels=(aphi[ihor,ny/2,0],))
    if not dostreamlines:
        cset2 = ax.contour(iaphi,linewidths=0.5,colors='k', extent=extent,hold='on',origin='lower',levels=levs)
    else:
        if dovarylw:
            lw = 0.5+1*ftr(np.log10(amax(ibsqo2rho,1e-6+0*ibsqorho)),np.log10(1),np.log10(2))
            lw += 1*ftr(np.log10(amax(iibeta,1e-6+0*ibsqorho)),np.log10(1),np.log10(2))
            lw *= ftr(np.log10(amax(iibeta,1e-6+0*iibeta)),-3.5,-3.4)
            #if t < 500:
            #    lw *= ftr(iaphi,0.001,0.002)

        fstreamplot(yi,xi,iBR,iBz,ua=iBaR,va=iBaz,density=density,downsample=downsample,linewidth=lw,ax=ax,detectLoops=detectLoops,dodiskfield=dodiskfield,dobhfield=dobhfield,startatmidplane=startatmidplane,a=a,minlendiskfield=minlendiskfield,minlenbhfield=minlenbhfield,dsval=dsval,color=color,doarrows=doarrows,dorandomcolor=dorandomcolor,skipblankint=skipblankint,minindent=minindent,minlengthdefault=minlengthdefault)
        #streamplot(yi,xi,iBR,iBz,density=3,linewidth=1,ax=ax)
    ax.set_xlim(extent[0],extent[1])
    ax.set_ylim(extent[2],extent[3])
    #CS.cmap=cm.jet
    #CS.set_axis_bgcolor("#bdb76b")
    if True == cb:
        plt.colorbar(CS,ax=ax,shrink=shrink) # draw colorbar
    #plt.title(r'$\log_{10}\rho$ at $t = %4.0f$' % t)
    if True == pt:
        plt.title('log rho at t = %4.0f' % t)
    #if None != fname:
    #    plt.savefig( fname + '.png' )

def mkframexy(fname,ax=None,cb=True,vmin=None,vmax=None,len=20,ncell=800,pt=True,shrink=1,dostreamlines=True):
    extent=(-len,len,-len,len)
    palette=cm.jet
    palette.set_bad('k', 1.0)
    #palette.set_over('r', 1.0)
    #palette.set_under('g', 1.0)
    ilrho = reinterpxy(np.log10(rho),extent,ncell,domask=1.0)
    aphi = fieldcalc()+rho*0
    iaphi = reinterpxy(aphi,extent,ncell)
    #maxabsiaphi=np.max(np.abs(iaphi))
    #maxabsiaphi = 100 #50
    #ncont = 100 #30
    #levs=np.linspace(-maxabsiaphi,maxabsiaphi,ncont)
    #cset2 = plt.contour(iaphi,linewidths=0.5,colors='k', extent=extent,hold='on',origin='lower',levels=levs)
    #for c in cset2.collections:
    #    c.set_linestyle('solid')
    #CS = plt.contourf(xi,yi,zi,15,cmap=palette)
    if dostreamlines:
        Br = dxdxp[1,1]*B[1]+dxdxp[1,2]*B[2]
        Bh = dxdxp[2,1]*B[1]+dxdxp[2,2]*B[2]
        Bp = B[3]*dxdxp[3,3]
        #
        Brnorm=Br
        Bhnorm=Bh*np.abs(r)
        Bpnorm=Bp*np.abs(r*np.sin(h))
        #
        Bznorm=Brnorm*np.cos(h)-Bhnorm*np.sin(h)
        BRnorm=Brnorm*np.sin(h)+Bhnorm*np.cos(h)
        Bxnorm=BRnorm*np.cos(ph)-Bpnorm*np.sin(ph)
        Bynorm=BRnorm*np.sin(ph)+Bpnorm*np.cos(ph)
        #
        iBx = reinterpxy(Bxnorm,extent,ncell,domask=1)
        iBy = reinterpxy(Bynorm,extent,ncell,domask=1)
        iibeta = reinterpxy(0.5*bsq/(gam-1)/ug,extent,ncell,domask=0)
        ibsqorho = reinterpxy(bsq/rho,extent,ncell,domask=0)
        ibsqo2rho = 0.5 * ibsqorho
        xi = np.linspace(extent[0], extent[1], ncell)
        yi = np.linspace(extent[2], extent[3], ncell)
    if ax == None:
        CS = plt.imshow(ilrho, extent=extent, cmap = palette, norm = colors.Normalize(clip = False),origin='lower',vmin=vmin,vmax=vmax)
        plt.xlim(extent[0],extent[1])
        plt.ylim(extent[2],extent[3])
    else:
        CS = ax.imshow(ilrho, extent=extent, cmap = palette, norm = colors.Normalize(clip = False),origin='lower',vmin=vmin,vmax=vmax)
        if dostreamlines:
            lw = 0.5+1*ftr(np.log10(amax(ibsqo2rho,1e-6+0*ibsqorho)),np.log10(1),np.log10(2))
            lw += 1*ftr(np.log10(amax(iibeta,1e-6+0*ibsqorho)),np.log10(1),np.log10(2))
            lw *= ftr(np.log10(amax(iibeta,1e-6+0*iibeta)),-3.5,-3.4)
            # if t < 1500:
            #     lw *= ftr(ilrho,-2.,-1.9)
            #lw *= ftr(iaphi,0.001,0.002)

            fstreamplot(yi,xi,iBx,iBy,density=1,downsample=1,linewidth=lw,detectLoops=True,dodiskfield=False,dobhfield=False,startatmidplane=False,a=a)
        ax.set_xlim(extent[0],extent[1])
        ax.set_ylim(extent[2],extent[3])
    #CS.cmap=cm.jet
    #CS.set_axis_bgcolor("#bdb76b")
    if True == cb:
        plt.colorbar(CS,ax=ax,shrink=shrink) # draw colorbar
    #plt.title(r'$\log_{10}\rho$ at $t = %4.0f$' % t)
    if True == pt:
        plt.title('log rho at t = %4.0f' % t)
    #
    #if None != fname:
    #    plt.savefig( fname + '.png' )

def mainfunc(imgname):
    global xi,yi,zi,CS
    #grid3d("gdump")
    #rfd("fieldline0250.bin")
    xraw=r*np.sin(h)
    yraw=r*np.cos(h)
    lrhoraw=np.log10(rho)
    x=xraw[:,:,0].view().reshape(-1)
    y=yraw[:,:,0].view().reshape(-1)
    lrho=lrhoraw[:,:,0].view().reshape(-1)
    #mirror
    x=np.concatenate((-x,x))
    y=np.concatenate((y,y))
    lrho=np.concatenate((lrho,lrho))
    extent=(-41,41,-41,41)
    # define grid.
    xi = np.linspace(-41.0, 41.0, 800)
    yi = np.linspace(-41.0, 41.0, 800)
    # grid the data.
    zi = griddata((x, y), lrho, (xi[None,:], yi[:,None]), method='cubic')
    interior = np.sqrt((xi[None,:]**2) + (yi[:,None]**2)) < 1+np.sqrt(1-a**2)
    #zi[interior] = np.ma.masked
    zim = ma.masked_where(interior, zi)
    palette=cm.jet
    palette.set_bad('k', 1.0)
    palette.set_over('r', 1.0)
    palette.set_under('g', 1.0)
    # contour the gridded data, plotting dots at the randomly spaced data points.
    cset2 = plt.contour(zi,15,linewidths=0.5,colors='k', extent=extent,hold='on',origin='lower')
    #for c in cset2.collections:
    #    c.set_linestyle('solid')
    #CS = plt.contourf(xi,yi,zi,15,cmap=palette)
    #CS = plt.imshow(zim, extent=[0.01,80,-40,40], cmap = palette, norm = colors.Normalize(vmin=-1,vmax=-0.2,clip = False))
    CS = plt.imshow(zim, extent=extent, cmap = palette, norm = colors.Normalize(clip = False),origin='lower')
    #CS.cmap=cm.jet
    #CS.set_axis_bgcolor("#bdb76b")
    plt.colorbar(CS) # draw colorbar
    plt.xlim(-40,40)
    plt.ylim(-40,40)
    plt.title('t = %f' % t)
    #plt.show()
    # rbf = Rbf(x[0:288:8,:,0].view().reshape(-1),y[0:288:8,:,0].view().reshape(-1),rho[0:288:8,:,0].view().reshape(-1),epsilon=2)
    # ZI = rbf( XI, YI )
    # # plot the result
    # n = plt.normalize(0.0, 40.0)
    # plt.subplot(1, 1, 1)
    # plt.imshow(XI, YI, ZI, cmap=cm.jet)
    # #plt.scatter(x, y, 100, z, cmap=cm.jet)
    # plt.title('RBF interpolation - multiquadrics')
    # plt.xlim(0, 40.0)
    # plt.ylim(0, 40.0)
    # plt.colorbar()
    # plt.figure()
    # plt.plot(r[:,0,0],np.log10(absflux),'b')
    # plt.legend(['Grid'])
    # plt.axis([r[0,0,0],100,-5,5])
    # plt.title('Grid plot')
    # plt.show()

def ravg(dumpname):
    global t,nx,ny,nz,_dx1,_dx2,_dx3,gam,a,Rin,Rout,avgU,avgTud10
    #read image
    ilist=np.array([128,144,160,176,192,208,224])
    for (j,i) in enumerate(ilist):
        fin = open( "dumps/%s-col%04d" % ( dumpname, i ) , "rb" )
        print("Reading %s-col%04d..." % (dumpname,i) )
        header = fin.readline().split()
        t = myfloat(np.float64(header[0]))
        nx = int(header[1])
        ny = int(header[2])
        nz = int(header[3])
        if j == 0:
            avgU=np.zeros((ilist.shape[0],nx,ny,nz),dtype=np.float32)
        _dx1=myfloat(float(header[7]))
        _dx2=myfloat(float(header[8]))
        _dx3=myfloat(float(header[9]))
        gam=myfloat(float(header[11]))
        a=myfloat(float(header[12]))
        Rin=myfloat(float(header[14]))
        Rout=myfloat(float(header[15]))
        if dumpname.endswith(".bin"):
            body = np.fromfile(fin,dtype=np.float64,count=-1)  #nx*ny*nz*11)
            gd = body.view().reshape((-1,nx,ny,nz),order='F')
            fin.close()
        else:
            fin.close()
            gd = np.loadtxt( "dumps/"+dumpname, 
                          dtype=np.float64, 
                          skiprows=1, 
                          unpack = True ).view().reshape((-1,nx,ny,nz), order='F')
        #print np.max(gd)
        avgU[j:j+1] = gd[:,:,:,:].view() 
    avgTud10=avgU.sum(axis=0)
    return

def computeavg(qty):
    avgqty=intangle(gdet*qty)
    return(avgqty)

def doall():
    grid3d("gdump.bin",use2d=True)
    
    if np.abs(a - 0.99)<1e-4 and scaletofullwedge(1.0) < 1.5:
        #lo-res 0.99 settings
        print( "Using hires a = 0.99 settings")
        ilist=np.arange(221,286)
        dtlist=100.+0*ilist
        dtlist[ilist==221]=22200-22167.6695855045
        dtlist[ilist==222]=22300-22231.9647756934
        dtlist[ilist==228]=22900-22890.8671337456
        dtlist[ilist==232]=23300-23292.5857662206
        dtlist[ilist==239]=24000-23951.5226133435
        dtlist[ilist==245]=24600-24594.4658011928
        dtlist[ilist==251]=25200-25124.6341346588
        dtlist[ilist==257]=25800-25799.8775611997
        dtlist[ilist==263]=26400-26330.0889135128
        dtlist[ilist==267]=26800-26763.9946654502
        dtlist[ilist==274]=27500-27406.4732593203
        dtlist[ilist==280]=28100-28097.4708711805
    elif np.abs(a - 0.99)<1e-4 and scaletofullwedge(1.0) > 1.5:
        #lo-res 0.99 settings
        print( "Using lores a = 0.99 settings")
        ilist=np.arange(120,137)
        dtlist=100.+0*ilist

    print dtlist 

    for (j,i) in enumerate(ilist):
        dt=dtlist[j]
        ravg("avg%04d.bin" % i)
        if j == 0:
            FE=computeavg(avgTud10)*dt
        else:
            FE+=computeavg(avgTud10)*dt
    #get time average by dividing by the total averaging time
    FE /= dtlist.sum()
    np.save("fe.npy",FE)
    plt.clf()
    plt.plot(r[:,0,0],FE); 
    plt.xlim(rhor,20)
    plt.ylim(-15,15)

def rfloor(dumpname):
    global t,nx,ny,nz,_dx1,_dx2,_dx3,gam,a,Rin,Rout,dUfloor
    #read image
    fin = open( "dumps/" + dumpname, "rb" )
    print("Reading %s..." % dumpname)
    header = fin.readline().split()
    t = np.float64(header[0])
    nx = int(header[1])
    ny = int(header[2])
    nz = int(header[3])
    _dx1=float(header[7])
    _dx2=float(header[8])
    _dx3=float(header[9])
    gam=float(header[11])
    a=float(header[12])
    Rin=float(header[14])
    Rout=float(header[15])
    if dumpname.endswith(".bin"):
        body = np.fromfile(fin,dtype=np.float64,count=-1)  #nx*ny*nz*11)
        gd = body.view().reshape((-1,nx,ny,nz),order='F')
        fin.close()
    else:
        fin.close()
        gd = np.loadtxt( "dumps/"+dumpname, 
                      dtype=np.float64, 
                      skiprows=1, 
                      unpack = True ).view().reshape((-1,nx,ny,nz), order='F')
    dUfloor = gd[:,:,:,:].view() 
    return

def rrdump(dumpname,write2xphi=False):
    global nx,ny,nz,t,a,rho,ug,vu,vd,B,gd,gd1,numcols,gdetB
    #print( "Reading " + "dumps/" + dumpname + " ..." )
    gin = open( "dumps/" + dumpname, "rb" )
    header = gin.readline().split()
    nx = int(header[0])
    ny = int(header[1])
    nz = int(header[2])
    t  = float(header[3])
    a  = float(header[6])
    #nx+=8
    #ny+=8
    #nz+=8
    if dumpname.endswith(".bin"):
        body = np.fromfile(gin,dtype=np.float64,count=-1)  #nx*ny*nz*11)
        gdraw = body
        gin.close()
    else:
        gin.close()
        gdraw = np.loadtxt( "dumps/"+dump, 
                      dtype=np.float64, 
                      skiprows=1, 
                      unpack = True )
    gd=gdraw.view().reshape((-1,nx,ny,nz), order='F')
    rho,ug = gd[0:2,:,:,:].view() 
    B = np.zeros_like(gd[4:8])
    vu = np.zeros_like(B)
    vu[1:4] = gd[2:5].view() #relative 4-velocity only has non-zero spatial components
    B[1:4] = gd[5:8].view()
    numcols = gd.shape[0]  #total number of columns is made up of (n prim vars) + (n cons vars) = numcols
    gdetB = np.zeros_like(B)
    gdetB[1:4] = gd[numcols/2+5:numcols/2+5+3]  #gdetB starts with 5th conserved variable
    if 'gv3' in globals() and 'gn3' in globals(): 
        vd = mdot(gv3,vu)
        gamma = (1+mdot(mdot(gv3,vu),vu))**0.5
        etad = np.zeros_like(vu)
        etad[0] = -1/(-gn3[0,0])**0.5      #ZAMO frame velocity (definition)
        etau = mdot(gn3,etad)
        uu = gamma * etau + vu
        ud = mdot(gv3,uu)
    else:
        print( 'Metric (gv3, gn3) not defined, I am skipping the computation of uu and ud' )
    if write2xphi:
        print( "Writing out 2xphi rdump...", )
        #write out a dump with twice as many cells in phi-direction:
        gout = open( "dumps/" + dumpname + "2xphi", "wb" )
        #double the number of phi-cells
        header[2] = "%d" % (2*nz)
        for headerel in header:
            s = "%s " % headerel
            gout.write( s )
        gout.write( "\n" )
        gout.flush()
        os.fsync(gout.fileno())
        #reshape the rdump content
        gd1 = gdraw.view().reshape((nz,ny,nx,-1),order='C')
        #allocate memory for refined grid, nz' = 2*nz
        gd2 = np.zeros((2*nz,ny,nx,numcols),order='C',dtype=np.float64)
        #copy even k's
        gd2[0::2,:,:,:] = gd1[:,:,:,:]
        #copy odd k's
        gd2[1::2,:,:,:] = gd1[:,:,:,:]
        #in the new cells, adjust gdetB[3] to be averages of immediately adjacent cells (this ensures divb=0)
        gdetB3index = numcols/2+5+2
        gd2[1:-1:2,:,:,gdetB3index] = 0.5*(gd1[:-1,:,:,gdetB3index]+gd1[1:,:,:,gdetB3index])
        gd2[-1,:,:,gdetB3index] = 0.5*(gd1[0,:,:,gdetB3index]+gd1[-1,:,:,gdetB3index])
        gd2.tofile(gout)
        gout.close()
        print( " done!" )
        

def fieldcalctoth():
    """
    Computes the field vector potential
    """
    daphi = -(gdetB[1]).sum(-1)*_dx2/nz
    aphi=daphi[:,::-1].cumsum(axis=1)[:,::-1]
    aphi-=0.5*daphi #correction for half-cell shift between face and center in theta
    return(aphi)
   
def fieldcalcU(gdetB1=None):
    """
    Computes cell-centered vector potential
    """
    aphi=fieldcalcface(gdetB1)
    #center it properly in theta
    aphi[:,0:ny-1]=0.5*(aphi[:,0:ny-1]+aphi[:,1:ny]) 
    #special treatment for last cell since no cell at j = ny, and we know aphi[:,ny] should vanish
    aphi[:,ny-1] *= 0.5
    #and in r
    aphi[0:nx-1] = 0.5*(aphi[0:nx-1]  +aphi[1:nx])
    aphi/=(nz*_dx3)
    return(aphi)

def fieldcalcface(gdetB1=None):
    """
    Computes the field vector potential
    """
    global aphi
    if gdetB1 == None:
        gdetB1 = gdetB[1]
    #average in phi and add up
    daphi = (gdetB1).sum(-1)[:,:,None]/nz*_dx2
    aphi = np.zeros_like(daphi)
    aphi[:,1:ny/2+1]=(daphi.cumsum(axis=1))[:,0:ny/2]
    #sum up from the other pole
    aphi[:,ny/2+1:ny]=(-daphi[:,::-1].cumsum(axis=1))[:,::-1][:,ny/2+1:ny]
    return(aphi)

def fieldcalcface2():
    """
    Computes the field vector potential
    """
    daphi = np.sum(gdetB[2], axis=2)[:,:,None]*_dx1*_dx3
    aphi=daphi.cumsum(axis=0)
    aphi-=daphi #correction for half-cell shift between face and center in theta
    #aphi[0:nx-1] = 0.5*(aphi[0:nx-1]+aphi[1:nx]) #and in r
    aphi/=(nz*_dx3)
    return(aphi)

def rdo(dump,oldfmt=False):
    """ Read in old dump format """
    rd(dump,oldfmt=True)

def rd(dump,oldfmt=False):
    global t,nx,ny,nz,_dx1,_dx2,_dx3,gam,a,Rin,Rout,ti,tj,tk,x1,x2,x3,r,h,ph,rho,ug,vu,B,pg,cs2,Sden,U,gdetB,divb,uu,ud,bu,bd
    global v1m,v1p,v2m,v2p,v3m,v3p,bsq,olddumpfmt
    #read image
    olddumpfmt = oldfmt
    fin = open( "dumps/" + dump, "rb" )
    header = fin.readline().split()
    t = myfloat(np.float64(header[0]))
    nx = int(header[1])
    ny = int(header[2])
    nz = int(header[3])
    _dx1=myfloat(float(header[7]))
    _dx2=myfloat(float(header[8]))
    _dx3=myfloat(float(header[9]))
    gam=myfloat(float(header[11]))
    a=myfloat(float(header[12]))
    Rin=myfloat(float(header[14]))
    Rout=myfloat(float(header[15]))
    if dump.endswith(".bin"):
        body = np.fromfile(fin,dtype=np.float64,count=-1)  #nx*ny*nz*11)
        gd = body.view().reshape((-1,nx,ny,nz),order='F')
        fin.close()
    else:
        fin.close()
        gd = np.loadtxt( "dumps/"+dump, 
                      dtype=np.float64, 
                      skiprows=1, 
                      unpack = True ).view().reshape((-1,nx,ny,nz), order='F')
    gd=myfloat(gd)
    gc.collect()
    ti,tj,tk,x1,x2,x3,r,h,ph,rho,ug = gd[0:11,:,:,:].view() 
    vu=np.zeros_like(gd[0:4])
    B=np.zeros_like(gd[0:4])
    vu[1:4] = gd[11:14]
    B[1:4] = gd[14:17]
    if not oldfmt:
        pg,cs2,Sden = gd[17:20]
        U = gd[20:29]
        gdetB = np.zeros_like(B)
        gdetB[1:4] = U[5:8]
        divb = gd[29]
        uu = gd[30:34]
        ud = gd[34:38]
        bu = gd[38:42]
        bd = gd[42:46]
        bsq = mdot(bu,bd)
        v1m,v1p,v2m,v2p,v3m,v3p=gd[46:52]
        gdet=gd[53]
    else:
        U = gd[17:25]
        divb = gd[25]
        uu = gd[26:30]
        ud = gd[30:34]
        bu = gd[34:38]
        bd = gd[38:42]
        bsq = mdot(bu,bd)
        v1m,v1p,v2m,v2p,v3m,v3p=gd[42:48]
        gdet=gd[48]
        #gdetB = np.zeros_like(B)
        #gdetB[1:4] = U[5:8]
        gdetB = gdet*B

def rgfd(fieldlinefilename,**kwargs):
    if not os.path.isfile(os.path.join("dumps/", fieldlinefilename)):
        print( "File " + fieldlinefilename + " does not exist. Aborting." )
        return
    if 'gv3' not in globals():
        gdumpname = glob.glob( os.path.join("dumps/", "gdump*") )
        #read the 1st found file
        grid3d(os.path.basename(gdumpname[0]))
    rfd(fieldlinefilename,**kwargs)
    cvel()


#  http://norvig.com/python-lisp.html   

def rfd(fieldlinefilename,**kwargs):
    #read information from "fieldline" file: 
    #Densities: rho, u, 
    #Velocity components: u1, u2, u3, 
    #Cell-centered magnetic field components: B1, B2, B3, 
    #Face-centered magnetic field components multiplied by metric determinant: gdetB1, gdetB2, gdetB3
    global t,nx,ny,nz,_dx1,_dx2,_dx3,gam,a,Rin,Rout,rho,lrho,ug,uu,uut,uu,B,uux,gdetB,rhor
    #read image
    fin = open( "dumps/" + fieldlinefilename, "rb" )
    header = fin.readline().split()
    #time of the dump
    t = myfloat(np.float64(header[0]))
    #dimensions of the grid
    nx = int(header[1])
    ny = int(header[2])
    nz = int(header[3])
    #cell size in internal coordintes
    _dx1=myfloat(float(header[7]))
    _dx2=myfloat(float(header[8]))
    _dx3=myfloat(float(header[9]))
    #other information: 
    #polytropic index
    gam=myfloat(float(header[11]))
    #black hole spin
    a=myfloat(float(header[12]))
    rhor = 1+(1-a**2)**0.5
    #Spherical polar radius of the innermost radial cell
    Rin=myfloat(float(header[14]))
    #Spherical polar radius of the outermost radial cell
    Rout=myfloat(float(header[15]))
    #
    #read grid dump per-cell data
    #
    if(0):
        # new way
        # http://www.mail-archive.com/numpy-discussion@scipy.org/msg07631.html
        # http://docs.scipy.org/doc/numpy/reference/generated/numpy.memmap.html
        # still doesn't quite work once beyond this function!
        numcolumns=int(header[29])
        from numpy import memmap
        d = np.memmap(fin, dtype='float32', mode='c', shape=(numcolumns,nx,ny,nz),order='F')
    #
    else:
        # old way:
        body = np.fromfile(fin,dtype=np.float32,count=-1)
        #body = np.load(fin,dtype=np.float32,count=-1)
        d=body.view().reshape((-1,nx,ny,nz),order='F')
        del(body)
    #
    #rho, u, -hu_t, -T^t_t/U0, u^t, v1,v2,v3,B1,B2,B3
    #matter density in the fluid frame
    rho=np.zeros((1,nx,ny,nz),dtype='float32',order='F')
    rho=d[0,:,:,:]
    lrho=np.zeros((1,nx,ny,nz),dtype='float32',order='F')
    lrho = np.log10(rho)
    #matter internal energy in the fluid frame
    ug=np.zeros((1,nx,ny,nz),dtype='float32',order='F')
    ug=d[1,:,:,:]
    #d[4] is the time component of 4-velocity, u^t
    #d[5:8] are 3-velocities, v^i
    uu=np.zeros((4,nx,ny,nz),dtype='float32',order='F')
    uu=d[4:8,:,:,:]  #again, note uu[i] are 3-velocities (as read from the fieldline file)
    #multiply by u^t to get 4-velocities: u^i = u^t v^i
    uu[1:4]=uu[1:4] * uu[0]
    #B = np.zeros_like(uu)
    #cell-centered magnetic field components
    #B[1:4,:,:,:]=d[8:11,:,:,:]
    # start at 7 so B[1] is correct.  7=<ignore> 8=B[1] 9=B[2] 10=B[3]
    # below assumes B[0] is never needed
    B=np.zeros((4,nx,ny,nz),dtype='float32',order='F')
    B=d[7:11,:,:,:]
    #if the input file contains additional data
    #
    if(d.shape[0]>=14): 
        #new image format additionally contains gdet*B^i
        #face-centered magnetic field components multiplied by gdet
        # below assumes gdetB[0] is never needed
        gdetB=np.zeros((4,nx,ny,nz),dtype='float32',order='F')
        gdetB = d[10:14,:,:,:]
    else:
        print("No data on gdetB, approximating it.")
        gdetB = np.zeros((4,nx,ny,nz),dtype='float32',order='F')
        gdetB[1:4] = gdet * B[1:4]
        #

    #     if 'gdet' in globals():
    #         #first set everything approximately (B's are at shifted locations by half-cell)
    #         B = gdetB/gdet  
    #         #then, average the inner cells to proper locations
    #         B[1,0:nx-1,:,:] = 0.5*(gdetB[1,0:nx-1,:,:]+gdetB[1,1:nx,:,:])/gdet[0:nx-1,:,:]
    #         B[2,:,0:ny-1,:] = 0.5*(gdetB[2,:,0:ny-1,:]+gdetB[2,:,1:ny,:])/gdet[:,0:ny-1,:]
    #         B[3,:,:,0:nz-1] = 0.5*(gdetB[3,:,:,0:nz-1]+gdetB[3,:,:,1:nz])/gdet[:,:,0:nz-1]
    #         #note: last cells on the grids (near upper boundaries of each dir are at
    #         #      approximate locations
    #     else:
    #         print( "rfd: warning: since gdet is not defined, I am skipping the computation of cell-centered fields, B" )
    # else:
    #
    # clean-up unused memory
    del(d)
    fin.close()
    gc.collect()


def cvel():
    global ud,etad, etau, gamma, vu, vd, bu, bd, bsq
    ud = mdot(gv3,uu)                  #g_mn u^n
    etad = np.zeros_like(uu)
    etad[0] = -1/(-gn3[0,0])**0.5      #ZAMO frame velocity (definition)
    etau = mdot(gn3,etad)
    gamma=-mdot(uu,etad)                #Lorentz factor as measured by ZAMO
    vu = uu - gamma*etau               #u^m = v^m + gamma eta^m
    vd = mdot(gv3,vu)
    bu=np.empty_like(uu)              #allocate memory for bu
    #set component per component
    bu[0]=mdot(B[1:4], ud[1:4])             #B^i u_i
    bu[1:4]=(B[1:4] + bu[0]*uu[1:4])/uu[0]  #b^i = (B^i + b^t u^i)/u^t
    bd=mdot(gv3,bu)
    bsq=mdot(bu,bd)


def decolumnify(dumpname):
    print( "Reading data from " + "dumps/" + dumpname + " ..." )
    gin = open( "dumps/" + dumpname + "-col0000", "rb" )
    header = gin.readline()
    gin.close()
    headersplt = header.split()
    nx = int(headersplt[1])
    ny = int(headersplt[2])
    nz = int(headersplt[3])
    gout = open( "dumps/" + dumpname, "wb" )
    gout.write(header)
    gout.flush()
    os.fsync(gout.fileno())
    flist = np.sort(glob.glob( os.path.join("dumps/", "gdump.bin-col*") ) )
    numfiles = flist.shape[0]
    gd = np.zeros((nz,ny,nx,numfiles),order='C',dtype=np.float64)
    for i,f in enumerate(flist):
        print( "Reading from " + f + " ..." )
        gin = open( f, "rb" )
        header = gin.readline()
        body = np.fromfile(gin,dtype=np.float64,count=-1)  #nx*ny*nz*1
        gd[:,:,:,i:i+1] = body.view().reshape((nz,ny,nx,-1),order='C')
        gin.close()
    print( "Writing to file..." )
    gd.tofile(gout)
    gout.close()
    print( "Done!" )

             
def myfloat(f,acc=1):
    """ acc=1 means np.float32, acc=2 means np.float64 """
    if acc==1:
        return( np.float32(f) )
    else:
        return( np.float64(f) )

def grid3d(dumpname,use2d=False,doface=False): #read grid dump file: header and body
    #The internal cell indices along the three axes: (ti, tj, tk)
    #The internal uniform coordinates, (x1, x2, x3), are mapped into the physical
    #non-uniform coordinates, (r, h, ph), which correspond to radius (r), polar angle (theta), and toroidal angle (phi).
    #There are more variables, e.g., dxdxp, which is the Jacobian of (x1,x2,x3)->(r,h,ph) transformation, that I can
    #go over, if needed.
    global nx,ny,nz,_startx1,_startx2,_startx3,_dx1,_dx2,_dx3,gam,a,Rin,Rout,ti,tj,tk,x1,x2,x3,r,h,ph,conn,gn3,gv3,ck,dxdxp,gdet
    global tif,tjf,tkf,rf,hf,phf,rhor
    print( "Reading grid from " + "dumps/" + dumpname + " ..." )
    gin = open( "dumps/" + dumpname, "rb" )
    #First line of grid dump file is a text line that contains general grid information:
    header = gin.readline().split()
    #dimensions of the grid
    nx = int(header[1])
    ny = int(header[2])
    nz = int(header[3])
    #grid internal coordinates starting point
    _startx1=myfloat(float(header[4]))
    _startx2=myfloat(float(header[5]))
    _startx3=myfloat(float(header[6]))
    #cell size in internal coordintes
    _dx1=myfloat(float(header[7]))
    _dx2=myfloat(float(header[8]))
    _dx3=myfloat(float(header[9]))
    #other information: 
    #polytropic index
    gam=myfloat(float(header[11]))
    #black hole spin
    a=myfloat(float(header[12]))
    rhor = 1+(1-a**2)**0.5
    #Spherical polar radius of the innermost radial cell
    Rin=myfloat(float(header[14]))
    #Spherical polar radius of the outermost radial cell
    Rout=myfloat(float(header[15]))
    #read grid dump per-cell data
    #
    if use2d:
        lnz = 1
    else:
        lnz = nz
    ncols = 126
    if dumpname.endswith(".bin"):
        body = np.fromfile(gin,dtype=np.float64,count=ncols*nx*ny*lnz) 
        gd = body.view().reshape((-1,nx,ny,lnz),order='F')
        gin.close()
    else:
        gin.close()
        gd = np.loadtxt( "dumps/" + dumpname, 
                      dtype=np.float64, 
                      skiprows=1, 
                      unpack = True ).view().reshape((126,nx,ny,lnz), order='F')
    gd=myfloat(gd)
    gc.collect()
    ti,tj,tk,x1,x2,x3,r,h,ph = gd[0:9,:,:,:].view()
    #get the right order of indices by reversing the order of indices i,j(,k)
    #conn=gd[9:73].view().reshape((4,4,4,nx,ny,lnz), order='F').transpose(2,1,0,3,4,5)
    #contravariant metric components, g^{\mu\nu}
    gn3 = gd[73:89].view().reshape((4,4,nx,ny,lnz), order='F').transpose(1,0,2,3,4)
    #covariant metric components, g_{\mu\nu}
    gv3 = gd[89:105].view().reshape((4,4,nx,ny,lnz), order='F').transpose(1,0,2,3,4)
    #metric determinant
    gdet = gd[105]
    ck = gd[106:110].view().reshape((4,nx,ny,lnz), order='F')
    #grid mapping Jacobian
    dxdxp = gd[110:126].view().reshape((4,4,nx,ny,lnz), order='F').transpose(1,0,2,3,4)
    #CELL VERTICES:
    #RADIAL:
    #add an extra dimension to rf container since one more faces than centers
    rf = np.zeros((r.shape[0]+1,r.shape[1]+1,r.shape[2]+1))
    #operate on log(r): average becomes geometric mean, etc
    rf[1:nx,0:ny,0:lnz] = (r[1:nx]*r[0:nx-1])**0.5 #- 0.125*(dxdxp[1,1,1:nx]/r[1:nx]-dxdxp[1,1,0:nx-1]/r[0:nx-1])*_dx1
    #extend in theta
    rf[1:nx,ny,0:lnz] = rf[1:nx,ny-1,0:lnz]
    #extend in phi
    rf[1:nx,:,lnz]   = rf[1:nx,:,lnz-1]
    #extend in r
    rf[0] = 0*rf[0] + Rin
    rf[nx] = 0*rf[nx] + Rout
    #ANGULAR:
    hf = np.zeros((h.shape[0]+1,h.shape[1]+1,h.shape[2]+1))
    hf[0:nx,1:ny,0:lnz] = 0.5*(h[:,1:ny]+h[:,0:ny-1]) #- 0.125*(dxdxp[2,2,:,1:ny]-dxdxp[2,2,:,0:ny-1])*_dx2
    hf[1:nx-1,1:ny,0:lnz] = 0.5*(hf[0:nx-2,1:ny,0:lnz]+hf[1:nx-1,1:ny,0:lnz])
    #populate ghost cells in r
    hf[nx,1:ny,0:lnz] = hf[nx-1,1:ny,0:lnz]
    #populate ghost cells in phi
    hf[:,1:ny,lnz] = hf[:,1:ny,lnz-1]
    #populate ghost cells in theta (note: no need for this since already initialized everything to zero)
    hf[:,0] = 0*hf[:,0] + 0
    hf[:,ny] = 0*hf[:,ny] + np.pi
    #TOROIDAL:
    phf = np.zeros((ph.shape[0]+1,ph.shape[1]+1,ph.shape[2]+1))
    phf[0:nx,0:ny,0:lnz] = ph[0:nx,0:ny,0:lnz] - dxdxp[3,3,0,0,0]*0.5*_dx3
    #extend in phi
    phf[0:nx,0:ny,lnz]   = ph[0:nx,0:ny,lnz-1] + dxdxp[3,3,0,0,0]*0.5*_dx3
    #extend in r
    phf[nx,0:ny,:]   =   phf[nx-1,0:ny,:]
    #extend in theta
    phf[:,ny,:]   =   phf[:,ny-1,:]
    #indices
    #tif=np.zeros(ti.shape[0]+1,ti.shape[1]+1,ti.shape[2]+1)
    #tjf=np.zeros(tj.shape[0]+1,tj.shape[1]+1,tj.shape[2]+1)
    #tkf=np.zeros(tk.shape[0]+1,tk.shape[1]+1,tk.shape[2]+1)
    tif=np.arange(0,(nx+1)*(ny+1)*(lnz+1)).reshape((nx+1,ny+1,lnz+1),order='F')
    tjf=np.arange(0,(nx+1)*(ny+1)*(lnz+1)).reshape((nx+1,ny+1,lnz+1),order='F')
    tkf=np.arange(0,(nx+1)*(ny+1)*(lnz+1)).reshape((nx+1,ny+1,lnz+1),order='F')
    tif %= (nx+1)
    tjf /= (nx+1)
    tjf %= (ny+1)
    tkf /= (ny+1)*(lnz+1)
    gc.collect() #try to release unneeded memory
    print( "Done!" )

def grid3dlight(dumpname): #read gdump: header and body
    global nx,ny,nz,_dx1,_dx2,_dx3,ti,tj,tk,x1,x2,x3,r,h,ph,conn,gn3,gv3,ck,dxdxp,gdet
    print( "Reading grid from " + "dumps/" + dumpname + " ..." )
    gin = open( "dumps/" + dumpname, "rb" )
    header = gin.readline().split()
    nx = int(header[1])
    ny = int(header[2])
    nz = int(header[3])
    _dx1=float(header[7])
    _dx2=float(header[8])
    _dx3=float(header[9])
    gin.close()
    #read gdump
    #
    gd = np.loadtxt( "dumps/" + dumpname, 
                      dtype=np.float64, 
                      skiprows=1, 
                      unpack = True,
                      usecols=(0,1,2,3,4,5,6,7,8,105)).view().reshape((-1,nx,ny,nz), order='F')
    #gd = np.genfromtxt( "dumps/gdump", 
    #                 dtype=np.float64, 
    #                 skip_header=1, 
    #                 skip_footer=nx*ny*(nz-1),
    #                 unpack = True ).view().reshape((137,nx,ny,nz), order='F')
    ti,tj,tk,x1,x2,x3,r,h,ph,gdet = gd[:,:,:,:].view() 
    #get the right order of indices by reversing the order of indices i,j(,k)
    #conn=gd[9:73].view().reshape((4,4,4,nx,ny,nz), order='F').transpose(2,1,0,3,4,5)
    #gn3 = gd[73:89].view().reshape((4,4,nx,ny,nz), order='F').transpose(1,0,2,3,4)
    #gv3 = gd[89:105].view().reshape((4,4,nx,ny,nz), order='F').transpose(1,0,2,3,4)
    #gdet = gd[105]
    #ck = gd[106:110].view().reshape((4,nx,ny,nz), order='F')
    #dxdxp = gd[110:136].view().reshape((4,4,nx,ny,nz), order='F').transpose(1,0,2,3,4)

def rdebug(debugfname):
    global t,nx,ny,nz,_dx1,_dx2,_dx3,gam,a
    global fail0,floor0,limitgamma0,inflow0,failrho0,failu0,failrhou0,precgam0,precu0,toentropy0,tocold0,eosfail0
    global fail1,floor1,limitgamma1,inflow1,failrho1,failu1,failrhou1,precgam1,precu1,toentropy1,tocold1,eosfail1
    global fail2,floor2,limitgamma2,inflow2,failrho2,failu2,failrhou2,precgam2,precu2,toentropy2,tocold2,eosfail2
    global fail3,floor3,limitgamma3,inflow3,failrho3,failu3,failrhou3,precgam3,precu3,toentropy3,tocold3,eosfail3
    global dtot0, dtot1, dtot2, dtot3
    global lgdtot0, lgdtot1, lgdtot2, lgdtot3
    global failtot0, failtot1, failtot2, failtot3 
    global lgftot0, lgftot1, lgftot2, lgftot3 
    #read image
    fin = open( "dumps/" + debugfname, "rb" )
    header = fin.readline().split()
    t = np.float64(header[0])
    nx = int(header[1])
    ny = int(header[2])
    nz = int(header[3])
    _dx1=myfloat(float(header[7]))
    _dx2=myfloat(float(header[8]))
    _dx3=myfloat(float(header[9]))
    gam=myfloat(float(header[11]))
    a=myfloat(float(header[12]))
    if debugfname.endswith(".bin"):
        body = np.fromfile(fin,dtype=np.float64,count=-1)  #nx*ny*nz*11)
        gd = body.view().reshape((-1,nx,ny,nz),order='F')
        fin.close()
    else:
        fin.close()
        gd = np.loadtxt( "dumps/"+debugfname, 
                      dtype=np.float64, 
                      skiprows=1, 
                      unpack = True ).view().reshape((-1,nx,ny,nz), order='F')
    gd=myfloat(gd)
    (
       fail0,floor0,limitgamma0,inflow0,failrho0,failu0,failrhou0,precgam0,precu0,toentropy0,tocold0,eosfail0,
       fail1,floor1,limitgamma1,inflow1,failrho1,failu1,failrhou1,precgam1,precu1,toentropy1,tocold1,eosfail1,
       fail2,floor2,limitgamma2,inflow2,failrho2,failu2,failrhou2,precgam2,precu2,toentropy2,tocold2,eosfail2,
       fail3,floor3,limitgamma3,inflow3,failrho3,failu3,failrhou3,precgam3,precu3,toentropy3,tocold3,eosfail3
    ) = gd[0:48,:,:,:].view() 
 
    # shows where *ever* failed or not
    lg1fail=np.log10(fail0+1)
    lg1tot=np.log10(fail0+failrho0+failu0+failrhou0+1)
    #
    lg1precgam=np.log10(precgam0+1)
    lg1precu=np.log10(precu0+1)
    #
    failtot0=fail0+failrho0+failu0+failrhou0
    failtot1=fail1+failrho1+failu1+failrhou1
    failtot2=fail2+failrho2+failu2+failrhou2
    failtot3=fail3+failrho3+failu3+failrhou3
    #
    lgftot0=np.log10(failtot0+1)
    lgftot1=np.log10(failtot1+1)
    lgftot2=np.log10(failtot2+1)
    lgftot3=np.log10(failtot3+1)
    #
    failtot0sum=np.sum(failtot0)
    failtot1sum=np.sum(failtot1)
    failtot2sum=np.sum(failtot2)
    failtot3sum=np.sum(failtot3)
    #
    print( "failtotsum(0,1,2,3): %10d, %10d, %10d, %10d" % (failtot0sum, failtot1sum, failtot2sum, failtot3sum) )
    #
    # absolute totals
    dtot0=fail0+floor0+limitgamma0+failrho0+failu0+failrhou0+precgam0+precu0
    dtot1=fail1+floor1+limitgamma1+failrho1+failu1+failrhou1+precgam1+precu1
    dtot2=fail2+floor2+limitgamma2+failrho2+failu2+failrhou2+precgam2+precu2
    dtot3=fail3+floor3+limitgamma3+failrho3+failu3+failrhou3+precgam3+precu3
    #
    lgdtot0=np.log10(dtot0+1)
    lgdtot1=np.log10(dtot1+1)
    lgdtot2=np.log10(dtot2+1)
    lgdtot3=np.log10(dtot3+1)
    #
    dtot0sum=np.sum(dtot0)
    dtot1sum=np.sum(dtot1)
    dtot2sum=np.sum(dtot2)
    dtot3sum=np.sum(dtot3)
    #
    print( "   dtotsum(0,1,2,3): %10d, %10d, %10d, %10d" % (dtot0sum, dtot1sum, dtot2sum, dtot3sum) )
    #


def rfdgrid(dumpname): #read gdump: header and body
    global nx,ny,nz,_dx1,_dx2,_dx3,ti,tj,tk,x1,x2,x3,r,h,ph,conn,gn3,gv3,ck,dxdxp,gdet
    print( "Reading grid from " + "dumps/" + dumpname + " ..." )
    gin = open( "dumps/" + dumpname, "rb" )
    header = gin.readline().split()
    nx = int(header[1])
    ny = int(header[2])
    nz = int(header[3])
    _dx1=float(header[7])
    _dx2=float(header[8])
    _dx3=float(header[9])
    gin.close()
    #read gdump
    #
    gd = np.loadtxt( "dumps/" + dumpname, 
                      dtype=np.float64, 
                      skiprows=1, 
                      unpack = True,
                      usecols=(0,1,2,3,4,5,6,7,8)).view().reshape((-1,nx,ny,nz), order='F')
    #gd = np.genfromtxt( "dumps/gdump", 
    #                 dtype=float64, 
    #                 skip_header=1, 
    #                 skip_footer=nx*ny*(nz-1),
    #                 unpack = True ).view().reshape((137,nx,ny,nz), order='F')
    ti,tj,tk,x1,x2,x3,r,h,ph,gdet = gd[:,:,:,:].view() 

def compute_delta():
    """
    Returns a unit matrix
    """
    global delta
    if 'delta' in globals():
        return delta
    #
    delta = np.zeros_like((4,4,nx,ny,nz))
    for i in arange(0,4):
        delta[i,i] = 1
    return(delta)

def odot(a,b):
    """ Outer product of two vectors a^mu b_nu"""
    #the shape of the product is (4,4,nx,ny,max(a.nz,b.nz))
    outer_product = np.zeros(np.concatenate((np.array((4,4)),amax(a[0].shape,b[0].shape))),dtype=np.float32,order='F')
    for mu in np.arange(4):
        for nu in np.arange(4):
            outer_product[mu,nu] = a[mu]*b[nu]
    return(outer_product)

def mdot(a,b):
    """
    Computes a contraction of two tensors/vectors.  Assumes
    the following structure: tensor[m,n,i,j,k] OR vector[m,i,j,k], 
    where i,j,k are spatial indices and m,n are variable indices. 
    """
    if a.ndim == 4 and b.ndim == 4:
          c = (a*b).sum(0)
    elif a.ndim == 5 and b.ndim == 4:
          c = np.empty(amax(a[:,0,:,:,:].shape,b.shape),dtype=b.dtype)      
          for i in range(a.shape[0]):
                c[i,:,:,:] = (a[i,:,:,:,:]*b).sum(0)
    elif a.ndim == 4 and b.ndim == 5:
          c = np.empty(amax(b[0,:,:,:,:].shape,a.shape),dtype=a.dtype)      
          for i in range(b.shape[1]):
                c[i,:,:,:] = (a*b[:,i,:,:,:]).sum(0)
    elif a.ndim == 5 and b.ndim == 5:
          c = np.empty((a.shape[0],b.shape[1],a.shape[2],a.shape[3],max(a.shape[4],b.shape[4])),dtype=a.dtype)
          for i in range(c.shape[0]):
                for j in range(c.shape[1]):
                      c[i,j,:,:,:] = (a[i,:,:,:,:]*b[:,j,:,:,:]).sum(0)
    else:
           raise Exception('mdot', 'wrong dimensions')
    return c

def fieldcalc(gdetB1=None):
    """
    Computes the field vector potential
    """
    #return((1-h[:,:,0]/np.pi)[:,:,None]*fieldcalcp()+(h[:,:,0]/np.pi)[:,:,None]*fieldcalcm())
    return(fieldcalcU(gdetB1))

def mysum2(vec):
    #return( vec[:,:,0][:,:,None]*nz )
    return( np.sum(vec, axis=2)[:,:,None] )

def fcalc():
    """
    Computes the field vector potential
    """
    daphi = np.sum(gdet*B[1],axis=2)*_dx2*_dx3
    aphi=daphi.cumsum(axis=1)
    aphi/=(nz*_dx3)
    return(aphi)

def fieldcalcp():
    """
    Computes the field vector potential
    """
    daphi = mysum2(gdet*B[1])*_dx2*_dx3
    aphi=daphi.cumsum(axis=1)
    aphi/=(nz*_dx3)
    return(aphi)

def fieldcalcm():
    """
    Computes the field vector potential
    """
    daphi = mysum2(gdet*B[1])*_dx2*_dx3
    aphi=(-daphi[:,::-1].cumsum(axis=1))[:,::-1]
    aphi/=(nz*_dx3)
    return(aphi)

def fieldcalc2():
    """
    Computes the field vector potential
    """
    #daphi = (gdet*B[1]).sum(2)*_dx2*_dx3
    #aphi=daphi.cumsum(axis=1)
    daphi = (-gdet*B[2]).sum(2)*_dx2*_dx3
    #np.zeros_like(B[1,:,:,0:1])
    daphi1 = (gdet[0]*B[1,0]).sum(1).cumsum(axis=0)*_dx2*_dx3
    daphi[0,:] += daphi1
    aphi=daphi.cumsum(axis=0)
    aphi/=(nz*_dx3)
    return(aphi[:,:,None])

def fieldcalc2U():
    """
    Computes the field vector potential
    """
    #daphi = (gdet*B[1]).sum(2)*_dx2*_dx3
    #aphi=daphi.cumsum(axis=1)
    daphi = (-gdetB[2]).sum(2)*_dx2*_dx3
    #np.zeros_like(B[1,:,:,0:1])
    daphi1 = (gdetB[1,0]).sum(1).cumsum(axis=0)*_dx2*_dx3
    daphi[0,:] += daphi1
    aphi=daphi.cumsum(axis=0)
    aphi=scaletofullwedge(aphi)
    return(aphi[:,:,None])

def horfluxcalc(ihor=None,minbsqorho=10):
    """
    Computes the absolute flux through the sphere i = ihor
    """
    global gdetB, _dx2, _dx3
    #1D function of theta only:
    dfabs = (np.abs(gdetB[1]*(bsq/rho>minbsqorho))).sum(2)*_dx2*_dx3
    fabs = dfabs.sum(axis=1)
    #account for the wedge
    fabs=scaletofullwedge(fabs)
    #fabs *= 
    if ihor == None:
        return(fabs)
    else:
        return(fabs[ihor])


def scaletofullwedge(val):
    return(val * 2*np.pi/(dxdxp[3,3,0,0,0]*nz*_dx3))

# def mdotcalc(whichi=None,minbsqorho=None):
#     mdotden = -gdet*rho*uu[1]
#     if minbsqorho != None:
#         mdotden[bsq/rho<minbsqorho<minbsqorho] = 0*mdotden[bsq/rho<minbsqorho<minbsqorho] 
#     mdottot = scaletofullwedge(np.sum(np.sum(mdotden,axis=2),axis=1)*_dx2*_dx3)
#     if whichi == None:
#         return(mdottot)
#     else:
#         return(mdottot[whichi])

def mdotcalc(ihor=None,**kwargs):
    """
    Computes the absolute flux through the sphere i = ihor
    """
    #1D function of theta only:
    md = intangle( -gdet*rho*uu[1], **kwargs)
    if ihor==None:
        return(md)
    else:
        return(md[ihor])

def diskfluxcalc(jmid,rmin=None,rmax=None):
    """
    Computes the absolute flux through the disk midplane at j = jmid
    """
    global gdetB,_dx1,_dx3,r
    #1D function of theta only:
    dfabs = (np.abs(gdetB[2,:,jmid,:])).sum(1)*_dx1*_dx3
    if rmax != None:
        dfabs = dfabs*(r[:,0,0]<=rmax)
    if rmin != None:
        dfabs = dfabs*(r[:,0,0]>=rmin)
    fabs = dfabs.sum(axis=0)
    fabs=scaletofullwedge(fabs)
    return(fabs)

def mfjhorvstime(ihor):
    """
    Returns a tuple (ts,fs,mdot,pjetem,pjettot): lists of times, horizon fluxes, and Mdot
    """
    flist = np.sort(glob.glob( os.path.join("dumps/", "fieldline*.bin") ) )
    flist.sort()
    ts=np.empty(len(flist),dtype=np.float32)
    fs=np.empty(len(flist),dtype=np.float32)
    md=np.empty(len(flist),dtype=np.float32)
    jem=np.empty(len(flist),dtype=np.float32)
    jtot=np.empty(len(flist),dtype=np.float32)
    for findex, fname in enumerate(flist):
        print( "Reading " + fname + " ..." )
        rfd("../"+fname)
        cvel()
        Tcalcud()
        fs[findex]=horfluxcalc(ihor)
        md[findex]=mdotcalc(ihor)
        #EM
        jem[findex]=jetpowcalc(0)[ihor]
        #tot
        jtot[findex]=jetpowcalc(2)[ihor]
        ts[findex]=t
        #if os.path.isfile("lrho%04d.png" % findex):
        #    print( "Skipping " + fname + " as lrho%04d.png exists" % findex );
        #else:
        #    print( "Reinterpolating " + fname + " ..." )
        #    plt.figure(0)
        #    plt.clf()
        #    mkframe("lrho%04d" % findex, vmin=-8,vmax=0.2)
    print( "Done!" )
    return((ts,fs,md,jem,jtot))

def mergeqtyvstime(n):
    for i in np.arange(n):
        #load each file
        fname = "qty2_%d_%d.npy" % (i, n)
        print( "Loading " + fname + " ..." )
        sys.stdout.flush()
        qtymemtemp = np.load( fname )
        #per-element sum relevant parts of each file
        if i == 0:
            qtymem = np.zeros_like(qtymemtemp)
        #1st index: whichqty
        #2nd index: whichdumpnumber
        qtymem[:,i::n] += qtymemtemp[:,i::n]
    fname = "qty2.npy"
    print( "Saving into " + fname + " ..." )
    sys.stdout.flush()
    np.save( fname , qtymem )
    print( "Done!" )
        

def getqtyvstime(ihor,horval=0.2,fmtver=2,dobob=0,whichi=None,whichn=None):
    """
    Returns a tuple (ts,fs,mdot,pjetem,pjettot): lists of times, horizon fluxes, and Mdot
    """
    if whichn != None and (whichi < 0 or whichi > whichn):
        print( "whichi = %d shoudl be >= 0 and < whichn = %d" % (whichi, whichn) )
        return( -1 )
    if 'rho' in globals():
        tiny=np.finfo(rho.dtype).tiny
    else:
        tiny = np.finfo(np.float64).tiny
    flist = glob.glob( os.path.join("dumps/", "fieldline*.bin") )
    flist.sort()
    nqtyold=98+134*(dobob==1)
    nqtyold2=98+134*(dobob==1)+32+1
    # jon's mumax addition and edm addition
    nqty=98+134*(dobob==1)+32+1+8+2+1
    #store 1D data
    numtimeslices=len(flist)
    qtymem=np.zeros((nqty,numtimeslices,nx),dtype=np.float32)
    #np.seterr(invalid='raise',divide='raise')
    #
    print "Number of time slices: %d" % numtimeslices
    if whichi >=0 and whichi < whichn:
        fname = "qty2_%d_%d.npy" % (whichi, whichn)
    else:
        fname = "qty2.npy" 
    if fmtver == 2 and os.path.isfile( fname ):
        qtymem2=np.load( fname )
        numtimeslices2 = qtymem2.shape[1]
        #require same number of variables, don't allow format changes on the fly for safety
        print "Number of previously saved time slices: %d" % numtimeslices2 
        if( numtimeslices2 >= numtimeslices ):
            print "Number of previously saved time slices is >= than of timeslices to be loaded, re-using previously saved time slices"
            return(qtymem2)
        else:
            assert qtymem2.shape[0] == qtymem.shape[0]
            print "Number of previously saved time slices is < than of timeslices to be loaded, re-using previously saved time slices"
            qtymem[:,0:numtimeslices2] = qtymem2[:,0:numtimeslices2]
            qtymem2=None
    elif fmtver == 1 and os.path.isfile("qty.npy"):
        qtymem2=np.load( "qty.npy" )
        numtimeslices2 = qtymem2.shape[1]
        print "Number of previously saved time slices: %d" % numtimeslices2 
        print "Instructed to use old format, reusing prev. saved slices"
        return(qtymem2)
    else:
        numtimeslices2 = 0
    #qty defs
    i=0
    ts=qtymem[i,:,0];i+=1
    #HoverR
    hoverr=qtymem[i];i+=1
    thetamid=qtymem[i];i+=1
    #rhosq:
    rhosqs=qtymem[i];i+=1
    rhosrhosq=qtymem[i];i+=1
    ugsrhosq=qtymem[i];i+=1
    uu0rhosq=qtymem[i];i+=1
    uus1rhosq=qtymem[i];i+=1
    uuas1rhosq=qtymem[i];i+=1
    uus3rhosq=qtymem[i];i+=1
    uuas3rhosq=qtymem[i];i+=1
    Bs1rhosq=qtymem[i];i+=1
    Bas1rhosq=qtymem[i];i+=1
    Bs2rhosq=qtymem[i];i+=1
    Bas2rhosq=qtymem[i];i+=1
    Bs3rhosq=qtymem[i];i+=1
    Bas3rhosq=qtymem[i];i+=1
    #2h
    gdetint2h=qtymem[i];i+=1
    rhos2h=qtymem[i];i+=1
    ugs2h=qtymem[i];i+=1
    uu02h=qtymem[i];i+=1
    uus12h=qtymem[i];i+=1
    uuas12h=qtymem[i];i+=1
    uus32h=qtymem[i];i+=1
    uuas32h=qtymem[i];i+=1
    Bs12h=qtymem[i];i+=1
    Bas12h=qtymem[i];i+=1
    Bs22h=qtymem[i];i+=1
    Bas22h=qtymem[i];i+=1
    Bs32h=qtymem[i];i+=1
    Bas32h=qtymem[i];i+=1
    #4h
    gdetint4h=qtymem[i];i+=1
    rhos4h=qtymem[i];i+=1
    ugs4h=qtymem[i];i+=1
    uu04h=qtymem[i];i+=1
    uus14h=qtymem[i];i+=1
    uuas14h=qtymem[i];i+=1
    uus34h=qtymem[i];i+=1
    uuas34h=qtymem[i];i+=1
    Bs14h=qtymem[i];i+=1
    Bas14h=qtymem[i];i+=1
    Bs24h=qtymem[i];i+=1
    Bas24h=qtymem[i];i+=1
    Bs34h=qtymem[i];i+=1
    Bas34h=qtymem[i];i+=1
    #2hor
    gdetint2hor=qtymem[i];i+=1
    rhos2hor=qtymem[i];i+=1
    ugs2hor=qtymem[i];i+=1
    bsqs2hor=qtymem[i];i+=1
    bsqorhos2hor=qtymem[i];i+=1
    bsqougs2hor=qtymem[i];i+=1
    uu02hor=qtymem[i];i+=1
    uus12hor=qtymem[i];i+=1
    uuas12hor=qtymem[i];i+=1
    uus32hor=qtymem[i];i+=1
    uuas32hor=qtymem[i];i+=1
    Bs12hor=qtymem[i];i+=1
    Bas12hor=qtymem[i];i+=1
    Bs22hor=qtymem[i];i+=1
    Bas22hor=qtymem[i];i+=1
    Bs32hor=qtymem[i];i+=1
    Bas32hor=qtymem[i];i+=1
    #Flux
    fstot=qtymem[i];i+=1
    fs2hor=qtymem[i];i+=1
    fsj5=qtymem[i];i+=1
    fsj10=qtymem[i];i+=1
    fsj20=qtymem[i];i+=1
    fsj30=qtymem[i];i+=1
    fsj40=qtymem[i];i+=1
    #Mdot
    mdtot=qtymem[i];i+=1
    md2h=qtymem[i];i+=1
    md4h=qtymem[i];i+=1
    md2hor=qtymem[i];i+=1
    md5=qtymem[i];i+=1
    md10=qtymem[i];i+=1
    md20=qtymem[i];i+=1
    md30=qtymem[i];i+=1
    mdwind=qtymem[i];i+=1
    mdjet=qtymem[i];i+=1
    md40=qtymem[i];i+=1
    mdrhosq=qtymem[i];i+=1
    mdtotbound=qtymem[i];i+=1
    #Edot
    edtot=qtymem[i];i+=1
    ed2h=qtymem[i];i+=1
    ed4h=qtymem[i];i+=1
    ed2hor=qtymem[i];i+=1
    edrhosq=qtymem[i];i+=1
    edma=qtymem[i];i+=1
    edm=qtymem[i];i+=1
    edtotbound=qtymem[i];i+=1
    edmabound=qtymem[i];i+=1
    #Pjet
    pjem5=qtymem[i];i+=1
    pjem10=qtymem[i];i+=1
    pjem20=qtymem[i];i+=1
    pjem30=qtymem[i];i+=1
    pjem40=qtymem[i];i+=1
    pjma5=qtymem[i];i+=1
    pjma10=qtymem[i];i+=1
    pjma20=qtymem[i];i+=1
    pjma30=qtymem[i];i+=1
    pjma40=qtymem[i];i+=1
    #new format?
    if qtymem.shape[0] > nqtyold:
        #yes!
        pjem_n_mu10=qtymem[i];i+=1
        pjem_n_mu5=qtymem[i];i+=1
        pjem_n_mu2=qtymem[i];i+=1
        pjem_n_mu1=qtymem[i];i+=1
        pjem_n_mumax1=qtymem[i];i+=1
        pjrm_n_mu10=qtymem[i];i+=1
        pjrm_n_mu5=qtymem[i];i+=1
        pjrm_n_mu2=qtymem[i];i+=1
        pjrm_n_mu1=qtymem[i];i+=1
        pjrm_n_mumax1=qtymem[i];i+=1
        pjma_n_mu10=qtymem[i];i+=1
        pjma_n_mu5=qtymem[i];i+=1
        pjma_n_mu2=qtymem[i];i+=1
        pjma_n_mu1=qtymem[i];i+=1
        pjma_n_mumax1=qtymem[i];i+=1
        phiabsj_n_mu10=qtymem[i];i+=1
        phiabsj_n_mu5=qtymem[i];i+=1
        phiabsj_n_mu2=qtymem[i];i+=1
        phiabsj_n_mu1=qtymem[i];i+=1
        phiabsj_n_mumax1=qtymem[i];i+=1
        pjem_s_mu10=qtymem[i];i+=1
        pjem_s_mu5=qtymem[i];i+=1
        pjem_s_mu2=qtymem[i];i+=1
        pjem_s_mu1=qtymem[i];i+=1
        pjem_s_mumax1=qtymem[i];i+=1
        pjrm_s_mu10=qtymem[i];i+=1
        pjrm_s_mu5=qtymem[i];i+=1
        pjrm_s_mu2=qtymem[i];i+=1
        pjrm_s_mu1=qtymem[i];i+=1
        pjrm_s_mumax1=qtymem[i];i+=1
        pjma_s_mu10=qtymem[i];i+=1
        pjma_s_mu5=qtymem[i];i+=1
        pjma_s_mu2=qtymem[i];i+=1
        pjma_s_mu1=qtymem[i];i+=1
        pjma_s_mumax1=qtymem[i];i+=1
        phiabsj_s_mu10=qtymem[i];i+=1
        phiabsj_s_mu5=qtymem[i];i+=1
        phiabsj_s_mu2=qtymem[i];i+=1
        phiabsj_s_mu1=qtymem[i];i+=1
        phiabsj_s_mumax1=qtymem[i];i+=1
        if i < qtymem.shape[0]:
            ldtot=qtymem[i];i+=1
        else:
            ldtot=None
    else:
        print( "Oldish format: missing north/south jet power and flux" )
        sys.stdout.flush()
        pjem_n_mu10=None
        pjem_n_mu5=None
        pjem_n_mu2=None
        pjem_n_mu1=None
        pjem_n_mumax1=None
        pjrm_n_mu10=None
        pjrm_n_mu5=None
        pjrm_n_mu2=None
        pjrm_n_mu1=None
        pjrm_n_mumax1=None
        pjma_n_mu10=None
        pjma_n_mu5=None
        pjma_n_mu2=None
        pjma_n_mu1=None
        pjma_n_mumax1=None
        phiabsj_n_mu10=None
        phiabsj_n_mu5=None
        phiabsj_n_mu2=None
        phiabsj_n_mu1=None
        phiabsj_n_mumax1=None
        pjem_s_mu10=None
        pjem_s_mu5=None
        pjem_s_mu2=None
        pjem_s_mu1=None
        pjem_s_mumax1=None
        pjrm_s_mu10=None
        pjrm_s_mu5=None
        pjrm_s_mu2=None
        pjrm_s_mu1=None
        pjrm_s_mumax1=None
        pjma_s_mu10=None
        pjma_s_mu5=None
        pjma_s_mu2=None
        pjma_s_mu1=None
        pjma_s_mumax1=None
        phiabsj_s_mu10=None
        phiabsj_s_mu5=None
        phiabsj_s_mu2=None
        phiabsj_s_mu1=None
        phiabsj_s_mumax1=None
        ldtot=None
    if dobob == 1:
        print "Total number of quantities: %d+134 = %d" % (i, i+134)
    else:
        print "Total number of quantities: %d" % (i)
    if( whichi >=0 and whichn > 0 ):
        print "Doing every %d-th slice of %d" % (whichi, whichn)
    sys.stdout.flush()
    #end qty defs
    for findex, fname in enumerate(flist):
        if( whichi >=0 and whichn > 0 ):
            if( findex % whichn != whichi ):
                continue
        #skip pre-loaded time slices
        if findex < numtimeslices2: 
            continue
        #call garbage collector -- trying to get req'd memory under control
        gc.collect()
        print( "Reading " + fname + " ..." )
        sys.stdout.flush()
        rfd("../"+fname)
        print( "Computing " + fname + " ..." )
        sys.stdout.flush()
        cvel()
        Tcalcud()
        ts[findex]=t
        #HoverR
        diskcondition=bsq/rho<10
        hoverr3d,thetamid3d=horcalc(which=diskcondition)
        hoverr[findex]=hoverr3d.sum(2).sum(1)/(ny*nz)
        thetamid[findex]=thetamid3d.sum(2).sum(1)/(ny*nz)
        #rhosq:
        keywordsrhosq={'which': diskcondition}
        gdetint=intangle(gdet,**keywordsrhosq)
        rhosqint=intangle(gdet*rho**2,**keywordsrhosq)+tiny
        rhosqs[findex]=rhosqint
        maxrhosq2d=(rho**2*diskcondition).max(1)+tiny
        maxrhosq3d=np.empty_like(rho)
        for j in np.arange(0,ny):
            maxrhosq3d[:,j,:] = maxrhosq2d
        rhosrhosq[findex]=intangle(gdet*rho**2*rho,**keywordsrhosq)/rhosqint
        ugsrhosq[findex]=intangle(gdet*rho**2*ug,**keywordsrhosq)/rhosqint
        uu0rhosq[findex]=intangle(gdet*rho**2*uu[0],**keywordsrhosq)/rhosqint
        uus1rhosq[findex]=intangle(gdet*rho**2*uu[1],**keywordsrhosq)/rhosqint
        uuas1rhosq[findex]=intangle(gdet*rho**2*np.abs(uu[1]),**keywordsrhosq)/rhosqint
        uus3rhosq[findex]=intangle(gdet*rho**2*uu[3],**keywordsrhosq)/rhosqint
        uuas3rhosq[findex]=intangle(gdet*rho**2*np.abs(uu[3]),**keywordsrhosq)/rhosqint
        Bs1rhosq[findex]=intangle(gdetB[1]*rho**2,**keywordsrhosq)/rhosqint
        Bas1rhosq[findex]=intangle(np.abs(gdetB[1])*rho**2,**keywordsrhosq)/rhosqint
        Bs2rhosq[findex]=intangle(gdetB[2]*rho**2,**keywordsrhosq)/rhosqint
        Bas2rhosq[findex]=intangle(np.abs(gdetB[2])*rho**2,**keywordsrhosq)/rhosqint
        Bs3rhosq[findex]=intangle(gdetB[3]*rho**2,**keywordsrhosq)/rhosqint
        Bas3rhosq[findex]=intangle(np.abs(gdetB[3])*rho**2,**keywordsrhosq)/rhosqint
        #2h
        keywords2h={'hoverr': 2*horval, 'which': diskcondition}
        gdetint=intangle(gdet,**keywords2h)+tiny
        gdetint2h[findex]=gdetint
        rhos2h[findex]=intangle(gdet*rho,**keywords2h)/gdetint
        ugs2h[findex]=intangle(gdet*ug,**keywords2h)/gdetint
        uu02h[findex]=intangle(gdet*uu[0],**keywords2h)/gdetint
        uus12h[findex]=intangle(gdet*uu[1],**keywords2h)/gdetint
        uuas12h[findex]=intangle(gdet*np.abs(uu[1]),**keywords2h)/gdetint
        uus32h[findex]=intangle(gdet*uu[3],**keywords2h)/gdetint
        uuas32h[findex]=intangle(gdet*np.abs(uu[3]),**keywords2h)/gdetint
        Bs12h[findex]=intangle(gdetB[1],**keywords2h)/gdetint
        Bas12h[findex]=intangle(np.abs(gdetB[1]),**keywords2h)/gdetint
        Bs22h[findex]=intangle(gdetB[2],**keywords2h)/gdetint
        Bas22h[findex]=intangle(np.abs(gdetB[2]),**keywords2h)/gdetint
        Bs32h[findex]=intangle(gdetB[3],**keywords2h)/gdetint
        Bas32h[findex]=intangle(np.abs(gdetB[3]),**keywords2h)/gdetint
        #4h
        keywords4h={'hoverr': 4*horval, 'which': diskcondition}
        gdetint=intangle(gdet,**keywords4h)
        gdetint4h[findex]=gdetint+tiny
        rhos4h[findex]=intangle(gdet*rho,**keywords4h)/gdetint
        ugs4h[findex]=intangle(gdet*ug,**keywords4h)/gdetint
        uu04h[findex]=intangle(gdet*uu[0],**keywords4h)/gdetint
        uus14h[findex]=intangle(gdet*uu[1],**keywords4h)/gdetint
        uuas14h[findex]=intangle(gdet*np.abs(uu[1]),**keywords4h)/gdetint
        uus34h[findex]=intangle(gdet*uu[3],**keywords4h)/gdetint
        uuas34h[findex]=intangle(gdet*np.abs(uu[3]),**keywords4h)/gdetint
        Bs14h[findex]=intangle(gdetB[1],**keywords4h)/gdetint
        Bas14h[findex]=intangle(np.abs(gdetB[1]),**keywords4h)/gdetint
        Bs24h[findex]=intangle(gdetB[2],**keywords4h)/gdetint
        Bas24h[findex]=intangle(np.abs(gdetB[2]),**keywords4h)/gdetint
        Bs34h[findex]=intangle(gdetB[3],**keywords4h)/gdetint
        Bas34h[findex]=intangle(np.abs(gdetB[3]),**keywords4h)/gdetint
        #2hor
        keywords2hor={'hoverr': 2*hoverr3d, 'thetamid': thetamid3d, 'which': diskcondition}
        gdetint=intangle(gdet,**keywords2hor)
        gdetint2hor[findex]=gdetint+tiny
        rhos2hor[findex]=intangle(gdet*rho,**keywords2hor)/gdetint
        ugs2hor[findex]=intangle(gdet*ug,**keywords2hor)/gdetint
        bsqs2hor[findex]=intangle(bsq,**keywords2hor)/gdetint
        bsqorhos2hor[findex]=intangle(bsq/rho,**keywords2hor)/gdetint
        bsqougs2hor[findex]=intangle(bsq/ug,**keywords2hor)/gdetint
        uu02hor[findex]=intangle(gdet*uu[0],**keywords2hor)/gdetint
        uus12hor[findex]=intangle(gdet*uu[1],**keywords2hor)/gdetint
        uuas12hor[findex]=intangle(gdet*np.abs(uu[1]),**keywords2hor)/gdetint
        uus32hor[findex]=intangle(gdet*uu[3],**keywords2hor)/gdetint
        uuas32hor[findex]=intangle(gdet*np.abs(uu[3]),**keywords2hor)/gdetint
        Bs12hor[findex]=intangle(gdetB[1],**keywords2hor)/gdetint
        Bas12hor[findex]=intangle(np.abs(gdetB[1]),**keywords2hor)/gdetint
        Bs22hor[findex]=intangle(gdetB[2],**keywords2hor)/gdetint
        Bas22hor[findex]=intangle(np.abs(gdetB[2]),**keywords2hor)/gdetint
        Bs32hor[findex]=intangle(gdetB[3],**keywords2hor)/gdetint
        Bas32hor[findex]=intangle(np.abs(gdetB[3]),**keywords2hor)/gdetint
        #Flux
        fstot[findex]=horfluxcalc(minbsqorho=0)
        fs2hor[findex]==intangle(np.abs(gdetB[1]),**keywords2hor)
        fsj5[findex]=horfluxcalc(minbsqorho=5)
        fsj10[findex]=horfluxcalc(minbsqorho=10)
        fsj20[findex]=horfluxcalc(minbsqorho=20)
        fsj30[findex]=horfluxcalc(minbsqorho=30)
        fsj40[findex]=horfluxcalc(minbsqorho=40)
        #Mdot
        enth=1+ug*gam/rho
        mdtot[findex]=mdotcalc()
        mdtotbound[findex]=mdotcalc(which=(-enth*ud[0]<=1))
        md2h[findex]=mdotcalc(**keywords2h)
        md4h[findex]=mdotcalc(**keywords4h)
        md2hor[findex]=mdotcalc(**keywords2hor)
        md5[findex]=intangle(-gdet*rho*uu[1],minbsqorho=5)
        md10[findex]=intangle(-gdet*rho*uu[1],minbsqorho=10)
        md20[findex]=intangle(-gdet*rho*uu[1],minbsqorho=20)
        md30[findex]=intangle(-gdet*rho*uu[1],minbsqorho=30)
        mdwind[findex]=intangle(gdet*rho*uu[1],mumax=1,maxbeta=3)
        mdjet[findex]=intangle(gdet*rho*uu[1],mumin=1)
        md40[findex]=intangle(-gdet*rho*uu[1],minbsqorho=40)
        mdrhosq[findex]=scaletofullwedge(((-gdet*rho**2*rho*uu[1]*diskcondition).sum(1)/maxrhosq2d).sum(1)*_dx2*_dx3)
        #mdrhosq[findex]=(-gdet*rho**2*rho*uu[1]).sum(1).sum(1)/(-gdet*rho**2).sum(1).sum(1)*(-gdet).sum(1).sum(1)*_dx2*_dx3
        #Edot
        edtot[findex]=intangle(-gdet*Tud[1][0])
        edma[findex]=intangle(-gdet*TudMA[1][0])
        edm[findex]=intangle(gdet*rho*uu[1])
        edtotbound[findex]=intangle(-gdet*Tud[1][0],which=(-enth*ud[0]<=1))
        edmabound[findex]=intangle(-gdet*TudMA[1][0],which=(-enth*ud[0]<=1))
        ed2h[findex]=intangle(-gdet*Tud[1][0],hoverr=2*horval)
        ed4h[findex]=intangle(-gdet*Tud[1][0],hoverr=4*horval)
        ed2hor[findex]=intangle(-gdet*Tud[1][0],hoverr=2*hoverr3d,thetamid=thetamid3d)
        edrhosq[findex]=scaletofullwedge(((-gdet*rho**2*Tud[1][0]).sum(1)/maxrhosq2d).sum(1)*_dx2*_dx3)
        #Pjet
        pjem5[findex]=jetpowcalc(0,minbsqorho=5)
        pjem10[findex]=jetpowcalc(0,minbsqorho=10)
        pjem20[findex]=jetpowcalc(0,minbsqorho=20)
        pjem30[findex]=jetpowcalc(0,minbsqorho=30)
        pjem40[findex]=jetpowcalc(0,minbsqorho=40)
        pjma5[findex]=jetpowcalc(1,minbsqorho=5)
        pjma10[findex]=jetpowcalc(1,minbsqorho=10)
        pjma20[findex]=jetpowcalc(1,minbsqorho=20)
        pjma30[findex]=jetpowcalc(1,minbsqorho=30)
        pjma40[findex]=jetpowcalc(1,minbsqorho=40)

        #new format?
        if qtymem.shape[0] > nqtyold:
            #yes!
            #north hemisphere
            pjem_n_mu10[findex]=jetpowcalc(0,mumin=10,donorthsouth=1)
            pjem_n_mu5[findex]=jetpowcalc(0,mumin=5,donorthsouth=1)
            pjem_n_mu2[findex]=jetpowcalc(0,mumin=2,donorthsouth=1)
            pjem_n_mu1[findex]=jetpowcalc(0,mumin=1,donorthsouth=1)
            pjem_n_mumax1[findex]=jetpowcalc(0,mumax=1,maxbeta=3,donorthsouth=1)
            pjrm_n_mu10[findex]=jetpowcalc(3,mumin=10,donorthsouth=1)
            pjrm_n_mu5[findex]=jetpowcalc(3,mumin=5,donorthsouth=1)
            pjrm_n_mu2[findex]=jetpowcalc(3,mumin=2,donorthsouth=1)
            pjrm_n_mu1[findex]=jetpowcalc(3,mumin=1,donorthsouth=1)
            pjrm_n_mumax1[findex]=jetpowcalc(3,mumax=1,maxbeta=3,donorthsouth=1)
            pjma_n_mu10[findex]=jetpowcalc(1,mumin=10,donorthsouth=1)
            pjma_n_mu5[findex]=jetpowcalc(1,mumin=5,donorthsouth=1)
            pjma_n_mu2[findex]=jetpowcalc(1,mumin=2,donorthsouth=1)
            pjma_n_mu1[findex]=jetpowcalc(1,mumin=1,donorthsouth=1)
            pjma_n_mumax1[findex]=jetpowcalc(1,mumax=1,maxbeta=3,donorthsouth=1)
            phiabsj_n_mu10[findex]=jetpowcalc(4,mumin=10,donorthsouth=1)
            phiabsj_n_mu5[findex]=jetpowcalc(4,mumin=5,donorthsouth=1)
            phiabsj_n_mu2[findex]=jetpowcalc(4,mumin=2,donorthsouth=1)
            phiabsj_n_mu1[findex]=jetpowcalc(4,mumin=1,donorthsouth=1)
            phiabsj_n_mumax1[findex]=jetpowcalc(4,mumax=1,maxbeta=3,donorthsouth=1)
            #south hemisphere
            pjem_s_mu10[findex]=jetpowcalc(0,mumin=10,donorthsouth=-1)
            pjem_s_mu5[findex]=jetpowcalc(0,mumin=5,donorthsouth=-1)
            pjem_s_mu2[findex]=jetpowcalc(0,mumin=2,donorthsouth=-1)
            pjem_s_mu1[findex]=jetpowcalc(0,mumin=1,donorthsouth=-1)
            pjem_s_mumax1[findex]=jetpowcalc(0,mumax=1,maxbeta=3,donorthsouth=-1)
            pjrm_s_mu10[findex]=jetpowcalc(3,mumin=10,donorthsouth=-1)
            pjrm_s_mu5[findex]=jetpowcalc(3,mumin=5,donorthsouth=-1)
            pjrm_s_mu2[findex]=jetpowcalc(3,mumin=2,donorthsouth=-1)
            pjrm_s_mu1[findex]=jetpowcalc(3,mumin=1,donorthsouth=-1)
            pjrm_s_mumax1[findex]=jetpowcalc(3,mumax=1,maxbeta=3,donorthsouth=-1)
            pjma_s_mu10[findex]=jetpowcalc(1,mumin=10,donorthsouth=-1)
            pjma_s_mu5[findex]=jetpowcalc(1,mumin=5,donorthsouth=-1)
            pjma_s_mu2[findex]=jetpowcalc(1,mumin=2,donorthsouth=-1)
            pjma_s_mu1[findex]=jetpowcalc(1,mumin=1,donorthsouth=-1)
            pjma_s_mumax1[findex]=jetpowcalc(1,mumax=1,maxbeta=3,donorthsouth=-1)
            phiabsj_s_mu10[findex]=jetpowcalc(4,mumin=10,donorthsouth=-1)
            phiabsj_s_mu5[findex]=jetpowcalc(4,mumin=5,donorthsouth=-1)
            phiabsj_s_mu2[findex]=jetpowcalc(4,mumin=2,donorthsouth=-1)
            phiabsj_s_mu1[findex]=jetpowcalc(4,mumin=1,donorthsouth=-1)
            phiabsj_s_mumax1[findex]=jetpowcalc(4,mumax=1,maxbeta=3,donorthsouth=-1)
            if ldtot is not None:
                ldtot[findex]=intangle(gdet*Tud[1][3])

        #Bob's 1D quantities
        if dobob==1:
                dVF=_dx1*_dx2*_dx3
                dVA=_dx2*_dx3
                Dt=1
                TT=0
                RR=1
                TH=2
                PH=3
        	qtymem[i+0,findex]=intangle(Dt*dVF*gdet*rho,**keywords2hor)
        	qtymem[i+1,findex]=intangle(Dt*dVF*gdet*rho*rho,**keywords2hor)
        	qtymem[i+2,findex]=intangle(Dt*dVF*gdet*rho*ug,**keywords2hor)
        	qtymem[i+3,findex]=intangle(Dt*dVF*gdet*rho*bsq,**keywords2hor)
        
        	qtymem[i+4,findex]=intangle(Dt*dVF*gdet*rho*uu[1],**keywords2hor) #pr[2]
        	qtymem[i+5,findex]=intangle(Dt*dVF*gdet*rho*uu[2],**keywords2hor) #pr[3]
        	qtymem[i+6,findex]=intangle(Dt*dVF*gdet*rho*uu[3],**keywords2hor) #pr[4]
        
        	qtymem[i+7,findex]=intangle(Dt*dVF*gdet*rho*B[1],**keywords2hor) #pr[5]
        	qtymem[i+8,findex]=intangle(Dt*dVF*gdet*rho*B[2],**keywords2hor) #pr[6]
        	qtymem[i+9,findex]=intangle(Dt*dVF*gdet*rho*B[3],**keywords2hor) #pr[7]
        
        	#rho * u * u
        
        	qtymem[i+10,findex]=intangle(Dt*dVA*gdet*rho*(ud[TT])*(ud[TT]),**keywords2hor)
        	qtymem[i+11,findex]=intangle(Dt*dVA*gdet*rho*(ud[TT])*(ud[RR]),**keywords2hor)
        	qtymem[i+12,findex]=intangle(Dt*dVA*gdet*rho*(ud[TT])*(ud[TH]),**keywords2hor)
        	qtymem[i+13,findex]=intangle(Dt*dVA*gdet*rho*(ud[TT])*(ud[PH]),**keywords2hor)
        	qtymem[i+14,findex]=intangle(Dt*dVA*gdet*rho*(ud[RR])*(ud[RR]),**keywords2hor)
        	qtymem[i+15,findex]=intangle(Dt*dVA*gdet*rho*(ud[RR])*(ud[TH]),**keywords2hor)
        	qtymem[i+16,findex]=intangle(Dt*dVA*gdet*rho*(ud[RR])*(ud[PH]),**keywords2hor)
        	qtymem[i+17,findex]=intangle(Dt*dVA*gdet*rho*(ud[TH])*(ud[TH]),**keywords2hor)
        	qtymem[i+18,findex]=intangle(Dt*dVA*gdet*rho*(ud[TH])*(ud[PH]),**keywords2hor)
        	qtymem[i+19,findex]=intangle(Dt*dVA*gdet*rho*(ud[PH])*(ud[PH]),**keywords2hor)
        
        	qtymem[i+20,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT])*(ud[TT]),**keywords2hor)
        	qtymem[i+21,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT])*(ud[RR]),**keywords2hor)
        	qtymem[i+22,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT])*(ud[TH]),**keywords2hor)
        	qtymem[i+23,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT])*(ud[PH]),**keywords2hor)
        	qtymem[i+24,findex]=intangle(Dt*dVA*gdet*rho*(uu[RR])*(ud[RR]),**keywords2hor)
        	qtymem[i+25,findex]=intangle(Dt*dVA*gdet*rho*(uu[RR])*(ud[TH]),**keywords2hor)
        	qtymem[i+26,findex]=intangle(Dt*dVA*gdet*rho*(uu[RR])*(ud[PH]),**keywords2hor)
        	qtymem[i+27,findex]=intangle(Dt*dVA*gdet*rho*(uu[TH])*(ud[TH]),**keywords2hor)
        	qtymem[i+28,findex]=intangle(Dt*dVA*gdet*rho*(uu[TH])*(ud[PH]),**keywords2hor)
        	qtymem[i+29,findex]=intangle(Dt*dVA*gdet*rho*(uu[PH])*(ud[PH]),**keywords2hor)
        
        	qtymem[i+30,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT])*(uu[TT]),**keywords2hor)
        	qtymem[i+31,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT])*(uu[RR]),**keywords2hor)
        	qtymem[i+32,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT])*(uu[TH]),**keywords2hor)
        	qtymem[i+33,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT])*(uu[PH]),**keywords2hor)
        	qtymem[i+34,findex]=intangle(Dt*dVA*gdet*rho*(uu[RR])*(uu[RR]),**keywords2hor)
        	qtymem[i+35,findex]=intangle(Dt*dVA*gdet*rho*(uu[RR])*(uu[TH]),**keywords2hor)
        	qtymem[i+36,findex]=intangle(Dt*dVA*gdet*rho*(uu[RR])*(uu[PH]),**keywords2hor)
        	qtymem[i+37,findex]=intangle(Dt*dVA*gdet*rho*(uu[TH])*(uu[TH]),**keywords2hor)
        	qtymem[i+38,findex]=intangle(Dt*dVA*gdet*rho*(uu[TH])*(uu[PH]),**keywords2hor)
        	qtymem[i+39,findex]=intangle(Dt*dVA*gdet*rho*(uu[PH])*(uu[PH]),**keywords2hor)
        
        
        	#UU * u * u
        
        	qtymem[i+40,findex]=intangle(Dt*dVA*gdet*ug*(ud[TT])*(ud[TT]),**keywords2hor)
        	qtymem[i+41,findex]=intangle(Dt*dVA*gdet*ug*(ud[TT])*(ud[RR]),**keywords2hor)
        	qtymem[i+42,findex]=intangle(Dt*dVA*gdet*ug*(ud[TT])*(ud[TH]),**keywords2hor)
        	qtymem[i+43,findex]=intangle(Dt*dVA*gdet*ug*(ud[TT])*(ud[PH]),**keywords2hor)
        	qtymem[i+44,findex]=intangle(Dt*dVA*gdet*ug*(ud[RR])*(ud[RR]),**keywords2hor)
        	qtymem[i+45,findex]=intangle(Dt*dVA*gdet*ug*(ud[RR])*(ud[TH]),**keywords2hor)
        	qtymem[i+46,findex]=intangle(Dt*dVA*gdet*ug*(ud[RR])*(ud[PH]),**keywords2hor)
        	qtymem[i+47,findex]=intangle(Dt*dVA*gdet*ug*(ud[TH])*(ud[TH]),**keywords2hor)
        	qtymem[i+48,findex]=intangle(Dt*dVA*gdet*ug*(ud[TH])*(ud[PH]),**keywords2hor)
        	qtymem[i+49,findex]=intangle(Dt*dVA*gdet*ug*(ud[PH])*(ud[PH]),**keywords2hor)
        
        	qtymem[i+50,findex]=intangle(Dt*dVA*gdet*ug*(uu[TT])*(ud[TT]),**keywords2hor)
        	qtymem[i+51,findex]=intangle(Dt*dVA*gdet*ug*(uu[TT])*(ud[RR]),**keywords2hor)
        	qtymem[i+52,findex]=intangle(Dt*dVA*gdet*ug*(uu[TT])*(ud[TH]),**keywords2hor)
        	qtymem[i+53,findex]=intangle(Dt*dVA*gdet*ug*(uu[TT])*(ud[PH]),**keywords2hor)
        	qtymem[i+54,findex]=intangle(Dt*dVA*gdet*ug*(uu[RR])*(ud[RR]),**keywords2hor)
        	qtymem[i+55,findex]=intangle(Dt*dVA*gdet*ug*(uu[RR])*(ud[TH]),**keywords2hor)
        	qtymem[i+56,findex]=intangle(Dt*dVA*gdet*ug*(uu[RR])*(ud[PH]),**keywords2hor)
        	qtymem[i+57,findex]=intangle(Dt*dVA*gdet*ug*(uu[TH])*(ud[TH]),**keywords2hor)
        	qtymem[i+58,findex]=intangle(Dt*dVA*gdet*ug*(uu[TH])*(ud[PH]),**keywords2hor)
        	qtymem[i+59,findex]=intangle(Dt*dVA*gdet*ug*(uu[PH])*(ud[PH]),**keywords2hor)
        
        	qtymem[i+60,findex]=intangle(Dt*dVA*gdet*ug*(uu[TT])*(uu[TT]),**keywords2hor)
        	qtymem[i+61,findex]=intangle(Dt*dVA*gdet*ug*(uu[TT])*(uu[RR]),**keywords2hor)
        	qtymem[i+62,findex]=intangle(Dt*dVA*gdet*ug*(uu[TT])*(uu[TH]),**keywords2hor)
        	qtymem[i+63,findex]=intangle(Dt*dVA*gdet*ug*(uu[TT])*(uu[PH]),**keywords2hor)
        	qtymem[i+64,findex]=intangle(Dt*dVA*gdet*ug*(uu[RR])*(uu[RR]),**keywords2hor)
        	qtymem[i+65,findex]=intangle(Dt*dVA*gdet*ug*(uu[RR])*(uu[TH]),**keywords2hor)
        	qtymem[i+66,findex]=intangle(Dt*dVA*gdet*ug*(uu[RR])*(uu[PH]),**keywords2hor)
        	qtymem[i+67,findex]=intangle(Dt*dVA*gdet*ug*(uu[TH])*(uu[TH]),**keywords2hor)
        	qtymem[i+68,findex]=intangle(Dt*dVA*gdet*ug*(uu[TH])*(uu[PH]),**keywords2hor)
        	qtymem[i+69,findex]=intangle(Dt*dVA*gdet*ug*(uu[PH])*(uu[PH]),**keywords2hor)
        
        	#bsq * u * u
        
        	qtymem[i+70,findex]=intangle(Dt*dVA*gdet*bsq*(ud[TT])*(ud[TT]),**keywords2hor)
        	qtymem[i+71,findex]=intangle(Dt*dVA*gdet*bsq*(ud[TT])*(ud[RR]),**keywords2hor)
        	qtymem[i+72,findex]=intangle(Dt*dVA*gdet*bsq*(ud[TT])*(ud[TH]),**keywords2hor)
        	qtymem[i+73,findex]=intangle(Dt*dVA*gdet*bsq*(ud[TT])*(ud[PH]),**keywords2hor)
        	qtymem[i+74,findex]=intangle(Dt*dVA*gdet*bsq*(ud[RR])*(ud[RR]),**keywords2hor)
        	qtymem[i+75,findex]=intangle(Dt*dVA*gdet*bsq*(ud[RR])*(ud[TH]),**keywords2hor)
        	qtymem[i+76,findex]=intangle(Dt*dVA*gdet*bsq*(ud[RR])*(ud[PH]),**keywords2hor)
        	qtymem[i+77,findex]=intangle(Dt*dVA*gdet*bsq*(ud[TH])*(ud[TH]),**keywords2hor)
        	qtymem[i+78,findex]=intangle(Dt*dVA*gdet*bsq*(ud[TH])*(ud[PH]),**keywords2hor)
        	qtymem[i+79,findex]=intangle(Dt*dVA*gdet*bsq*(ud[PH])*(ud[PH]),**keywords2hor)
        
        	qtymem[i+80,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TT])*(ud[TT]),**keywords2hor)
        	qtymem[i+81,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TT])*(ud[RR]),**keywords2hor)
        	qtymem[i+82,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TT])*(ud[TH]),**keywords2hor)
        	qtymem[i+83,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TT])*(ud[PH]),**keywords2hor)
        	qtymem[i+84,findex]=intangle(Dt*dVA*gdet*bsq*(uu[RR])*(ud[RR]),**keywords2hor)
        	qtymem[i+85,findex]=intangle(Dt*dVA*gdet*bsq*(uu[RR])*(ud[TH]),**keywords2hor)
        	qtymem[i+86,findex]=intangle(Dt*dVA*gdet*bsq*(uu[RR])*(ud[PH]),**keywords2hor)
        	qtymem[i+87,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TH])*(ud[TH]),**keywords2hor)
        	qtymem[i+88,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TH])*(ud[PH]),**keywords2hor)
        	qtymem[i+89,findex]=intangle(Dt*dVA*gdet*bsq*(uu[PH])*(ud[PH]),**keywords2hor)
        
        	qtymem[i+90,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TT])*(uu[TT]),**keywords2hor)
        	qtymem[i+91,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TT])*(uu[RR]),**keywords2hor)
        	qtymem[i+92,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TT])*(uu[TH]),**keywords2hor)
        	qtymem[i+93,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TT])*(uu[PH]),**keywords2hor)
        	qtymem[i+94,findex]=intangle(Dt*dVA*gdet*bsq*(uu[RR])*(uu[RR]),**keywords2hor)
        	qtymem[i+95,findex]=intangle(Dt*dVA*gdet*bsq*(uu[RR])*(uu[TH]),**keywords2hor)
        	qtymem[i+96,findex]=intangle(Dt*dVA*gdet*bsq*(uu[RR])*(uu[PH]),**keywords2hor)
        	qtymem[i+97,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TH])*(uu[TH]),**keywords2hor)
        	qtymem[i+98,findex]=intangle(Dt*dVA*gdet*bsq*(uu[TH])*(uu[PH]),**keywords2hor)
        	qtymem[i+99,findex]=intangle(Dt*dVA*gdet*bsq*(uu[PH])*(uu[PH]),**keywords2hor)
        
        	# b * b
        
        	qtymem[i+100,findex]=intangle(Dt*dVA*gdet*(bd[TT])*(bd[TT]),**keywords2hor)
        	qtymem[i+101,findex]=intangle(Dt*dVA*gdet*(bd[TT])*(bd[RR]),**keywords2hor)
        	qtymem[i+102,findex]=intangle(Dt*dVA*gdet*(bd[TT])*(bd[TH]),**keywords2hor)
        	qtymem[i+103,findex]=intangle(Dt*dVA*gdet*(bd[TT])*(bd[PH]),**keywords2hor)
        	qtymem[i+104,findex]=intangle(Dt*dVA*gdet*(bd[RR])*(bd[RR]),**keywords2hor)
        	qtymem[i+105,findex]=intangle(Dt*dVA*gdet*(bd[RR])*(bd[TH]),**keywords2hor)
        	qtymem[i+106,findex]=intangle(Dt*dVA*gdet*(bd[RR])*(bd[PH]),**keywords2hor)
        	qtymem[i+107,findex]=intangle(Dt*dVA*gdet*(bd[TH])*(bd[TH]),**keywords2hor)
        	qtymem[i+108,findex]=intangle(Dt*dVA*gdet*(bd[TH])*(bd[PH]),**keywords2hor)
        	qtymem[i+109,findex]=intangle(Dt*dVA*gdet*(bd[PH])*(bd[PH]),**keywords2hor)
        
        	qtymem[i+110,findex]=intangle(Dt*dVA*gdet*(bu[TT])*(bd[TT]),**keywords2hor)
        	qtymem[i+111,findex]=intangle(Dt*dVA*gdet*(bu[TT])*(bd[RR]),**keywords2hor)
        	qtymem[i+112,findex]=intangle(Dt*dVA*gdet*(bu[TT])*(bd[TH]),**keywords2hor)
        	qtymem[i+113,findex]=intangle(Dt*dVA*gdet*(bu[TT])*(bd[PH]),**keywords2hor)
        	qtymem[i+114,findex]=intangle(Dt*dVA*gdet*(bu[RR])*(bd[RR]),**keywords2hor)
        	qtymem[i+115,findex]=intangle(Dt*dVA*gdet*(bu[RR])*(bd[TH]),**keywords2hor)
        	qtymem[i+116,findex]=intangle(Dt*dVA*gdet*(bu[RR])*(bd[PH]),**keywords2hor)
        	qtymem[i+117,findex]=intangle(Dt*dVA*gdet*(bu[TH])*(bd[TH]),**keywords2hor)
        	qtymem[i+118,findex]=intangle(Dt*dVA*gdet*(bu[TH])*(bd[PH]),**keywords2hor)
        	qtymem[i+119,findex]=intangle(Dt*dVA*gdet*(bu[PH])*(bd[PH]),**keywords2hor)
        
        	qtymem[i+120,findex]=intangle(Dt*dVA*gdet*(bu[TT])*(bu[TT]),**keywords2hor)
        	qtymem[i+121,findex]=intangle(Dt*dVA*gdet*(bu[TT])*(bu[RR]),**keywords2hor)
        	qtymem[i+122,findex]=intangle(Dt*dVA*gdet*(bu[TT])*(bu[TH]),**keywords2hor)
        	qtymem[i+123,findex]=intangle(Dt*dVA*gdet*(bu[TT])*(bu[PH]),**keywords2hor)
        	qtymem[i+124,findex]=intangle(Dt*dVA*gdet*(bu[RR])*(bu[RR]),**keywords2hor)
        	qtymem[i+125,findex]=intangle(Dt*dVA*gdet*(bu[RR])*(bu[TH]),**keywords2hor)
        	qtymem[i+126,findex]=intangle(Dt*dVA*gdet*(bu[RR])*(bu[PH]),**keywords2hor)
        	qtymem[i+127,findex]=intangle(Dt*dVA*gdet*(bu[TH])*(bu[TH]),**keywords2hor)
        	qtymem[i+128,findex]=intangle(Dt*dVA*gdet*(bu[TH])*(bu[PH]),**keywords2hor)
        	qtymem[i+129,findex]=intangle(Dt*dVA*gdet*(bu[PH])*(bu[PH]),**keywords2hor)
        
        
        	#mass flux
        	qtymem[i+130,findex]=intangle(Dt*dVA*gdet*rho*(uu[TT]),**keywords2hor)
        	qtymem[i+131,findex]=intangle(Dt*dVA*gdet*rho*(uu[RR]),**keywords2hor)
        	qtymem[i+132,findex]=intangle(Dt*dVA*gdet*rho*(uu[TH]),**keywords2hor)
        	qtymem[i+133,findex]=intangle(Dt*dVA*gdet*rho*(uu[PH]),**keywords2hor)
        #END BOB's QUANTITIES
        #if os.path.isfile("lrho%04d.png" % findex):
        #    print( "Skipping " + fname + " as lrho%04d.png exists" % findex );
        #else:
        #    print( "Reinterpolating " + fname + " ..." )
        #    plt.figure(0)
        #    plt.clf()
        #    mkframe("lrho%04d" % findex, vmin=-8,vmax=0.2)
    print( "Saving to file..." )
    if( whichi >=0 and whichn > 0 ):
        np.save( "qty2_%d_%d.npy" % (whichi, whichn), qtymem )
    else:
        np.save( "qty2.npy", qtymem )
    print( "Done!" )
    return(qtymem)

def fhorvstime(ihor):
    """
    Returns a tuple (ts,fs,mdot): lists of times, horizon fluxes, and Mdot
    """
    flist = glob.glob( os.path.join("dumps/", "fieldline*.bin") )
    ts=np.empty(len(flist),dtype=np.float32)
    fs=np.empty(len(flist),dtype=np.float32)
    md=np.empty(len(flist),dtype=np.float32)
    for findex, fname in enumerate(flist):
        print( "Reading " + fname + " ..." )
        rfd("../"+fname)
        fs[findex]=horfluxcalc(ihor)
        md[findex]=mdotcalc(ihor)
        ts[findex]=t
    print( "Done!" )
    return((ts,fs,md))

def amax(arg1,arg2):
    arr1 = np.array(arg1)
    arr2 = np.array(arg2)
    ret=np.zeros_like(arr1)
    ret[arr1>=arr2]=arr1[arr1>=arr2]
    ret[arr2>arr1]=arr2[arr2>arr1]
    return(ret)
def amin(arg1,arg2):
    arr1 = np.array(arg1)
    arr2 = np.array(arg2)
    ret=np.zeros_like(arr1)
    ret[arr1<=arr2]=arr1[arr1<=arr2]
    ret[arr2<arr1]=arr2[arr2<arr1]
    return(ret)

def Tcalcud():
    global Tud, TudEM, TudMA
    global mu, sigma
    global enth
    global unb, isunbound
    pg = (gam-1)*ug
    w=rho+ug+pg
    eta=w+bsq
    Tud = np.zeros((4,4,nx,ny,nz),dtype=np.float32,order='F')
    TudMA = np.zeros((4,4,nx,ny,nz),dtype=np.float32,order='F')
    TudEM = np.zeros((4,4,nx,ny,nz),dtype=np.float32,order='F')
    for kapa in np.arange(4):
        for nu in np.arange(4):
            if(kapa==nu): delta = 1
            else: delta = 0
            TudEM[kapa,nu] = bsq*uu[kapa]*ud[nu] + 0.5*bsq*delta - bu[kapa]*bd[nu]
            TudMA[kapa,nu] = w*uu[kapa]*ud[nu]+pg*delta
            #Tud[kapa,nu] = eta*uu[kapa]*ud[nu]+(pg+0.5*bsq)*delta-bu[kapa]*bd[nu]
            Tud[kapa,nu] = TudEM[kapa,nu] + TudMA[kapa,nu]
    mu = -Tud[1,0]/(rho*uu[1])
    bsqo2rho = bsq/(2.0*rho)
    sigma = TudEM[1,0]/TudMA[1,0]
    enth=1+ug*gam/rho
    unb=enth*ud[0]
    isunbound=(-unb>1.0)

def faraday():
    global fdd, fuu, omegaf1, omegaf2
    # these are native values according to HARM
    fdd = np.zeros((4,4,nx,ny,nz),dtype=rho.dtype)
    #fdd[0,0]=0*gdet
    #fdd[1,1]=0*gdet
    #fdd[2,2]=0*gdet
    #fdd[3,3]=0*gdet
    fdd[0,1]=gdet*(uu[2]*bu[3]-uu[3]*bu[2]) # f_tr
    fdd[1,0]=-fdd[0,1]
    fdd[0,2]=gdet*(uu[3]*bu[1]-uu[1]*bu[3]) # f_th
    fdd[2,0]=-fdd[0,2]
    fdd[0,3]=gdet*(uu[1]*bu[2]-uu[2]*bu[1]) # f_tp
    fdd[3,0]=-fdd[0,3]
    fdd[1,3]=gdet*(uu[2]*bu[0]-uu[0]*bu[2]) # f_rp = gdet*B2
    fdd[3,1]=-fdd[1,3]
    fdd[2,3]=gdet*(uu[0]*bu[1]-uu[1]*bu[0]) # f_hp = gdet*B1
    fdd[3,2]=-fdd[2,3]
    fdd[1,2]=gdet*(uu[0]*bu[3]-uu[3]*bu[0]) # f_rh = gdet*B3
    fdd[2,1]=-fdd[1,2]
    #
    fuu = np.zeros((4,4,nx,ny,nz),dtype=rho.dtype)
    #fuu[0,0]=0*gdet
    #fuu[1,1]=0*gdet
    #fuu[2,2]=0*gdet
    #fuu[3,3]=0*gdet
    fuu[0,1]=-1/gdet*(ud[2]*bd[3]-ud[3]*bd[2]) # f^tr
    fuu[1,0]=-fuu[0,1]
    fuu[0,2]=-1/gdet*(ud[3]*bd[1]-ud[1]*bd[3]) # f^th
    fuu[2,0]=-fuu[0,2]
    fuu[0,3]=-1/gdet*(ud[1]*bd[2]-ud[2]*bd[1]) # f^tp
    fuu[3,0]=-fuu[0,3]
    fuu[1,3]=-1/gdet*(ud[2]*bd[0]-ud[0]*bd[2]) # f^rp
    fuu[3,1]=-fuu[1,3]
    fuu[2,3]=-1/gdet*(ud[0]*bd[1]-ud[1]*bd[0]) # f^hp
    fuu[3,2]=-fuu[2,3]
    fuu[1,2]=-1/gdet*(ud[0]*bd[3]-ud[3]*bd[0]) # f^rh
    fuu[2,1]=-fuu[1,2]
    #
    # these 2 are equal in degen electrodynamics when d/dt=d/dphi->0
    omegaf1=fdd[0,1]/fdd[1,3] # = ftr/frp
    omegaf2=fdd[0,2]/fdd[2,3] # = fth/fhp
    #


def jetpowcalc(which=2,minbsqorho=10,mumin=None,mumax=None,maxbeta=None,donorthsouth=0):
    if which==0:
        jetpowden = -gdet*TudEM[1,0]
    if which==1:
        jetpowden = -gdet*TudMA[1,0]
    if which==2:
        jetpowden = -gdet*Tud[1,0]
    if which==3:
        #rest-mass flux
        jetpowden = gdet*rho*uu[1]
    if which==4:
        #phi (mag. flux)
        jetpowden = np.abs(gdetB[1])
    #jetpowden[tj>=ny-2] = 0*jetpowden[tj>=ny-2]
    #jetpowden[tj<1] = 0*jetpowden[tj<1]
    if mumin is None:
        jetpowden[bsq/rho<minbsqorho] = 0*jetpowden[bsq/rho<minbsqorho]
    else:
        #zero out outside jet (cut out low magnetization region)
        #cond=(mu<mumin)
        #
        #zero out outside jet (cut out low magnetization region)
        # for u^r\to 0, \mu \to b^2 \gamma/\rho, but \mu numerically becomes sick, so look at 4-Alfven velocity instead
        # v4a=1 is same as bsq=rho when ug=pg=0
        # follow mu unless <0.1 since the mu is unreliable
        v4asq=bsq/(rho+ug+(gam-1)*ug)
        mum1fake=uu[0]*(1.0+v4asq)-1.0
        if mumax is None:
            cond=(mum1fake<mumin)
        else:
            cond=(mum1fake>mumax)            
        #
        # avoid disk component that might be unbound and moving out as transient or as part of outer part of disk
        beta=((gam-1)*ug)/(bsq/2)
        if maxbeta is None:
            donothing0000temp=1
        else:
            cond+=(beta>maxbeta)            
        #zero out bound region
        cond+=(1-isunbound)
        #zero out infalling region
        cond+=(uu[1]<=0.0)
        # 1 = north
        #-1 = south
        if donorthsouth==1:
            #NORTH
            #[zero out south hemisphere]
            cond += (tj>=ny/2)
        elif donorthsouth==-1:
            #SOUTH
            #[zero out north hemisphere]
            cond += (tj<ny/2)
        jetpowden[cond] = 0*jetpowden[cond]
    jetpowtot = scaletofullwedge(np.sum(np.sum(jetpowden,axis=2),axis=1)*_dx2*_dx3)
    #print "which = %d, minbsqorho = %g" % (which, minbsqorho)
    return(jetpowtot)
    
def plotit(ts,fs,md):
    #rc('font', family='serif')
    #plt.figure( figsize=(12,9) )
    fig,plotlist=plt.subplots(nrows=2,ncols=1,sharex=True,figsize=(12,9))
    #plt.subplots_adjust(hspace=0.4) #increase vertical spacing to avoid crowding
    plotlist[0].plot(ts,fs,label=r'$\Phi_{\rm h}/\Phi_{\rm i}$: Normalized Horizon Magnetic Flux')
    plotlist[0].plot(ts,fs,'r+') #, label=r'$\Phi_{\rm h}/0.5\Phi_{\rm i}$: Data Points')
    plotlist[0].legend(loc='lower right')
    #plt.xlabel(r'$t\;(GM/c^3)$')
    plotlist[0].set_ylabel(r'$\Phi_{\rm h}$',fontsize=16)
    plt.setp( plotlist[0].get_xticklabels(), visible=False)
    plotlist[0].grid(True)
    #
    #plotlist[1].subplot(212,sharex=True)
    plotlist[1].plot(ts,md,label=r'$\dot M_{\rm h}$: Horizon Accretion Rate')
    plotlist[1].plot(ts,md,'r+') #, label=r'$\dot M_{\rm h}$: Data Points')
    plotlist[1].legend(loc='upper right')
    plotlist[1].set_xlabel(r'$t\;(GM/c^3)$')
    plotlist[1].set_ylabel(r'$\dot M_{\rm h}$',fontsize=16)
    
    #title("\TeX\ is Number $\displaystyle\sum_{n=1}^\infty\frac{-e^{i\pi}}{2^n}$!", 
    #      fontsize=16, color='r')
    plotlist[1].grid(True)
    fig.savefig('test.pdf')

def iofr(rval):
    res = interp1d(r[:,0,0], ti[:,0,0], kind='linear')
    return(np.floor(res(rval)+0.5))

def plotqtyvstime(qtymem,ihor=11,whichplot=None,ax=None,findex=None,fti=None,ftf=None,showextra=True,prefactor=100):
    global mdotfinavgvsr, mdotfinavgvsr5, mdotfinavgvsr10,mdotfinavgvsr20, mdotfinavgvsr30,mdotfinavgvsr40
    #
    rjet=100.0
    #
    nqtyold=98
    nqtyold2=98+32+1
    # with jon's mumax and new eff definition
    nqty=98+32+1+8+2+1
    ###############################
    #copy this from getqtyvstime()
    ###############################
    if qtymem.shape[0] == 71:
        print "Plot using old fmt"
        #old fmt
        i=0
        ts=qtymem[i,:,0];i+=1
        #HoverR
        hoverr=qtymem[i];i+=1
        thetamid=qtymem[i];i+=1
        #rhosq:
        rhosqs=qtymem[i];i+=1
        rhosrhosq=qtymem[i];i+=1
        ugsrhosq=qtymem[i];i+=1
        uu0rhosq=qtymem[i];i+=1
        uus1rhosq=qtymem[i];i+=1
        uuas1rhosq=qtymem[i];i+=1
        uus3rhosq=qtymem[i];i+=1
        uuas3rhosq=qtymem[i];i+=1
        Bs1rhosq=qtymem[i];i+=1
        Bas1rhosq=qtymem[i];i+=1
        Bs3rhosq=qtymem[i];i+=1
        Bas3rhosq=qtymem[i];i+=1
        #2h
        rhos2h=qtymem[i];i+=1
        ugs2h=qtymem[i];i+=1
        uu02h=qtymem[i];i+=1
        uus12h=qtymem[i];i+=1
        uuas12h=qtymem[i];i+=1
        uus32h=qtymem[i];i+=1
        uuas32h=qtymem[i];i+=1
        Bs12h=qtymem[i];i+=1
        Bas12h=qtymem[i];i+=1
        Bs32h=qtymem[i];i+=1
        Bas32h=qtymem[i];i+=1
        #4h
        rhos4h=qtymem[i];i+=1
        ugs4h=qtymem[i];i+=1
        uu04h=qtymem[i];i+=1
        uus14h=qtymem[i];i+=1
        uuas14h=qtymem[i];i+=1
        uus34h=qtymem[i];i+=1
        uuas34h=qtymem[i];i+=1
        Bs14h=qtymem[i];i+=1
        Bas14h=qtymem[i];i+=1
        Bs34h=qtymem[i];i+=1
        Bas34h=qtymem[i];i+=1
        #2hor
        rhos2hor=qtymem[i];i+=1
        ugs2hor=qtymem[i];i+=1
        uu02hor=qtymem[i];i+=1
        uus12hor=qtymem[i];i+=1
        uuas12hor=qtymem[i];i+=1
        uus32hor=qtymem[i];i+=1
        uuas32hor=qtymem[i];i+=1
        Bs12hor=qtymem[i];i+=1
        Bas12hor=qtymem[i];i+=1
        Bs32hor=qtymem[i];i+=1
        Bas32hor=qtymem[i];i+=1
        #Flux
        fstot=qtymem[i]*2;i+=1
        fsj5=qtymem[i]*2;i+=1
        fsj10=qtymem[i]*2;i+=1
        #Mdot
        mdtot=qtymem[i]*2;i+=1
        md2h=qtymem[i]*2;i+=1
        md4h=qtymem[i]*2;i+=1
        md2hor=qtymem[i]*2;i+=1
        md5=qtymem[i]*2;i+=1
        md10=qtymem[i]*2;i+=1
        mdrhosq=qtymem[i]*2;i+=1
        mdtotbound=qtymem[i]*2;i+=1
        #Edot
        edtot=qtymem[i]*2;i+=1
        ed2h=qtymem[i]*2;i+=1
        ed4h=qtymem[i]*2;i+=1
        ed2hor=qtymem[i]*2;i+=1
        edrhosq=qtymem[i]*2;i+=1
        edma=qtymem[i]*2;i+=1
        edm=qtymem[i]*2;i+=1
        edtotbound=qtymem[i]*2;i+=1
        edmabound=qtymem[i]*2;i+=1
        #Pjet
        pjem5=qtymem[i];i+=1
        pjem10=qtymem[i];i+=1
        pjma5=qtymem[i];i+=1
        pjma10=qtymem[i];i+=1
    else:
        #new fmt
        #qty defs
        i=0
        ts=qtymem[i,:,0];i+=1
        #HoverR
        hoverr=qtymem[i];i+=1
        thetamid=qtymem[i];i+=1
        #rhosq:
        rhosqs=qtymem[i];i+=1
        rhosrhosq=qtymem[i];i+=1
        ugsrhosq=qtymem[i];i+=1
        uu0rhosq=qtymem[i];i+=1
        uus1rhosq=qtymem[i];i+=1
        uuas1rhosq=qtymem[i];i+=1
        uus3rhosq=qtymem[i];i+=1
        uuas3rhosq=qtymem[i];i+=1
        Bs1rhosq=qtymem[i];i+=1
        Bas1rhosq=qtymem[i];i+=1
        Bs2rhosq=qtymem[i];i+=1
        Bas2rhosq=qtymem[i];i+=1
        Bs3rhosq=qtymem[i];i+=1
        Bas3rhosq=qtymem[i];i+=1
        #2h
        gdetint2h=qtymem[i];i+=1
        rhos2h=qtymem[i];i+=1
        ugs2h=qtymem[i];i+=1
        uu02h=qtymem[i];i+=1
        uus12h=qtymem[i];i+=1
        uuas12h=qtymem[i];i+=1
        uus32h=qtymem[i];i+=1
        uuas32h=qtymem[i];i+=1
        Bs12h=qtymem[i];i+=1
        Bas12h=qtymem[i];i+=1
        Bs22h=qtymem[i];i+=1
        Bas22h=qtymem[i];i+=1
        Bs32h=qtymem[i];i+=1
        Bas32h=qtymem[i];i+=1
        #4h
        gdetint4h=qtymem[i];i+=1
        rhos4h=qtymem[i];i+=1
        ugs4h=qtymem[i];i+=1
        uu04h=qtymem[i];i+=1
        uus14h=qtymem[i];i+=1
        uuas14h=qtymem[i];i+=1
        uus34h=qtymem[i];i+=1
        uuas34h=qtymem[i];i+=1
        Bs14h=qtymem[i];i+=1
        Bas14h=qtymem[i];i+=1
        Bs24h=qtymem[i];i+=1
        Bas24h=qtymem[i];i+=1
        Bs34h=qtymem[i];i+=1
        Bas34h=qtymem[i];i+=1
        #2hor
        gdetint2hor=qtymem[i];i+=1
        rhos2hor=qtymem[i];i+=1
        ugs2hor=qtymem[i];i+=1
        bsqs2hor=qtymem[i];i+=1
        bsqorhos2hor=qtymem[i];i+=1
        bsqougs2hor=qtymem[i];i+=1
        uu02hor=qtymem[i];i+=1
        uus12hor=qtymem[i];i+=1
        uuas12hor=qtymem[i];i+=1
        uus32hor=qtymem[i];i+=1
        uuas32hor=qtymem[i];i+=1
        Bs12hor=qtymem[i];i+=1
        Bas12hor=qtymem[i];i+=1
        Bs22hor=qtymem[i];i+=1
        Bas22hor=qtymem[i];i+=1
        Bs32hor=qtymem[i];i+=1
        Bas32hor=qtymem[i];i+=1
        #Flux
        fstot=qtymem[i];i+=1
        fs2hor=qtymem[i];i+=1
        fsj5=qtymem[i];i+=1
        fsj10=qtymem[i];i+=1
        fsj20=qtymem[i];i+=1
        fsj30=qtymem[i];i+=1
        fsj40=qtymem[i];i+=1
        #Mdot
        mdtot=qtymem[i];i+=1
        md2h=qtymem[i];i+=1
        md4h=qtymem[i];i+=1
        md2hor=qtymem[i];i+=1
        md5=qtymem[i];i+=1
        md10=qtymem[i];i+=1
        md20=qtymem[i];i+=1
        md30=qtymem[i];i+=1
        mdwind=qtymem[i];i+=1
        mdjet=qtymem[i];i+=1
        md40=qtymem[i];i+=1
        mdrhosq=qtymem[i];i+=1
        mdtotbound=qtymem[i];i+=1
        #Edot
        edtot=qtymem[i];i+=1
        ed2h=qtymem[i];i+=1
        ed4h=qtymem[i];i+=1
        ed2hor=qtymem[i];i+=1
        edrhosq=qtymem[i];i+=1
        edma=qtymem[i];i+=1
        edm=qtymem[i];i+=1
        edtotbound=qtymem[i];i+=1
        edmabound=qtymem[i];i+=1
        #Pjet
        pjem5=qtymem[i];i+=1
        pjem10=qtymem[i];i+=1
        pjem20=qtymem[i];i+=1
        pjem30=qtymem[i];i+=1
        pjem40=qtymem[i];i+=1
        pjma5=qtymem[i];i+=1
        pjma10=qtymem[i];i+=1
        pjma20=qtymem[i];i+=1
        pjma30=qtymem[i];i+=1
        pjma40=qtymem[i];i+=1
        #new format?
        if qtymem.shape[0] > nqtyold:
            #yes!
            pjem_n_mu10=qtymem[i];i+=1
            pjem_n_mu5=qtymem[i];i+=1
            pjem_n_mu2=qtymem[i];i+=1
            pjem_n_mu1=qtymem[i];i+=1
            pjem_n_mumax1=qtymem[i];i+=1
            pjrm_n_mu10=qtymem[i];i+=1
            pjrm_n_mu5=qtymem[i];i+=1
            pjrm_n_mu2=qtymem[i];i+=1
            pjrm_n_mu1=qtymem[i];i+=1
            pjrm_n_mumax1=qtymem[i];i+=1
            pjma_n_mu10=qtymem[i];i+=1
            pjma_n_mu5=qtymem[i];i+=1
            pjma_n_mu2=qtymem[i];i+=1
            pjma_n_mu1=qtymem[i];i+=1
            pjma_n_mumax1=qtymem[i];i+=1
            phiabsj_n_mu10=qtymem[i];i+=1
            phiabsj_n_mu5=qtymem[i];i+=1
            phiabsj_n_mu2=qtymem[i];i+=1
            phiabsj_n_mu1=qtymem[i];i+=1
            phiabsj_n_mumax1=qtymem[i];i+=1
            #
            pjem_s_mu10=qtymem[i];i+=1
            pjem_s_mu5=qtymem[i];i+=1
            pjem_s_mu2=qtymem[i];i+=1
            pjem_s_mu1=qtymem[i];i+=1
            pjem_s_mumax1=qtymem[i];i+=1
            pjrm_s_mu10=qtymem[i];i+=1
            pjrm_s_mu5=qtymem[i];i+=1
            pjrm_s_mu2=qtymem[i];i+=1
            pjrm_s_mu1=qtymem[i];i+=1
            pjrm_s_mumax1=qtymem[i];i+=1
            pjma_s_mu10=qtymem[i];i+=1
            pjma_s_mu5=qtymem[i];i+=1
            pjma_s_mu2=qtymem[i];i+=1
            pjma_s_mu1=qtymem[i];i+=1
            pjma_s_mumax1=qtymem[i];i+=1
            phiabsj_s_mu10=qtymem[i];i+=1
            phiabsj_s_mu5=qtymem[i];i+=1
            phiabsj_s_mu2=qtymem[i];i+=1
            phiabsj_s_mu1=qtymem[i];i+=1
            phiabsj_s_mumax1=qtymem[i];i+=1
            if i < qtymem.shape[0]:
                ldtot=qtymem[i];i+=1
            else:
                ldtot=None
            #derived
            pjke_n_mu2 = pjem_n_mu2 + pjma_n_mu2 - pjrm_n_mu2
            pjke_s_mu2 = pjem_s_mu2 + pjma_s_mu2 - pjrm_s_mu2
            pjke_mu2 = pjke_n_mu2 + pjke_s_mu2
            phiabsj_mu2 = phiabsj_n_mu2 + phiabsj_s_mu2
            #
            pjke_n_mu1 = pjem_n_mu1 + pjma_n_mu1 - pjrm_n_mu1
            pjke_s_mu1 = pjem_s_mu1 + pjma_s_mu1 - pjrm_s_mu1
            pjke_mu1 = pjke_n_mu1 + pjke_s_mu1
            phiabsj_mu1 = phiabsj_n_mu1 + phiabsj_s_mu1
            #
            pjke_n_mumax1 = pjem_n_mumax1 + pjma_n_mumax1 - pjrm_n_mumax1
            pjke_s_mumax1 = pjem_s_mumax1 + pjma_s_mumax1 - pjrm_s_mumax1
            pjke_mumax1 = pjke_n_mumax1 + pjke_s_mumax1
            phiabsj_mumax1 = phiabsj_n_mumax1 + phiabsj_s_mumax1
        else:
            print( "Oldish format: missing north/south jet power and flux" )
            sys.stdout.flush()
            pjem_n_mu10=None
            pjem_n_mu5=None
            pjem_n_mu2=None
            pjem_n_mu1=None
            pjem_n_mumax1=None
            pjrm_n_mu10=None
            pjrm_n_mu5=None
            pjrm_n_mu2=None
            pjrm_n_mu1=None
            pjrm_n_mumax1=None
            pjma_n_mu10=None
            pjma_n_mu5=None
            pjma_n_mu2=None
            pjma_n_mu1=None
            pjma_n_mumax1=None
            phiabsj_n_mu10=None
            phiabsj_n_mu5=None
            phiabsj_n_mu2=None
            phiabsj_n_mu1=None
            phiabsj_n_mumax1=None
            pjem_s_mu10=None
            pjem_s_mu5=None
            pjem_s_mu2=None
            pjem_s_mu1=None
            pjem_s_mumax1=None
            pjrm_s_mu10=None
            pjrm_s_mu5=None
            pjrm_s_mu2=None
            pjrm_s_mu1=None
            pjrm_s_mumax1=None
            pjma_s_mu10=None
            pjma_s_mu5=None
            pjma_s_mu2=None
            pjma_s_mu1=None
            pjma_s_mumax1=None
            phiabsj_s_mu10=None
            phiabsj_s_mu5=None
            phiabsj_s_mu2=None
            phiabsj_s_mu1=None
            phiabsj_s_mumax1=None
            ldtot=None
            #derived
            pjke_n_mu2=None
            pjke_s_mu2=None
            pjke_mu2=None
            phiabsj_mu2=None
            pjke_n_mu1=None
            pjke_s_mu1=None
            pjke_mu1=None
            phiabsj_mu1=None
            pjke_n_mumax1=None
            pjke_s_mumax1=None
            pjke_mumax1=None
            phiabsj_mumax1=None
    #end qty defs
    ##############################
    #end copy
    ##############################
    #
    #rc('font', family='serif')
    #plt.figure( figsize=(12,9) )
    if ftf is not None:
        iti = 1000 #dummy
        itf = 2000 #dummy
    elif os.path.isfile(os.path.join("titf.txt")):
        dotavg=1
        gd1 = np.loadtxt( "titf.txt",
                          dtype=np.float64, 
                          skiprows=1, 
                          unpack = True )
        iti = gd1[0]
        itf = gd1[1]
        fti = gd1[2]
        ftf = gd1[3]
    else:
        print( "Warning: titf.txt not found: using default numbers for averaging" )
        dotavg=1
        iti = 3000
        itf = 4000
        fti = 8000
        ftf = 1e5

    #mdotiniavg = timeavg(mdtot[:,ihor]-md10[:,ihor],ts,fti,ftf)
    #mdotfinavg = (mdtot[:,ihor]-md10[:,ihor])[(ts<ftf)*(ts>=fti)].sum()/(mdtot[:,ihor]-md10[:,ihor])[(ts<ftf)*(ts>=fti)].shape[0]
    mdotiniavgvsr = timeavg(mdtot,ts,iti,itf)
    mdotfinavgvsr = timeavg(mdtot,ts,fti,ftf)
    # full (disk + jet) accretion rate
    mdtotvsr = mdotfinavgvsr
    edtotvsr = timeavg(edtot,ts,fti,ftf)
    edmavsr = timeavg(edma,ts,fti,ftf)
    edmvsr = timeavg(edm,ts,fti,ftf)
    if ldtot is not None:
        ldtotvsr = timeavg(ldtot,ts,fti,ftf)
    else:
        ldtotvsr = None

    #
    phiabsj_mu2vsr = timeavg(phiabsj_mu2[:,:],ts,fti,ftf)
    phiabsj_mu1vsr = timeavg(phiabsj_mu1[:,:],ts,fti,ftf)
    #
    #########
    mdotfinavgvsr5 = timeavg(mdtot[:,:]-md5[:,:],ts,fti,ftf)
    mdotfinavgvsr10 = timeavg(mdtot[:,:]-md10[:,:],ts,fti,ftf)
    mdotfinavgvsr20 = timeavg(mdtot[:,:]-md20[:,:],ts,fti,ftf)
    #        etaj = prefactor*pjke_mu1[:,iofr(rjet)]/mdotfinavg

    mdotfinavgvsr30 = timeavg(mdtot[:,:]-md30[:,:],ts,fti,ftf)
    #mdotwindfinavgvsr30 = timeavg(mdwind[:,:]-md30[:,:],ts,fti,ftf)
    #mdotjetfinavgvsr30 = timeavg(mdjet[:,:]-md30[:,:],ts,fti,ftf)
    #
    mdotiniavgvsr30 = timeavg(mdtot[:,:]-md30[:,:],ts,iti,itf)
    #mdotwindiniavgvsr30 = timeavg(mdwind[:,:]-md30[:,:],ts,iti,itf)
    #mdotjetiniavgvsr30 = timeavg(mdjet[:,:]-md30[:,:],ts,iti,itf)
    #
    mdotfinavgvsr40 = timeavg(mdtot[:,:]-md40[:,:],ts,fti,ftf)
    #
    mdotiniavg = np.float64(mdotiniavgvsr30)[r[:,0,0]<10].mean()
    mdotfinavg = np.float64(mdotfinavgvsr30)[r[:,0,0]<10].mean()
    #
    mdotwindiniavg = timeavg(np.abs(mdwind[:,iofr(rjet)]-md30[:,ihor]),ts,iti,itf)
    mdotwindfinavg = timeavg(np.abs(mdwind[:,iofr(rjet)]-md30[:,ihor]),ts,fti,ftf)
    mdotjetiniavg = timeavg(np.abs(mdjet[:,iofr(rjet)]-md30[:,ihor]),ts,iti,itf)
    mdotjetfinavg = timeavg(np.abs(mdjet[:,iofr(rjet)]-md30[:,ihor]),ts,fti,ftf)
    #
    pjetiniavg = timeavg(pjem30[:,ihor],ts,iti,itf)
    pjetfinavg = timeavg(pjem30[:,ihor],ts,fti,ftf)
    #pjemfinavgvsr = timeavg(edtot-edma,ts,fti,ftf)
    #pjemtot = edtot-edma
    # new efficiency definition
    pjemfinavgvsr = timeavg(edtot-edm,ts,fti,ftf)
    pjemtot = edtot-edm
    pjemfinavgvsr5 = timeavg(pjem5[:,:],ts,fti,ftf)
    pjemfinavgvsr10 = timeavg(pjem10[:,:],ts,fti,ftf)
    pjemfinavgvsr20 = timeavg(pjem20[:,:],ts,fti,ftf)
    pjemfinavgvsr30 = timeavg(pjem30[:,:],ts,fti,ftf)
    pjemfinavgvsr40 = timeavg(pjem40[:,:],ts,fti,ftf)
    #
    #pjemfinavgtot = timeavg((edtot-edma)[:,ihor],ts,fti,ftf)
    #pjmafinavgvsr = timeavg(edma[:,:],ts,fti,ftf)
    # new efficiency definition
    pjemfinavgtot = timeavg((edtot-edm)[:,ihor],ts,fti,ftf)
    pjmafinavgvsr = timeavg(edma[:,:],ts,fti,ftf)
    #
    pjmafinavgvsr5 = timeavg(pjma5[:,:],ts,fti,ftf)
    pjmafinavgvsr10 = timeavg(pjma10[:,:],ts,fti,ftf)
    pjmafinavgvsr20 = timeavg(pjma20[:,:],ts,fti,ftf)
    pjmafinavgvsr30 = timeavg(pjma30[:,:],ts,fti,ftf)
    pjmafinavgvsr40 = timeavg(pjma40[:,:],ts,fti,ftf)
    pjtotfinavgvsr = pjemfinavgvsr + pjmafinavgvsr
    pjtotfinavgvsr5 = pjemfinavgvsr5 + pjmafinavgvsr5
    pjtotfinavgvsr10 = pjemfinavgvsr10 + pjmafinavgvsr10
    pjtotfinavgvsr20 = pjemfinavgvsr20 + pjmafinavgvsr20
    pjtotfinavgvsr30 = pjemfinavgvsr30 + pjmafinavgvsr30
    pjtotfinavgvsr40 = pjemfinavgvsr40 + pjmafinavgvsr40

    #radius of stagnation point (Pjmabsqorho5(rstag) = 0)
    indices=ti[:,0,0][pjmafinavgvsr5>0]
    if indices.shape[0]>0:
        istag=indices[0]
        rstag=r[istag,0,0]
        i2stag=iofr(2*rstag)
        i4stag=iofr(4*rstag)
        i8stag=iofr(8*rstag)
        pjtotfinavgvsr5max    = np.max(pjtotfinavgvsr5)
        pjtotfinavgvsr5rstag  = pjtotfinavgvsr5[istag]
        pjtotfinavgvsr5r2stag = pjtotfinavgvsr5[i2stag]
        pjtotfinavgvsr5r4stag = pjtotfinavgvsr5[i4stag]
        pjtotfinavgvsr5r8stag = pjtotfinavgvsr5[i8stag]
    else:
        istag=0
        rstag=0
        i2stag=0
        i4stag=0
        i8stag=0
        pjtotfinavgvsr5max    = np.max(pjtotfinavgvsr5)
        pjtotfinavgvsr5rstag  = 0
        pjtotfinavgvsr5r2stag = 0
        pjtotfinavgvsr5r4stag = 0
        pjtotfinavgvsr5r8stag = 0

    
    

    fstotfinavg = timeavg(fstot[:,ihor],ts,fti,ftf)
    fstotsqfinavg = timeavg(fstot[:,ihor]**2,ts,fti,ftf)**0.5
        
    fsj30finavg = timeavg(fsj30[:,ihor],ts,fti,ftf)
    fsj30sqfinavg = timeavg(fsj30[:,ihor]**2,ts,fti,ftf)**0.5
    
    fc=0
    if showextra:
        ofc = 1
        clr = 'r'
    else:
        ofc = 0
        clr = 'k'
    #######################
    #
    # Mdot ***
    #
    #######################
    #
    # MB09
    #windplotfactor=1.0
    # thickdisk models
    windplotfactor=0.1
    #
    #
    if whichplot == 1:
        if dotavg:
            ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+mdotfinavg,color=(ofc,fc,fc))
            if showextra:
                ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+mdotjetfinavg,'--',color=(fc,fc+0.5*(1-fc),fc))
                ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+mdotwindfinavg*windplotfactor,'-.',color=(fc,fc,1))
            if(iti>fti):
                ax.plot(ts[(ts<itf)*(ts>=iti)],0*ts[(ts<itf)*(ts>=iti)]+mdotiniavg,color=(ofc,fc,fc))
                if showextra:
                    ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+mdotjetiniavg,color=(fc,fc+0.5*(1-fc),fc))
                    ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+mdotwindiniavg*windplotfactor,color=(fc,fc,1))
        #
        ax.plot(ts,np.abs(mdtot[:,ihor]-md30[:,ihor]),clr,label=r'$\dot Mc^2$')
        if showextra:
            ax.plot(ts,np.abs(mdjet[:,iofr(rjet)]-md30[:,ihor]),'g--',label=r'$\dot M_{\rm jet}c^2$')
            if windplotfactor==1.0:
                ax.plot(ts,windplotfactor*np.abs(mdwind[:,iofr(rjet)]-md30[:,ihor]),'b-.',label=r'$\dot M_{\rm wind}c^2$')
            elif windplotfactor==0.1:
                ax.plot(ts,windplotfactor*np.abs(mdwind[:,iofr(rjet)]-md30[:,ihor]),'b-.',label=r'$0.1\dot M_{\rm wind}c^2$')
        #
        if findex != None:
            if not isinstance(findex,tuple):
                ax.plot(ts[findex],np.abs(mdtot[:,ihor]-md30[:,ihor])[findex],'o',mfc='r')
                if showextra:
                    ax.plot(ts[findex],np.abs(mdjet[:,iofr(rjet)]-md30[:,ihor])[findex],'gs')
                    ax.plot(ts[findex],windplotfactor*np.abs(mdwind[:,iofr(rjet)]-md30[:,ihor])[findex],'bv')
            else:
                for fi in findex:
                    ax.plot(ts[fi],np.abs(mdtot[:,ihor]-md30[:,ihor])[fi],'o',mfc='r')#,label=r'$\dot M$')
                    if showextra:
                        ax.plot(ts[fi],np.abs(mdjet[:,iofr(rjet)]-md30[:,ihor])[fi],'gs')
                        ax.plot(ts[fi],windplotfactor*np.abs(mdwind[:,iofr(rjet)]-md30[:,ihor])[fi],'bv')
        #
        #ax.set_ylabel(r'$\dot Mc^2$',fontsize=16,labelpad=9)
        ax.set_ylabel(r'$\dot Mc^2$',fontsize=16,ha='left',labelpad=20)
        plt.setp( ax.get_xticklabels(), visible=False)
        ax.set_xlim(ts[0],ts[-1])
        if showextra:
            # http://matplotlib.sourceforge.net/examples/pylab_examples/legend_demo.html
            plt.legend(loc='upper left',bbox_to_anchor=(0.05,0.95),ncol=1,borderaxespad=0,frameon=True,labelspacing=0)
            # set some legend properties.  All the code below is optional.  The
            # defaults are usually sensible but if you need more control, this
            # shows you how
            leg = plt.gca().get_legend()
            ltext  = leg.get_texts()  # all the text.Text instance in the legend
            llines = leg.get_lines()  # all the lines.Line2D instance in the legend
            frame  = leg.get_frame()  # the patch.Rectangle instance surrounding the legend
            # see text.Text, lines.Line2D, and patches.Rectangle for more info on
            # the settable properties of lines, text, and rectangles
            #frame.set_facecolor('0.80')      # set the frame face color to light gray
            plt.setp(ltext, fontsize=12)    # the legend text fontsize
            #plt.setp(llines, linewidth=1.5)      # the legend linewidth
            #leg.draw_frame(False)           # don't draw the legend frame
    #######################
    #
    # Pjet
    #
    #######################
    if whichplot == 2:
        ax.plot(ts,(pjem10[:,ihor]),label=r'P_{\rm j}$')
        #ax.legend(loc='upper left')
        if dotavg:
            ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+pjetfinavg)#,label=r'$\langle P_{\rm j}\rangle$')
        ax.set_ylabel(r'$P_{\rm j}$',fontsize=16)
        plt.setp( ax.get_xticklabels(), visible=False)
        ax.set_xlim(ts[0],ts[-1])
    #######################
    #
    # eta instantaneous
    #
    #######################
    if whichplot == 3:
        ax.plot(ts,(pjem10[:,ihor]/(mdtot[:,ihor]-md10[:,ihor])))#,label=r'$P_{\rm j}/\dot M$')
        #ax.legend(loc='upper left')
        if dotavg:
            ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+pjetfinavg/mdotfinavg)#,label=r'$\langle P_j\rangle/\langle\dot M\rangle$')
        ax.set_ylim(0,4)
        #ax.set_xlabel(r'$t\;(GM/c^3)$')
        ax.set_ylabel(r'$P_{\rm j}/\dot M$',fontsize=16)
        ax.set_xlim(ts[0],ts[-1])
    #######################
    #
    # eta ***
    #
    #######################
    if whichplot == 4:
        etabh = prefactor*pjemtot[:,ihor]/mdotfinavg
        #etaj = prefactor*pjke_mu2[:,iofr(rjet)]/mdotfinavg
        #etaw = prefactor*(pjke_mu1-pjke_mu2)[:,iofr(rjet)]/mdotfinavg
        etaj = prefactor*pjke_mu1[:,iofr(rjet)]/mdotfinavg
        etaw = prefactor*pjke_mumax1[:,iofr(rjet)]/mdotfinavg
        #
        etabh2 = prefactor*pjemtot[:,ihor]/mdotiniavg
        #etaj2 = prefactor*pjke_mu2[:,iofr(rjet)]/mdotiniavg
        #etaw2 = prefactor*(pjke_mu1-pjke_mu2)[:,iofr(rjet)]/mdotiniavg
        etaj2 = prefactor*pjke_mu1[:,iofr(rjet)]/mdotiniavg
        etaw2 = prefactor*pjke_mumax1[:,iofr(rjet)]/mdotiniavg
        #
        if(1 and iti>fti):
            #use mdot averaged over the same time interval for iti<t<=itf
            icond=(ts>=iti)*(ts<itf)
            etabh[icond]=etabh2[icond]
            etaj[icond]=etaj2[icond]
            etaw[icond]=etaw2[icond]
        if dotavg:
            etaj_avg = timeavg(etaj,ts,fti,ftf)
            etabh_avg = timeavg(etabh,ts,fti,ftf)
            etaw_avg = timeavg(etaw,ts,fti,ftf)
            ptot_avg = timeavg(pjemtot[:,ihor],ts,fti,ftf)
            #
            ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+etabh_avg,color=(ofc,fc,fc)) 
            if showextra:
                ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+etaj_avg,'--',color=(fc,fc+0.5*(1-fc),fc)) 
                ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+etaw_avg,'-.',color=(fc,fc+0.5*(1-fc),fc)) 
            #,label=r'$\langle P_j\rangle/\langle\dot M\rangle$')
            #,label=r'$\langle P_j\rangle/\langle\dot M\rangle$')
            #,label=r'$\langle P_j\rangle/\langle\dot M\rangle$')
            if(iti>fti):
                etaj2_avg = timeavg(etaj2,ts,iti,itf)
                etabh2_avg = timeavg(etabh2,ts,iti,itf)
                etaw2_avg = timeavg(etaw2,ts,iti,itf)
                ptot2_avg = timeavg(pjemtot[:,ihor],ts,iti,itf)
                #
                ax.plot(ts[(ts<itf)*(ts>=iti)],0*ts[(ts<itf)*(ts>=iti)]+etabh2_avg,color=(ofc,fc,fc))
                if showextra:
                    ax.plot(ts[(ts<itf)*(ts>=iti)],0*ts[(ts<itf)*(ts>=iti)]+etaj2_avg,'--',color=(fc,fc+0.5*(1-fc),fc))
                    ax.plot(ts[(ts<itf)*(ts>=iti)],0*ts[(ts<itf)*(ts>=iti)]+etaw2_avg,'-.',color=(fc,fc+0.5*(1-fc),fc))
        #
        ax.plot(ts,etabh,clr,label=r'$\eta_{\rm BH}$')
        if showextra:
            ax.plot(ts,etaj,'g--',label=r'$\eta_{\rm jet}$')
            ax.plot(ts,etaw,'b-.',label=r'$\eta_{\rm wind}$')
        if findex != None:
            if not isinstance(findex,tuple):
                ax.plot(ts[findex],etabh[findex],'o',mfc='r')
                if showextra:
                    ax.plot(ts[findex],etaj[findex],'gs')
                    ax.plot(ts[findex],etaw[findex],'bv')
            else:
                for fi in findex:
                    ax.plot(ts[fi],etabh[fi],'o',mfc='r')#,label=r'$\dot M$')
                    if showextra:
                        ax.plot(ts[fi],etaw[fi],'bv')#,label=r'$\dot M$')
                        ax.plot(ts[fi],etaj[fi],'gs')#,label=r'$\dot M$')
        #ax.set_ylim(0,2)
        ax.set_xlabel(r'$t\;[r_g/c]$',fontsize=16)
        ax.set_ylabel(r'$\eta\ [\%]$',fontsize=16,ha='left',labelpad=20)
        ax.set_xlim(ts[0],ts[-1])
        if showextra:
            plt.legend(loc='upper left',bbox_to_anchor=(0.05,0.95),ncol=1,borderpad = 0,borderaxespad=0,frameon=True,labelspacing=0)
            # set some legend properties.  All the code below is optional.  The
            # defaults are usually sensible but if you need more control, this
            # shows you how
            leg = plt.gca().get_legend()
            ltext  = leg.get_texts()  # all the text.Text instance in the legend
            llines = leg.get_lines()  # all the lines.Line2D instance in the legend
            frame  = leg.get_frame()  # the patch.Rectangle instance surrounding the legend
            # see text.Text, lines.Line2D, and patches.Rectangle for more info on
            # the settable properties of lines, text, and rectangles
            #frame.set_facecolor('0.80')      # set the frame face color to light gray
            plt.setp(ltext, fontsize=12)    # the legend text fontsize
            #plt.setp(llines, linewidth=1.5)      # the legend linewidth
            #leg.draw_frame(False)           # don't draw the legend frame


        print( "eta_BH = %g, eta_j = %g, eta_w = %g, eta_jw = %g, mdot = %g, mdotwind=%g, mdotjet=%g, ptot_BH = %g" % ( etabh_avg, etaj_avg, etaw_avg, etaj_avg + etaw_avg, mdotfinavg, mdotwindfinavg, mdotjetfinavg, ptot_avg ) )
        if iti > fti:
            print( "eta_BH2 = %g, eta_j2 = %g, eta_w2 = %g, eta_jw2 = %g, mdot2 = %g, mdotwind2=%g , mdotjet2=%g, ptot2_BH = %g" % ( etabh2_avg, etaj2_avg, etaw2_avg, etaj2_avg + etaw2_avg, mdotiniavg, mdotwindiniavg, mdotjetiniavg, ptot2_avg ) )

        #xxx
    #######################
    #
    # \Phi ***
    #
    #######################
    if whichplot == 5:
        # choose radius to measure jet quantities
        #
        omh = a / (2*(1+(1-a**2)**0.5))
        phibh=fstot[:,ihor]/4/np.pi/mdotfinavg**0.5
        #phij=phiabsj_mu2[:,iofr(rjet)]/4/np.pi/mdotfinavg**0.5
        #phiw=(phiabsj_mu1-phiabsj_mu2)[:,iofr(rjet)]/4/np.pi/mdotfinavg**0.5
        phij=phiabsj_mu1[:,iofr(rjet)]/4/np.pi/mdotfinavg**0.5
        phiw=phiabsj_mumax1[:,iofr(rjet)]/4/np.pi/mdotfinavg**0.5
        #
        #phijn=phiabsj_n_mu2[:,iofr(rjet)]/4/np.pi/mdotfinavg**0.5
        #phijs=phiabsj_s_mu2[:,iofr(rjet)]/4/np.pi/mdotfinavg**0.5
        phijn=phiabsj_n_mu1[:,iofr(rjet)]/4/np.pi/mdotfinavg**0.5
        phijs=phiabsj_s_mu1[:,iofr(rjet)]/4/np.pi/mdotfinavg**0.5
        #
        phibh2=fstot[:,ihor]/4/np.pi/mdotiniavg**0.5
        #phij2=phiabsj_mu2[:,iofr(rjet)]/4/np.pi/mdotiniavg**0.5
        #phiw2=(phiabsj_mu1-phiabsj_mu2)[:,iofr(rjet)]/4/np.pi/mdotiniavg**0.5
        phij2=phiabsj_mu1[:,iofr(rjet)]/4/np.pi/mdotiniavg**0.5
        phiw2=phiabsj_mumax1[:,iofr(rjet)]/4/np.pi/mdotiniavg**0.5
        #
        #phijn2=phiabsj_n_mu2[:,iofr(rjet)]/4/np.pi/mdotiniavg**0.5
        #phijs2=phiabsj_s_mu2[:,iofr(rjet)]/4/np.pi/mdotiniavg**0.5
        phijn2=phiabsj_n_mu1[:,iofr(rjet)]/4/np.pi/mdotiniavg**0.5
        phijs2=phiabsj_s_mu1[:,iofr(rjet)]/4/np.pi/mdotiniavg**0.5
        #
        if(1 and iti>fti):
            #use phi averaged over the same time interval for iti<t<=itf
            icond=(ts>=iti)*(ts<itf)
            phibh[icond]=phibh2[icond]
            phij[icond]=phij2[icond]
            phijs[icond]=phijs2[icond]
            phins[icond]=phijn2[icond]
            phiw[icond]=phiw2[icond]
        if dotavg:
            phibh_avg = timeavg(phibh**2,ts,fti,ftf)**0.5
            phij_avg = timeavg(phij**2,ts,fti,ftf)**0.5
            phiw_avg = timeavg(phiw**2,ts,fti,ftf)**0.5
            fstot_avg = timeavg(fstot[:,ihor]**2,ts,fti,ftf)**0.5
            #
            phijn_avg = timeavg(phijn**2,ts,fti,ftf)**0.5
            phijs_avg = timeavg(phijn**2,ts,fti,ftf)**0.5
            #
            if showextra:
                ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+timeavg(phij**2,ts,fti,ftf)**0.5,'--',color=(fc,fc+0.5*(1-fc),fc))
                ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+timeavg(phiw**2,ts,fti,ftf)**0.5,'-.',color=(fc,fc,1))
            ax.plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+phibh_avg,color=(ofc,fc,fc))
            if(iti>fti):
                phibh2_avg = timeavg(phibh2**2,ts,iti,itf)**0.5
                fstot2_avg = timeavg(fstot[:,ihor]**2,ts,iti,itf)**0.5
                if showextra:
                    ax.plot(ts[(ts<itf)*(ts>=iti)],0*ts[(ts<itf)*(ts>=iti)]+timeavg(phij2**2,ts,iti,itf)**0.5,'--',color=(fc,fc+0.5*(1-fc),fc))
                    ax.plot(ts[(ts<itf)*(ts>=iti)],0*ts[(ts<itf)*(ts>=iti)]+timeavg(phiw2**2,ts,iti,itf)**0.5,'-.',color=(fc,fc,1))
                ax.plot(ts[(ts<itf)*(ts>=iti)],0*ts[(ts<itf)*(ts>=iti)]+phibh2_avg,color=(ofc,fc,fc))
        #To approximately get efficiency:
        #ax.plot(ts,2./3.*np.pi*omh**2*np.abs(fsj30[:,ihor]/4/np.pi)**2/mdotfinavg)
        #prefactor to get sqrt(eta): (2./3.*np.pi*omh**2)**0.5
        ax.plot(ts,phibh,clr,label=r'$\phi_{\rm BH}$')
        ax.set_xlim(ts[0],ts[-1])
        #
        if showextra:
            ax.plot(ts,phij,'g--',label=r'$\phi_{\rm jet}$')
            ax.plot(ts,phiw,'b-.',label=r'$\phi_{\rm wind}$')
        if findex != None:
            if not isinstance(findex,tuple):
                if showextra:
                    ax.plot(ts[findex],phij[findex],'gs')
                ax.plot(ts[findex],phibh[findex],'o',mfc='r')
                ax.plot(ts[findex],phiw[findex],'bv')
            else:
                for fi in findex:
                    if showextra:
                        ax.plot(ts[fi],phij[fi],'gs')
                    ax.plot(ts[fi],phibh[fi],'o',mfc='r')
                    ax.plot(ts[fi],phiw[fi],'bv')
        #ax.set_ylabel(r'$\ \ \ k\Phi_j/\langle\dot M\rangle^{\!1/2}$',fontsize=16)
        ax.set_ylabel(r'$\phi$',fontsize=16,ha='left',labelpad=20)
        if showextra:
            plt.legend(loc='upper left',bbox_to_anchor=(0.05,0.95),ncol=1,borderpad = 0,borderaxespad=0,frameon=True,labelspacing=0)
            # set some legend properties.  All the code below is optional.  The
            # defaults are usually sensible but if you need more control, this
            # shows you how
            leg = plt.gca().get_legend()
            ltext  = leg.get_texts()  # all the text.Text instance in the legend
            llines = leg.get_lines()  # all the lines.Line2D instance in the legend
            frame  = leg.get_frame()  # the patch.Rectangle instance surrounding the legend
            # see text.Text, lines.Line2D, and patches.Rectangle for more info on
            # the settable properties of lines, text, and rectangles
            #frame.set_facecolor('0.80')      # set the frame face color to light gray
            plt.setp(ltext, fontsize=12)    # the legend text fontsize
            #plt.setp(llines, linewidth=1.5)      # the legend linewidth
            #leg.draw_frame(False)           # don't draw the legend frame
        #
        plt.setp( ax.get_xticklabels(), visible=False )
        print( "phi_BH = %g, fstot = %g" % ( phibh_avg, fstot_avg ) )
        print( "phi_jet = %g, phi_wind = %g" % ( phij_avg , phiw_avg ) )
        print( "phi_jetn = %g, phi_jets = %g" % ( phijn_avg , phijs_avg ) )
        if iti > fti:
            print( "phi2_BH = %g, fstot2 = %g" % ( phibh2_avg, fstot2_avg ) )

    if whichplot == -1:
        etajetavg = pjetfinavg/mdotfinavg
        foutpower = open( "pjet_power_%s.txt" %  os.path.basename(os.getcwd()), "w" )
        #foutpower.write( "#Name a Mdot   Pjet    Etajet  Psitot Psisqtot**0.5 Psijet Psisqjet**0.5 rstag Pjtotmax Pjtot1rstag Pjtot2rstag Pjtot4rstag Pjtot8rstag\n"  )
        foutpower.write( "%s %f %f %f %f %f %f %f %f %f %f %f %f %f %f\n" % (os.path.basename(os.getcwd()), a, mdotfinavg, 
                                                                       pjetfinavg, etajetavg, fstotfinavg, 
                                                                       fstotsqfinavg, fsj30finavg, fsj30sqfinavg, 
                                                                       rstag, pjtotfinavgvsr5max, pjtotfinavgvsr5rstag, 
                                                                       pjtotfinavgvsr5r2stag, pjtotfinavgvsr5r4stag, pjtotfinavgvsr5r8stag) )
        #flush to disk just in case to make sure all is written
        foutpower.flush()
        os.fsync(foutpower.fileno())
        foutpower.close()
        return( mdotfinavg, fstotfinavg, fstotsqfinavg, fsj30finavg, fsj30sqfinavg, pjemfinavgtot )

    if whichplot == -2:
        return( mdtotvsr, edtotvsr, edmavsr, ldtotvsr )

    if whichplot == -300:
        #BL metric g_rr
        rh = 1+(1-a**2)**0.5
        r1d = r[:,0,0]
        Sigma = r**2+a**2*np.cos(h)**2
        Delta = r**2-2*r+a**2
        gdrr = Sigma/Delta
        gdtt = -(1-2*r/Sigma)
        #
        uutKS = uu[0]
        uurKS = dxdxp[1,1]*uu[1]
        uuhKS = dxdxp[2,2]*uu[2] + dxdxp[2,1]*uu[1]
        uupKS = dxdxp[3,3]*uu[3]
        uurBL = uurKS
        uutBL = uutKS - 2*(r/Delta)*uurKS - (a/Delta) * uupKS
        vurBL = uurBL / uutBL
        vrBL = gdrr**0.5*vurBL 
        plt.figure(2)
        plt.loglog( r1d, -vrBL[:,ny/2].mean(-1), 'r', label=r"$t=%g$" % t )
        plt.xlim( rh, 100 )
        plt.ylim( 1e-3, 2 )
        plt.legend( loc = 'lower left' )
       
    if whichplot == -3:
        #BL metric g_rr
        rh = 1+(1-a**2)**0.5
        r1d = r[:,0,0]
        Sigma = r**2+a**2*np.cos(h)**2
        Delta = r**2-2*r+a**2
        gdrr = Sigma/Delta
        gdtt = -(1-2*r/Sigma)
        #
        uutKS = uu02h
        uurKS = dxdxp[1,1,None,:,ny/2,0]*uus12h
        uupKS = dxdxp[3,3,None,:,ny/2,0]*uus32h
        uurBL = uurKS
        uutBL = uutKS - 2*(r/Delta)[None,:,ny/2,0]*uurKS - (a/Delta)[None,:,ny/2,0] * uupKS
        vurBL = uurBL / uutBL
        vrBL = gdrr[None,:,ny/2,0]**0.5*vurBL 
        t1 = 0.5e4
        t2 = 1e4
        avg1_vr = timeavg(vrBL,ts,t1,t2) 
        t1 = 1e4
        t2 = 1.5e4
        avg2_vr = timeavg(vrBL,ts,t1,t2) 
        t1 = 1.5e4
        t2 = 2e4
        avg3_vr = timeavg(vrBL,ts,t1,t2) 
        plt.figure(1)
        plt.loglog( r1d, -avg1_vr, 'r', label=r"$5,000<t<10,000$" )
        plt.loglog( r1d, -avg2_vr, 'g', label=r"$10,000<t<15,000$" )
        plt.loglog( r1d, -avg3_vr, 'b', label=r"$15,000<t<20,000$" )
        plt.xlim( rh, 200 )
        plt.ylim( 1e-3, 2 )
        plt.grid()
        plt.ylabel( r"$v_{\hat r}$", fontsize = 20 )
        plt.xlabel( r"$r$", fontsize = 20 )
        plt.legend( loc = 'upper right' )

    if whichplot == -4:
        rh = 1+(1-a**2)**0.5
        r1d = r[:,0,0]
        plt.figure(1)
        plt.loglog( r1d, timeavg(rhos2h,ts,5000,10000), 'r', label=r"$5,000<t<10,000$" )
        plt.loglog( r1d, timeavg(rhos2h,ts,10000,15000), 'g', label=r"$10,000<t<15,000$" )
        plt.loglog( r1d, timeavg(rhos2h,ts,15000,20000), 'b', label=r"$15,000<t<20,000$" )
        plt.xlabel(r"$r$", fontsize = 15)
        plt.ylabel(r"$\rho$", fontsize = 15)
        plt.xlim( rh, 100 )
        plt.ylim( 1e-2, 15 )
        plt.grid()
        plt.legend( loc = 'lower left' )

    #if whichplot == -5:
        
    if whichplot == None:
        fig,plotlist=plt.subplots(nrows=4,ncols=1,sharex=True,figsize=(12,16),num=1)
        #plt.clf()
        plottitle = "a = %g: %s" % ( a, os.path.basename(os.getcwd()) )
        plt.suptitle( plottitle )
        plt.subplots_adjust(hspace=0.1) #increase vertical spacing to avoid crowding
        print fstot[:,ihor].shape
        plotlist[0].plot(ts,fstot[:,ihor],label=r'$\Phi_{\rm h,tot}$')
        #plotlist[0].plot(ts,fsj5[:,ihor],label=r'$\Phi_{\rm h,5}$')
        plotlist[0].plot(ts,fsj30[:,ihor],label=r'$\Phi_{\rm h,30}$')
        #plotlist[0].plot(ts,fs,'r+') #, label=r'$\Phi_{\rm h}/0.5\Phi_{\rm i}$: Data Points')
        if dotavg:
            plotlist[0].plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+fstotsqfinavg,label=r'$\langle \Phi^2_{\rm h,tot}\rangle^{1/2}$')
            plotlist[0].plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+fsj30sqfinavg,label=r'$\langle \Phi^2_{\rm h,30}\rangle^{1/2}$')
        plotlist[0].legend(loc='upper left')
        #plt.xlabel(r'$t\;(GM/c^3)$')
        plotlist[0].set_ylabel(r'$\Phi_{\rm h}$',fontsize=16)
        plt.setp( plotlist[0].get_xticklabels(), visible=False)
        plotlist[0].grid(True)
        #
        #plotlist[1].subplot(212,sharex=True)
        #plotlist[1].plot(ts,np.abs(mdtot[:,ihor]),label=r'$\dot M_{\rm h,tot}$')
        #plotlist[1].plot(ts,np.abs(mdtot[:,ihor]-md5[:,ihor]),label=r'$\dot M_{\rm h,tot,bsqorho<5}$')
        plotlist[1].plot(ts,np.abs(mdtot[:,ihor]-md10[:,ihor]),label=r'$\dot M_{{\rm h,tot}, b^2/rho<10}$')
        plotlist[1].plot(ts,np.abs(mdtot[:,ihor]-md30[:,ihor]),label=r'$\dot M_{{\rm h,tot}, b^2/rho<30}$')
        if dotavg:
            #plotlist[1].plot(ts[(ts<itf)*(ts>=iti)],0*ts[(ts<itf)*(ts>=iti)]+mdotiniavg,label=r'$\langle \dot M_{{\rm h,tot}, b^2/\rho<10}\rangle_{i}$')
            plotlist[1].plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+mdotfinavg,label=r'$\langle \dot M_{{\rm h,tot}, b^2/\rho<10}\rangle_{f}$')
        #plotlist[1].plot(ts,np.abs(md2h[:,ihor]),label=r'$\dot M_{\rm h,2h}$')
        #plotlist[1].plot(ts,np.abs(md4h[:,ihor]),label=r'$\dot M_{\rm h,4h}$')
        #plotlist[1].plot(ts,np.abs(md2hor[:,ihor]),label=r'$\dot M_{\rm h,2hor}$')
        #plotlist[1].plot(ts,np.abs(mdrhosq[:,ihor]),label=r'$\dot M_{\rm h,rhosq}$')
        #plotlist[1].plot(ts,np.abs(md5[:,ihor]),label=r'$\dot M_{\rm h,5}$')
        plotlist[1].plot(ts,np.abs(md10[:,ihor]),label=r'$\dot M_{\rm h,10}$')
        plotlist[1].plot(ts,np.abs(md30[:,ihor]),label=r'$\dot M_{\rm h,30}$')
        #plotlist[1].plot(ts,np.abs(md[:,ihor]),'r+') #, label=r'$\dot M_{\rm h}$: Data Points')
        plotlist[1].legend(loc='upper left')
        #plotlist[1].set_xlabel(r'$t\;(GM/c^3)$')
        plotlist[1].set_ylabel(r'$\dot M_{\rm h}$',fontsize=16)
        plt.setp( plotlist[1].get_xticklabels(), visible=False)

        plotlist[2].plot(ts,(pjem10[:,ihor]),label=r'$P_{\rm j,em10}$')
        plotlist[2].plot(ts,(pjem30[:,ihor]),label=r'$P_{\rm j,em30}$')
        if dotavg:
            plotlist[2].plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+pjetfinavg,label=r'$\langle P_{{\rm j,em30}\rangle_{f}}$')
        plotlist[2].legend(loc='upper left')
        #plotlist[2].set_xlabel(r'$t\;(GM/c^3)$')
        plotlist[2].set_ylabel(r'$P_{\rm j}$',fontsize=16)

        #plotlist[3].plot(ts,(pjem10[:,ihor]/mdtot[:,ihor]),label=r'$P_{\rm j,em10}/\dot M_{\rm tot}$')
        #plotlist[3].plot(ts,(pjem5[:,ihor]/(mdtot[:,ihor]-md5[:,ihor])),label=r'$P_{\rm j,em5}/\dot M_{{\rm tot},b^2/\rho<5}$')
        plotlist[3].plot(ts,(pjem30[:,ihor]/mdotfinavg),label=r'$\dot \eta_{10}=P_{\rm j,em10}/\dot M_{{\rm tot},b^2/\rho<30}$')
        if dotavg:
            #plotlist[3].plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+pjetfinavg/mdotiniavg,label=r'$\langle P_j\rangle/\langle\dot M_i\rangle_{f}$')
            plotlist[3].plot(ts[(ts<ftf)*(ts>=fti)],0*ts[(ts<ftf)*(ts>=fti)]+pjetfinavg/mdotfinavg,'r',label=r'$\langle P_j\rangle/\langle\dot M_f\rangle_{f}$')
        #plotlist[3].set_ylim(0,6)
        plotlist[3].legend(loc='upper left')
        plotlist[3].set_xlabel(r'$t\;(GM/c^3)$')
        #plotlist[3].set_ylabel(r'$P_{\rm j}/\dot M_{\rm h}$',fontsize=16)
        plotlist[3].set_ylabel(r'$\eta_{\rm jet}$',fontsize=16)

        #title("\TeX\ is Number $\displaystyle\sum_{n=1}^\infty\frac{-e^{i\pi}}{2^n}$!", 
        #      fontsize=16, color='r')
        plotlist[0].grid(True)
        plotlist[1].grid(True)
        plotlist[2].grid(True)
        plotlist[3].grid(True)
        fig.savefig('pjet1_%s.pdf' % os.path.basename(os.getcwd()) )

        #density/velocity/hor figure
        #!!!rhor=1+(1-a**2)**0.5
        fig,plotlist=plt.subplots(nrows=4,ncols=1,sharex=True,figsize=(12,16),num=2)
        #plt.clf()
        plottitle = r"\rho,u^r,h/r: a = %g: %s" % ( a, os.path.basename(os.getcwd()) )
        plt.suptitle( plottitle )
        plt.subplots_adjust(hspace=0.1) #increase vertical spacing to avoid crowding
        #print fstot[:,ihor].shape
        plotlist[0].plot(ts,hoverr[:,ihor],label=r'$(h/r)_{\rm h}$')
        plotlist[0].plot(ts,hoverr[:,iofr(2)],label=r'$(h/r)_{\rm 2}$') ##### continue here
        plotlist[0].plot(ts,hoverr[:,iofr(4)],label=r'$(h/r)_{\rm 4}$')
        plotlist[0].plot(ts,hoverr[:,iofr(8)],label=r'$(h/r)_{\rm 8}$')
        #lotlist[0].plot(ts,hoverr[:,iofr(10)],label=r'$(h/r)_{\rm 10}$')
        #plotlist[0].plot(ts,hoverr[:,iofr(12)],label=r'$(h/r)_{\rm 12}$')
        #plotlist[0].plot(ts,hoverr[:,iofr(15)],label=r'$(h/r)_{\rm 15}$')
        #thetamid
        plotlist[0].plot(ts,(thetamid-np.pi/2)[:,ihor],'--',label=r'$\theta_{\rm h}$')
        plotlist[0].plot(ts,(thetamid-np.pi/2)[:,iofr(2)],'--',label=r'$\theta_{\rm 2}$') ##### continue here
        plotlist[0].plot(ts,(thetamid-np.pi/2)[:,iofr(4)],'--',label=r'$\theta_{\rm 4}$')
        plotlist[0].plot(ts,(thetamid-np.pi/2)[:,iofr(8)],'--',label=r'$\theta_{\rm 8}$')
        #plotlist[0].plot(ts,(thetamid-np.pi/2)[:,iofr(10)],'--',label=r'$\theta_{\rm 10}$')
        #plotlist[0].plot(ts,(thetamid-np.pi/2)[:,iofr(12)],'--',label=r'$\theta_{\rm 12}$')
        #plotlist[0].plot(ts,(thetamid-np.pi/2)[:,iofr(15)],'--',label=r'$\theta_{\rm 15}$')
        #plotlist[0].plot(ts,fs,'r+') #, label=r'$\Phi_{\rm h}/0.5\Phi_{\rm i}$: Data Points')
        #legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand", borderaxespad=0.)
        plotlist[0].legend(loc='upper right',ncol=4)
        #plt.xlabel(r'$t\;(GM/c^3)$')
        plotlist[0].set_ylabel(r'$h/r$',fontsize=16)
        plt.setp( plotlist[0].get_xticklabels(), visible=False)
        plotlist[0].grid(True)
        #
        #plotlist[1].subplot(212,sharex=True)
        plotlist[1].plot(ts,(-uus12hor*dxdxp[1][1][:,0,0])[:,ihor],label=r'$-u^r_{\rm h}$')
        plotlist[1].plot(ts,(-uus12hor*dxdxp[1][1][:,0,0])[:,iofr(2)],label=r'$-u^r_{\rm 2}$') ##### continue here
        plotlist[1].plot(ts,(-uus12hor*dxdxp[1][1][:,0,0])[:,iofr(4)],label=r'$-u^r_{\rm 4}$')
        plotlist[1].plot(ts,(-uus12hor*dxdxp[1][1][:,0,0])[:,iofr(8)],label=r'$-u^r_{\rm 8}$')
        #plotlist[1].plot(ts,(-uus12hor*dxdxp[1][1][:,0,0])[:,iofr(10)],label=r'$-u^r_{\rm 10}$')
        #plotlist[1].plot(ts,(-uus12hor*dxdxp[1][1][:,0,0])[:,iofr(12)],label=r'$-u^r_{\rm 12}$')
        #plotlist[1].plot(ts,(-uus12hor*dxdxp[1][1][:,0,0])[:,iofr(15)],label=r'$-u^r_{\rm 15}$')
        plotlist[1].legend(loc='upper right')
        #plotlist[1].set_xlabel(r'$t\;(GM/c^3)$')
        plotlist[1].set_ylabel(r'$u^r$',fontsize=16)
        plt.setp( plotlist[1].get_xticklabels(), visible=False)

        plotlist[2].plot(ts,rhos2hor[:,ihor],label=r'$\rho_{\rm h}$')
        plotlist[2].plot(ts,rhos2hor[:,iofr(2)],label=r'$\rho_{\rm 2}$') ##### continue here
        plotlist[2].plot(ts,rhos2hor[:,iofr(4)],label=r'$\rho_{\rm 4}$')
        plotlist[2].plot(ts,rhos2hor[:,iofr(8)],label=r'$\rho_{\rm 8}$')
        #plotlist[2].plot(ts,rhos2hor[:,iofr(10)],label=r'$\rho_{\rm 10}$')
        #plotlist[2].plot(ts,rhos2hor[:,iofr(12)],label=r'$\rho_{\rm 12}$')
        #plotlist[2].plot(ts,rhos2hor[:,iofr(15)],label=r'$\rho_{\rm 15}$')
        plotlist[2].legend(loc='upper left')
        #plotlist[2].set_xlabel(r'$t\;(GM/c^3)$')
        plotlist[2].set_ylabel(r'$\rho$',fontsize=16)

        plotlist[3].plot(ts,(ugs2hor/rhos2hor)[:,ihor],label=r'$u^r_{\rm h}$')
        plotlist[3].plot(ts,(ugs2hor/rhos2hor)[:,iofr(2)],label=r'$u^r_{\rm 2}$') ##### continue here
        plotlist[3].plot(ts,(ugs2hor/rhos2hor)[:,iofr(4)],label=r'$u^r_{\rm 4}$')
        plotlist[3].plot(ts,(ugs2hor/rhos2hor)[:,iofr(8)],label=r'$u^r_{\rm 8}$')
        #plotlist[3].plot(ts,(ugs2hor/rhos2hor)[:,iofr(10)],label=r'$u^r_{\rm 10}$')
        #plotlist[3].plot(ts,(ugs2hor/rhos2hor)[:,iofr(12)],label=r'$u^r_{\rm 12}$')
        #plotlist[3].plot(ts,(ugs2hor/rhos2hor)[:,iofr(15)],label=r'$u^r_{\rm 15}$')
        plotlist[3].legend(loc='upper left')
        plotlist[3].set_xlabel(r'$t\;(GM/c^3)$')
        plotlist[3].set_ylabel(r'$u_g/\rho$',fontsize=16)

        #title("\TeX\ is Number $\displaystyle\sum_{n=1}^\infty\frac{-e^{i\pi}}{2^n}$!", 
        #      fontsize=16, color='r')
        plotlist[0].grid(True)
        plotlist[1].grid(True)
        plotlist[2].grid(True)
        plotlist[3].grid(True)
        fig.savefig('pjet2_%s.pdf' % os.path.basename(os.getcwd()) )
    
        plt.figure(3)
        plt.clf()
        plt.plot(r[:,0,0],mdotfinavgvsr,label=r'$\dot M_{\rm tot}$')
        plt.plot(r[:,0,0],mdotfinavgvsr5,label=r'$\dot M_{b^2/\rho<5}$')
        plt.plot(r[:,0,0],mdotfinavgvsr10,label=r'$\dot M_{b^2/\rho<10}$')
        plt.plot(r[:,0,0],mdotfinavgvsr20,label=r'$\dot M_{b^2/\rho<20}$')
        plt.plot(r[:,0,0],mdotfinavgvsr30,label=r'$\dot M_{b^2/\rho<30}$')
        plt.plot(r[:,0,0],mdotfinavgvsr40,label=r'$\dot M_{b^2/\rho<40}$')
        plt.xlim(1+(1-a**2)**0.5,20)
        plt.ylim(0,np.max(mdotfinavgvsr[r[:,0,0]<20]))
        plt.legend(loc='lower right')
        plt.grid()
        plt.savefig('pjet3_%s.pdf' % os.path.basename(os.getcwd()) )

        plt.figure(4)
        plt.clf()
        rmax=50
        plt.plot(r[:,0,0],pjemfinavgvsr,'b',label=r'$\dot Pem_{\rm tot}$')
        plt.plot(r[:,0,0],pjemfinavgvsr5,'g',label=r'$\dot Pem_{b^2/\rho>5}$')
        plt.plot(r[:,0,0],pjemfinavgvsr10,'r',label=r'$\dot Pem_{b^2/\rho>10}$')
        plt.plot(r[:,0,0],pjemfinavgvsr20,'c',label=r'$\dot Pem_{b^2/\rho>20}$')
        plt.plot(r[:,0,0],pjemfinavgvsr30,'m',label=r'$\dot Pem_{b^2/\rho>30}$')
        plt.plot(r[:,0,0],pjemfinavgvsr40,'y',label=r'$\dot Pem_{b^2/\rho>40}$')
        plt.plot(r[:,0,0],pjtotfinavgvsr,'b--',label=r'$\dot P_{\rm tot}$')
        plt.plot(r[:,0,0],pjtotfinavgvsr5,'g--',label=r'$\dot P_{b^2/\rho>5}$')
        plt.plot(r[:,0,0],pjtotfinavgvsr10,'r--',label=r'$\dot P_{b^2/\rho>10}$')
        plt.plot(r[:,0,0],pjtotfinavgvsr20,'c--',label=r'$\dot P_{b^2/\rho>20}$')
        plt.plot(r[:,0,0],pjtotfinavgvsr30,'m--',label=r'$\dot P_{b^2/\rho>30}$')
        plt.plot(r[:,0,0],pjtotfinavgvsr40,'y--',label=r'$\dot P_{b^2/\rho>40}$')
        plt.xlim(1+(1-a**2)**0.5,rmax)
        plt.ylim(0,np.max(pjemfinavgvsr[r[:,0,0]<rmax]))
        plt.legend(loc='lower right',ncol=2)
        plt.grid()
        plt.savefig('pjet4_%s.pdf' % os.path.basename(os.getcwd()) )

        plt.figure(5)
        plt.clf()
        rmax=200
        plt.plot(r[:,0,0],phiabsj_mu1vsr,'b',label=r'$\Phi_{\rm jet}$')
        plt.xlim(1+(1-a**2)**0.5,rmax)
        plt.ylim(0,np.max(phiabsj_mu1vsr[r[:,0,0]<rmax]))
        plt.legend(loc='lower right',ncol=2)
        plt.grid()
        plt.savefig('phi1_%s.pdf' % os.path.basename(os.getcwd()) )


def timeavg( qty, ts, fti, ftf, step = 1 ):
    cond = (ts<ftf)*(ts>=fti)
    #use masked array to remove any stray NaN's
    qtycond = np.ma.masked_array(qty[cond],np.isnan(qty[cond]))
    qtycond = qtycond[::step]
    qtyavg = qtycond.mean(axis=0,dtype=np.float64)
    return( qtyavg )

def getstagparams(var=None,rmax=20,doplot=1,doreadgrid=1):
    if doreadgrid:
        grid3d("gdump.bin",use2d=True)
    avgmem = get2davg(usedefault=1)
    assignavg2dvars(avgmem)
    #a large enough distance that floors are not applied, yet close enough that reaches inflow equilibrium
    rnoflooradded=20
    #radial index and radius of stagnation surface
    sol = avg_uu[1]*(r-rmax)
    istag = np.floor( findroot2d(sol, ti, axis = 1, isleft=True, fallback = 1, fallbackval = iofr(rnoflooradded)) + 0.5 )
    jstag = np.floor( findroot2d(sol, tj, axis = 1, isleft=True, fallback = 1, fallbackval = iofr(rnoflooradded)) + 0.5 )
    rstag = findroot2d( sol, r, axis = 1, isleft=True, fallback = 1, fallbackval = rnoflooradded )
    hstag = findroot2d( sol, h, axis = 1, isleft=True, fallback = 1, fallbackval = np.pi/2.)
    if doplot:
        plt.figure(1)
        plt.clf()
        plt.plot(hstag,rstag)
        plt.figure(2)
        plco(avg_uu[1],levels=(0,),colors='k',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plt.xlim(0,10)
        plt.ylim(-5,5)
    #cond=(ti==istag[None,:,None])*(tj==jstag[None,:,None])
    #print( zip(r[cond],rstag) )
    if var is not None:
        varstag = findroot2d( avg_uu[1], var, axis = 1, isleft=True, fallback = 0)
        return varstag
    else:
        return istag, jstag, hstag, rstag

def get_dUfloor( floordumpno, maxrinflowequilibrium = 20 ):
    """ maxrsteady should be chosen to be on the outside of the inflow equilibrium region """
    RR=0
    TH=1
    PH=2
    rfloor( "failfloordudump%04d.bin" % floordumpno )
    #add back in rest-mass energy to conserved energy
    dUfloor[1] -= dUfloor[0]
    condin = (avg_uu[1]<0)*(r[:,:,0:1]<maxrinflowequilibrium)
    condout = 1 - condin
    UfloorAout = (dUfloor*condout[None,:,:,:]).sum(1+PH).sum(1+TH).cumsum(1+RR)
    UfloorAin = (dUfloor*condin[None,:,:,:]).sum(1+PH).sum(1+TH).cumsum(1+RR)
    UfloorA = (UfloorAin-UfloorAin[:,nx-1:nx]) + UfloorAout
    UfloorAsum = UfloorA*scaletofullwedge(1.)
    return( UfloorAsum )


def takeoutfloors(doreload=1,dotakeoutfloors=1):
    global dUfloor, qtymem, DUfloorori, etad0
    #Mdot, E, L
    grid3d("gdump.bin",use2d=True)
    istag, jstag, hstag, rstag = getstagparams(rmax=20,doplot=0,doreadgrid=0)
    if np.abs(a - 0.99)<1e-4 and scaletofullwedge(1.0) < 1.5:
        #hi-res 0.99 settings
        print( "Using hires a = 0.99 settings")
        #DTd = 22800-22231.9647756934 + 22200-22167.669585504507268 #22119.452438349220756
        dt = 100.
        # Dt = np.array([dt,-dt])
        # Dno = np.array([224.,223.])
        # fti = 14700.
        # ftf = 25000.
        Dt = np.array([28200-28097.4708711805,
                       28000-27406.4732593203,
                       27400-26763.9946654502,
                       26700-26330.0889135128,
                       26300-25799.8775611997,
                       25700-25124.6341346588,
                       25100-24594.4658011928,
                       24500-23951.5226133435,
                       23900-23292.5857662206,
                       23200-22890.8671337456,
                       22800-22231.9647756934,
                       22200-22167.6695855045])
        Dno = np.array([282,
                        280,
                        274,
                        267,
                        263,
                        257,
                        251,
                        245,
                        239,
                        232,
                        228,
                        222])
        fti = 22167.6695855045
        ftf = 28200.
    elif np.abs(a - 0.99)<1e-4 and scaletofullwedge(1.0) > 1.5:
        #lo-res 0.99 settings
        print( "Using lores a = 0.99 settings")
        dt = 100.
        # Dt = np.array([13700-11887.3058391312,
        #                11800.-11547.5107224568,
        #                11500-9727.2561911212,
        #                9700-8435.61370926043,
        #                8400-8000,-(8400-8000)])
        # Dno = np.array([137,
        #                 118,
        #                 115,
        #                 97,
        #                 84,80])
        Dt = np.array([13700-11887.3058391312])
        Dno = np.array([137])
        fti = 11887.3058391312
        ftf = 13700.
    elif np.abs(a - 0.5)<1e-4:
        print( "Using a = 0.5 settings")
        dt = 13000.-10300.
        Dt = np.array([dt,-dt])
        Dno = np.array([130,103])
        fti = 10300.
        ftf = 13000.
    elif np.abs(a - 0.2)<1e-4:
        print( "Using a = 0.2 settings")
        Dt = np.array([13300.-10366.5933313178])
        Dno = np.array([133])
        fti = 10366.5933313178
        ftf = 13300.
    else:
        print( "Unknown case: a = %g, aborting..." % a )
        return
    #dotakeoutfloors=1
    RR=0
    TH=1
    PH=2
    if doreload:
        etad0 = -1/(-gn3[0,0])**0.5
        #!!!rhor = 1+(1-a**2)**0.5
        ihor = iofr(rhor)
        qtymem=getqtyvstime(ihor,0.2)
        #initialize with zeros
        DT = 0
        if dotakeoutfloors:
            for (i,iDT) in enumerate(Dt):
                gc.collect() #try to clean up memory if not used
                iDU = get_dUfloor( Dno[i] )
                if iDT > 0:
                    DT += iDT
                if i==0:
                    DU = iDU
                else:
                    DU += iDU * np.sign(iDT)
            #average in time
            DU /= DT
        else:
            DU = np.zeros((8,nx),dtype=np.float64)
    DUfloor0 = DU[0]
    DUfloor1 = DU[1]
    DUfloor4 = DU[4]
    mdtotvsr, edtotvsr, edmavsr, ldtotvsr = plotqtyvstime( qtymem, whichplot = -2, fti=fti, ftf=ftf )
    FE=np.load("fe.npy")
    #edtotvsr-=FE
    #avgmem = get2davg(usedefault=1)
    #assignavg2dvars(avgmem)
    #edtotvsr = -(gdet[:,1:ny-1,0:1]*avg_Tud[1][0][:,1:ny-1,0:1]*_dx2*_dx3*nz).sum(-1).sum(-1)
    #!!!rhor = 1+(1-a**2)**0.5
    rh=rhor
    ihor = iofr(rhor)
    #FIGURE: mass
    plt.figure(1)
    plt.clf()
    plt.plot(r[:,0,0],mdtotvsr,'b--',label=r"$F_M$ (raw)")
    if dotakeoutfloors:
        Fm=(mdtotvsr+DUfloor0)
        plt.plot(r[:,0,0],Fm,'b',label=r"$F_M$")
    if ldtotvsr is not None:
        Fl=-(ldtotvsr+DUfloor4)
        plt.plot(r[:,0,0],-ldtotvsr/dxdxp[3][3][:,0,0]/10.,'g--',label=r"$F_L/10$ (raw)")
        if dotakeoutfloors:
            plt.plot(r[:,0,0],Fl/dxdxp[3][3][:,0,0]/10.,'g',label=r"$F_L/10$")
    plt.plot(r[:,0,0],-edtotvsr,'r--',label=r"$F_E$ (raw)")
    plt.plot(r[:,0,0],FE,'k--',label=r"$F_E$")
    if dotakeoutfloors:
        Fe=-(edtotvsr+DUfloor1)
        plt.plot(r[:,0,0],Fe,'r',label=r"$F_E$")
        plt.plot(r[:,0,0],FE-DUfloor1,'k',label=r"$F_E$")
        plt.plot(r[:,0,0],(DUfloor1),'r:')
    eta = ((Fm-Fe)/Fm)
    etap = (Fm-Fe)/Fe
    print("Eff = %g, Eff' = %g" % ( eta[iofr(5)], etap[iofr(5)] ) )
    #plt.plot(r[:,0,0],DUfloor0,label=r"$dU^t$")
    #plt.plot(r[:,0,0],DUfloor*1e4,label=r"$dU^t\times10^4$")
    plt.legend(loc='lower right',ncol=3)
    plt.xlim(rhor,20)
    plt.ylim(-15,15)
    plt.grid()
    plt.xlabel(r"$r\ [r_g]$",fontsize=16)
    plt.ylabel("Flux",fontsize=16)
    plt.savefig("fig4.pdf",bbox_inches='tight',pad_inches=0.02)
    plt.savefig("fig4.eps",bbox_inches='tight',pad_inches=0.02)
    plt.savefig("fig4.png",bbox_inches='tight',pad_inches=0.02)
    #FIGURE: energy
    #plt.figure(2)
    #plt.plot(r[:,0,0],edtotvsr+DUfloor1,label=r"$\dot E+dU^1$")
    #plt.plot(r[:,0,0],DUfloor1,label=r"$dU^1$")
    #plt.legend()
    #plt.xlim(rhor,12)
    #plt.ylim(-3,20)
    #plt.grid()
    #
    avgmem = get2davg(usedefault=1)
    assignavg2dvars(avgmem)
    edtot2davg = (gdet[:,:,0:1]*avg_Tud[1][0][:,:,0:1]*_dx2*_dx3*nz).sum(-1).sum(-1)
    rhouuudtot2davg = (gdet[:,:,0:1]*avg_rhouuud[1][0][:,:,0:1]*_dx2*_dx3*nz).sum(-1).sum(-1)
    uguuudtot2davg = (gdet[:,:,0:1]*avg_uguuud[1][0][:,:,0:1]*_dx2*_dx3*nz).sum(-1).sum(-1)
    avg_tudmass = (gdet[:,:,0:1]*(avg_rhouu[1])*(avg_ud[0])*_dx2*_dx3*nz).sum(-1).sum(-1)
    avg_tudug = (gdet[:,:,0:1]*(avg_uguu[1])*(avg_ud[0])*_dx2*_dx3*nz).sum(-1).sum(-1)
    avg_tudmassug = (gdet[:,:,0:1]*(avg_rhouu[1]+avg_uguu[1])*(avg_ud[0])*_dx2*_dx3*nz).sum(-1).sum(-1)
    gc.collect()
    #
    # plt.figure(2)
    # plt.plot(r[:,0,0],edtotvsr,label="tot")
    # plt.plot(r[:,0,0],-edtot2davg,label="tot2davg")
    # #plt.plot(r[:,0,0],-rhouuudtot2davg,label="rhouuud")
    # #plt.plot(r[:,0,0],-gam*uguuudtot2davg,label="gamuguuud")
    # myma=-(rhouuudtot2davg+gam*uguuudtot2davg)
    # plt.plot(r[:,0,0],-avg_tudmass,label="mymass")
    # plt.plot(r[:,0,0],-avg_tudmassug,label="mymassug")
    # plt.plot(r[:,0,0],-avg_tudug,label="myug")
    # plt.plot(r[:,0,0],edmavsr,label="ma")
    # plt.plot(r[:,0,0],edtotvsr-edmvsr,label="tot-m")
    # #plt.plot(r[:,0,0],DUfloor[1])
    # plt.xlim(rh,20); plt.ylim(-20,20)
    # plt.legend()
    # if ldtotvsr is not None:
    #     plt.plot(r[:,0,0],ldtotvsr+DUfloor4,label=r"$Lwoutfloor$")
    #plt.xlim(rhor,12)
    #plt.ylim(-3,20)
    #xx
    # plt.grid()
    # #
    # plt.figure(3)
    # plt.plot(r[:,0,0],-edtot2davg,label="tot2davg")
    # gc.collect()



def plotj(ts,fs,md,jem,jtot):
    #rc('font', family='serif')
    #plt.figure( figsize=(12,9) )
    plt.clf()
    fig,plotlist=plt.subplots(nrows=3,ncols=1,sharex=True,figsize=(12,12))
    plottitle = "a = %g: %s" % ( a, os.path.basename(os.getcwd()) )
    plt.suptitle( plottitle )
    plt.subplots_adjust(hspace=0.1) #increase vertical spacing to avoid crowding
    plotlist[0].plot(ts,fs,label=r'$\Phi_{\rm h}/\Phi_{\rm i}$')
    #plotlist[0].plot(ts,fs,'r+') #, label=r'$\Phi_{\rm h}/0.5\Phi_{\rm i}$: Data Points')
    plotlist[0].legend(loc='lower right')
    #plt.xlabel(r'$t\;(GM/c^3)$')
    plotlist[0].set_ylabel(r'$\Phi_{\rm h}$',fontsize=16)
    plt.setp( plotlist[0].get_xticklabels(), visible=False)
    plotlist[0].grid(True)
    #
    #plotlist[1].subplot(212,sharex=True)
    plotlist[1].plot(ts,md,label=r'$\dot M_{\rm h}$')
    #plotlist[1].plot(ts,md,'r+') #, label=r'$\dot M_{\rm h}$: Data Points')
    plotlist[1].legend(loc='lower right')
    #plotlist[1].set_xlabel(r'$t\;(GM/c^3)$')
    plotlist[1].set_ylabel(r'$\dot M_{\rm h}$',fontsize=16)
    plt.setp( plotlist[1].get_xticklabels(), visible=False)
    
    #plotlist[2].subplot(212,sharex=True)
    plotlist[2].plot(ts,jem/md,label=r'$P_{\rm j,em}/\dot M$')
    #plotlist[2].plot(ts,jem/md,'r+') #, label=r'$\dot M_{\rm h}$: Data Points')
    plotlist[2].plot(ts,jtot/md,label=r'$P_{\rm j,tot}/\dot M$')
    #plotlist[2].plot(ts,jtot/md,'r+') #, label=r'$\dot M_{\rm h}$: Data Points')
    plotlist[2].legend(loc='lower right')
    plotlist[2].set_xlabel(r'$t\;(GM/c^3)$')
    plotlist[2].set_ylabel(r'$P_{\rm j}/\dot M_{\rm h}$',fontsize=16)

    #title("\TeX\ is Number $\displaystyle\sum_{n=1}^\infty\frac{-e^{i\pi}}{2^n}$!", 
    #      fontsize=16, color='r')
    plotlist[0].grid(True)
    plotlist[1].grid(True)
    plotlist[2].grid(True)
    fig.savefig('pjetf_%s.pdf' % os.path.basename(os.getcwd()) )


def test():
    t=np.arange(10)
    f=np.arange(10)**2
    plt.plot(t,f,label='$\Phi$')
    plt.title(r"This is a title")
    plt.legend(loc='upper right')
    plt.xlabel(r'$t (GM/c^3)$')
    plt.ylabel(r'$\Phi_{\rm h}$',fontsize=16)
    #plt.legend()

def gen_vpot(whichloop=None,phase=0.0,whichfield=None,fieldhor=0.194,rin=10):
    #whichfield = 0 -- single loop follows density contours
    #whichfield = None -- alternating loops
    global rho_av, rho_max, var, uq, uqc, uqcomax, aB, B, res,ud,etad, etau, gamma, vu, vd, bu, bd, bsq, phi
    #res=np.abs(bu[2]/np.sqrt(rho)/((uu[3]+1e-15)/uu[0])/_dx2)
    #plco(res,cb=True)
    #plt.plot(ti[:,ny/2,0],res[:,ny/2,0])
    #Old settings (now incorporated as defaults in this function call):
    #fieldhor = 0.194
    #rin = 10
    startfield = 1.1 * rin
    rho_av = np.copy(rho[:,:,0:1])
    #average to corners
    rho_av[1:nx,1:ny,0:1] = 0.25*(rho[0:nx-1,0:ny-1,0:1]+rho[1:nx,0:ny-1,0:1]+rho[0:nx-1,1:ny,0:1]+rho[1:nx,1:ny,0:1])
    rho_max=np.max(rho_av)
    #define aphi
    if( whichfield == None ):
        var = (r[:,:,0:1]**2*rho_av/rho_max) #**gam #*r[:,:,0:1]**1
        varc = (r[:,:,0:1]**2*rho/rho_max) #**gam #*r[:,:,0:1]**1
    else:
        var = (rho_av/rho_max) #**gam #*r[:,:,0:1]**1
        varc = (rho/rho_max) #**gam #*r[:,:,0:1]**1
    #note r should be shifted, too (not done yet):
    maxvar=np.max(var)
    maxvarc=np.max(varc)
    uq = (var-0.0*maxvar) #*r[:,:,0:1]**0.75 #/(0.1**2+(h-np.pi/2)**2)
    uqc = (varc-0.0*maxvarc) #*r[:,:,0:1]**0.75 #/(0.1**2+(h-np.pi/2)**2)
    uqcomax = varc/maxvarc #rho/rho_max #varc/maxvarc
    phi = np.log(r[:,:,0:1]/startfield)/fieldhor
    arg = phi-phase*np.pi
    #aaphi = uq**2 * (r-startfield)**1.1
    if( whichfield == None ):
        aaphi = uq**2 #* np.sin( arg )**1
    elif( whichfield == 0 ):
        aaphi = uq**2
    #aaphi = uq**2 * (1+0.2*np.sin( arg )**1)
    aaphi[uq<0] = 0
    if whichloop != None:
        notuse1 = arg > np.pi*(whichloop+1)
        notuse2 = arg < np.pi*whichloop
        aaphi[notuse1] = 0.0
        aaphi[notuse2] = 0.0
    #aaphi = uq**2 #* np.log(r[:,:,0:1]/startfield)
    #aaphi = uq**(2)
    aphi2B(aaphi)
    #reset field components outside torus to zero
    #B[1,uqc<0] = 0
    #B[2,uqc<0] = 0
    return(aaphi)

def aphi2B(aaphi):
    #aB -- face-centered
    #B -- cell-centered
    global B, aB, gdetB
    aB = np.zeros_like(B)
    gdetB = np.zeros_like(B)
    gdetB[1,1:nx,0:ny-1] = (aaphi[1:nx,1:ny]-aaphi[1:nx,0:ny-1])/_dx2
    gdetB[2,0:nx-1,1:ny] = (aaphi[1:nx,1:ny]-aaphi[0:nx-1,1:ny])/_dx1
    aB[1,1:nx,0:ny-1] = gdetB[1,1:nx,0:ny-1] / (0.5*(gdet[0:nx-1,0:ny-1]+gdet[1:nx,0:ny-1]))
    aB[2,0:nx-1,1:ny] = gdetB[2,0:nx-1,1:ny] / (0.5*(gdet[0:nx-1,0:ny-1]+gdet[0:nx-1,1:ny]))
    #ab[3] is zeroes
    #
    B=np.zeros_like(aB)
    #properly center the field
    B[1,0:nx-1,0:ny,:] = (aB[1,0:nx-1,0:ny,:] + aB[1,1:nx,0:ny,:])/2
    B[2,0:nx,0:ny-1,:] = (aB[2,0:nx,1:ny,:] + aB[2,0:nx,0:ny-1,:])/2

def pl(x,y,j=None):
    global ny
    if j == None: j = ny/2
    plt.plot(x[:,j,0],y[:,j,0])

def fac(ph):
    return(1+0.5*((ph/np.pi-1.5)/0.5)**2)

def avg2ctof(q):
    qavg2 = np.empty_like(q)
    qavg2[0:nx,1:ny,:] = (q[0:nx,1:ny,:] + q[0:nx,0:ny-1,:])/2
    return(qavg2)

def avg1ctof(q):
    qavg1 = np.empty_like(q)
    qavg1[1:nx,0:ny,:] = (q[0:nx-1,0:ny,:] + q[1:nx,0:ny,:])/2
    return(qavg1)

def avg0ctof(q):
    resavg0 = np.empty_like(q)
    resavg0[1:nx,1:ny,:] = 0.25*(q[0:nx-1,0:ny-1,:]+q[1:nx,0:ny-1,:]+q[0:nx-1,1:ny,:]+q[1:nx,1:ny,:])
    return(resavg0)

def normalize_field(targbsqoug):
    global B, gdetB, bsq, ug
    maxbsqoug = np.max(bsq/(ug+1e-5))
    rat = np.sqrt(targbsqoug/maxbsqoug)
    #rescale all field components
    B *= rat
    gdetB *= rat
    #recompute derived quantities
    cvel()
def plotbs(dy=0):
    plt.clf();
    plot(ti[:,ny/2,0],B[1,:,ny/2+dy,0])
    plot(ti[:,ny/2,0],B[2,:,ny/2+dy,0])
    plot(ti[:,ny/2,0],(bsq/ug)[:,ny/2+dy,0]/100)
    plot(ti[:,ny/2,0],(gdetB[1]/gdet)[:,ny/2+dy,0])
def plotaphi(dy=0):
    aphi=fieldcalc()
    plot(r[:,ny/2,0],aphi[:,ny/2,0])
    xlim(xmin=10,xmax=100)

def face2centdonor():
    global bcent
    bcent=np.zeros_like(B)
    bcent[1][0:nx-1,:,:]=0.5*(gdetB[1][0:nx-1,:,:]+gdetB[2][1:nx,:,:])/gdet[0:nx-1,:,:]
    bcent[2][:,0:ny-1,:]=0.5*(gdetB[2][:,0:ny-1,:]+gdetB[2][:,1:ny,:])/gdet[:,0:ny-1,:]
    bcent[3][:,:,0:nz-1]=0.5*(gdetB[2][:,:,0:nz-1]+gdetB[2][:,:,1:nz])/gdet[:,:,0:nz-1]

def pf(dir=2):
    global bcent
    grid3d("gdump.bin")
    #rfd("fieldline0000.bin")
    #rrdump("rdump--0000.bin")
    rd("dump0000.bin")
    face2centdonor(); 
    plt.clf(); 
    myi = 20
    myk = 0
    plt.plot(tj[myi,:,myk],bcent[dir,myi,:,myk]);
    plt.plot(tj[myi,:,myk],B[dir,myi,:,myk]);
    plt.plot(tj[myi,0:ny-1,myk]+0.5,gdetB[dir,myi,1:ny,myk]/(0.5*(gdet[myi,0:ny-1,myk]+gdet[myi,1:ny,myk])))


def chophi(var,maxvar):
    newvar = np.copy(var)
    newvar[var>maxvar]=0*var[var>maxvar]+maxvar
    return(newvar)

def choplo(var,minvar):
    newvar = np.copy(var)
    newvar[var<minvar]=0*var[var<minvar]+minvar
    return(newvar)

def Risco(a):
    Z1 = 1 + (1. - a**2)**(1./3.) * ((1. + a)**(1./3.) + (1. - a)**(1./3.))
    Z2 = (3*a**2 + Z1**2)**(1./2.)
    risco = 3 + Z2 - np.sign(a)* ( (3 - Z1)*(3 + Z1 + 2*Z2) )**0.5
    return(risco)

def plotpowers(fname,hor=0,format=1):
    if format == 0: #old format
        gd1 = np.loadtxt( fname, unpack = True, usecols = [1,2,3,4,5,6,7,8,9,10,11,12,13,14] )
        #gd=gd1.view().reshape((-1,nx,ny,nz), order='F')
        alist = gd1[0]
        rhorlist = 1+(1-alist**2)**0.5
        omhlist = alist / 2 / rhorlist
        mdotlist = gd1[1]
        #etalist = gd1[3]
        powlist=gd1[12] #pow(2*rstag)
        psitotsqlist = gd1[5]
        psi30sqlist = gd1[7]
    elif format == 1: #new avg2d format
        gd1 = np.loadtxt( fname, unpack = True, usecols = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27] )
        #gd=gd1.view().reshape((-1,nx,ny,nz), order='F')
        alist = gd1[0]
        rhorlist = 1+(1-alist**2)**0.5
        omhlist = alist / 2 / rhorlist
        mdotlist = gd1[5]
        ftotlist=gd1[6]
        fsqtotlist=gd1[7]
        f30list=gd1[8]
        f30sqlist=gd1[9]
        pjetemtotlist=gd1[10]
        eoutEMtotlist=gd1[11]
        #etalist = gd1[3]
        i = 12
        #1
        powEMKElist=gd1[i]; i+=1
        powwindEMKElist=gd1[i]; i+=1
        powlist=gd1[i]; i+=1
        powwindlist=gd1[i]; i+=1
        rlist=gd1[i]; i+=1
        #2
        powEMKElist2=gd1[i]; i+=1
        powwindlEMKEist2=gd1[i]; i+=1
        powlist2=gd1[i]; i+=1
        powwindlist2=gd1[i]; i+=1
        rlist2=gd1[i]; i+=1
        #3
        powEMKElist3=gd1[i]; i+=1
        powwindEMKElist3=gd1[i]; i+=1
        powlist3=gd1[i]; i+=1
        powwindlist3=gd1[i]; i+=1
        rlist3=gd1[i]; i+=1
    etalist = powEMKElist/mdotlist
    etaEMlist = eoutEMtotlist/mdotlist
    etawindlist = powwindEMKElist/mdotlist
    gin = open( fname, "rt" )
    emptyline = gin.readline()
    for i in np.arange(alist.shape[0]):
        simname = gin.readline().split()[0]
        print '%.2g & %.3g & %.3g & %.3g & %.3g & %% %s' % (alist[i], 100*etaEMlist[i], 100*etalist[i], 100*(etawindlist[i]-etalist[i]), 100*etawindlist[i], simname)
    gin.close()
    mya=np.arange(-1,1,0.001)
    rhor = 1+(1-mya**2)**0.5
    myomh = mya / 2/ rhor
    #fitting function
    f0 = 2.9
    f1 = -0.6
    f1n = 1.4
    f2 = 0.
    f = f0 * (1 + (f1*(1+np.sign(myomh))/2. + f1n*(1-np.sign(myomh))/2.) * myomh + f2 * myomh**2)
    #gammie way -- too large amplitude
    #gammieparamopi = (8./3.*(3.-mya**2+3.*(1-mya**2)**0.5))**0.5
    #f = f0 * 0.25 * gammieparamopi
    #mypwr = 5*myomh**2
    psi = 1.0
    mypwr = 2.0000 * 1.*1.0472*myomh**2 * 1.5*(psi**2-psi**3/3) #prefactor = 2pi/3, consistent with (A7) from TMN10a
    horx=0.09333
    #myr = Risco(mya) #does not work at all: a < 0 power is much greater than a > 0
    myeta = mypwr * (mya**2+3*rhor**2)/3 / (2*np.pi*horx)
    #plt.plot( mya, myeta )
    rhor6 = 1+(1-mspina6[mhor6==hor]**2)**0.5
    #Tried to equate pressures -- works but mistake in calculaton -- wrong power
    #plt.plot(mspina6[mhor6==hor],mpow6[mhor6==hor]* ((mspina6[mhor6==hor]**2+3*rhor6**2)/3/(2*np.pi*horx)) )
    #Simple multiplication by rhor -- works!  \Phi^2/Mdot * rhor ~ const
    fac = 0.838783 #0.044/(1./(6*np.pi))
    #plt.plot(mya,mya**2)
    #plt.plot(alist,etawindlist,'go',label=r'$\eta_{\rm jet}+\eta_{\rm wind}$')
    # plt.plot(mspina6[mhor6==hor],fac*6.94*mpow6[mhor6==hor],'r--',label=r'$P_{\rm BZ,6}$')
    # plt.plot(mspina6[mhor6==hor],fac*3.75*mpow6[mhor6==hor]*rhor6,'r',label=r'$P_{\rm BZ,6}\times\, r_h$' )
    if False:
        myomh6=np.concatenate((-momh6[mhor6==hor][::-1],momh6[mhor6==hor]))
        myspina6=np.concatenate((-mspina6[mhor6==hor][::-1],mspina6[mhor6==hor]))
        mypow6 = np.concatenate((mpow6[mhor6==hor][::-1],mpow6[mhor6==hor]))
    else:
        myomh6=momh6[mhor6==hor]
        myspina6=mspina6[mhor6==hor]
        mypow6 = mpow6[mhor6==hor]
    mypsiosqrtmdot = f0*(1.+(f1*(1+np.sign(myomh6))/2. + f1n*(1-np.sign(myomh6))/2.)*myomh6)
    myeta6 = (mypsiosqrtmdot)**2*mypow6
    # plt.figure(5)
    # plt.clf()
    # plt.plot(mspina6[mhor6==hor],mpow6[mhor6==hor] )
    # plt.plot(mspina2[mhor2==hor],mpow2a[mhor2==hor] )
    # mpow2ahere = 2.0000 * 1.*1.0472*momh2**2 * 1.5*(psi**2-psi**3/3)
    # plt.plot(mspina2[mhor2==hor], mpow2ahere[mhor2==hor])
    #plt.plot(mya,mya**2)
    #plt.plot(mya,mypwr)
    #
    if format==0:
        plt.figure(2)
        plt.clf()
        #plt.plot( mya, myeta )
        #plt.plot(mya,mya**2)
        #y = (psi30sqlist)**2/(2*mdotlist)
        y = (psi30sqlist)**2/(2*mdotlist)
        plt.plot(alist,y,'bo')
        plt.plot(mya,(250+0*mya)*rhor) 
        plt.plot(mya,250./((3./(mya**2 + 3*rhor**2))**2*2*rhor**2)) 
        #plt.plot(mya,((mya**2+3*rhor**2)/3)**2/(2/rhor)) 
        plt.ylim(ymin=0)
        #plt.plot(alist,2*mdotlist/(psitotsqlist)**2,'o')
        #plt.plot(mspina6[mhor6==hor],5*mpow6[mhor6==hor])
        #plt.plot(mspina2[mhor2==hor],5*mpow2a[mhor2==hor])
        # plt.figure(4)
        # plt.clf()
        # y = (psi30sqlist)**2/(2*mdotlist*rhorlist**2)
        # plt.plot(alist,1/(y/np.max(y)),'o')
        # plt.plot(mya,Risco(mya)**(1./2.)*0.9) 
        # plt.ylim(ymin=0)
    else:
        plt.figure(2)
        plt.clf()
        #plt.plot( mya, myeta )
        #plt.plot(mya,mya**2)
        #y = (psi30sqlist)**2/(2*mdotlist)
        y = (f30sqlist/2./(2*np.pi))/(mdotlist)**0.5
        y1= (fsqtotlist/2./(2*np.pi))/(mdotlist)**0.5
        #plt.plot(alist,y,'bo')
        plt.plot(alist,y1,'ro')
        plt.plot(mya,f,'g')
        # plt.plot(mya,(250+0*mya)*rhor) 
        # plt.plot(mya,250./((3./(mya**2 + 3*rhor**2))**2*2*rhor**2)) 
        #plt.plot(mya,((mya**2+3*rhor**2)/3)**2/(2/rhor)) 
        plt.ylim(ymin=0)
        #plt.plot(alist,2*mdotlist/(psitotsqlist)**2,'o')
        #plt.plot(mspina6[mhor6==hor],5*mpow6[mhor6==hor])
        #plt.plot(mspina2[mhor2==hor],5*mpow2a[mhor2==hor])
        # plt.figure(4)
        # plt.clf()
        # y = (psi30sqlist)**2/(2*mdotlist*rhorlist**2)
        # plt.plot(alist,1/(y/np.max(y)),'o')
        # plt.plot(mya,Risco(mya)**(1./2.)*0.9) 
        # plt.ylim(ymin=0)
    #
    plt.figure(1, figsize=(6,5.8),dpi=200)
    plt.clf()
    gs = GridSpec(3, 3)
    gs.update(left=0.12, right=0.94, top=0.95, bottom=0.1, wspace=0.01, hspace=0.04)
    #mdot
    ax1 = plt.subplot(gs[0,:])
    plt.plot(alist,y1,'o',label=r'$\langle\phi_{\rm BH}^2\rangle^{1/2}$',mfc='r')
    plt.plot(mya[mya>0],f[mya>0],'k-',label=r'$\phi_{\rm fit}=2.9(1-0.6 \Omega_{\rm H})$')
    # plt.plot(mya,(250+0*mya)*rhor) 
    # plt.plot(mya,250./((3./(mya**2 + 3*rhor**2))**2*2*rhor**2)) 
    #plt.plot(mya,((mya**2+3*rhor**2)/3)**2/(2/rhor)) 
    plt.ylim(ymin=0.0001)
    plt.ylabel(r"$\phi_{\rm BH}$",fontsize='x-large',ha='center',labelpad=16)
    plt.grid()
    plt.setp( ax1.get_xticklabels(), visible=False )
    plt.legend(ncol=1,loc='lower center')
    bbox_props = dict(boxstyle="round,pad=0.1", fc="w", ec="w", alpha=0.9)
    plt.text(-0.9, 2.5, r"$(\mathrm{a})$", size=16, rotation=0.,
             ha="center", va="center",
             color='k',weight='regular',bbox=bbox_props
             )
    #second y-axis
    ax1r = ax1.twinx()
    ax1r.set_xlim(-1,1)
    ax1r.set_ylim(ax1.get_ylim())
    #
    ax2 = plt.subplot(gs[1,:])
    plt.plot(alist,100*etaEMlist,'o',label=r'$\eta_{\rm BH}$',mfc='r')
    #plt.plot(alist,100*(etawindlist-etalist),'gv',label=r'$\eta_{\rm wind}$')
    #plt.plot(myspina6,0.9*100*fac*myeta6,'k',label=r'$0.9\eta_{\rm BZ6}(\phi_{\rm fit})$' )
    plt.plot(myspina6,100*fac*myeta6,'k-',label=r'$\eta_{\rm BZ6}(\phi_{\rm fit})$' )
    plt.ylim(0.0001,150)
    plt.grid()
    plt.setp( ax2.get_xticklabels(), visible=False )
    plt.ylabel(r"$\eta_{\rm BH}\  [\%]$",fontsize='x-large',ha='center',labelpad=12)
    plt.text(-0.9, 125, r"$(\mathrm{b})$", size=16, rotation=0.,
             ha="center", va="center",
             color='k',weight='regular',bbox=bbox_props
             )
    plt.legend(ncol=2,loc='upper center')
    #second y-axis
    ax2r = ax2.twinx()
    ax2r.set_xlim(-1,1)
    ax2r.set_ylim(0.0001,150)
    #
    ax3 = plt.subplot(gs[-1,:])
    newy1 = 100*fac*myeta6
    newy2 = 0.8*100*fac*myeta6
    ax3.fill_between(myspina6,newy1,newy2,where=newy1>newy2,facecolor=(0.8,1,0.8,1),edgecolor=(0.8,1,0.8,1))
    #plt.plot(myspina6,myeta6,'r:',label=r'$\eta_{\rm BZ,6}$')
    plt.plot(alist,100*etalist,'gs',label=r'$\eta_{\rm jet}$')
    #plt.plot(alist,100*etaEMlist,'rx',label=r'$\eta_{\rm jet}$')
    plt.plot(alist,100*(etawindlist-etalist),'bv',label=r'$\eta_{\rm wind}$')
    plt.plot(myspina6,100*fac*myeta6,'k-',label=r'$\eta_{\rm BZ6}(\phi_{\rm fit})$' )
    plt.plot(myspina6,0.9*100*fac*myeta6,'k--',label=r'$0.9\eta_{\rm BZ6}(\phi_{\rm fit})$' )
    plt.ylim(0.0001,150)
    plt.grid()
    plt.legend(ncol=2,loc='upper center')
    plt.xlabel(r"$a$",fontsize='x-large')
    plt.ylabel(r"$\eta_{\rm jet},\ \eta_{\rm wind}\  [\%]$",fontsize='x-large',ha='center',labelpad=12)
    plt.text(-0.9, 125, r"$(\mathrm{c})$", size=16, rotation=0.,
             ha="center", va="center",
             color='k',weight='regular',bbox=bbox_props
             )
    #second y-axis
    ax3r = ax3.twinx()
    ax3r.set_xlim(-1,1)
    ax3r.set_ylim(ax3.get_ylim())
    #
    #plt.savefig("jetwindeta.pdf",bbox_inches='tight',pad_inches=0)
    #plt.savefig("jetwindeta.eps",bbox_inches='tight',pad_inches=0)
    plt.savefig("jetwindeta.pdf",bbox_inches='tight',pad_inches=0.02)
    plt.savefig("jetwindeta.eps",bbox_inches='tight',pad_inches=0.02)
    plt.savefig("jetwindeta.png",bbox_inches='tight',pad_inches=0.02)
    #plt.plot(mspina2[mhor2==hor],5*mpow2a[mhor2==hor])
    #
    #
    plt.figure(3)
    plt.clf()
    #plt.plot( mya, myeta )
    #plt.plot(mya,mya**2)
    psi=1.0
    pow6func = interp1d(momh6[mhor6==hor], mpow6[mhor6==hor])
    #divide flux by 2 (converts flux to single hemisphere) and by dxdxp33 (accounts for A_3 -> A_\phi):
    # pwrlist = (psi30sqlist/2/(2*np.pi))**2*2.0000 * 1.*1.0472*omhlist**2 * 1.5*(psi**2-psi**3/3)
    # plt.plot(alist,pwrlist6/mdotlist,'o')
    if format == 0:
        pwrlist6 = (psi30sqlist/2/(2*np.pi))**2*pow6func(np.abs(omhlist))
        plt.plot(alist,pwrlist6/mdotlist,'o')
    plt.ylim(ymin=0,ymax=3)
    #plt.plot(alist,2*mdotlist/(psitotsqlist)**2,'o')
    plt.plot( mya, myeta )
    plt.plot(mspina6[mhor6==hor],5*mpow6[mhor6==hor])
    plt.plot(mspina2[mhor2==hor],5*mpow2a[mhor2==hor])
    # psi = 1
    # mp = 2.0000 * 1.*1.0472*myomh**2 * 1.5*(psi**2-psi**3/3)
    # plt.plot(mya,1.5*mp)
    # plt.figure(2)
    # plt.clf()
    # plt.plot(mya,myomh)
    # plt.plot(mspina2[mhor2==hor],momh2[mhor2==hor])
    

def readmytests1():
    global momh2, mhor2, mpsi2, mpow2, mBr2, mtheta2, mspina2, mpow2a
    global momh4, mhor4, mpsi4, mpow4, mBr4, mtheta4, mspina4
    global momh6, mhor6, mpsi6, mpow6, mBr6, mtheta6, mspina6
    #
    gd2 = np.loadtxt( "mytest2", unpack = True )
    momh2, mhor2, mpsi2, mpow2, mBr2 = gd2[0:5]
    mtheta2 = np.pi/2-mhor2
    mspina2 = 4*momh2/(1+4*momh2**2)
    psi = (1-np.cos(np.pi/2-mhor2))
    mpow2a = 2.0000 * 1.*1.0472*momh2**2 * 1.5*(psi**2-psi**3/3)  #for two jets? 1.0472=pi/3
    #
    gd4 = np.loadtxt( "mytest4", unpack = True )
    momh4, mhor4, mpsi4, mpow4, mBr4 = gd4[0:5]
    mtheta4 = np.pi/2-mhor4
    mspina4 = 4*momh4/(1+4*momh4**2)
    #
    gd6 = np.loadtxt( "mytest6", unpack = True )
    momh6, mhor6, mpsi6, mpow6, mBr6 = gd6[0:5]
    mtheta6 = np.pi/2-mhor6
    mspina6 = 4*momh6/(1+4*momh6**2)

def plotomegaf2hor():
    #plot omegaf2/omegah on the horizon
    plt.clf(); 
    rhor = 1 + (1-a**2)**0.5
    omh = a / (2*rhor)
    ihor = iofr(rhor)
    rhoavg=(rho[ihor].sum(1)/nz)
    bsqorhoavg=(bsq/rho)[ihor].sum(1)/nz
    TudEM10avg = (-gdet*TudEM[1,0])[ihor].sum(1)/nz
    Etot = (-gdet*TudEM[1,0])[ihor].sum()*_dx2*_dx3*2
    plt.plot(tj[ihor,:,0],omegaf2[ihor].sum(1)/nz*dxdxp[3][3][0,0,0]/omh); 
    plt.plot(tj[ihor,:,0],0.5*rhoavg/np.max(rhoavg)); 
    plt.plot(tj[ihor,:,0],bsqorhoavg/100); 
    plt.plot(tj[ihor,:,0],0.5*TudEM10avg/np.max(TudEM10avg)); 
    print( "Etot = %g" % Etot )
    plt.ylim(0,0.5)

def plotakshay():
    #grid3d("gdump.bin")
    #rfd("fieldline4670.bin")
    #cvel()
    #rhor = 1+(1-a**2)**0.5
    #ihor = iofr(rhor)
    iref = 0
    rref = r[iref,0,0]
    #far view
    plt.figure(1)
    plt.clf()
    #Density
    plt.suptitle(r"Angular density profile ($a = %g$ at $i = %d$, $r = %g$, $t = %g$)" % (a, iref, rref,t))
    plt.plot(h[iref,:,0],rho[iref,:,0])
    plt.plot(h[iref,:,0],rho[iref,:,0],'o')
    plt.xlim(0,3.5)
    plt.xlabel(r"$\theta-\pi/2$")
    plt.ylabel(r"$\rho$")
    plt.savefig("rho-i0.pdf")
    #close view
    plt.figure(2)
    plt.clf()
    #Density
    plt.suptitle(r"[blowup] Angular density profile ($a = %g$ at $i = %d$, $r = %g$, $t = %g)$" % (a, iref, rref,t))
    plt.plot(h[iref,:,0]-np.pi/2,rho[iref,:,0])
    plt.plot(h[iref,:,0]-np.pi/2,rho[iref,:,0],'o')
    plt.xlim(-0.2,0.2)
    plt.xlabel(r"$\theta-\pi/2$")
    plt.ylabel(r"$\rho$")
    plt.savefig("rho-i0_blowup.pdf")
    #Time step
    #dt2 = _dx2 / amax(np.abs(v2m),np.abs(v2p)) 
    #plt.plot(h[iref,:,0]-np.pi/2,dt2*1000)
 
def plotrfisco():
    plco(v1p,levels=(0,),xcoord=r*np.sin(h),ycoord=r*np.cos(h),colors='c'); plt.xlim(0,10); plt.ylim(-5,5)
    plc(np.log10(rho),xcoord=r*np.sin(h),ycoord=r*np.cos(h),cb=True)
    rh=1+(1-a**2)**0.5
    plc(r-rh,levels=(0,),colors='k',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
    risco = Risco(a)
    print( "Risco(a=%g) = %g" % (a, risco) )
    plc(r*np.sin(h)-risco,levels=(0,),colors='g',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
    plt.grid()

def plotaphivsr():
    plt.clf();plt.semilogx(r[:,0,0],aphi[:,ny/2,0]/10,label=r'$\Phi/10$')
    plt.semilogx(r[:,0,0],15+lrho[:,ny/2,0],label=r'$\log_{10}\rho+15$')
    plt.semilogx(r[:,0,0],20+np.log10(ug[:,ny/2,0]),label=r'$\log_{10}u_g\!+20$')
    plt.semilogx(r[:,0,0],(r[:,0,0]-34)**(2./3.)/2.1,label=r'$\propto (r-r_{\rm max})^{2/3}\!$')
    plt.grid()
    plt.legend()
    plt.xlabel(r'$r$')
    plt.ylim(0,20)

def div( vec ):
    res = np.zeros_like(vec[1])
    res[0:-1]  = (vec[1][1:]-vec[1][:-1])
    return( res )

def plotdiv():    
    global madded, eadded
    rh = 1+(1-a**2)**0.5
    omegah=a/2/rh
    etad = np.zeros_like(uu)
    mdotden = (gdet[:,:,0:1]*avg_rhouu)[1]
    mdotval = scaletofullwedge(nz*(mdotden*_dx2*_dx3).sum(axis=-1).sum(-1))
    edotval = -scaletofullwedge(nz*(gdet*avg_Tud[1,0]*_dx2*_dx3).sum(axis=-1).sum(-1))
    ldotval = scaletofullwedge(nz*(gdet*avg_Tud[1,3]/dxdxp[3][3][:,:,0:1]*_dx2*_dx3).sum(axis=-1).sum(-1))
    etad[0] = -1/(-gn3[0,0])**0.5
    gdetdivrhouu=div(gdet[:,:,0:1]*avg_rhouu)
    etot = scaletofullwedge(nz*(-gdet*avg_Tud[1,0]*_dx2*_dx3).sum(axis=-1).sum(-1))
    madded = scaletofullwedge(nz*(gdetdivrhouu*_dx2*_dx3).sum(axis=-1)).sum(-1).cumsum(0)
    madded -= madded[iofr(10)]
    eadded = scaletofullwedge(nz*(etad[0]*gdetdivrhouu*_dx2*_dx3).sum(axis=-1)).sum(-1).cumsum(0)
    eadded -= eadded[iofr(10)]
    eadded/=nz
    plt.figure(10)
    #xxx
    #plt.plot(r[:,0,0], mdotval-mdotval[iofr(10)],label="mdotval")
    #$plt.plot(r[:,0,0], madded,label="madded")
    #plt.plot(r[:,0,0], eadded,label="eadded")
    plt.plot(r[:,0,0], edotval,label="Etot")
    plt.plot(r[:,0,0], ldotval/10.,label="Ltot/10")
    #plt.plot(r[:,0,0], ldotval*omegah,label="Omegah * Ltot")
    plt.plot(r[:,0,0], -mdotval,label="Mtot")
    plt.ylim(0,10)
    plt.legend(loc='lower right')
    rh = 1+(1-a**2)**0.5
    plt.xlim(rh,30)
    #plt.ylim(-20,20)
    #res[:,1:-1] += (vec[2][:,2:]-vec[2][:,:-2])  

def ploteta():
    #FIGURE 1 LOTSOPANELS
    #Figure 1
    #To make plot, run 
    #run ~/py/mread/__init__.py 1 1
    #To re-make plot without reloading the fiels, run
    #run ~/py/mread/__init__.py 1 -1
    bbox_props = dict(boxstyle="round,pad=0.1", fc="w", ec="w", alpha=0.9)
    #AT: plt.legend( loc = 'upper left', bbox_to_anchor = (0.5, 0.5) ) #0.5, 0.5 = center of plot
    #To generate movies for all sub-folders of a folder:
    #cd ~/Research/runart; for f in *; do cd ~/Research/runart/$f; (python  ~/py/mread/__init__.py &> python.out &); done
    grid3d( os.path.basename(glob.glob(os.path.join("dumps/", "gdump*"))[0]), use2d=True )
    #rd( "dump0000.bin" )
    #rfd("fieldline0000.bin")  #to definea
    #grid3dlight("gdump")
    qtymem=None #clear to free mem
    rhor=1+(1+a**2)**0.5
    ihor = np.floor(iofr(rhor)+0.5);
    qtymem=getqtyvstime(ihor,0.2)
    fig=plt.figure(0, figsize=(12,6), dpi=100)
    plt.clf()
    #
    # eta = pjet/<mdot>
    #
    ax34 = plt.gca()
    plotqtyvstime(qtymem,ax=ax34,whichplot=4,prefactor=1)
    ymax=ax34.get_ylim()[1]
    #if 1 < ymax and ymax < 2: 
    #    #ymax = 2
    #    tck=(1,)
    #    ax34.set_yticks(tck)
    #    #ax34.set_yticklabels(('','1','2'))
    #elif ymax < 1: 
    #    #ymax = 1
    #    tck=np.arange(ymax/10,ymax)
    #    ax34.set_yticks(tck)
    #    #ax34.set_yticklabels(('','1'))
    if ymax >= 1:
        ymax=np.floor(ymax)+1
        tck=np.arange(1,ymax,(ymax-1.0)/2.0)
        ax34.set_yticks(tck)
    else:
        #ymax=np.floor(ymax)+1
        ymax=2*(np.floor(np.floor(ymax+1.5)/2))
        tck=np.arange(0,ymax,ymax/2.0)
        ax34.set_yticks(tck)
    #
    #reset lower limit to 0
    #ax34.set_ylim((0,ax34.get_ylim()[1]))
    ax34.set_ylim((0,ymax))
    ax34.grid(True)
    ax34.set_ylabel(r"$\eta$")
    # plt.text(ax34.get_xlim()[1]/40., 0.8*ax34.get_ylim()[1], r"$(\mathrm{g})$", size=16, rotation=0.,
    #          ha="center", va="center",
    #          color='k',weight='regular',bbox=bbox_props
    #          )
    ax34r = ax34.twinx()
    ax34r.set_ylim(ax34.get_ylim())
    ax34r.set_yticks(tck)
    gc.collect()

def mkmovie(framesize=50, domakeavi=False):
    #Rz and xy planes side by side
    plotlenf=10
    plotleni=framesize
    plotlenti=1e6 #so high that never gets used
    plotlentf=2e6
    #To generate movies for all sub-folders of a folder:
    #cd ~/Research/runart; for f in *; do cd ~/Research/runart/$f; (python  ~/py/mread/__init__.py &> python.out &); done
    if len(sys.argv[1:])==2 and sys.argv[1].isdigit() and (sys.argv[2].isdigit() or sys.argv[2][0]=="-") :
        whichi = int(sys.argv[1])
        whichn = int(sys.argv[2])
        print( "Doing every %d slice of total %d slices" % (whichi, whichn) )
        sys.stdout.flush()
    else:
        whichi = None
        whichn = None
    if whichn < 0 and whichn is not None:
        whichn = -whichn
        dontloadfiles = True
    else:
        dontloadfiles = False
        grid3d( os.path.basename(glob.glob(os.path.join("dumps/", "gdump*"))[0]), use2d=True )
        rd( "dump0000.bin" )
        rfd("fieldline0000.bin")  #to definea
        #grid3dlight("gdump")
        qtymem=None #clear to free mem
        rhor=1+(1+a**2)**0.5
        ihor = np.floor(iofr(rhor)+0.5);
        qtymem=getqtyvstime(ihor,0.2)
        flist = np.sort(glob.glob( os.path.join("dumps/", "fieldline*.bin") ) )

    for findex, fname in enumerate(flist):
        if findex % whichn != whichi:
            continue
        if dontloadfiles == False and os.path.isfile("lrho%04d_Rzxym1.png" % (findex)):
            print( "Skipping " + fname + " as lrho%04d_Rzxym1.png exists" % (findex) );
        else:
            print( "Processing " + fname + " ..." )
            sys.stdout.flush()
            rfd("../"+fname)
            cvel() #for calculating bsq
            plotlen = plotleni+(plotlenf-plotleni)*(t-plotlenti)/(plotlentf-plotlenti)
            plotlen = min(plotlen,plotleni)
            plotlen = max(plotlen,plotlenf)
            plt.figure(0, figsize=(12,9), dpi=100)
            plt.clf()
            #SWITCH OFF SUPTITLE
            #plt.suptitle(r'$\log_{10}\rho$ at t = %4.0f' % t)
            ##########
            #
            #mdot,pjet,pjet/mdot plots
            gs3 = GridSpec(3, 3)
            gs3.update(left=0.055, right=0.97, top=0.42, bottom=0.06, wspace=0.01, hspace=0.04)
            #gs3.update(left=0.055, right=0.95, top=0.42, bottom=0.03, wspace=0.01, hspace=0.04)
            #
            ##############
            #mdot
            ax31 = plt.subplot(gs3[-3,:])
            plotqtyvstime(qtymem,ax=ax31,whichplot=1,findex=findex)
            ymax=ax31.get_ylim()[1]
            #ymax=2*(np.floor(np.floor(ymax+1.5)/2))
            ax31.set_yticks((ymax/2.0,ymax,ymax/2.0))
            ax31.grid(True)
            #ax31.set_ylim((0,ymax))
            #pjet
            # ax32 = plt.subplot(gs3[-2,:])
            # plotqtyvstime(qtymem,ax=ax32,whichplot=2)
            # ymax=ax32.get_ylim()[1]
            # ax32.set_yticks((ymax/2.0,ymax))
            # ax32.grid(True)
            #pjet/mdot
            # ax33 = plt.subplot(gs3[-1,:])
            # plotqtyvstime(qtymem,ax=ax33,whichplot=3)
            # ymax=ax33.get_ylim()[1]
            # ax33.set_yticks((ymax/2.0,ymax))
            # ax33.grid(True)
            #
            ##############
            #\phi
            #
            ax35 = plt.subplot(gs3[-2,:])
            plotqtyvstime(qtymem,ax=ax35,whichplot=5,findex=findex)
            ymax=ax35.get_ylim()[1]
            #if 1 < ymax and ymax < 2: 
            #    #ymax = 2
            #    tck=(1,)
            #    ax35.set_yticks(tck)
            #    #ax35.set_yticklabels(('','1','2'))
            #elif ymax < 1: 
            #    #ymax = 1
            #    tck=(ymax/10,ymax)
            #    ax35.set_yticks(tck)
            #    ax35.set_yticklabels(('','1'))
            if ymax >=1:
                ymax=np.floor(ymax*0.9999)+1
                tck=np.arange(1,ymax,(ymax-1.0)/2.0)
                ax35.set_yticks(tck)
            elif ymax <1 and ymax > 0.1:
                ymax=1
                ax35.set_ylim((0,ymax))
                tck=np.arange(ymax/2.0,(3.0/2.0)*ymax,ymax/2.0)
                ax35.set_yticks(tck)
            else:
                ax35.set_yticks((ymax/2.0,ymax))
                #ax35.set_ylim((0,ymax))
            #
            ax35.grid(True)
            #
            #####################
            # eta=pjet/<mdot>
            #
            ax34 = plt.subplot(gs3[-1,:])
            plotqtyvstime(qtymem,ax=ax34,whichplot=4,findex=findex)
            ymax=ax34.get_ylim()[1]
            #if 100 < ymax and ymax < 200: 
            #    #ymax = 2
            #    tck=(100,)
            #    ax34.set_yticks(tck)
            #    #ax34.set_yticklabels(('','100','200'))
            #elif ymax < 100: 
            #    #ymax = 100
            #    tck=(ymax/10,ymax)
            #    ax34.set_yticks(tck)
            #    ax34.set_yticklabels(('','100'))
            if ymax>=100:
                ymax=np.floor(ymax/100.*0.9999)+1
                ymax*=100
                tck=np.arange(1,ymax/100.,(ymax/100.0-1.0)/2.0)*100
                ax34.set_yticks(tck)
            elif ymax>=10:
                ymax=np.floor(ymax/10.*0.9999)+1
                ymax*=10
                tck=np.arange(1,ymax/10.,(ymax/10.0-1.0)/2.0)*10
                ax34.set_yticks(tck)
            else:
                ax34.set_yticks((ymax/2.0,ymax))
            #
            ax34.grid(True)
            #reset lower limit to 0
            #Rz xy
            #
            # for Jon's new fiducial model
            vminforframe=-2.4
            vmaxforframe=1.5625
            # for MB09 dipolar fiducial model
            #vminforframe=-4.0
            #vmaxforframe=0.5
            #
            gs1 = GridSpec(1, 1)
            gs1.update(left=0.05, right=0.45, top=0.99, bottom=0.48, wspace=0.01, hspace=0.05)
            ax1 = plt.subplot(gs1[:, -1])
            mkframe("lrho%04d_Rz%g" % (findex,plotlen),vmin=vminforframe,vmax=vmaxforframe,len=plotlen,ax=ax1,cb=False,pt=False)
            #
            plt.xlabel(r"$x\ [r_g]$",fontsize=16,ha='center')
            plt.ylabel(r"$z\ [r_g]$",ha='left',labelpad=10,fontsize=16)
            #
            gs2 = GridSpec(1, 1)
            gs2.update(left=0.5, right=1, top=0.99, bottom=0.48, wspace=0.01, hspace=0.05)
            ax2 = plt.subplot(gs2[:, -1])
            #
            # If using 2D data, then for now, have to replace below with mkframe version above and replace ax1->ax2
            mkframexy("lrho%04d_xy%g" % (findex,plotlen),vmin=vminforframe,vmax=vmaxforframe,len=plotlen,ax=ax2,cb=True,pt=False,dostreamlines=True)
            #
            plt.xlabel(r"$x\ [r_g]$",fontsize=16,ha='center')
            plt.ylabel(r"$y\ [r_g]$",ha='left',labelpad=10,fontsize=16)
            #
            #
            #print xxx
            plt.savefig( "lrho%04d_Rzxym1.png" % (findex)  )
            plt.savefig( "lrho%04d_Rzxym1.eps" % (findex)  )
            #print xxx
    print( "Done!" )
    sys.stdout.flush()
    if domakeavi:
        #print( "Now you can make a movie by running:" )
        #print( "ffmpeg -fflags +genpts -r 10 -i lrho%04d.png -vcodec mpeg4 -qmax 5 mov.avi" )
        os.system("mv mov_%s_Rzxym1.avi mov_%s_Rzxym1.bak.avi" % ( os.path.basename(os.getcwd()), os.path.basename(os.getcwd())) )
        #os.system("ffmpeg -fflags +genpts -r 20 -i lrho%%04d_Rzxym1.png -vcodec mpeg4 -qmax 5 mov_%s_Rzxym1.avi" % (os.path.basename(os.getcwd())) )
        os.system("ffmpeg -fflags +genpts -r 20 -i lrho%%04d_Rzxym1.png -vcodec mpeg4 -qmax 5 -b 10000k -pass 1 mov_%s_Rzxym1p1.avi" % (os.path.basename(os.getcwd())) )
        os.system("ffmpeg -fflags +genpts -r 20 -i lrho%%04d_Rzxym1.png -vcodec mpeg4 -qmax 5 -b 10000k -pass 2 mov_%s_Rzxym1.avi" % (os.path.basename(os.getcwd())) )
        #os.system("scp mov.avi 128.112.70.76:Research/movies/mov_`basename \`pwd\``.avi")

def mk2davg():
    if len(sys.argv[1:])!=0:
        grid3d("gdump.bin",use2d=True)
        #rd("dump0000.bin")
        rfd("fieldline0000.bin")
    if len(sys.argv[1:])==2 and sys.argv[1].isdigit() and sys.argv[2].isdigit():
        whichgroup = int(sys.argv[1])
        step = int(sys.argv[2])
        itemspergroup = 20
        for whichgroup in np.arange(whichgroup,1000,step):
            avgmem = get2davg(whichgroup=whichgroup,itemspergroup=itemspergroup)
        #plot2davg(avgmem)
    elif len(sys.argv[1:])==3 and sys.argv[1].isdigit() and sys.argv[2].isdigit() and sys.argv[3].isdigit():
        whichgroups = int(sys.argv[1])
        whichgroupe = int(sys.argv[2])
        step = int(sys.argv[3])
        itemspergroup = 20
        if step == 0:
            avgmem = get2davg(usedefault=1)
        elif step == 1:
            avgmem = get2davg(whichgroups=whichgroups,whichgroupe=whichgroupe,itemspergroup=itemspergroup)
        else:
            for whichgroup in np.arange(whichgroups,whichgroupe,step):
                avgmem = get2davg(whichgroup=whichgroup,itemspergroup=itemspergroup)
        print( "Assigning averages..." )
        assignavg2dvars(avgmem)
    plot2davg(whichplot=1)
    gc.collect()

def mkstreamlinefigure():
    mylen = 30
    grid3d("gdump.bin",use2d=True)
    rfd("fieldline0000.bin")
    avgmem = get2davg(usedefault=1)
    assignavg2dvars(avgmem)
    fig=plt.figure(1,figsize=(12,9))
    ax = fig.add_subplot(111, aspect='equal')
    if False:
        #velocity
        B[1:] = avg_uu[1:]
        bsq = avg_bsq
        mkframe("myframe",len=mylen,ax=ax,density=24,downsample=1,cb=False,pt=False,dorho=False,dovarylw=False,vmin=-6,vmax=0.5,dobhfield=False,dodiskfield=False,minlenbhfield=0.2,minlendiskfield=0.5,dsval=0.005,color='k',doarrows=False,dorandomcolor=True,lw=1,skipblankint=True,detectLoops=False,ncell=800,minindent=5,minlengthdefault=0.2,startatmidplane=False)
    if True:
        #field
        B[1] = avg_B[0]
        B[2] = avg_B[1]
        B[3] = avg_B[2]
        bsq = avg_bsq
        plt.figure(1)
        gdetB[1:] = avg_gdetB[0:]
        mu = avg_mu
        mkframe("myframe",len=25./30.*mylen,ax=ax,density=1,downsample=4,cb=False,pt=False,dorho=False,dovarylw=False,vmin=-6,vmax=0.5,dobhfield=12,dodiskfield=True,minlenbhfield=0.2,minlendiskfield=0.5,dsval=0.01,color='r',lw=1,startatmidplane=True,showjet=False)
    if False:
        x = (r*np.sin(h))[:,:,0]
        z = (r*np.cos(h))[:,:,0]
        x = np.concatenate(-x,x)
        z = np.concatenate(y,y)
        mu = np.concatenate(avg_mu[:,:,0],avg_mu[:,:,0])
        plt.contourf( x, z, mu )
    ax.set_aspect('equal')   
    rhor=1+(1-a**2)**0.5
    el = Ellipse((0,0), 2*rhor, 2*rhor, facecolor='k', alpha=1)
    art=ax.add_artist(el)
    art.set_zorder(20)
    mylenshow = 25./30.*mylen
    plt.xlim(-mylenshow,mylenshow)
    plt.ylim(-mylenshow,mylenshow)
    plt.xlabel(r"$x\ [r_g]$",fontsize=16,ha='center')
    plt.ylabel(r"$z\ [r_g]$",ha='left',labelpad=15,fontsize=16)
    # plt.savefig("fig2.pdf",bbox_inches='tight',pad_inches=0.02)
    # plt.savefig("fig2.eps",bbox_inches='tight',pad_inches=0.02)
    plt.savefig("fig2.png",bbox_inches='tight',pad_inches=0.02)

def mklotsopanels():
    #Figure 1
    #To make plot, run 
    #run ~/py/mread/__init__.py 1 1
    #To re-make plot without reloading the fiels, run
    #run ~/py/mread/__init__.py 1 -1
    domakeframes=True
    doslines=True
    plotlenf=10
    plotleni=25
    plen=plotleni
    plotlenti=40000
    plotlentf=45000
    bbox_props = dict(boxstyle="round,pad=0.1", fc="w", ec="w", alpha=0.9)
    #AT: plt.legend( loc = 'upper left', bbox_to_anchor = (0.5, 0.5) ) #0.5, 0.5 = center of plot
    #To generate movies for all sub-folders of a folder:
    #cd ~/Research/runart; for f in *; do cd ~/Research/runart/$f; (python  ~/py/mread/__init__.py &> python.out &); done
    if len(sys.argv[1:])==2 and sys.argv[1].isdigit() and (sys.argv[2].isdigit() or sys.argv[2][0]=="-") :
        whichi = int(sys.argv[1])
        whichn = int(sys.argv[2])
        print( "Doing every %d slice of total %d slices" % (whichi, whichn) )
        sys.stdout.flush()
    else:
        whichi = None
        whichn = None
    if whichn < 0 and whichn is not None:
        whichn = -whichn
        dontloadfiles = True
    else:
        dontloadfiles = False
        grid3d( os.path.basename(glob.glob(os.path.join("dumps/", "gdump*"))[0]), use2d=True )
        rd( "dump0000.bin" )
        rfd("fieldline0000.bin")  #to definea
        #grid3dlight("gdump")
        qtymem=None #clear to free mem
        rhor=1+(1+a**2)**0.5
        ihor = np.floor(iofr(rhor)+0.5);
        qtymem=getqtyvstime(ihor,0.2)
        flist = np.sort(glob.glob( os.path.join("dumps/", "fieldline*.bin") ) )
    #make accretion rate plot, etc.
    sys.stdout.flush()
    plotlen = plotleni+(plotlenf-plotleni)*(t-plotlenti)/(plotlentf-plotlenti)
    plotlen = min(plotlen,plotleni)
    plotlen = max(plotlen,plotlenf)
    fig=plt.figure(0, figsize=(12,9), dpi=100)
    plt.clf()
    #findexlist=(0,600,1285,1459)
    findexlist=(0,600,1225,1369)
    #SWITCH OFF SUPTITLE
    #plt.suptitle(r'$\log_{10}\rho$ at t = %4.0f' % t)
    #mdot,pjet,pjet/mdot plots
    findex = 0
    gs3 = GridSpec(3, 3)
    gs3.update(left=0.055, right=0.97, top=0.42, bottom=0.06, wspace=0.01, hspace=0.04)
    #mdot
    ax31 = plt.subplot(gs3[-3,:])
    plotqtyvstime(qtymem,ax=ax31,whichplot=1,findex=findexlist) #AT: need to specify index!
    ymax=ax31.get_ylim()[1]
    ymax=2*(np.floor(np.floor(ymax+1.5)/2))
    ax31.set_yticks((0,ymax,ymax/2.0))
    #ax31.set_xlabel(r"$t\ [r_g/c]")
    ax31.grid(True)
    plt.text(ax31.get_xlim()[1]/40., 0.8*ax31.get_ylim()[1], "$(\mathrm{e})$", size=16, rotation=0.,
             ha="center", va="center",
             color='k',weight='regular',bbox=bbox_props
             )
    ax31r = ax31.twinx()
    ax31r.set_ylim(ax31.get_ylim())
    ax31r.set_yticks((0,ymax,ymax/2.0))
    #pjet
    # ax32 = plt.subplot(gs3[-2,:])
    # plotqtyvstime(qtymem,ax=ax32,whichplot=2)
    # ymax=ax32.get_ylim()[1]
    # ax32.set_yticks((ymax/2.0,ymax))
    # ax32.grid(True)
    #pjet/mdot
    # ax33 = plt.subplot(gs3[-1,:])
    # plotqtyvstime(qtymem,ax=ax33,whichplot=3)
    # ymax=ax33.get_ylim()[1]
    # ax33.set_yticks((ymax/2.0,ymax))
    # ax33.grid(True)
    #
    #\phi
    #

    # plt.text(250, 0.9*ymax, "i", size=10, rotation=0.,
    #          ha="center", va="center",
    #          bbox = dict(boxstyle="square",
    #                      ec=(1., 0.5, 0.5),
    #                      fc=(1., 0.8, 0.8),
    #                      )
    #          )
    ax35 = plt.subplot(gs3[-2,:])
    plotqtyvstime(qtymem,ax=ax35,whichplot=5,findex=findexlist)
    ymax=ax35.get_ylim()[1]
    #if 1 < ymax and ymax < 2: 
    #    #ymax = 2
    #    tck=(1,)
    #    ax35.set_yticks(tck)
    #    #ax35.set_yticklabels(('','1','2'))
    #elif ymax < 1: 
    #    #ymax = 1
    #    tck=(ymax/10,ymax)
    #    ax35.set_yticks(tck)
    #    ax35.set_yticklabels(('','1'))
    if ymax >=1:
        ymax=np.floor(ymax*0.9999)+1
        tck=np.arange(1,ymax,(ymax-1.0)/2.0)
        ax35.set_yticks(tck)
    else:
        ax35.set_yticks((ymax/2.0,ymax))
        #ax35.set_ylim((0,ymax))
    #
    ax35.grid(True)
    plt.text(ax35.get_xlim()[1]/40., 0.8*ax35.get_ylim()[1], r"$(\mathrm{f})$", size=16, rotation=0.,
             ha="center", va="center",
             color='k',weight='regular',bbox=bbox_props
             )
    ax35r = ax35.twinx()
    ax35r.set_ylim(ax35.get_ylim())
    ax35r.set_yticks(tck)
    #
    #pjet/<mdot>
    #
    ax34 = plt.subplot(gs3[-1,:])
    plotqtyvstime(qtymem,ax=ax34,whichplot=4,findex=findexlist)
    ymax=ax34.get_ylim()[1]
    #if 100 < ymax and ymax < 200: 
    #    #ymax = 2
    #    tck=(100,)
    #    ax34.set_yticks(tck)
    #    #ax34.set_yticklabels(('','100','200'))
    #elif ymax < 100: 
    #    #ymax = 100
    #    tck=(ymax/10,ymax)
    #    ax34.set_yticks(tck)
    #    ax34.set_yticklabels(('','100'))
    if ymax >=100:
        ymax=np.floor(ymax/100.*0.9999)+1
        ymax*=100
        tck=np.arange(1,ymax/100.,(ymax/100.0-1.0)/2.0)*100
        ax34.set_yticks(tck)
    else:
        ax34.set_yticks((ymax/2.0,ymax))
        #ax34.set_ylim((0,ymax))
    #
    ax34.grid(True)
    #reset lower limit to 0
    plt.text(ax34.get_xlim()[1]/40., 0.8*ax34.get_ylim()[1], r"$(\mathrm{g})$", size=16, rotation=0.,
             ha="center", va="center",
             color='k',weight='regular',bbox=bbox_props
             )
    ax34r = ax34.twinx()
    ax34r.set_ylim(ax34.get_ylim())
    ax34r.set_yticks(tck)
    #
    if domakeframes:
        #
        # Make Frames
        #
        dogrid = False
        downsample=4
        density=2
        dodiskfield=True
        minlenbhfield=0.2
        minlendiskfield=0.2
        #
        # PLOT 1
        #
        fname = "fieldline%04d.bin" % findexlist[0]
        rfd(fname)
        cvel() #for calculating bsq
        #xz
        gs1 = GridSpec(4, 4)
        gs1.update(left=0.04, right=0.94, top=0.995, bottom=0.48, wspace=0.05)
        #
        ax1 = plt.subplot(gs1[2:4, 0])
        # plt.text(-0.75*plen, 0.75*plen, r"$(\mathrm{a})$", size=16, rotation=0.,
        #          ha="center", va="center",
        #          color='k',weight='regular',bbox=bbox_props
        #          )
        mkframe("lrho%04d_Rz%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,ax=ax1,cb=False,pt=False,dostreamlines=doslines,downsample=downsample,density=density,dodiskfield=False)
        ax1.set_ylabel(r'$z\ [r_g]$',fontsize=16,ha='center')
        ax1.set_xlabel(r'$x\ [r_g]$',fontsize=16)
        if dogrid: plt.grid()
        #xy
        ax2 = plt.subplot(gs1[0:2, 0])
        mkframexy("lrho%04d_xy%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,ax=ax2,cb=False,pt=False,dostreamlines=False)
        plt.setp( ax2.get_xticklabels(), visible=False)
        plt.text(-0.75*plen, 0.8*plen, r"$(\mathrm{a})$", size=16, rotation=0.,
                 ha="center", va="center",
                 color='w',weight='regular' #,bbox=bbox_props
                 )
        plt.text(0.9*plen, 0.8*plen, r"$t=%g$" % np.floor(t), size=16, rotation=0.,
                 ha="right", va="center",
                 color='w',weight='regular' #,bbox=bbox_props
                 )
        ax2.set_ylabel(r'$y\ [r_g]$',fontsize=16,ha='center')
        if dogrid: plt.grid()
        plt.subplots_adjust(hspace=0.03) #increase vertical spacing to avoid crowding
        #
        # PLOT 2
        #
        fname = "fieldline%04d.bin" % findexlist[1]
        rfd(fname)
        cvel() #for calculating bsq
        #Rz
        #gs1 = GridSpec(4, 4)
        #
        ax1 = plt.subplot(gs1[2:4, 1])
        # plt.text(-0.75*plen, 0.75*plen, r"$(\mathrm{c})$", size=16, rotation=0.,
        #          ha="center", va="center",
        #          color='k',weight='regular',bbox=bbox_props
        #          )
        mkframe("lrho%04d_Rz%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,
                ax=ax1,cb=False,pt=False,dostreamlines=doslines,downsample=downsample,
                density=density,dodiskfield=dodiskfield,minlendiskfield=minlendiskfield,minlenbhfield=minlenbhfield)
        ax1.set_xlabel(r'$x\ [r_g]$',fontsize=16)
        if dogrid: plt.grid()
        #xy
        ax2 = plt.subplot(gs1[0:2, 1])
        plt.text(-0.75*plen, 0.8*plen, r"$(\mathrm{b})$", size=16, rotation=0.,
                 ha="center", va="center",
                 color='w',weight='regular' #,bbox=bbox_props
                 )
        mkframexy("lrho%04d_xy%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,ax=ax2,cb=False,pt=False,dostreamlines=False)
        plt.setp( ax2.get_xticklabels(), visible=False)
        plt.text(0.9*plen, 0.8*plen, r"$t=%g$" % np.floor(t), size=16, rotation=0.,
                 ha="right", va="center",
                 color='w',weight='regular' #,bbox=bbox_props
                 )
        if dogrid: plt.grid()
        plt.subplots_adjust(hspace=0.03) #increase vertical spacing to avoid crowding
        #
        # PLOT 3
        #
        fname = "fieldline%04d.bin" % findexlist[2]
        rfd(fname)
        cvel() #for calculating bsq
        #Rz
        ax1 = plt.subplot(gs1[2:4, 2])
        # plt.text(-0.75*plen, 0.75*plen, r"$(\mathrm{e})$", size=16, rotation=0.,
        #          ha="center", va="center",
        #          color='k',weight='regular',bbox=bbox_props
        #          )
        mkframe("lrho%04d_Rz%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,ax=ax1,cb=False,pt=False,dostreamlines=doslines,downsample=downsample,density=density,dodiskfield=dodiskfield,minlendiskfield=minlendiskfield,minlenbhfield=minlenbhfield)
        ax1.set_xlabel(r'$x\ [r_g]$',fontsize=16)
        if dogrid: plt.grid()
        #xy
        ax2 = plt.subplot(gs1[0:2, 2])
        plt.text(-0.75*plen, 0.8*plen, r"$(\mathrm{c})$", size=16, rotation=0.,
                 ha="center", va="center",
                 color='w',weight='regular' #,bbox=bbox_props
                 )
        plt.text(0.9*plen, 0.8*plen, r"$t=%g$" % np.floor(t), size=16, rotation=0.,
                 ha="right", va="center",
                 color='w',weight='regular' #,bbox=bbox_props
                 )
        mkframexy("lrho%04d_xy%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,ax=ax2,cb=False,pt=False,dostreamlines=False)
        plt.setp( ax2.get_xticklabels(), visible=False)
        if dogrid: plt.grid()
        plt.subplots_adjust(hspace=0.03) #increase vertical spacing to avoid crowding
        #
        # PLOT 4
        #
        fname = "fieldline%04d.bin" % findexlist[3]
        rfd(fname)
        cvel() #for calculating bsq
        #Rz
        ax1 = plt.subplot(gs1[2:4, 3])
        # plt.text(-0.75*plen, 0.75*plen, r"$(\mathrm{g})$", size=16, rotation=0.,
        #          ha="center", va="center",
        #          color='k',weight='regular',bbox=bbox_props
        #          )
        mkframe("lrho%04d_Rz%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,ax=ax1,cb=False,pt=False,dostreamlines=doslines,downsample=downsample,density=density,dodiskfield=dodiskfield,minlendiskfield=minlendiskfield,minlenbhfield=minlenbhfield)
        ax1.set_xlabel(r'$x\ [r_g]$',fontsize=16)
        if dogrid: plt.grid()
        #xy
        ax2 = plt.subplot(gs1[0:2, 3])
        plt.text(-0.75*plen, 0.8*plen, r"$(\mathrm{d})$", size=16, rotation=0.,
                 ha="center", va="center",
                 color='w',weight='regular' #,bbox=bbox_props
                 )
        plt.text(0.9*plen, 0.8*plen, r"$t=%g$" % np.floor(t), size=16, rotation=0.,
                 ha="right", va="center",
                 color='w',weight='regular' #,bbox=bbox_props
                 )
        mkframexy("lrho%04d_xy%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,ax=ax2,cb=False,pt=False,dostreamlines=False)
        plt.setp( ax2.get_xticklabels(), visible=False)
        if dogrid: plt.grid()
        #
        plt.subplots_adjust(hspace=0.03) #increase vertical spacing to avoid crowding
        #
        #(left=0.02, right=0.94, top=0.99, bottom=0.45, wspace=0.05)
        ax1 = fig.add_axes([0.94, 0.48, 0.02, 0.515])
        #
        # Set the colormap and norm to correspond to the data for which
        # the colorbar will be used.
        cmap = mpl.cm.jet
        norm = mpl.colors.Normalize(vmin=-6, vmax=0.5625)
        # ColorbarBase derives from ScalarMappable and puts a colorbar
        # in a specified axes, so it has everything needed for a
        # standalone colorbar.  There are many more kwargs, but the
        # following gives a basic continuous colorbar with ticks
        # and labels.
        cb1 = mpl.colorbar.ColorbarBase(ax1, cmap=cmap,
                                           norm=norm,
                                           orientation='vertical')
        #
        #
        plt.savefig( "fig1.png" )
        plt.savefig( "fig1.eps" )
    #
    print( "Done!" )
    sys.stdout.flush()

def generate_time_series():
        #cd ~/run; for f in rtf*; do cd ~/run/$f; (nice -n 10 python  ~/py/mread/__init__.py &> python.out); done
        grid3d("gdump.bin",use2d=True)
        #rd("dump0000.bin")
        rfd("fieldline0000.bin")
        rhor=1+(1-a**2)**0.5
        ihor = np.floor(iofr(rhor)+0.5);
        #diskflux=diskfluxcalc(ny/2)
        #qtymem=None #clear to free mem
        if len(sys.argv[1:])==2 and sys.argv[1].isdigit() and sys.argv[2].isdigit():
            whichi = int(sys.argv[1])
            whichn = int(sys.argv[2])
            if whichi >= whichn:
                mergeqtyvstime(whichn)
            else:
                qtymem=getqtyvstime(ihor,0.2,whichi=whichi,whichn=whichn)
        else:
            qtymem=getqtyvstime(ihor,0.2)
            plotqtyvstime(qtymem)

def oldstuff():
    if False:
        #cd into the directory that contains the dumps/ directory
        #read in the grid file
        grid3d("gdump.bin")
        #plot log10(radius) vs. grid index, ti
        #plt.plot( ti[:,0,0], np.log10(r[:,0,0]) )
        plt.figure( 1, figsize=(6,12) )
        plt.clf()
        small=1e-5
        #theta grid lines through cell centers
        levs = np.linspace(0,nx-1-small,nx)
        plc(ti,xcoord=r*np.sin(h),ycoord=r*np.cos(h),levels=levs,colors='#0fffff')
        levs = np.linspace(0,ny-1-small,ny)
        plc(tj,xcoord=r*np.sin(h),ycoord=r*np.cos(h),levels=levs,colors='#0fffff')
        levs = np.linspace(0,nx-small,nx+1)
        plc(tif,xcoord=rf*np.sin(hf),ycoord=rf*np.cos(hf),levels=levs,colors='k')
        #radial grid lines through cell centers
        levs = np.linspace(0,ny-small,ny+1)
        plc(tjf,xcoord=rf*np.sin(hf),ycoord=rf*np.cos(hf),levels=levs,colors='k')
        plt.xlim(0,2)
        plt.ylim(-2,2)
        plt.savefig("grid.png")
        #
        #Read in the dump file and plot it
        #
        #read in the 1000th dump file
        plt.figure( 2, figsize=(6,12) )
        plt.clf()
        rfd("fieldline1000.bin")
        #plot contours of density
        plc(lrho,xcoord=r*np.sin(h),ycoord=r*np.cos(h),cb=True,nc=50)
        plt.xlim(0,2)
        plt.ylim(-2,2)
        plt.savefig("logdensity.png")
    if False:
        grid3d("gdump.bin"); rfd("fieldline0000.bin")
        aphi = fieldcalcface()
        sig=intangle(gdet*rho)
        plt.clf()
        plt.plot(r[:,0,0],-gdetB[2,:,ny/2,0]/dxdxp[1,1,:,ny/2,0]/dxdxp[3,3,0,0,0]/sig) 
        plt.xlim(0,200)
        plt.ylim(0,2)
    if False:
        #grid3d("gdump")
        #rfd("fieldline0250.bin")
        #cvel()
        #plc(rho)
        grid3d("gdump.bin")
        rfd("fieldline0000.bin")
        diskflux=diskfluxcalc(ny/2)
        ts,fs,md=fhorvstime(11)
        plotit(ts,fs/(diskflux),md)
    if False:
        #cd ~/run; for f in rtf*; do cd ~/run/$f; (nice -n 10 python  ~/py/mread/__init__.py &> python.out); done
        grid3d("gdump.bin")
        rfd("fieldline0000.bin")
        diskflux=diskfluxcalc(ny/2)
        ts,fs,md,jem,jtot=mfjhorvstime(11)
        plotj(ts,fs/(diskflux),md,jem,jtot)
    if False:
        rfd("fieldline2344.bin")
        cvel()
        Tcalcud()
        xxx=-Tud[1,0]/(rho*uu[1])
        yyy=choplo(chophi(xxx.sum(2)/nz,50),-50)[:,:,None]
        plco(yyy,cb=True,nc=20)
        aphi=fieldcalcface()
        plc(aphi,nc=30)

    if False:
        #OLD FORMAT
        #Plot qtys vs. time
        #cd ~/run; for f in rtf*; do cd ~/run/$f; (nice -n 10 python  ~/py/mread/__init__.py &> python.out); done
        grid3d("gdump.bin")
        rfd("fieldline0000.bin")
        rhor=1+(1-a**2)**0.5
        ihor = np.floor(iofr(rhor)+0.5);
        #diskflux=diskfluxcalc(ny/2)
        qtymem=None #clear to free mem, doesn't seem to work
        qtymem=getqtyvstime(ihor,0.2,fmtver=1)
        plotqtyvstime(qtymem)
    if False:
        rfd("fieldline0320.bin")
        plt.figure(1)
        aphi=fieldcalc()
        plc(aphi)
        plt.figure(2)
        aphi2=fieldcalc2()
        plc(aphi2)
        test()
    if False:
        grid3d( os.path.basename(glob.glob(os.path.join("dumps/", "gdump*"))[0]) )
        flist = np.sort(glob.glob( os.path.join("dumps/", "fieldline*.bin") ))
        for findex, fname in enumerate(flist):
            print( "Reading " + fname + " ..." )
            rfd("../"+fname)
            plt.clf()
            mkframe("lrho%04d" % findex, vmin=-8,vmax=0.2)
        print( "Done!" )
    if False:
        grid3d("gdump.bin")
        rfd("fieldline0000.bin")
        rhor=1+(1+a**2)**0.5
        ihor = np.floor(iofr(rhor)+0.5);
        hf=horfluxcalc(ihor)
        df=diskfluxcalc(ny/2)
        print "Initial (t=%-8g): BHflux = %g, Diskflux = %g" % (t, hf, df)
        rfd("fieldline1308.bin")
        hf=horfluxcalc(ihor)
        df=diskfluxcalc(ny/2,rmin=rhor)
        print "Final   (t=%-8g): BHflux = %g, Diskflux = %g" % (t, hf, df)
    if False:
        if len(sys.argv[1:])==2 and sys.argv[1].isdigit() and (sys.argv[2].isdigit() or sys.argv[2][0]=="-") :
            whichi = int(sys.argv[1])
            whichn = int(sys.argv[2])
            sys.stdout.flush()
        if whichn < 0 and whichn is not None:
            whichn = -whichn
            dontloadfiles = True
        else:
            dontloadfiles = False
            grid3d( os.path.basename(glob.glob(os.path.join("dumps/", "gdump*"))[0]), use2d=True )
            rd( "dump0000.bin" )
            qtymem=None #clear to free mem
            rhor=1+(1+a**2)**0.5
            ihor = np.floor(iofr(rhor)+0.5);
            qtymem=getqtyvstime(ihor,0.2)
            flist = np.sort(glob.glob( os.path.join("dumps/", "fieldline*.bin") ) )
        fname=flist[whichi]
        print( "Processing " + fname + " ..." )
        sys.stdout.flush()
        rfd("../"+fname)
        cvel() #for calculating bsq
        plt.figure(0, figsize=(12,9), dpi=100)
        plt.clf()
        mkframe("lrho%04d_Rz%g" % (findex,plotlen), vmin=-6.,vmax=0.5625,len=plotlen,ax=ax1,cb=False,pt=False)
    if False:
        len=10
        #To generate movies for all sub-folders of a folder:
        #cd ~/Research/runart; for f in *; do cd ~/Research/runart/$f; (python  ~/py/mread/__init__.py &> python.out &); done
        grid3d( os.path.basename(glob.glob(os.path.join("dumps/", "gdump*"))[0]) )
        #rfd("fieldline0000.bin")  #to define _dx#
        #grid3dlight("gdump")
        flist = np.sort(glob.glob( os.path.join("dumps/", "fieldline0000.bin") ) )
        for findex, fname in enumerate(flist):
            if os.path.isfile("lrho%04d_xy%g.png" % (findex,len)):
                print( "Skipping " + fname + " as lrho%04d_xy%g.png exists" % (findex,len) );
            else:
                print( "Processing " + fname + " ..." )
                rfd("../"+fname)
                plt.clf()
                mkframexy("lrho%04d_xy%g" % (findex,len), vmin=-8,vmax=1.5,len=len)
        print( "Done!" )
        #print( "Now you can make a movie by running:" )
        #print( "ffmpeg -fflags +genpts -r 10 -i lrho%04d.png -vcodec mpeg4 -qmax 5 mov.avi" )
        os.system("mv mov_%s_xy%g.avi mov_%s_xy%g.bak.avi" % ( os.path.basename(os.getcwd()), len, os.path.basename(os.getcwd()), len) )
        os.system("ffmpeg -fflags +genpts -r 10 -i lrho%%04d_xy%g.png -vcodec mpeg4 -qmax 5 mov_%s_xy%g.avi" % (len, os.path.basename(os.getcwd()), len) )
        #os.system("scp mov.avi 128.112.70.76:Research/movies/mov_`basename \`pwd\``.avi")

    #plt.clf(); rfd("fieldline0000.bin"); aphi=fieldcalc(); plc(ug/bsq) 
    #rfd("fieldline0002.bin")
    if False:
        grid3d( "gdump.bin" )
        rfd("fieldline0000.bin")
        plt.clf();
        mkframe("lrho%04d" % 0, vmin=-8,vmax=0.2)
    if False:
        grid3d("gdump"); rfd("fieldline0000.bin"); rrdump("rdump--0000"); plt.clf(); cvel(); plc(bsq,cb=True)
        plt.clf();plt.plot(x1[:,ny/2,0],(bsq/(2*(gam-1)*ug))[:,ny/2,0])
        plt.plot(x1[:,ny/2,0],(bsq/(2*(gam-1)*ug))[:,ny/2,0],'+')
        plt.plot(x1[:,ny/2,0],(0.01*rho)[:,ny/2,0])
    if False:
        plt.clf();plco(lrho,r*np.sin(h),r*np.cos(h),cb=True,levels=np.arange(-12,0,0.5)); plt.xlim(0,40); plt.ylim(-20,20)
    if False:
        rd( os.path.basename(glob.glob(os.path.join("dumps/", "dump0000*"))[0]) )
        #rrdump("rdump--0000")
        aphi = fieldcalc()
        plt.clf(); plt.plot(x1[:,ny/2,0],aphi[:,ny/2,0])
    if False:
        gen_vpot()
    if False:
        #Generates 6 co-aligned half-loops which combine into one big loop.
        #However, the field is noisy and probably the total flux in the big
        #loop is smaller than max possible given max ibeta.
        npow=4
        ap=np.zeros((6,rho.shape[0],rho.shape[1],rho.shape[2]))
        ap1=np.zeros((6,rho.shape[0],rho.shape[1],rho.shape[2]))
        #gives nearly uniform aphi at maxes
        #c=np.array([10,1.5,1,1,2.7,16])
        #gives uniform bsq/rho**gam at maxes
        c=np.array([3.5,2,1,2,3,10])
        phases=np.array([0,0.5,1,1.5,2,2.5])
        for i,phase in enumerate(phases):
            ap[i]=c[i]*gen_vpot(whichloop=0,phase=phase)
            ap1[i]=gen_vpot(whichloop=0,phase=phase)
        aaphi = np.sum(ap,axis=0)
        aaphi1 = np.sum(ap1,axis=0)
        aaphi2 = aaphi1 * fac(phi)
        plt.clf()
        if True:
            plt.plot(x1[:,ny/2,0],((ap[0]))[:,ny/2,0])
            plt.plot(x1[:,ny/2,0],((ap[1]))[:,ny/2,0])
            plt.plot(x1[:,ny/2,0],((ap[2]))[:,ny/2,0])
            plt.plot(x1[:,ny/2,0],((ap[3]))[:,ny/2,0])
            plt.plot(x1[:,ny/2,0],((ap[4]))[:,ny/2,0])
            plt.plot(x1[:,ny/2,0],((ap[5]))[:,ny/2,0])
            plt.plot(x1[:,ny/2,0],((aaphi))[:,ny/2,0])
        aphi2B(aaphi2)
        cvel()
        res=Qmri()
        #plt.plot(x1[:,ny/2,0],(res)[:,ny/2,0])
        #plt.clf();pl(x1,res)
        #plt.clf();pl(x1,aaphi)
        #plco(bsq/rho**gam,cb=True)
        #plco(res,cb=True)
        #pl(ti,10*fac(phi)); plt.ylim(0,ny-1)
        #pl(x1,res)
        #pl(x1,aaphi2)
        pl(x1,aaphi1)
    if False:
        rgfd("fieldline0000.bin")
        if False:
            #generate your favorite vector potential
            aaphi=gen_vpot(whichfield=None)
            #compute the field from that potential
            aphi2B(aaphi)
            B[2] = 1*B[2]
            cvel()
            #generate smoothing function
            profile = ((uqcomax-0.05)/0.1)
            profile[profile>1] = 1
            profile[profile<0] = 0
            #set target beta and desired bsqoug
            beta = 100.
            constbsqoug = 2*(gam-1)/beta
            #smooth bsqoug
            targbsqoug = constbsqoug*profile
            rat = ( targbsqoug/(bsq/ug+1e-15) )**0.5
            cvel()
        #rescale the field
        if False:
            B[1] *= rat
            B[2] *= rat
            #cvel()
            aphim=fieldcalcm()
            aphip=fieldcalcp()
            #aphi0 = avg0c2f(aphim)
            aphi2B(aphim)
            cvel()
        if False:
            rat2 = avg2ctof( rat )
            rat1 = avg1ctof( rat )
            gdetB[1] *= rat1
            gdetB[2] *= rat2
        if False:
            rat2 = avg2ctof( rat )
            rat1 = avg1ctof( rat )
            gdetB[1] *= rat1
            gdetB[2] *= rat2
            if False:
            #unsuccessful try to chop off the field spike in the middle of the loop
                minB1 = np.min(gdetB[1]/gdet)/1.5
                maxB1 = np.max(gdetB[1]/gdet)/1.5
                #gdetB1old=np.copy(gdetB[1])
                (gdetB[1])[gdetB[1]<gdet*minB1] = (minB1*gdet)[gdetB[1]<gdet*minB1]
                (gdetB[1])[gdetB[1]>gdet*maxB1] = (maxB1*gdet)[gdetB[1]>gdet*maxB1]
            #gdetB1new=np.copy(gdetB[1])
        if False:
            #at this point divb!=0, i.e. there are monopoles
            #to remove monopoles, compute vector potential
            aphi = fieldcalcface()
            #and compute the field from the potential
            #(this leaves B[1] the same and resets B[2]
            aphi2B(aphi)
        if False:
            cvel()
            normalize_field(constbsqoug)
            cvel()
        print("Disk flux = %g (@r<20: %g)" % (diskfluxcalc(ny/2), diskfluxcalc(ny/2,rmax=20)) )
    if False:
        #pf()
        grid3d("gdump.bin")
        rd("dump0000.bin")
        cvel()
        plco(np.log10(rho))
        plc(bsq/rho**gam)
        print("Disk flux = %g (@r<20: %g)" % (diskfluxcalc(ny/2,rmax=Rout), diskfluxcalc(ny/2,rmax=20)) )
        rh = 1+(1-a**2)**0.5
        print "r[5]/rh = %g\n" % (r[5,0,0]/rh) + "r[10]/rh = %g\n" % (r[10,0,0]/rh)
        res = Qmri()
        res[res>20] = 20+0*res[res>20]
        plc(res,cb=True)
        #plt.plot(x1[:,ny/2,0],(res)[:,ny/2,0])
        #plt.clf();pl(x1,res)
        #plt.clf();pl(x1,aaphi)
        #plco(bsq/rho**gam,cb=True)
        #plco(res,cb=True)
    if False:
        rin=15;
        R=r*np.sin(h);z=r*np.cos(h);
        alpha=1.5;t=0.9;aphi=(R/rin)**2/(1+(np.abs(z)/t/rin/(1+np.log10(1+r/rin)**2))**alpha)**(2/alpha); aphi[aphi>1]=0*aphi[aphi>1]+1; plco(np.log10(rho));plc(aphi)
    if False:
        grid3d("gdump.bin")
        rd("dump0040.bin")
        aphi=fieldcalcface()
        plco(np.log10(rho))
        plc(aphi,nc=50)
    if False:
        grid3d("gdump.bin")
        rfd("fieldline0222.bin")
        cvel()
        Tcalcud()
        jetpowcalc(whichbsqorho=0)[11]
        mdotcalc(11)
    if False:
        cvel()
        #entk=((gam-1)*ug/rho**gam);entk[entk>1]=0*entk[entk>1]+1;
        #plt.clf();
        #plt.figure();
        #pl(r,np.log10(entk));plt.xlim(1,20);plt.ylim(-3,-0.5)
    if False:
        #VRPLOT
        #grid3d("gdump.bin",use2d=True)
        #rd("dump0000.bin")
        #rfd("fieldline0000.bin")
        rhor=1+(1-a**2)**0.5
        ihor = np.floor(iofr(rhor)+0.5);
        #diskflux=diskfluxcalc(ny/2)
        #qtymem=None #clear to free mem
        #qtymem=getqtyvstime(ihor,0.2)
        plt.figure(1)
        plotqtyvstime(qtymem,whichplot=-3)
        #plt.figure(2)
        #plotqtyvstime(qtymem,whichplot=-4)





if __name__ == "__main__":
    if False:
        readmytests1()
        plotpowers('powerlist.txt',format=0) #old format
    if False:
        #Figure 3
        readmytests1()
        plotpowers('powerlist2davg.txt',format=1) #new format; data from 2d average dumps
    if False:
        #2DAVG
        mk2davg()
    if False:
        #NEW FORMAT
        #Plot qtys vs. time
        generate_time_series()
    if False:
        #make a movie
        mkmovie()
    if False:
        #fig2 with grayscalestreamlines and red field lines
        mkstreamlinefigure()
    if False:
        #FIGURE 1 LOTSOPANELS
        mklotsopanels()
    if False:
        #Short tutorial. Some of the names will sound familiar :)
        print( "Running a short tutorial: read in grid, 0th dump, plot and compute some things." )
        #1 read in gdump (specifying "use2d=True" reads in just one r-theta slice to save memory)
        grid3d("gdump.bin", use2d = True)
        #2 read in dump0000
        doreaddump = 0
        if doreaddump:
            rd("dump0000.bin")
        #   or, instead of dump, you could read in fieldline0000.bin
        rfd("fieldline0000.bin")
        #3 compute extra things
        docomputeextrathings = False
        if docomputeextrathings:
            cvel()
            Tcalcud()
            faraday()
        #4 compute vector potential
        aphi = fieldcalc()
        #5 plot density and overplotted vector potential
        plt.figure(1)  #open figure 1
        plco(lrho,cb=True,nc=50) #plco -- erases and plots; cb=True tells it to draw color bar, nc = number of contours
        plc(aphi,colors='k') #plc -- overplots without erasing; colors='k' says plot in blac'k'
        #5a compute same in x-z coordinates
        fig = plt.figure(2)  #open figure 2
        ax = fig.add_subplot(111, aspect='equal')
        plco(lrho,cb=True,nc=50,xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plc(aphi,nc=100,colors='k',xcoord=r*np.sin(h),ycoord=r*np.cos(h))
        plt.xlim(0,50)
        plt.ylim(-25,25)
        ax.set_aspect('equal')   
        #6 compute u^\phi
        uuphi = uu[3] * dxdxp[3,3]
        #7 compute u_\phi
        #  first, lower the index
        ud_computed = mdot(gv3,uu)  #<-- this is already computed as 'ud' inside of cvel() call
        #  then, take 3rd component and convert to phi from x3
        udphi = (ud_computed/dxdxp[3,3])[3]
        #8 phi-average density
        rhophiavg = rho.mean(axis=-1)  #-1 says to average over the last dimension
        #9 clean up some memory
        ud_computed = None
        uuphi = None
        udphi = None
        aphi = None
        gc.collect()
