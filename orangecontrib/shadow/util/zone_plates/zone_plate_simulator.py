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
# %% Fresnel zone plate simulation code
# %--------------------------------------------------------------------------
# % by Joan Vila-Comamala from original IDL version of Ana Diaz (February, 2009)
# % June, 2010
# %
# % code modified by Michael Wojcik Oct, 2013
# %
# % It simulates wavefront after FZP and propagates to the focal plane
# % plots wavefield all through the propagation from the FZP to the focus.
# %
# % 2D Extension Code --> Wavefront propagation in made using the Hankel
# % transform for a circularly symmetric function a long the radial
# % coordinate. Hankel transform routine is Hankel_Transform_MGS.
# %
# % Keep your eyes open, this code has not been throughly debugged or tested!
# %
# %
# %% ------------------------------------------------------------------------

import numpy

from matplotlib import cm, rcParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

try:
    from mpl_toolkits.mplot3d import Axes3D  # to load plot 3D
except:
    pass

from scipy import interpolate

from oasys.widgets import gui as oasysgui
from silx.gui.plot import Plot2D

from orangecontrib.shadow.util.zone_plates import bessel_zeros
from orangecontrib.shadow.util.zone_plates.hankel_transform import hankel_transform
from orangecontrib.shadow.util.zone_plates.refractive_index import get_delta_beta


# % ------------------------------------------
#
# cs_diameter = beamstop diameter [m]
# osa_position = distance FZP-OSA [m]
# osa_diameter = OSA diameter [m]
#
# zone_plate_type = 0  # equal to 0 --> Ordinary FZP
#                      # equal to 1 --> Zone-Doubled FZP
#                      # equal to 2 --> Zone-Filled FZP
#                      # equal to 3 --> Two-Level FZP
#                      # equal to 4 --> Three-Level FZP           - not implemented
#                      # equal to 5 --> ALD Multideposition FZP 1 - not implemented
#                      # equal to 6 --> ALD Multideposition FZP 2 - not implemented
#                      # equal to 7 --> Zone-Edge Slanted FZP     - not implemented
#
# width_coating  = Width of the coated material for a zone-filled FZP
#
# height1_factor = multiply height < 1 for Two-level profile
# height2_factor = multiply height < 1 for Two-level profile
#
# with_range =  False --> plot to focal length
#               True  --> plot in a given range
#
# range_i  = initial position of the range
# range_f  = final position of the range
# n_z      = number of positions
#
# n_slices           = number of slices
# with_complex_amplitude = False
#
# % ------------------------------------------
class ZonePlateSimulatorOptions():

    def __init__(self,
                 with_central_stop=True,
                 cs_diameter=10e-6,
                 with_order_sorting_aperture=False,
                 osa_position=0.01,
                 osa_diameter=30e-6,
                 zone_plate_type=0,
                 width_coating=20e-9,
                 height1_factor=(1 / 3),
                 height2_factor=(2 / 3),
                 with_range=False,
                 range_i=-2e-6,
                 range_f=2e-6,
                 n_z=3,
                 with_multi_slicing=False,
                 n_slices=100,
                 with_complex_amplitude=False
                 ):
        self.with_central_stop = with_central_stop
        self.cs_diameter = cs_diameter
        self.with_order_sorting_aperture = with_order_sorting_aperture
        self.osa_position = osa_position
        self.osa_diameter = osa_diameter
        self.zone_plate_type = zone_plate_type
        self.width_coating = width_coating
        self.height1_factor = height1_factor
        self.height2_factor = height2_factor
        self.with_range = with_range
        self.range_i = range_i
        self.range_f = range_f
        self.n_z = n_z
        self.with_multi_slicing = with_multi_slicing
        self.n_slices = n_slices
        self.with_complex_amplitude = with_complex_amplitude


# % ------------------------------------------
#
# height =  zone thickness or height [m]
# diameter = FZP diameter [m]
# b_min = outermost zone width [m] / outermost period for ZD [m]
#
# % ------------------------------------------
class ZonePlateAttributes():

    def __init__(self,
                 height=20000e-9,
                 diameter=50e-6,
                 b_min=50e-9,
                 zone_plate_material='Au',
                 template_material='SiO2'
                 ):
        self.height = height
        self.diameter = diameter
        self.b_min = b_min
        self.zone_plate_material = zone_plate_material
        self.template_material = template_material


