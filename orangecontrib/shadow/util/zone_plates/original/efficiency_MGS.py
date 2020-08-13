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
#% Calculates the Diffraction Efficiency of FZP
#% -------------------------------------------------------------------------
#% by Joan Vila, July 2010
#
#% Data from FZP simulations in 2D has to be loaded in memory.
#%
#% F_POS --> The position of the focus in units of Nz step has to be given.
#% N_points --> Number of points considered around the focal spot to
#%              integrate the intensity. (default = N)
#%
#% The code computes the incoming intensity by taking 1 for every pixel of
#% the structure. The intensity in focus is integrate considering the
#% profile that is obtained during the simulation.
#%
#% 27.11.2011 -- The formula for I had was taking the wrong range for map_d
#%               by one point. This has been corrected.
#%
#% 10.11.2010 -- The code was adapted to the output ot the codes that use
#%               Hankel Transform based on Manuel's code.
#%
#% 24.10.2010 -- The previous version was very roughly calculating the area
#%               under the intensity distribution with rough rectangle
#%               approximation. The new version is using a trapezoidal
#%               integration of MATLAB.
#% 01.09.2010 -- Version 1.0
#%
#% -------------------------------------------------------------------------

import numpy

def Efficiency_MGS(F_POS, map_d, profile_h, r, N, N_points=0):
    if N_points <= 0: N_points = N

    I_dens_0 = numpy.zeros(N)
    I_dens_0[numpy.where(profile_h != 0.j)] = 1.0
    #I_dens_0[numpy.where(numpy.logical_or(numpy.real(profile_h) != 0.0, numpy.imag(profile_h) != 0.0))] = 1.0
    I_0 = numpy.trapz(numpy.multiply(r, I_dens_0), r)
    I   = numpy.trapz(numpy.multiply(r[0:N_points+1], map_d[N-1:(N+N_points), F_POS]), r[0:N_points+1])

    return numpy.divide(I, I_0)
