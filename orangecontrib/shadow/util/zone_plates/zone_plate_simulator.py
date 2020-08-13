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
from orangecontrib.shadow.util.zone_plates.hankel_transform import hankel_transform
from orangecontrib.shadow.util.zone_plates.refractive_index import get_delta_beta





class ZonePlateSimulatorOptions:
    with_central_stop = True
    cs_diameter = 10e-6  # beamstop diameter [m]

    with_order_sorting_aperture = False
    osa_position = 0.01  # distance FZP-OSA [m]
    osa_diameter = 30e-6  # OSA diameter [m]

    zone_plate_type = 0  # equal to 0 --> Ordinary FZP
                         # equal to 1 --> Zone-Doubled FZP
                         # equal to 2 --> Zone-Filled FZP
                         # equal to 3 --> Two-Level FZP
                         # equal to 4 --> Three-Level FZP           - not implemented
                         # equal to 5 --> ALD Multideposition FZP 1 - not implemented
                         # equal to 6 --> ALD Multideposition FZP 2 - not implemented
                         # equal to 7 --> Zone-Edge Slanted FZP     - not implemented
    # Width of the coated material for a zone-filled FZP.
    width_coating  = 20e-9
    #Two-level profile
    height1_factor = (1/3)
    height2_factor = (2/3)

    with_range = False  # False --> plot to focal length
                        # True  --> plot in a given range
    factor_z = 1.6
    range_i  = -2e-6
    range_f  = 2e-6
    n_z      = 3

    with_multi_slicing = False
    n_slices           = 100

    with_complex_amplitude = False


class ZonePlateAttributes:
    height = 20000e-9  # zone thickness or height [m]
    diameter = 50e-6  # FZP diameter [m]
    b_min = 50e-9  # outermost zone width [m] / outermost period for ZD [m]

    zone_plate_material = 'Au'
    template_material   = 'SiO2'

