# #########################################################################
# Copyright (c) 2020, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2020. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################
#%% Fresnel zone plate simulation code
#%--------------------------------------------------------------------------
#% by Joan Vila-Comamala from original IDL version of Ana Diaz (February, 2009)
#% June, 2010
#%
#% code modified by Michael Wojcik Oct, 2013
#%
#% It simulates wavefront after FZP and propagates to the focal plane
#% plots wavefield all through the propagation from the FZP to the focus.
#%
#% 2D Extension Code --> Wavefront propagation in made using the Hankel
#% transform for a circularly symmetric function a long the radial
#% coordinate. Hankel transform routine is Hankel_Transform_MGS.
#%
#% Keep your eyes open, this code has not been throughly debugged or tested!
#%
#%
#%% ------------------------------------------------------------------------

import numpy
from orangecontrib.shadow.util.zone_plates import bessel_zeros
from orangecontrib.shadow.util.zone_plates.hankel_transform_MGS import Hankel_Transform_MGS
from orangecontrib.shadow.util.zone_plates.refractive_index import RefractiveIndex
## FZP, CS, OSA and simulation parameters
#--------------------------------------------------------------------------
  
with_CS = 1     # equal to 0 --> without CS - CENTRAL STOP
                # equal to 1 --> with CS
               
with_OSA = 0    # equal to 0 --> without OSA - ORDER SORTING APERTURE
                # equal to 1 --> with OSA
               
FZP_TYPE = 0    # equal to 0 --> Ordinary FZP
                # equal to 1 --> Zone-Doubled FZP
                # equal to 2 --> Zone-Filled FZP
                # equal to 3 --> Two-Level FZP
                # equal to 4 --> Three-Level FZP
                # equal to 5 --> ALD Multideposition FZP 1
                # equal to 6 --> ALD Multideposition FZP 2
                # equal to 7 --> Zone-Edge Slanted FZP
              
with_Range = 1  # equal to 0 --> plot to focal length
                # equal to 1 --> plot in a given range
               
with_MultiSlicing = 0 # equal to 1 --> apply multisilcing of the element 
                       # equal to 0 --> no multislicing

with_Complex = 0  # equal to 0 --> Complex Wavefront is not stored
                  # equal to 1 --> Complex Wavefront is storedk
 
energy = 8                         # photon energy [keV]
wavelength = 12.398/energy*1e-10   # wavelength [m]
k = 2*numpy.pi/wavelength          # wavevector [m-1]
height = 20000e-9                  # zone thickness or height [m]
diam = 50e-6                       # FZP diameter [m]
bmin = 50e-9                       # outermost zone width [m] / outermost period for ZD [m]
f = diam*bmin/wavelength           # focal distance [m]
Misalign = 0e-9                    # Misalignment of chosen zone plate in radial direction

Range_i = f-2e-6 # distance to FZP
Range_f = f+2e-6 # distance to FZP

CS_diam = 10e-6              # beamstop diameter [m]
OSA_position = 0.03          # distance FZP-OSA [m]
OSA_diam = 30e-6             # OSA diameter [m]

N = 5000                     # Number of sampling point in radial direction
R = diam                     # Radius of the simulation
step = R/N
Nzeros = numpy.floor(1.25*diam/2/R*N) # Parameter to speed up the Hankel Transform
                                      # when the function has zeros for N > Nzero
Nz = 3                                # Number of sampling points along the z axis
factor_z = 1.6                        # Z axis range up to factor_z*f

ii = 0 + 1j

#% FZP Material
#--------------------------------------------------------------------------

FZP_Material = 'Au'
Template_Material = 'SiO2'

delta_FZP, beta_FZP = RefractiveIndex(energy, FZP_Material)
delta_template, beta_template =  RefractiveIndex(energy, Template_Material)

if (with_MultiSlicing==1): NSlices = 100 # Number of slices of the element
else: NSlices = 1

width_coating = 20e-9                  # Width of the coated material for 
                                        # for a zone-filled FZP.
## Parameters for Stair Case Profiles 
#  Currently parameters for maximum at 6.2 keV using Au as FZP material                                        
                                       
#Two-level profile
height1 = (2/3)*1000e-9
height2 = (4/3)*1000e-9

## Contruction of the FZP profile
#--------------------------------------------------------------------------

Nzones = int(numpy.floor(1.0/4.0*(diam/bmin)))

radia = numpy.sqrt(numpy.arange(0, Nzones+1)*wavelength*f + ((numpy.arange(0, Nzones+1)*wavelength)**2)/4)
profile = numpy.full(N, 1 + 0j)
profile[int(numpy.floor(radia[Nzones]/step)):N] = 0

# Ordinary FZP
if (FZP_TYPE==0):
    for i in range (1, Nzones, 2):
       position_i = int(numpy.floor(radia[i]/step))
       position_f = int(numpy.floor(radia[i+1]/step)) # N.B. the index is excluded
       profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height-1j*2*numpy.pi*beta_FZP/wavelength*height))

    Membrane_Transmission = 1

# Zone-doubled FZP
if (FZP_TYPE==1):
    for i in range (1, Nzones, 2):
       position_i = int(numpy.floor((radia[i]+bmin/4)/step))
       position_f = int(numpy.floor((radia[i+1]-bmin/4)/step))
       profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_template/wavelength*height-1j*2*numpy.pi*beta_template/wavelength*height))
       
       position_i = int(numpy.floor((radia[i]-width_coating/2)/step))
       position_f = int(numpy.floor((radia[i]+width_coating/2)/step))
       profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height-1j*2*numpy.pi*beta_FZP/wavelength*height))
       
       position_i = int(numpy.floor((radia[i+1]-width_coating/2)/step))
       position_f = int(numpy.floor((radia[i+1]+width_coating/2)/step))
       profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height-1j*2*numpy.pi*beta_FZP/wavelength*height))

    #including absorption of coating material 
    Membrane_Transmission = numpy.exp(-1j*(-1j*2*numpy.pi*beta_FZP/wavelength*width_coating/2))