class ZonePlateSimulator(object):

    def __init__(self, options=ZonePlateSimulatorOptions(), attributes=ZonePlateAttributes()):
        self.__options = options
        self.__attributes = attributes

    def initialize(self, energy_in_KeV=8.0, n_points=5000):
        at = self.__attributes
        op = self.__options

        if energy_in_KeV <= 0: raise ValueError("Energy must be > 0")
        if n_points <= 0: raise ValueError("Number of integration points must be > 0")

        if at.height <= 0: raise ValueError("ZP Height must be > 0")
        if at.b_min <= 0: raise ValueError("ZP outermost zone width must be > 0")
        if at.diameter <= 0: raise ValueError("ZP Diameter must be > 0")

        if op.zone_plate_type == 2:
            if op.width_coating <= 0: raise ValueError("Coating Width must be > 0")
        if op.zone_plate_type == 3:
            if op.height1_factor <= 0: raise ValueError("Height 1 Factor must be > 0")
            if op.height2_factor <= 0: raise ValueError("Height 2 Factor must be > 0")

        self.energy_in_KeV = energy_in_KeV
        self.n_points = n_points

        self.wavelength = 12.398 / energy_in_KeV * 1e-10  # wavelength [m]
        self.k = 2 * numpy.pi / self.wavelength  # wavevector [m-1]

        self.focal_distance = at.diameter * at.b_min / self.wavelength  # focal distance [m]

        self.max_radius = at.diameter
        self.step = self.max_radius / self.n_points

        self.n_zeros = numpy.floor(1.25 * at.diameter / 2 / self.max_radius * n_points)  # Parameter to speed up the Hankel Transform
        # when the function has zeros for N > Nzero

        self.delta_FZP, self.beta_FZP = get_delta_beta(energy_in_KeV, at.zone_plate_material)
        self.delta_template, self.beta_template = get_delta_beta(energy_in_KeV, at.template_material)

        if op.with_multi_slicing:
            self.n_slices = op.n_slices
        else:
            self.n_slices = 1

        if op.with_range:
            if op.range_f <= op.range_i: raise ValueError("Range final position is smaller than initial position")
            if op.n_z < 2: raise ValueError("Number of position must be >= 2")

            self.n_z = op.n_z
        else:
            self.n_z = 1

        if op.with_order_sorting_aperture:
            if op.osa_position <= 0: raise ValueError("OSA position must be > 0")
            if op.osa_position >= self.focal_distance: raise ValueError("OSA position beyond focal distance")
            if op.osa_diameter <= 0: raise ValueError("OSA diameter must be > 0")

    def simulate(self):
        at = self.__attributes
        op = self.__options

        profile, membrane_transmission = self.__build_zone_plate_profile()

        # Loading the position of the zeros, as much position as N+1. The file
        # c.mat contains up to 200000 zeros of the 1st order Bessel function.
        c = bessel_zeros['c'][0, :self.n_points + 1]

        # Definition of the position where the calculated input and transformed
        # functions are evaluated. We define also the maximum frequency in the
        # angular domain.
        Q = c[self.n_points] / (2 * numpy.pi * self.max_radius)  # Maximum frequency
        r = c[:self.n_points] * self.max_radius / c[self.n_points]  # Radius vector
        q = c[:self.n_points] / (2 * numpy.pi * self.max_radius)  # Frequency vector

        # Recalculation of the position where the initial profile is defined.
        profile_h = self.__get_profile_h(profile, r)

        map_int = numpy.zeros((self.n_slices + self.n_z, self.n_points))
        map_complex = numpy.full((self.n_slices + self.n_z, self.n_points), 0j)

        # Calculation of the first angular spectrum
        # --------------------------------------------------------------------------

        field0 = profile_h * membrane_transmission
        map_int[0, :] = numpy.multiply(numpy.abs(field0), numpy.abs(field0))
        map_complex[0, :] = field0[0: self.n_points]
        four0 = hankel_transform(field0, self.max_radius, c)
        field0 = profile_h

        if op.with_multi_slicing: four0 = self.__propagate_multislicing(map_int, map_complex, field0, four0, Q, q, c)

        if op.with_range:
            self.__propagate_on_range(map_int, map_complex, four0, Q, q, c)
        else:
            self.__propagate_to_focus(map_int, map_complex, four0, Q, q, c)

        map_index = self.n_slices

        efficiency = self.__calculate_efficiency(map_index, map_int, profile_h, r, int(numpy.floor(10 * at.b_min / self.step)))

        return map_int, map_complex, efficiency

    def plot_1D(self, plot_canvas, profile_1D, last_index=-1, show=False, replace=True, profile_name="z pos #1", control=False, color='blue'):
        if plot_canvas is None:
            plot_canvas = oasysgui.plotWindow(parent=None,
                                              backend=None,
                                              resetzoom=True,
                                              autoScale=True,
                                              logScale=True,
                                              grid=True,
                                              curveStyle=True,
                                              colormap=False,
                                              aspectRatio=False,
                                              yInverted=False,
                                              copy=True,
                                              save=True,
                                              print_=True,
                                              control=control,
                                              position=True,
                                              roi=False,
                                              mask=False,
                                              fit=True)

            plot_canvas.setDefaultPlotLines(True)
            plot_canvas.setActiveCurveColor(color="#00008B")

        title  = "Radial Intensity Profile"
        xtitle = "Radius [m]"
        ytitle = "Intensity [A.U.]"

        plot_canvas.setGraphTitle(title)
        plot_canvas.setGraphXLabel(xtitle)
        plot_canvas.setGraphYLabel(ytitle)

        rcParams['axes.formatter.useoffset']='False'

        radius = numpy.arange(0, self.max_radius, self.step)

        plot_canvas.addCurve(radius[:last_index], profile_1D[:last_index], profile_name, symbol='', color=color, xlabel=xtitle, ylabel=ytitle, replace=replace) #'+', '^', ','

        plot_canvas.setInteractiveMode('zoom', color='orange')
        plot_canvas.resetZoom()
        plot_canvas.replot()

        plot_canvas.setActiveCurve("Radial Intensity Profile")

        if show: plot_canvas.show()

        return plot_canvas

    def plot_2D(self, plot_canvas, profile_1D, last_index=-1, show=False):
        radius = numpy.arange(0, self.max_radius, self.step)

        X, Y, data2D = ZonePlateSimulator.create_2D_profile(radius[:last_index], profile_1D[:last_index])
        dataX = X[0, :]
        dataY = Y[:, 0]

        origin = (dataX[0], dataY[0])
        scale = (dataX[1] - dataX[0], dataY[1] - dataY[0])

        data_to_plot = data2D.T

        colormap = {"name": "temperature", "normalization": "linear", "autoscale": True, "vmin": 0, "vmax": 0, "colors": 256}

        if plot_canvas is None:
            plot_canvas = Plot2D()

            plot_canvas.resetZoom()
            plot_canvas.setXAxisAutoScale(True)
            plot_canvas.setYAxisAutoScale(True)
            plot_canvas.setGraphGrid(False)
            plot_canvas.setKeepDataAspectRatio(True)
            plot_canvas.yAxisInvertedAction.setVisible(False)

            plot_canvas.setXAxisLogarithmic(False)
            plot_canvas.setYAxisLogarithmic(False)

            plot_canvas.getMaskAction().setVisible(False)
            plot_canvas.getRoiAction().setVisible(False)
            plot_canvas.getColormapAction().setVisible(True)
            plot_canvas.setKeepDataAspectRatio(False)

        plot_canvas.addImage(numpy.array(data_to_plot),
                                                legend="rotated",
                                                scale=scale,
                                                origin=origin,
                                                colormap=colormap,
                                                replace=True)

        plot_canvas.setActiveImage("rotated")
        plot_canvas.setGraphXLabel("X [m]")
        plot_canvas.setGraphYLabel("Y [m]")
        plot_canvas.setGraphTitle("2D Intensity Profile")

        if show: plot_canvas.show()

        return plot_canvas

    def plot_3D(self, figure_canvas, profile_1D, last_index=-1, show=False):
        radius = numpy.arange(0, self.max_radius, self.step)

        X, Y, data2D = ZonePlateSimulator.create_2D_profile(radius[:last_index], profile_1D[:last_index])

        if figure_canvas is None:
            figure = Figure(figsize=(600, 600))
            figure.patch.set_facecolor('white')

            ax = figure.add_subplot(111, projection='3d')
            figure_canvas = FigureCanvasQTAgg(figure)
        else:
            ax = figure_canvas.figure.axes[0]

        ax.clear()

        figure.suptitle("3D Intensity Profile")
        ax.plot_surface(X, Y, data2D, rstride=1, cstride=1, cmap=cm.coolwarm, linewidth=0.5, antialiased=True)

        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.set_zlabel("Intensity [A.U.]")
        ax.mouse_init()

        if show: figure_canvas.show()

        return figure_canvas

    @classmethod
    def create_2D_profile(cls, r, profile_1D):
        interpol_index = interpolate.interp1d(r, profile_1D, bounds_error=False, fill_value=0.0)

        xv = numpy.arange(-r[-1], r[-1], r[1] - r[0])  # adjust your matrix values here
        X, Y = numpy.meshgrid(xv, xv)
        profilegrid = numpy.zeros(X.shape, float)
        for i, x in enumerate(X[0, :]):
            for k, y in enumerate(Y[:, 0]):
                current_radius = numpy.sqrt(x ** 2 + y ** 2)
                profilegrid[i, k] = interpol_index(current_radius)

        return X, Y, profilegrid

    ###################################################
    #
    def __build_zone_plate_profile(self):
        at = self.__attributes
        op = self.__options

        n_zones = int(numpy.floor(1.0 / 4.0 * (at.diameter / at.b_min)))

        radia = numpy.sqrt(numpy.arange(0, n_zones + 1) * self.wavelength * self.focal_distance + ((numpy.arange(0, n_zones + 1) * self.wavelength) ** 2) / 4)
        profile = numpy.full(self.n_points, 1 + 0j)
        profile[int(numpy.floor(radia[n_zones] / self.step)):self.n_points] = 0

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

    ###################################################
    #
    def __get_profile_h(self, profile, r):
        # Recalculation of the position where the initial profile is defined.
        # Originally the profile is defined in position r0, that are linear for all
        # the values of position. Now we need to define the function in a new
        # coordinates that are by r. The next loop is interpolating the values of
        # the profile from the coordinates in r0 to the coordinates in r.
        # The output intensity profiles will be defined in r coordinates.
        r0 = numpy.arange(0, self.max_radius, self.step)
        profile_h = numpy.full(self.n_points, 0j)
        for i in range(0, self.n_points - 1):
            profile_h[i] = profile[i] + (profile[i + 1] - profile[i]) / (r0[i + 1] - r0[i]) * (r[i] - r0[i])
        profile_h[self.n_points - 1] = profile[self.n_points - 1]

        return profile_h

    ###################################################
    #
    def __propagate_multislicing(self, map_int, map_complex, field0, four0, Q, q, c):
        step_slice = self.__attributes.height

        for n in range(self.n_slices - 1):
            proj = numpy.exp(-1j * step_slice * ((2 * numpy.pi * q) ** 2) / (2 * self.k))

            fun = numpy.multiply(proj, four0)
            field = hankel_transform(fun, Q, c)
            fun = numpy.multiply(field0, field)

            map_int[1 + n, :] = numpy.multiply(numpy.abs(fun), numpy.abs(fun))
            map_complex[1 + n, :] = fun

            four0 = hankel_transform(fun, self.max_radius, c, self.n_zeros)

        return four0

    ###################################################
    #
    def __propagate_to_focus(self, map_int, map_complex, four0, Q, q, c):
        op = self.__options

        if not op.with_order_sorting_aperture:
            self.__propagate_to_distance(map_int, map_complex, self.focal_distance, four0, Q, q, c)
        else:
            # Propagation to OSA position and OSA insertion
            # --------------------------------------------------------------------------
            four_OSA = self.__propagate_to_OSA(four0, Q, q, c)

            # Propagation at the focus position
            # --------------------------------------------------------------------------
            self.__propagate_to_distance(map_int, map_complex, self.focal_distance - op.osa_position, four_OSA, Q, q, c)

    ###################################################
    #
    def __propagate_on_range(self, map_int, map_complex, four0, Q, q, c):
        op = self.__options

        stepz = (op.range_f - op.range_i) / (op.n_z - 1)
        z = (op.range_i + numpy.arange(op.n_z) * stepz)

        if not op.with_order_sorting_aperture:
            for o in range(op.n_z):
                self.__propagate_to_distance(map_int, map_complex, z[o], four0, Q, q, c, index=o)
        else:
            if op.osa_position < op.range_i:
                # Propagation to OSA position and OSA insertion
                # --------------------------------------------------------------------------
                four_OSA = self.__propagate_to_OSA(four0, Q, q, c)

                # Continue the propagation from OSA on the range
                #--------------------------------------------------------------------------
                for o in range(op.n_z):
                    self.__propagate_to_distance(map_int, map_complex, z[o] - op.osa_position, four_OSA, Q, q, c, index=o)
            else:
                z_before = z[numpy.where(z <= op.osa_position)]
                last_before = len(z_before)

                # Propagation from initial position to last position before OSA
                # ------------------------------------------------------------------
                for o in range(last_before):
                    self.__propagate_to_distance(map_int, map_complex, z_before[o], four0, Q, q, c, index=o)

                # Propagation to OSA position and OSA insertion
                # --------------------------------------------------------------------------
                four_OSA = self.__propagate_to_OSA(four0, Q, q, c)

                # Continue the propagation from first position after OSA to final position
                #--------------------------------------------------------------------------
                for o in range(last_before, op.n_z):
                    self.__propagate_to_distance(map_int, map_complex, z[o] - op.osa_position, four_OSA, Q, q, c, index=o)

    ###################################################
    #
    def __propagate_to_distance(self, map_int, map_complex, z, four0, Q, q, c, index=0):
        print("Propagation to distance: ", z, " m")

        proj = numpy.exp(-1j * z * ((2 * numpy.pi * q) ** 2) / (2 * self.k))
        fun = numpy.multiply(proj, four0)
        four11 = hankel_transform(fun, Q, c)

        map_int[index + self.n_slices, :] = numpy.multiply(numpy.abs(four11), numpy.abs(four11))
        map_complex[index + self.n_slices, :] = four11

    ###################################################
    #
    def __propagate_to_OSA(self, four0, Q, q, c):
        op = self.__options

        print("Propagation to OSA: ", op.osa_position, " m")
        # Propagation at the OSA position
        # --------------------------------------------------------------------------
        proj_OSA = numpy.exp(-1j * op.osa_position * ((2 * numpy.pi * q) ** 2) / (2 * self.k))
        fun = numpy.multiply(proj_OSA, four0)
        field_OSA = hankel_transform(fun, Q, c)

        # Inserting OSA
        # --------------------------------------------------------------------------
        OSA_pix = int(numpy.floor(op.osa_diameter / self.step) - 1)
        field_OSA[int(OSA_pix / 2) + 1:self.n_points] = 0
        four_OSA = hankel_transform(field_OSA, self.max_radius, c)

        return four_OSA

    ###################################################
    #
    def __calculate_efficiency(self, map_index, map_out, profile_h, r, n_integration_points=0):
        shape = map_out.shape

        map_d = numpy.full((2 * shape[1], shape[0]), None)
        map_d[:self.n_points, :] = numpy.flipud(map_out[:, :self.n_points].T)
        map_d[self.n_points:2 * self.n_points, :] = map_out[:, :self.n_points].T

        if n_integration_points <= 0: n_integration_points = self.n_points

        I_dens_0 = numpy.zeros(self.n_points)
        I_dens_0[numpy.where(profile_h != 0.j)] = 1.0
        I_0 = numpy.trapz(numpy.multiply(r, I_dens_0), r)
        I = numpy.trapz(numpy.multiply(r[:n_integration_points + 1], map_d[self.n_points - 1:(self.n_points + n_integration_points), map_index]), r[:n_integration_points + 1])

        return numpy.divide(I, I_0)

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout

if __name__ == "__main__":
    app = QApplication([])

    n_z = 5
    zs = ZonePlateSimulator(options=ZonePlateSimulatorOptions(with_range=True,
                                                              range_i=0.0160,
                                                              range_f=0.0162,
                                                              n_z=n_z),
                            attributes=ZonePlateAttributes())

    zs.initialize(energy_in_KeV=8.0, n_points=5000)

    map_int, _, efficiency = zs.simulate()

    print("Efficiency:", efficiency)

    container = QWidget()
    container.setFixedWidth(1500)

    layout = QHBoxLayout()

    figure = None
    for i in range(n_z):
        figure = zs.plot_1D(figure, map_int[1+i, :], 50, replace=i==0, profile_name="z pos #" + str(i+1))

    layout.addWidget(figure)
    layout.addWidget(zs.plot_2D(None, map_int[4, :], 50))
    layout.addWidget(zs.plot_3D(None, map_int[2, :], 50))

    container.setLayout(layout)
    container.show()

    app.exec_()