class ZonePlateSimulator(object):

    def __init__(self, options, attributes):
        self.__options    = options
        self.__attributes = attributes

    def simulate(self, energy_in_KeV=8.0, n_points=5000):
        at = self.__attributes
        op = self.__options

        self.__initialize(energy_in_KeV, n_points)

        profile, membrane_transmission = self.__build_zone_plate_profile(n_points)

        # Loading the position of the zeros, as much position as N+1. The file
        # c.mat contains up to 200000 zeros of the 1st order Bessel function.
        c = bessel_zeros['c'][0, :n_points + 1]

        # Definition of the position where the calculated input and transformated
        # funtions are evaluated. We define also the maximum frequency in the
        # angular domain.
        Q = c[n_points] / (2 * numpy.pi * self.max_radius)   # Maximum frequency
        r = c[:n_points] * self.max_radius / c[n_points]     # Radius vector
        q = c[:n_points] / (2 * numpy.pi * self.max_radius)  # Frequency vector

        # Recalculation of the position where the initial profile is defined.
        profile_h = self.__get_profile_h(profile, r, n_points)

        map_int     = numpy.zeros((self.n_slices + self.n_z, n_points))
        map_complex = numpy.full((self.n_slices + self.n_z, n_points), 0j)

        # Calculation of the first angular spectrum
        # --------------------------------------------------------------------------

        field0            = profile_h * membrane_transmission
        map_int[0, :]     = numpy.multiply(numpy.abs(field0), numpy.abs(field0))
        map_complex[0, :] = field0[0: n_points]
        four0             = hankel_transform(field0, self.max_radius, c)
        field0            = profile_h

        if op.with_multi_slicing: four0 = self.__propagate_multislicing(map_int, map_complex, field0, four0, Q, q, c)

        if op.with_range: self.__propagate_on_range(map_int, map_complex, four0, Q, q, c)
        else:             self.__propagate_to_focus(map_int, map_complex, four0, Q, q, c)

        map_index = self.n_slices

        efficiency = self.__calculate_efficiency(map_index, map_int, profile_h, r, n_points, int(numpy.floor(10*at.b_min/self.step)))

        return map_int, map_complex, efficiency

    def __initialize(self, energy_in_KeV, n_points):
        at = self.__attributes
        op = self.__options

        self.wavelength = 12.398 / energy_in_KeV * 1e-10  # wavelength [m]
        self.k = 2 * numpy.pi / self.wavelength  # wavevector [m-1]

        self.focal_distance = at.diameter * at.b_min / self.wavelength  # focal distance [m]

        self.max_radius = at.diameter
        self.step = self.max_radius / n_points

        self.n_zeros = numpy.floor(1.25 * at.diameter / 2 / self.max_radius * n_points)  # Parameter to speed up the Hankel Transform
        # when the function has zeros for N > Nzero

        self.delta_FZP, self.beta_FZP = get_delta_beta(energy_in_KeV, at.zone_plate_material)
        self.delta_template, self.beta_template = get_delta_beta(energy_in_KeV, at.template_material)

        if op.with_multi_slicing: self.n_slices = op.n_slices
        else:                     self.n_slices = 1

        if op.with_range: self.n_z = op.n_z
        else:             self.n_z = 1

    def __build_zone_plate_profile(self, n_points):
        at = self.__attributes
        op = self.__options

        n_zones = int(numpy.floor(1.0 / 4.0 * (at.diameter / at.b_min)))
        
        radia = numpy.sqrt(numpy.arange(0, n_zones + 1) * self.wavelength * self.focal_distance + ((numpy.arange(0, n_zones + 1) * self.wavelength) ** 2) / 4)
        profile = numpy.full(n_points, 1 + 0j)
        profile[int(numpy.floor(radia[n_zones] / self.step)):n_points] = 0
        
        # Ordinary FZP
        if op.zone_plate_type == 0:
            for i in range(1, n_zones, 2):
                position_i = int(numpy.floor(radia[i] / self.step))
                position_f = int(numpy.floor(radia[i + 1] / self.step))  # N.B. the index is excluded
                profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * at.height))
        
            membrane_transmission = 1
        
        # Zone-doubled FZP
        if op.zone_plate_type == 1:
            for i in range(1, n_zones, 2):
                position_i = int(numpy.floor((radia[i] + at.b_min / 4) / self.step))
                position_f = int(numpy.floor((radia[i + 1] - at.b_min / 4) / self.step))
                profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_template / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_template / self.wavelength * at.height))
        
                position_i = int(numpy.floor((radia[i] - op.width_coating / 2) / self.step))
                position_f = int(numpy.floor((radia[i] + op.width_coating / 2) / self.step))
                profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * at.height))
        
                position_i = int(numpy.floor((radia[i + 1] - op.width_coating / 2) / self.step))
                position_f = int(numpy.floor((radia[i + 1] + op.width_coating / 2) / self.step))
                profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * at.height))
        
            # including absorption of coating material 
            membrane_transmission = numpy.exp(-1j * (-1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * op.width_coating / 2))
        
        # Zone-filled FZP
        if op.zone_plate_type == 2:
            for i in range(1, n_zones, 2):
        
                position_i = int(numpy.floor(radia[i] / self.step))
                position_f = int(numpy.floor(radia[i + 1] / self.step))
        
                width = numpy.abs(int(numpy.floor((radia[i + 1] - radia[i]) / self.step)))
                op.width_coating_step = numpy.abs(int(numpy.floor(op.width_coating / self.step / 2)))
        
                if op.width_coating < width:
                    profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_template / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_template / self.wavelength * at.height))
        
                    position_i = int(numpy.floor((radia[i] - op.width_coating) / self.step))
                    position_f = int(numpy.floor(radia[i] / self.step))
                    profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * at.height))
        
                    position_i = int(numpy.floor(radia[i + 1] / self.step))
                    position_f = int(numpy.floor((radia[i + 1] + op.width_coating) / self.step))
                    profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * at.height))
                else:
                    profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_template / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_template / self.wavelength * at.height))
        
                    position_i = int(numpy.floor((radia[i] - op.width_coating) / self.step))
                    position_f = int(numpy.floor(radia[i] / self.step))
                    profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * at.height))
        
                    position_i = int(numpy.floor(radia[i + 1] / self.step))
                    position_f = int(numpy.floor((radia[i + 1] - op.width_coating) / self.step))
                    profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * at.height - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * at.height))
        
            # including absorption of coating material 
            membrane_transmission = numpy.exp(-1j * (-1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * op.width_coating))
        
        # Two-Level FZP - stop here refactoring
        if op.zone_plate_type == 3:
            height1 = op.height1_factor * at.height
            height2 = op.height2_factor * at.height

            for i in range(1, n_zones, 2):
                position_i = int(numpy.floor((2 * radia[i - 1] / 3 + radia[i + 1] / 3) / self.step))
                position_f = int(numpy.floor((radia[i - 1] / 3 + 2 * radia[i + 1] / 3) / self.step))
                profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * height1 - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * height1))
        
                position_i = int(numpy.floor((radia[i - 1] / 3 + 2 * radia[i + 1] / 3) / self.step))
                position_f = int(numpy.floor((radia[i + 1]) / self.step))
                profile[position_i:position_f] = numpy.exp(-1j * (-2 * numpy.pi * self.delta_FZP / self.wavelength * height2 - 1j * 2 * numpy.pi * self.beta_FZP / self.wavelength * height2))
        
            membrane_transmission = 1

        # Inserting the CS
        # --------------------------------------------------------------------------

        if op.with_central_stop:
            cs_pix = numpy.floor(op.cs_diameter / self.step)
            profile[0: int(numpy.floor(cs_pix / 2))] = 0

        return profile, membrane_transmission

    def __get_profile_h(self, profile, r, n_points):
        # Recalculation of the position where the initial profile is defined.
        # Originally the profile is defined in position r0, that are linear for all
        # the values of position. Now we need to define the function in a new
        # coordinates that are by r. The next loop is interpolating the values of
        # the profile from the coordinates in r0 to the coordinates in r.
        # The output intensity profiles will be defined in r coordinates.
        r0        = numpy.arange(0, self.max_radius, self.step)
        profile_h = numpy.full(n_points, 0j)
        for i in range(0, n_points - 1):
            profile_h[i] = profile[i] + (profile[i + 1] - profile[i]) / (r0[i + 1] - r0[i]) * (r[i] - r0[i])
        profile_h[n_points - 1] = profile[n_points - 1]

        return profile_h

    def __propagate_multislicing(self, map_int, map_complex, field0, four0, Q, q, c):
        step_slice = self.__attributes.height

        for n in range(self.n_slices - 1):
            proj  = numpy.exp(-1j * step_slice * ((2 * numpy.pi * q) ** 2) / (2 * self.k))

            fun   = numpy.multiply(proj, four0)
            field = hankel_transform(fun, Q, c)
            fun = numpy.multiply(field0, field)

            map_int[1 + n, :] = numpy.multiply(numpy.abs(fun), numpy.abs(fun))
            map_complex[1 + n, :] = fun

            four0 = hankel_transform(fun, self.max_radius, c, self.n_zeros)

        return four0

    def __propagate_to_focus(self, map_int, map_complex, four0, Q, q, c):
        at = self.__attributes
        op = self.__options

        if not op.with_order_sorting_aperture:
            self.__propagate_to_distance(map_int, map_complex, self.focal_distance, four0, Q, q, c)
        else:
            pass

    def __propagate_on_range(self, map_int, map_complex, four0, Q, q, c):
        at = self.__attributes
        op = self.__options


    def __propagate_to_distance(self, map_int, map_complex, z, four0, Q, q, c, index=0):
        print("Propagation to distance: ", z, " m")
        proj = numpy.exp(-1j * z * ((2 * numpy.pi * q) ** 2) / (2 * self.k))
        fun = numpy.multiply(proj, four0)
        four11 = hankel_transform(fun, Q, c)
        map_int[index + self.n_slices, :] = numpy.multiply(numpy.abs(four11), numpy.abs(four11))
        map_complex[index + self.n_slices, :] = four11

    def __calculate_efficiency(self, map_index, map_out, profile_h, r, n_points, n_integration_points=0):
        shape = map_out.shape

        map_d = numpy.full((2 * shape[1], shape[0]), None)
        map_d[:n_points, :]           = numpy.flipud(map_out[:, :n_points].T)
        map_d[n_points:2*n_points, :] = map_out[:, :n_points].T

        if n_integration_points <= 0: n_integration_points = n_points

        I_dens_0 = numpy.zeros(n_points)
        I_dens_0[numpy.where(profile_h != 0.j)] = 1.0
        I_0 = numpy.trapz(numpy.multiply(r, I_dens_0), r)
        I   = numpy.trapz(numpy.multiply(r[:n_integration_points+1], map_d[n_points-1:(n_points+n_integration_points), map_index]), r[:n_integration_points+1])

        return numpy.divide(I, I_0)

