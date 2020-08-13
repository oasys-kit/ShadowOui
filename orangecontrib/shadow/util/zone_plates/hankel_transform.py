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
# %% Function to perform the 0th Order Hankel Transform
# % Implemented by Joan Vila-Comamala from a routine based on the paper:
# %
# % M. Guizar-Sicairos and J. C. Gutierrez-Vega, Computation of quasi-discrete
# % Hankel transforms of integer order for propagating optical wave fields,
# % J. Opt. Soc. Am. A 21, 53-58 (2004).
# %
# % November 2010
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

import numpy
from scipy.special import jv as besselj

def hankel_transform(wavefield, max_radius, bessel_zeros, n_zeros=0):
    n = len(wavefield)
    if n_zeros <= 0: n_zeros = n

    wavefield = wavefield.conjugate().T
    m1 = (numpy.abs(besselj(1, bessel_zeros[:n])) / max_radius).conjugate().T
    max_frequency = bessel_zeros[n] / (2 * numpy.pi * max_radius)
    m2 = m1 * max_radius / max_frequency
    f = numpy.divide(wavefield, m1)
    bessel_jn = numpy.abs(besselj(1, bessel_zeros[:n_zeros])) / (2 / bessel_zeros[n])
    bessel_jm = numpy.abs(besselj(1, bessel_zeros))

    result = numpy.full(n, 0j)
    for jj in range(0, n):
        c = besselj(0, bessel_zeros[:n_zeros] * bessel_zeros[jj] / bessel_zeros[n]) / (bessel_jn * bessel_jm[jj])
        result[jj] = numpy.dot(c[:n_zeros], f[:n_zeros])

    result = result.conjugate().T
    result = numpy.multiply(result, m2)
    result = result.conjugate().T

    return result
