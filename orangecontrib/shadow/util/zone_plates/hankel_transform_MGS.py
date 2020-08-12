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
#
# This is a translation from the matlab code:
#
#%% Function to perform the 0th Order Hankel Transform
#% Implemented by Joan Vila-Comamala from a routine based on the paper:
#%
#% M. Guizar-Sicairos and J. C. Gutierrez-Vega, Computation of quasi-discrete
#% Hankel transforms of integer order for propagating optical wave fields,
#% J. Opt. Soc. Am. A 21, 53-58 (2004).
#%
#% November 2010
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

import numpy
from scipy.special import jv as besselj

#
# h is the 1D wavefield
# R is the maximum radius in Q space
# c are the zeros of the bessel functions

def Hankel_Transform_MGS(h, R, c, Nzeros=0):
    N = len(h)

    if Nzeros <= 0: Nzeros = N
    H = numpy.full(N, 0j)

    V = c[N]/(2*numpy.pi*R)

    h = h.conjugate().T

    m1 = (numpy.abs(besselj(1, c[0:N]))/R).conjugate().T
    m2 = m1*R/V

    F = numpy.divide(h, m1)

    Bessel_Jn = numpy.abs(besselj(1, c[0:Nzeros])) / (2 / c[N])
    Bessel_Jm = numpy.abs(besselj(1, c))

    for jj in range(0, N):
        C     = besselj(0, c[0:Nzeros] * c[jj] / c[N]) / (Bessel_Jn * Bessel_Jm[jj])
        H[jj] = numpy.dot(C[0:Nzeros], F[0:Nzeros])

    H = H.conjugate().T
    H = numpy.multiply(H, m2)
    H = H.conjugate().T

    return H


'''
N = size(h,2);

H(1:N) = 0;

if nargin < 4 || isempty(Nzero)
   Nzero=N;
end

V = c(N+1)/(2*pi*R);    % Maximum frequency

h=h';

m1 = (abs(besselj(1,c(1:N)))/R)';   %% m1 prepares input vector for transformation
m2 = m1*R/V;                        %% m2 prepares output vector for display

F = h./m1;
H(1:N)=0;

Bessel_Jn = abs(besselj(1,c(1:Nzero)))/(2/c(N+1));
Bessel_Jm = abs(besselj(1,c));

parfor jj=1:N
    C = besselj(0,c(1:Nzero)*c(jj)/c(N+1))./(Bessel_Jn*Bessel_Jm(jj));
    H(jj)=C(1:Nzero)*F(1:Nzero);
end

H = H';
H = H.*m2;
H = H';
'''
