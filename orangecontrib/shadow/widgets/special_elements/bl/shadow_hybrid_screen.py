#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------- #
# Copyright (c) 2023, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2023. UChicago Argonne, LLC. This software was produced       #
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
# ----------------------------------------------------------------------- #
from oasys.widgets import congruence
from oasys.util.oasys_util import read_surface_file

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowPhysics, ShadowPreProcessor

from hybrid_methods.coherence.hybrid_screen import *

IMPLEMENTATION = "SHADOW3"

# -------------------------------------------------------------
# RAY-TRACING WRAPPERS
# -------------------------------------------------------------

class ShadowHybridBeam(HybridBeamWrapper):
    def __init__(self, beam : ShadowBeam, length_units):
        super(ShadowHybridBeam, self).__init__(beam, length_units)

    def duplicate(self): return ShadowHybridBeam(self.wrapped_beam.duplicate(), self.length_units)

class ShadowHybridOE(HybridOEWrapper):
    def __init__(self, optical_element, name):
        super(ShadowHybridOE, self).__init__(optical_element, name)

    def check_congruence(self, calculation_type : int):
        if   calculation_type == HybridCalculationType.SIMPLE_APERTURE                and not ("ScreenSlits" in self.name):                       raise Exception("Simple Aperture calculation runs for Screen-Slits widgets only")
        elif calculation_type == HybridCalculationType.MIRROR_OR_GRATING_SIZE         and not ("Mirror" in self.name or "Grating" in self.name): raise Exception("Mirror/Grating calculation runs for Mirror/Grating widgets only")
        elif calculation_type == HybridCalculationType.MIRROR_SIZE_AND_ERROR_PROFILE  and not ("Mirror" in self.name):                            raise Exception("Mirror calculation runs for Mirror widgets only")
        elif calculation_type == HybridCalculationType.GRATING_SIZE_AND_ERROR_PROFILE and not ("Grating" in self.name):                           raise Exception("Grating calculation runs for Mirror widgets only")
        elif calculation_type in [HybridCalculationType.CRL_SIZE, HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE] and \
                not ("Lens" in self.name or "CRL" in self.name or "Transfocator" in self.name):                                                 raise Exception("CRL calculation runs for Lens, CRLs or Transfocators widgets only")
        
        shadow_oe = self.wrapped_optical_element
        
        if calculation_type in [HybridCalculationType.GRATING_SIZE_AND_ERROR_PROFILE, HybridCalculationType.MIRROR_SIZE_AND_ERROR_PROFILE]:
            if shadow_oe._oe.F_RIPPLE == 1 and shadow_oe._oe.F_G_S == 2: shadow_oe._oe.F_RIPPLE = 0 # disable slope error calculation for OE, must be done by HYBRID!
            else:                                                        raise Exception("O.E. has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")
        elif calculation_type == HybridCalculationType.MIRROR_OR_GRATING_SIZE: # ADDED BY XIANBO SHI
            shadow_oe._oe.F_RIPPLE = 0 # better safe than sorry

    def duplicate(self): return ShadowHybridOE(self.wrapped_optical_element.duplicate(), self.name)

# -------------------------------------------------------------
# HYBRID SCREENS HELPER CLASSES
# -------------------------------------------------------------

