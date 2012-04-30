import matplotlib
matplotlib.use('Agg')
from matplotlib import rc
from streamlines import streamplot
from streamlines import fstreamplot
from pychip import pchip_init, pchip_eval
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
from scipy.integrate import quad
from scipy.integrate import odeint
from scipy.integrate import simps
from scipy.optimize import brentq
from scipy.optimize import curve_fit
from scipy.interpolate import InterpolatedUnivariateSpline
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
from matplotlib import mpl
from matplotlib import cm,ticker
from numpy import ma
import matplotlib.colors as colors
import os,glob
import pylab
import sys
import streamlines
from matplotlib.patches import Ellipse
import pdb

import casc as casc
reload(casc)

def test_fg( Eold, Enew, seed ):
    Egmin = 2*seed.Emin*Enew**2 / (1.-2*seed.Emin*Enew)
    Egmax = 2*seed.Emax*Enew**2 / (1.-2*seed.Emax*Enew)
    plt.plot(Eold-Enew, fg_p(Eold-Enew, Eold, seed))
    plt.xscale("log")
    plt.yscale("log")
    plt.xlim(0.5*Egmin,2*Egmax)
    

def main():
    #
    Ngenmax = 10
    #
    E0 = 1e8
    ii = np.round(np.log(E0)/np.log(Emax)*Ngrid)
    dx = np.log(Evec[1]/Evec[0])
    dE = Evec[ii] * dx
    dN = np.zeros_like(Evec)
    dN[ii]  = 1/dE
    dNold = dN
    dNnew = np.copy(dN)
    nskip = 1
    plt.plot(Evec, dNold)
    for gen in xrange(0,Ngenmax):
        Ntot = simps( dNnew*Evec, dx=dx,axis=-1 )
        print( gen, Ntot )
        sys.stdout.flush()
        dNold = dNnew
        dNnew = casc.flnew( grid, dNold, seed )
        #pdb.set_trace()
        plt.plot(Evec, dNnew)
        plt.xscale("log")
        plt.yscale("log")
        plt.ylim(1e-15,1e-4)
        plt.xlim(1e4,Emax)
        # plt.draw()


if __name__ == "__main__":
    #main()
    print ("Hello")
    #energy grid, Lorentz factor of initial electron
    warnings.simplefilter("error")
    Emin = 1e-5
    Emax = 1e10
    Ngrid = 1e2
    # Evec = exp(np.linspace(-5,np.log(Emax),Ngrid))
    E0grid = 0
    grid = casc.Grid(Emin, Emax, E0grid, Ngrid)
    Evec = grid.Egrid
    ivec = np.arange(len(Evec))
    #1 eV in units of m_e c^2
    eV = 1/(511.e3)
    #spectral index
    s = 2
    #lower cutoff
    Esmin = 0.5e-3 * eV
    Esmax = 2 * eV
    seed = casc.SeedPhoton( Esmin, Esmax, s )