# Zone-filled FZP
if (FZP_TYPE==2):
    for i in range (1, Nzones, 2):
        
       position_i = int(numpy.floor(radia[i]/step))
       position_f = int(numpy.floor(radia[i+1]/step))
       
       width = numpy.abs(int(numpy.floor((radia[i+1]-radia[i])/step)))
       width_coating_step = numpy.abs(int(numpy.floor(width_coating/step/2)))
       
       if((width_coating<width)):
            profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_template/wavelength*height-1j*2*numpy.pi*beta_template/wavelength*height))
            
            position_i = int(numpy.floor((radia[i]-width_coating)/step))
            position_f = int(numpy.floor(radia[i]/step))
            profile[position_i:position_f] =  numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height-1j*2*numpy.pi*beta_FZP/wavelength*height))
            
            position_i = int(numpy.floor(radia[i+1]/step))
            position_f = int(numpy.floor((radia[i+1]+width_coating)/step))  
            profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height-1j*2*numpy.pi*beta_FZP/wavelength*height))
       else:
            profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_template/wavelength*height-1j*2*numpy.pi*beta_template/wavelength*height))
            
            position_i = int(numpy.floor((radia[i]-width_coating)/step))
            position_f = int(numpy.floor(radia[i]/step))
            profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height-1j*2*numpy.pi*beta_FZP/wavelength*height))
            
            position_i = int(numpy.floor(radia[i+1]/step))
            position_f = int(numpy.floor((radia[i+1]-width_coating)/step))
            profile[position_i:position_f] =  numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height-1j*2*numpy.pi*beta_FZP/wavelength*height))

    #including absorption of coating material 
    Membrane_Transmission = numpy.exp(-1j*(-1j*2*numpy.pi*beta_FZP/wavelength*width_coating))


# Two-Level FZP - stop here refactoring
if (FZP_TYPE==3):
    for i in range (1, Nzones, 2):
        position_i = int(numpy.floor((2*radia[i-1]/3+radia[i+1]/3)/step))
        position_f = int(numpy.floor((radia[i-1]/3+2*radia[i+1]/3)/step))
        profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height1-1j*2*numpy.pi*beta_FZP/wavelength*height1))
        
        position_i = int(numpy.floor((radia[i-1]/3+2*radia[i+1]/3)/step))
        position_f = int(numpy.floor((radia[i+1])/step))
        profile[position_i:position_f] = numpy.exp(-1j*(-2*numpy.pi*delta_FZP/wavelength*height2-1j*2*numpy.pi*beta_FZP/wavelength*height2))
   
    Membrane_Transmission = 1


# Inserting the CS
# --------------------------------------------------------------------------
CS_pix = numpy.floor(CS_diam / step)

if (with_CS == 1): profile[0: int(numpy.floor(CS_pix / 2))] = 0

#% Propagation of the wavefield
# The routine performing the 0th order Hankel tranform is based in a
# algorithm that calculates the function at positision related to the zeros
# of the 0th order Bessel function.
#--------------------------------------------------------------------------

# Loading the position of the zeros, as much position as N+1. The file
# c.mat contains up to 200000 zeros of the 1st order Bessel function.
c = bessel_zeros['c'][0, 0:N+1]

# Definition of the position where the calculated input and transformated
# funtions are evaluated. We define also the maximum frequency in the
# angular domain.

Q = c[N]/(2*numpy.pi*R)   # Maximum frequency
r = c[0:N]*R/c[N]         # Radius vector
q = c[0:N]/(2*numpy.pi*R) # Frequency vector

## Recalculation of the position where the initial profile is defined.
# Originally the profile is defined in position r0, that are linear for all
# the values of position. Now we need to define the function in a new
# coordinates that are by r. The next loop is interpolating the values of
# the profile from the coordinates in r0 to the coordinates in r.
# The output intensity profiles will be defined in r coordinates.
#--------------------------------------------------------------------------

r0 = numpy.arange(0, R, step)
profile_h = numpy.full(N, 0j)
for i in range(0, N-1):
    profile_h[i] = profile[i]+(profile[i+1]-profile[i])/(r0[i+1]-r0[i])*(r[i]-r0[i])
profile_h[N-1] = profile[N-1]

## Calculatio of the first angular spectrum 
#--------------------------------------------------------------------------
map_int=numpy.zeros((NSlices+Nz, N))
if (with_Complex==1): map_complex = numpy.zeros((NSlices+Nz, N))

# The function 'Hankel_Transform_MGS' needs as input the field 'field0', 
# the maximum radius R and the zeros of the 0th Bessel function. In case of
# the inverse transformation from the angular domain back to spatial domain
# the function needs as a input the angular specturm 'fun', the maximum
# frequency Q and the zeros of the Bessel function.

field0 = profile_h*Membrane_Transmission
map_int[0, :] = numpy.multiply(numpy.abs(field0), numpy.abs(field0))
if (with_Complex==1): map_complex[0, :] = field0[0:N]

four0 = Hankel_Transform_MGS(field0, R, c)
field0 = profile_h