class _ShadowOEHybridScreen():
    NPOLY_ANGLE = 3
    NPOLY_L     = 6

    def _no_lost_rays_from_oe(self, input_parameters : HybridInputParameters):
        shadow_beam   = input_parameters.beam.wrapped_beam
        history_entry = shadow_beam.getOEHistory(shadow_beam._oe_number)

        beam_after = shadow_beam
        beam_before = history_entry._input_beam

        number_of_good_rays_before = len(beam_before._beam.rays[numpy.where(beam_before._beam.rays[:, 9] == 1)])
        number_of_good_rays_after = len(beam_after._beam.rays[numpy.where(beam_after._beam.rays[:, 9] == 1)])

        return number_of_good_rays_before == number_of_good_rays_after

    def _extract_calculation_parameters(self, input_parameters: HybridInputParameters):
        calculation_parameters = self._check_compound_oe(input_parameters)

        input_shadow_beam = calculation_parameters.get("shadow_beam")

        # Before ray-tracing save the original history:
        calculation_parameters.set("original_beam_history", input_shadow_beam.getOEHistory())

        history_entry = input_shadow_beam.getOEHistory(input_shadow_beam._oe_number)
    
        shadow_oe            = history_entry._shadow_oe_start.duplicate()  # no changes to the original object!
        shadow_oe_input_beam = history_entry._input_beam.duplicate(history=False)

        hybrid_screen_file_name = self._set_hybrid_screen(input_parameters, shadow_oe)

        # tracing must be done without o.e. movements: hybrid is going to take care of that
        x_rot = shadow_oe._oe.X_ROT
        y_rot = shadow_oe._oe.Y_ROT
        z_rot = shadow_oe._oe.Z_ROT

        shadow_oe._oe.X_ROT = 0.0
        shadow_oe._oe.Y_ROT = 0.0
        shadow_oe._oe.Z_ROT = 0.0

        input_parameters.listener.status_message("Creating HYBRID screen: redo simulation with modified O.E.")

        shadow_beam_at_image_plane = ShadowBeam.traceFromOE(shadow_oe_input_beam, shadow_oe, history=False)

        # restore o.e. setting for further calculations
        shadow_oe._oe.X_ROT = x_rot
        shadow_oe._oe.Y_ROT = y_rot
        shadow_oe._oe.Z_ROT = z_rot

        calculation_parameters.set("shadow_beam", shadow_beam_at_image_plane)

        image_beam, image_beam_lo = self._process_shadow_beam(shadow_beam_at_image_plane, lost=True)  # xshi change from 0 to 1
        image_beam.set_initial_flux(input_parameters.original_beam.wrapped_beam.get_initial_flux())

        calculation_parameters.set("shadow_oe_end",  shadow_oe)
        calculation_parameters.set("image_plane_beam",  image_beam)
        calculation_parameters.set("image_plane_beam_lost", image_beam_lo)

        # read shadow screen file
        screen_beam = self._read_shadow_file(hybrid_screen_file_name)

        calculation_parameters.set("screen_plane_beam",  screen_beam)

        energy     =     ShadowPhysics.getEnergyFromShadowK(screen_beam._beam.rays[:, 10])
        wavelength = ShadowPhysics.getWavelengthFromShadowK(screen_beam._beam.rays[:, 10])

        input_parameters.listener.status_message("Using MEAN photon energy [eV]:" + str(numpy.average(energy)))

        xx_screen = screen_beam._beam.rays[:, 0]
        zz_screen = screen_beam._beam.rays[:, 2]
        xp_screen = screen_beam._beam.rays[:, 3]
        yp_screen = screen_beam._beam.rays[:, 4]
        zp_screen = screen_beam._beam.rays[:, 5]

        x_min     = numpy.min(xx_screen)
        x_max     = numpy.max(xx_screen)
        z_min     = numpy.min(zz_screen)
        z_max     = numpy.max(zz_screen)
        dx_ray    = numpy.arctan(xp_screen / yp_screen)  # calculate divergence from direction cosines from SHADOW file  dx = atan(v_x/v_y)
        dz_ray    = numpy.arctan(zp_screen / yp_screen)  # calculate divergence from direction cosines from SHADOW file  dz = atan(v_z/v_y)

        calculation_parameters.set("energy",     energy)
        calculation_parameters.set("wavelength", wavelength)
        calculation_parameters.set("xp_screen",  xp_screen)
        calculation_parameters.set("yp_screen",  yp_screen)
        calculation_parameters.set("zp_screen",  zp_screen)
        calculation_parameters.set("xx_screen",  xx_screen)
        calculation_parameters.set("zz_screen",  zz_screen)
        calculation_parameters.set("x_min",      x_min)
        calculation_parameters.set("x_max",      x_max)
        calculation_parameters.set("z_min",      z_min)
        calculation_parameters.set("z_max",      z_max)
        calculation_parameters.set("dx_ray",     dx_ray)
        calculation_parameters.set("dz_ray",     dz_ray)

        self._extract_specific_calculation_parameters(input_parameters, calculation_parameters)

        return calculation_parameters

    def _set_hybrid_screen(self, input_parameters, shadow_oe):
        # Set Hybrid Screen
        if shadow_oe._oe.F_SCREEN == 1:
            if shadow_oe._oe.N_SCREEN == 10: raise Exception("Hybrid Screen has not been created: O.E. has already 10 screens")

            n_screen = shadow_oe._oe.N_SCREEN + 1
            i_screen = shadow_oe._oe.I_SCREEN
            sl_dis = shadow_oe._oe.I_ABS
            i_abs = shadow_oe._oe.SL_DIS
            i_slit = shadow_oe._oe.I_SLIT
            i_stop = shadow_oe._oe.I_STOP
            k_slit = shadow_oe._oe.K_SLIT
            thick = shadow_oe._oe.THICK
            file_abs = numpy.copy(shadow_oe._oe.FILE_ABS)
            rx_slit = shadow_oe._oe.RX_SLIT
            rz_slit = shadow_oe._oe.RZ_SLIT
            cx_slit = shadow_oe._oe.CX_SLIT
            cz_slit = shadow_oe._oe.CZ_SLIT
            file_scr_ext = numpy.copy(shadow_oe._oe.FILE_SCR_EXT)

            screen_index = n_screen - 1

            i_screen[screen_index] = 0
            sl_dis[screen_index] = 0
            i_abs[screen_index] = 0
            i_slit[screen_index] = 0
            i_stop[screen_index] = 0
            k_slit[screen_index] = 0
            thick[screen_index] = 0
            rx_slit[screen_index] = 0
            rz_slit[screen_index] = 0
            cx_slit[screen_index] = 0
            cz_slit[screen_index] = 0
        else:
            n_screen = 1
            i_screen = numpy.zeros(10)  # after
            i_abs = numpy.zeros(10)
            i_slit = numpy.zeros(10)
            i_stop = numpy.zeros(10)
            k_slit = numpy.zeros(10)
            thick = numpy.zeros(10)
            file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
            rx_slit = numpy.zeros(10)
            rz_slit = numpy.zeros(10)
            sl_dis = numpy.zeros(10)
            file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
            cx_slit = numpy.zeros(10)
            cz_slit = numpy.zeros(10)

            screen_index = 0
        shadow_oe._oe.set_screens(n_screen,
                                  i_screen,
                                  i_abs,
                                  sl_dis,
                                  i_slit,
                                  i_stop,
                                  k_slit,
                                  thick,
                                  file_abs,
                                  rx_slit,
                                  rz_slit,
                                  cx_slit,
                                  cz_slit,
                                  file_scr_ext)
        self._fix_specific_oe_attributes(shadow_oe, input_parameters.optical_element.wrapped_optical_element, screen_index)

        return "screen." + self._get_oe_string(input_parameters) + ("0" + str(n_screen)) if n_screen < 10 else "10"

    def _check_compound_oe(self, input_parameters: HybridInputParameters): 
        calculation_parameters = AbstractHybridScreen.HybridCalculationParameters()
        calculation_parameters.set("shadow_beam", input_parameters.beam.wrapped_beam)
        
        return calculation_parameters
    
    def _fix_specific_oe_attributes(self, shadow_oe, original_shadow_oe, screen_index):
        # for all except aperture types
        if shadow_oe._oe.FWRITE > 1 or shadow_oe._oe.F_ANGLE == 0:
            shadow_oe._oe.FWRITE  = 0  # all
            shadow_oe._oe.F_ANGLE = 1  # angles

    def _extract_specific_calculation_parameters(self, input_parameters, calculation_parameters): pass

    @staticmethod
    def _get_oe_string(input_parameters):
        oe_number = input_parameters.beam.wrapped_beam._oe_number

        str_n_oe = str(oe_number)
        if oe_number < 10: str_n_oe = "0" + str_n_oe

        return str_n_oe

    @staticmethod
    def _process_shadow_beam(shadow_beam, lost=False):
        cursor_go = numpy.where(shadow_beam._beam.rays[:, 9] == 1)
    
        image_beam_rays = copy.deepcopy(shadow_beam._beam.rays[cursor_go])
        image_beam_rays[:, 11] = numpy.arange(1, len(image_beam_rays) + 1, 1)
    
        out_beam_go = ShadowBeam()
        out_beam_go._beam.rays = image_beam_rays
    
        if lost:
            cursor_lo = numpy.where(shadow_beam._beam.rays[:, 9] != 1)
    
            lost_rays = copy.deepcopy(shadow_beam._beam.rays[cursor_lo])
            lost_rays[:, 11] = numpy.arange(1, len(lost_rays) + 1, 1)
    
            out_beam_lo = ShadowBeam()
            out_beam_lo._beam.rays = lost_rays
    
            return out_beam_go, out_beam_lo
        else:
            return out_beam_go
        
    @staticmethod
    def _read_shadow_file(file_name):
        image_beam = ShadowBeam()
        image_beam.loadFromFile(congruence.checkFile(file_name))
    
        return _ShadowOEHybridScreen._process_shadow_beam(image_beam)