if __name__=="__main__":
    zs = ZonePlateSimulator(options=ZonePlateSimulatorOptions(), attributes=ZonePlateAttributes())

    map_int, _, efficiency = zs.simulate(energy_in_KeV=8.0, n_points=5000)

    print("Efficiency:", efficiency)

    ###################################################
    #
    # Plotting
    #
    ###################################################
    from scipy import interpolate

    def rotate(r, profile):
        interpol_index = interpolate.interp1d(r, profile, bounds_error=False, fill_value=0.0)

        xv = numpy.arange(-r[-1], r[-1], r[1] - r[0])  # adjust your matrix values here
        X, Y = numpy.meshgrid(xv, xv)
        profilegrid = numpy.zeros(X.shape, float)
        for i, x in enumerate(X[0, :]):
            for k, y in enumerate(Y[:, 0]):
                current_radius = numpy.sqrt(x ** 2 + y ** 2)
                profilegrid[i, k] = interpol_index(current_radius)

        return profilegrid


    r0 = numpy.arange(0, zs.max_radius, zs.step)

    from matplotlib import pyplot as plt

    print("Shape:", map_int.shape)

    for i in range(1, map_int.shape[0]):
        plt.plot(r0[:50], map_int[i, :50])
    plt.show()

    plt.imshow(rotate(r0[:50], map_int[1, :50]))
    plt.show()