class _ShadowApertureHybridScreen(_ShadowOEHybridScreen):
    def _fix_specific_oe_attributes(self, shadow_oe, original_shadow_oe, screen_index):
        if (original_shadow_oe._oe.FMIRR == 5 and \
            original_shadow_oe._oe.F_CRYSTAL == 0 and \
            original_shadow_oe._oe.F_REFRAC == 2 and \
            original_shadow_oe._oe.F_SCREEN==1 and \
            original_shadow_oe._oe.N_SCREEN==1):

            shadow_oe._oe.I_ABS[screen_index] = original_shadow_oe._oe.I_ABS[screen_index]
            shadow_oe._oe.I_SLIT[screen_index] = original_shadow_oe._oe.I_SLIT[screen_index]

            if original_shadow_oe._oe.I_SLIT[screen_index] == 1:
                shadow_oe._oe.I_STOP[screen_index] = original_shadow_oe._oe.I_STOP[screen_index]
                shadow_oe._oe.K_SLIT[screen_index] = original_shadow_oe._oe.K_SLIT[screen_index]

                if original_shadow_oe._oe.K_SLIT[screen_index] == 2:
                    shadow_oe._oe.FILE_SCR_EXT[screen_index] = original_shadow_oe._oe.FILE_SCR_EXT[screen_index]
                else:
                    shadow_oe._oe.RX_SLIT[screen_index] = original_shadow_oe._oe.RX_SLIT[screen_index]
                    shadow_oe._oe.RZ_SLIT[screen_index] = original_shadow_oe._oe.RZ_SLIT[screen_index]
                    shadow_oe._oe.CX_SLIT[screen_index] = original_shadow_oe._oe.CX_SLIT[screen_index]
                    shadow_oe._oe.CZ_SLIT[screen_index] = original_shadow_oe._oe.CZ_SLIT[screen_index]

            if original_shadow_oe._oe.I_ABS[screen_index] == 1:
                shadow_oe._oe.THICK[screen_index] = original_shadow_oe._oe.THICK[screen_index]
                shadow_oe._oe.FILE_ABS[screen_index] = original_shadow_oe._oe.FILE_ABS[screen_index]
        else:
            raise Exception("Connected O.E. is not a Screen-Slit or CRL widget!")

class _ShadowOEWithSurfaceHybridScreen(_ShadowOEHybridScreen):
    def _check_oe_displacements(self, input_parameters: HybridInputParameters):
        shadow_oe = input_parameters.optical_element.wrapped_optical_element
        diffraction_plane = input_parameters.diffraction_plane

        if shadow_oe._oe.F_MOVE == 1:
            if diffraction_plane == HybridDiffractionPlane.SAGITTAL:  # X
                if shadow_oe._oe.X_ROT != 0.0 or shadow_oe._oe.Z_ROT != 0.0: raise Exception("Only rotations around the Y axis are supported for sagittal diffraction plane")
            elif (diffraction_plane == HybridDiffractionPlane.TANGENTIAL or diffraction_plane == HybridDiffractionPlane.BOTH_2D):  # Z
                if shadow_oe._oe.Y_ROT != 0.0 or shadow_oe._oe.Z_ROT != 0.0: raise Exception("Only rotations around the X axis are supported for tangential or Both (2D) diffraction planes")
            elif diffraction_plane == HybridDiffractionPlane.BOTH_2X1D:  # Z
                if shadow_oe._oe.Z_ROT != 0.0:                               raise Exception("Only rotations around the X and Y axis are supported for Both (1D+1D) diffraction planes")

    def _calculate_geometrical_parameters(self, input_parameters: HybridInputParameters):
        geometrical_parameters = ShadowSimpleApertureHybridScreen.GeometricalParameters()

        beam_after = input_parameters.beam.wrapped_beam
        history_entry = beam_after.getOEHistory(beam_after._oe_number)

        beam_before = history_entry._input_beam.duplicate()
        oe_before = history_entry._shadow_oe_start.duplicate()

        if oe_before._oe.FHIT_C == 0:  # infinite
            geometrical_parameters.is_infinite = True
        else:
            str_n_oe = str(input_parameters.beam.wrapped_beam._oe_number)
            if input_parameters.beam.wrapped_beam._oe_number < 10: str_n_oe = "0" + str_n_oe

            beam_before._beam.rays = beam_before._beam.rays[numpy.where(beam_before._beam.rays[:, 9] == 1)]  # GOOD ONLY BEFORE THE BEAM

            oe_before._oe.FWRITE = 1
            mirror_beam = ShadowBeam.traceFromOE(beam_before, oe_before, history=False)
            mirror_beam.loadFromFile("mirr." + str_n_oe)

            geometrical_parameters.max_tangential = oe_before._oe.RLEN1
            geometrical_parameters.min_tangential = oe_before._oe.RLEN2
            geometrical_parameters.max_sagittal = oe_before._oe.RWIDX1
            geometrical_parameters.min_sagittal = oe_before._oe.RWIDX2
            geometrical_parameters.ticket_tangential = mirror_beam._beam.histo1(2, nbins=500, nolost=0, ref=23)  # ALL THE RAYS FOR ANALYSIS
            geometrical_parameters.ticket_sagittal = mirror_beam._beam.histo1(1, nbins=500, nolost=0, ref=23)  # ALL THE RAYS  FOR ANALYSIS

        return geometrical_parameters

    def _fix_specific_oe_attributes(self, shadow_oe, original_shadow_oe, screen_index):
        super(_ShadowOEWithSurfaceHybridScreen, self)._fix_specific_oe_attributes(shadow_oe, original_shadow_oe, screen_index)
        shadow_oe._oe.F_RIPPLE = 0

    def _extract_specific_calculation_parameters(self, input_parameters, calculation_parameters):
        mirror_beam = self._read_shadow_file("mirr." + self._get_oe_string(input_parameters))

        xx_mirr = mirror_beam._beam.rays[:, 0]
        yy_mirr = mirror_beam._beam.rays[:, 1]

        # read in angle files
        angle_inc, angle_ref = self.read_shadow_angles("angle." + self._get_oe_string(input_parameters), mirror_beam)

        calculation_parameters.set("angle_inc", angle_inc)
        calculation_parameters.set("angle_ref", angle_ref)

        xx_screen = calculation_parameters.get("xx_screen")
        zz_screen = calculation_parameters.get("zz_screen")

        # generate theta(z) and l(z) curve over a continuous grid
        if numpy.amax(xx_screen) == numpy.amin(xx_screen):
            if input_parameters.diffraction_plane in [HybridDiffractionPlane.SAGITTAL, HybridDiffractionPlane.BOTH_2D, HybridDiffractionPlane.BOTH_2X1D]:
                raise Exception("Inconsistent calculation: Diffraction plane is set on SAGITTAL, but the beam has no extension in that direction")
        else:
            calculation_parameters.set("wangle_x", numpy.poly1d(numpy.polyfit(xx_screen, angle_inc, self.NPOLY_ANGLE)))
            calculation_parameters.set("wl_x",     numpy.poly1d(numpy.polyfit(xx_screen, xx_mirr,   self.NPOLY_L)))

        if numpy.amax(zz_screen) == numpy.amin(zz_screen):
            if input_parameters.diffraction_plane in [HybridDiffractionPlane.TANGENTIAL, HybridDiffractionPlane.BOTH_2D, HybridDiffractionPlane.BOTH_2X1D]:
                raise Exception("Inconsistent calculation: Diffraction plane is set on TANGENTIAL, but the beam has no extension in that direction")
        else:
            calculation_parameters.set("wangle_z", numpy.poly1d(numpy.polyfit(zz_screen, angle_inc, self.NPOLY_ANGLE)))
            calculation_parameters.set("wl_z",     numpy.poly1d(numpy.polyfit(zz_screen, yy_mirr,   self.NPOLY_L)))

    @staticmethod
    def read_shadow_angles(filename, mirror_beam=None):
        values    = numpy.loadtxt(congruence.checkFile(filename))
        dimension = len(mirror_beam._beam.rays)

        angle_inc = numpy.zeros(dimension)
        angle_ref = numpy.zeros(dimension)

        ray_index = 0
        for index in range(0, len(values)):
            if values[index, 3] == 1:
                angle_inc[ray_index] = values[index, 1]
                angle_ref[ray_index] = values[index, 2]

                ray_index += 1

        angle_inc = (90.0 - angle_inc)/180.0*1e3*numpy.pi
        angle_ref = (90.0 - angle_ref)/180.0*1e3*numpy.pi

        return angle_inc, angle_ref

class _ShadowOEWithSurfaceAndErrorHybridScreen(_ShadowOEWithSurfaceHybridScreen):
    def _fix_specific_oe_attributes(self, shadow_oe, original_shadow_oe, screen_index):
        super(_ShadowOEWithSurfaceHybridScreen, self)._fix_specific_oe_attributes(shadow_oe, original_shadow_oe, screen_index)
        # disable slope error calculation for OE, must be done by HYBRID!
        if shadow_oe._oe.F_RIPPLE == 1 and shadow_oe._oe.F_G_S == 2: shadow_oe._oe.F_RIPPLE = 0
        else: raise Exception("O.E. has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")

    def _extract_specific_calculation_parameters(self, input_parameters, calculation_parameters):
        super(_ShadowOEWithSurfaceAndErrorHybridScreen, self)._extract_specific_calculation_parameters(input_parameters, calculation_parameters)

        calculation_parameters.set("w_mirr_2D_values", self._read_shadow_surface(input_parameters.optical_element.wrapped_optical_element._oe.FILE_RIP, dimension=2))
    
    @staticmethod
    def _read_shadow_surface(filename, dimension):
        if dimension == 1:
            values = numpy.loadtxt(congruence.checkFile(filename))
    
            return ScaledArray(values[:, 1], values[:, 0])
        elif dimension == 2:
            x_coords, y_coords, z_values = ShadowPreProcessor.read_surface_error_file(filename)
    
            return ScaledMatrix(x_coords, y_coords, z_values)


class _ShadowOELensHybridScreen(_ShadowApertureHybridScreen):
    def _check_oe_displacements(self, input_parameters : HybridInputParameters): pass

    def _calculate_geometrical_parameters(self, input_parameters: HybridInputParameters):
        geometrical_parameters = ShadowSimpleApertureHybridScreen.GeometricalParameters()

        beam_after    = input_parameters.beam.wrapped_beam
        history_entry = beam_after.getOEHistory(beam_after._oe_number)
        beam_before   = history_entry._input_beam

        oes_list = history_entry._shadow_oe_end._oe.list

        beam_at_the_slit = beam_before.duplicate(history=False)
        beam_at_the_slit._beam.retrace(oes_list[0].T_SOURCE)  # TRACE INCIDENT BEAM UP TO THE SLIT

        is_infinite = True
        max_tangential_list = []
        min_tangential_list = []
        max_sagittal_list = []
        min_sagittal_list = []
        for oe in oes_list:
            if oe.FHIT_C == 1:
                is_infinite = False

                max_tangential_list.append(numpy.abs(oe.RLEN2))
                min_tangential_list.append(-numpy.abs(oe.RLEN2))
                max_sagittal_list.append(numpy.abs(oe.RWIDX2))
                min_sagittal_list.append(-numpy.abs(oe.RWIDX2))

        if not is_infinite:
            geometrical_parameters.max_tangential = numpy.min(max_tangential_list)
            geometrical_parameters.min_tangential = numpy.max(min_tangential_list)
            geometrical_parameters.max_sagittal   = numpy.min(max_sagittal_list)
            geometrical_parameters.min_sagittal   = numpy.max(min_sagittal_list)

        geometrical_parameters.is_infinite = is_infinite

        geometrical_parameters.ticket_tangential = beam_at_the_slit._beam.histo1(3, nbins=500, nolost=1, ref=23)
        geometrical_parameters.ticket_sagittal   = beam_at_the_slit._beam.histo1(1, nbins=500, nolost=1, ref=23)

        return geometrical_parameters

    def _check_compound_oe(self, input_parameters: HybridInputParameters):
        calculation_parameters = AbstractHybridScreen.HybridCalculationParameters()
        
        history_entry = input_parameters.beam.wrapped_beam.getOEHistory(input_parameters.beam.wrapped_beam._oe_number)
        compound_oe = history_entry._shadow_oe_end

        for oe in compound_oe._oe.list:
            if oe.FHIT_C == 0: raise Exception("Calculation not possible: at least one lens have infinite diameter")

        last_oe = compound_oe._oe.list[-1]

        image_plane_distance = last_oe.T_IMAGE

        screen_slit = ShadowOpticalElement.create_screen_slit()

        screen_slit._oe.DUMMY        = input_parameters.beam.length_units_to_m*100.0 # units to CM 
        screen_slit._oe.T_SOURCE     = -image_plane_distance
        screen_slit._oe.T_IMAGE      = image_plane_distance
        screen_slit._oe.T_INCIDENCE  = 0.0
        screen_slit._oe.T_REFLECTION = 180.0
        screen_slit._oe.ALPHA        = 0.0

        n_screen = 1
        i_screen = numpy.zeros(10)  # after
        i_abs = numpy.zeros(10)
        i_slit = numpy.zeros(10)
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        i_slit[0] = 1
        k_slit[0] = 1

        rx_slit[0] = numpy.abs(2 * last_oe.RWIDX2)
        rz_slit[0] = numpy.abs(2 * last_oe.RLEN2)

        screen_slit._oe.set_screens(n_screen,
                                    i_screen,
                                    i_abs,
                                    sl_dis,
                                    i_slit,
                                    i_stop,
                                    k_slit,
                                    thick,
                                    file_abs,
                                    rx_slit,
                                    rz_slit,
                                    cx_slit,
                                    cz_slit,
                                    file_scr_ext)
        
        # in case of CRL, regeneration of the input beam as incident on the last lens
        calculation_parameters.set("shadow_beam", ShadowBeam.traceFromOE(input_parameters.beam.wrapped_beam, screen_slit))
        
        return calculation_parameters

# -------------------------------------------------------------
# HYBRID SCREENS IMPLEMENTATION CLASSES
# -------------------------------------------------------------

class ShadowSimpleApertureHybridScreen(_ShadowApertureHybridScreen, AbstractSimpleApertureHybridScreen):
    def __init__(self, wave_optics_provider : HybridWaveOpticsProvider):
        AbstractSimpleApertureHybridScreen.__init__(self, wave_optics_provider)
    
    def _check_oe_displacements(self, input_parameters : HybridInputParameters):
        shadow_oe = input_parameters.optical_element.wrapped_optical_element
        if shadow_oe._oe.F_MOVE == 1: raise Exception("O.E. Movements are not supported for this kind of calculation")

    def _calculate_geometrical_parameters(self, input_parameters: HybridInputParameters):
        geometrical_parameters = ShadowSimpleApertureHybridScreen.GeometricalParameters()

        beam_after    = input_parameters.beam.wrapped_beam
        history_entry = beam_after.getOEHistory(beam_after._oe_number)

        beam_before = history_entry._input_beam
        oe_before = history_entry._shadow_oe_start

        if oe_before._oe.I_SLIT[0] == 0:
            geometrical_parameters.is_infinite = True
        else:
            if oe_before._oe.I_STOP[0] == 1: raise Exception("Simple Aperture calculation runs for apertures only")

            beam_at_the_slit = beam_before.duplicate(history=False)
            beam_at_the_slit._beam.retrace(oe_before._oe.T_SOURCE)  # TRACE INCIDENT BEAM UP TO THE SLIT

            # TODO: MANAGE CASE OF ROTATED SLITS (OE MOVEMENT OR SOURCE MOVEMENT)
            geometrical_parameters.max_tangential    = oe_before._oe.CZ_SLIT[0] + oe_before._oe.RZ_SLIT[0] / 2
            geometrical_parameters.min_tangential    = oe_before._oe.CZ_SLIT[0] - oe_before._oe.RZ_SLIT[0] / 2
            geometrical_parameters.max_sagittal      = oe_before._oe.CX_SLIT[0] + oe_before._oe.RX_SLIT[0] / 2
            geometrical_parameters.min_sagittal      = oe_before._oe.CX_SLIT[0] - oe_before._oe.RX_SLIT[0] / 2
            geometrical_parameters.ticket_tangential = beam_at_the_slit._beam.histo1(3, nbins=500, nolost=1, ref=23)
            geometrical_parameters.ticket_sagittal   = beam_at_the_slit._beam.histo1(1, nbins=500, nolost=1, ref=23)

        return geometrical_parameters

class ShadowMirrorOrGratingSizeHybridScreen(_ShadowOEWithSurfaceHybridScreen, AbstractMirrorOrGratingSizeHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractMirrorOrGratingSizeHybridScreen.__init__(self, wave_optics_provider)

class ShadowMirrorSizeAndErrorHybridScreen(_ShadowOEWithSurfaceHybridScreen, AbstractMirrorSizeAndErrorHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractMirrorSizeAndErrorHybridScreen.__init__(self, wave_optics_provider)

class ShadowGratingSizeAndErrorHybridScreen(_ShadowOEWithSurfaceHybridScreen, AbstractGratingSizeAndErrorHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractGratingSizeAndErrorHybridScreen.__init__(self, wave_optics_provider)

    def _extract_specific_calculation_parameters(self, input_parameters, calculation_parameters):
        super(ShadowGratingSizeAndErrorHybridScreen, self)._extract_specific_calculation_parameters(input_parameters, calculation_parameters)

        angle_ref = calculation_parameters.get("angle_ref")
        xx_screen = calculation_parameters.get("xx_screen")
        zz_screen = calculation_parameters.get("zz_screen")

        calculation_parameters.set("wangle_ref_x",  numpy.poly1d(numpy.polyfit(xx_screen, angle_ref, self.NPOLY_ANGLE)))
        calculation_parameters.set("wangle_ref_z",  numpy.poly1d(numpy.polyfit(zz_screen, angle_ref, self.NPOLY_ANGLE)))

class ShadowCRLSizeHybridScreen(_ShadowOELensHybridScreen, AbstractCRLSizeHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractCRLSizeHybridScreen.__init__(self, wave_optics_provider)

class ShadowCRLSizeAndErrorHybridScreen(_ShadowOELensHybridScreen, AbstractCRLSizeAndErrorHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractCRLSizeAndErrorHybridScreen.__init__(self, wave_optics_provider)

    def _extract_specific_calculation_parameters(self, input_parameters, calculation_parameters):
        calculation_parameters.set("w_mirr_2D_values", [self._read_oasys_surface(thickness_error_file) for thickness_error_file in input_parameters.get("crl_error_profiles")])
    
    @staticmethod
    def _read_oasys_surface(filename):
        x_coords, y_coords, z_values = read_surface_file(filename)
    
        return ScaledMatrix(x_coords, y_coords, z_values.T)




# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------
# FACTORY METHOD INITIALIZATION
# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

try:
    hsm = HybridScreenManager.Instance()
    hsm.add_hybrid_screen_class(IMPLEMENTATION, ShadowSimpleApertureHybridScreen)
    hsm.add_hybrid_screen_class(IMPLEMENTATION, ShadowMirrorOrGratingSizeHybridScreen)
    hsm.add_hybrid_screen_class(IMPLEMENTATION, ShadowMirrorSizeAndErrorHybridScreen)
    hsm.add_hybrid_screen_class(IMPLEMENTATION, ShadowGratingSizeAndErrorHybridScreen)
    hsm.add_hybrid_screen_class(IMPLEMENTATION, ShadowCRLSizeHybridScreen)
    hsm.add_hybrid_screen_class(IMPLEMENTATION, ShadowCRLSizeAndErrorHybridScreen)
except Exception as e:
    print(e)
