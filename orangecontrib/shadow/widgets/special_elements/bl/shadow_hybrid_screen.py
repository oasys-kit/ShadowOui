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
from typing import Tuple, Union

from oasys.widgets import congruence
from oasys.util.oasys_util import read_surface_file

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement, ShadowCompoundOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowPhysics, ShadowPreProcessor

from hybrid_methods.coherence.hybrid_screen import *

IMPLEMENTATION = "SHADOW3"

# -------------------------------------------------------------
# RAY-TRACING WRAPPERS
# -------------------------------------------------------------

class ShadowHybridBeam(HybridBeamWrapper):
    def __init__(self, beam : Union[ShadowBeam, Tuple[ShadowBeam, ShadowBeam]], length_units=HybridLengthUnits.MILLIMETERS, **kwargs):
        super(ShadowHybridBeam, self).__init__(beam, length_units, **kwargs)

    def duplicate(self, **kwargs):
        if isinstance(self.wrapped_beam, ShadowBeam): return ShadowHybridBeam(self.wrapped_beam.duplicate(**kwargs), self.length_units)
        else:                                         return ShadowHybridBeam([wb.duplicate(**kwargs) for wb in self.wrapped_beam], self.length_units)

class ShadowHybridOE(HybridOEWrapper):
    def __init__(self, optical_element: Union[Union[ShadowOpticalElement, ShadowCompoundOpticalElement], 
                                              Tuple[Union[ShadowOpticalElement, ShadowCompoundOpticalElement], 
                                                    Union[ShadowOpticalElement, ShadowCompoundOpticalElement]]], name, **kwargs):
        if isinstance(optical_element, list): super(ShadowHybridOE, self).__init__(optical_element, name="KB" if name is None else name, **kwargs)
        else:                                 super(ShadowHybridOE, self).__init__(optical_element, name=name, **kwargs)

    def check_congruence(self, calculation_type : int):
        if   calculation_type == HybridCalculationType.SIMPLE_APERTURE                and not ("ScreenSlits" in self.name):                       raise Exception("Simple Aperture calculation runs for Screen-Slits widgets only")
        elif calculation_type == HybridCalculationType.MIRROR_OR_GRATING_SIZE         and not ("Mirror" in self.name or "Grating" in self.name): raise Exception("Mirror/Grating calculation runs for Mirror/Grating widgets only")
        elif calculation_type == HybridCalculationType.MIRROR_SIZE_AND_ERROR_PROFILE  and not ("Mirror" in self.name):                            raise Exception("Mirror calculation runs for Mirror widgets only")
        elif calculation_type == HybridCalculationType.GRATING_SIZE_AND_ERROR_PROFILE and not ("Grating" in self.name):                           raise Exception("Grating calculation runs for Grating widgets only")
        elif calculation_type in [HybridCalculationType.CRL_SIZE, HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE] and \
                not ("Lens" in self.name or "CRL" in self.name or "Transfocator" in self.name):                                                 raise Exception("CRL calculation runs for Lens, CRLs or Transfocators widgets only")
        elif calculation_type in [HybridCalculationType.KB_SIZE, HybridCalculationType.KB_SIZE_AND_ERROR_PROFILE] and  not ("KB" in self.name): raise Exception("KB calculation runs for a pair of mirrors widgets only")
        
        shadow_oe = self.wrapped_optical_element
        
        if calculation_type in [HybridCalculationType.GRATING_SIZE_AND_ERROR_PROFILE, HybridCalculationType.MIRROR_SIZE_AND_ERROR_PROFILE]:
            if shadow_oe._oe.F_RIPPLE == 1 and shadow_oe._oe.F_G_S == 2: shadow_oe._oe.F_RIPPLE = 0 # disable slope error calculation for OE, must be done by HYBRID!
            else:                                                        raise Exception("O.E. has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")
        elif calculation_type == HybridCalculationType.KB_SIZE_AND_ERROR_PROFILE:
            kb_1 = shadow_oe[0]
            kb_2 = shadow_oe[1]
            
            if kb_1._oe.F_RIPPLE == 1 and kb_1._oe.F_G_S == 2: kb_1._oe.F_RIPPLE = 0 # disable slope error calculation for OE, must be done by HYBRID!
            else:                                              raise Exception("KB1 has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")
            if kb_2._oe.F_RIPPLE == 1 and kb_2._oe.F_G_S == 2: kb_2._oe.F_RIPPLE = 0 # disable slope error calculation for OE, must be done by HYBRID!
            else:                                              raise Exception("KB2 has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")
        elif calculation_type == HybridCalculationType.MIRROR_OR_GRATING_SIZE: # ADDED BY XIANBO SHI
            shadow_oe._oe.F_RIPPLE = 0 # better safe than sorry

    def duplicate(self, **kwargs):
        if isinstance(self.wrapped_optical_element, list): return ShadowHybridOE([wo.duplicate(**kwargs) for wo in self.wrapped_optical_element], self.name)
        else:                                              return ShadowHybridOE(self.wrapped_optical_element.duplicate(**kwargs), self.name)

# -------------------------------------------------------------
# HYBRID SCREENS HELPER CLASSES
# -------------------------------------------------------------

class _ShadowOEHybridScreen():
    NPOLY_ANGLE = 3
    NPOLY_L     = 6

    def _set_image_distance_from_optical_element(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters):
        shadow_oe = input_parameters.optical_element.wrapped_optical_element
        to_m      = input_parameters.beam.length_units_to_m

        calculation_parameters.image_plane_distance = shadow_oe._oe.T_IMAGE * to_m

    def _no_lost_rays_from_oe(self, input_parameters : HybridInputParameters) -> bool:
        shadow_beam   = input_parameters.beam.wrapped_beam
        history_entry = shadow_beam.getOEHistory(shadow_beam._oe_number)

        beam_after = shadow_beam
        beam_before = history_entry._input_beam

        number_of_good_rays_before = len(beam_before._beam.rays[numpy.where(beam_before._beam.rays[:, 9] == 1)])
        number_of_good_rays_after  = len(beam_after._beam.rays[numpy.where(beam_after._beam.rays[:, 9] == 1)])

        return number_of_good_rays_before == number_of_good_rays_after

    def _manage_common_initial_screen_projection_data(self, input_parameters: HybridInputParameters, calculation_parameters: AbstractHybridScreen.CalculationParameters):
        self._check_compound_oe(input_parameters, calculation_parameters)

        input_shadow_beam = calculation_parameters.get("shadow_beam")

        # Before ray-tracing save the original history:
        calculation_parameters.set("original_beam_history", input_shadow_beam.getOEHistory())

        history_entry = input_shadow_beam.getOEHistory(input_shadow_beam._oe_number)

        shadow_oe            = history_entry._shadow_oe_start.duplicate()  # no changes to the original object!
        shadow_oe_input_beam = history_entry._input_beam.duplicate(history=False)

        # tracing must be done without o.e. movements: hybrid is going to take care of that
        x_rot                = shadow_oe._oe.X_ROT
        y_rot                = shadow_oe._oe.Y_ROT
        z_rot                = shadow_oe._oe.Z_ROT

        shadow_oe._oe.X_ROT   = 0.0
        shadow_oe._oe.Y_ROT   = 0.0
        shadow_oe._oe.Z_ROT   = 0.0

        self._fix_specific_oe_attributes(shadow_oe, input_parameters.optical_element.wrapped_optical_element, screen_index=0)

        shadow_beam_at_image_plane = ShadowBeam.traceFromOE(shadow_oe_input_beam, shadow_oe, history=False)

        # restore o.e. setting for further calculations
        shadow_oe._oe.X_ROT   = x_rot
        shadow_oe._oe.Y_ROT   = y_rot
        shadow_oe._oe.Z_ROT   = z_rot

        calculation_parameters.set("shadow_beam", shadow_beam_at_image_plane)

        image_beam, image_beam_lo = self._process_shadow_beam(shadow_beam_at_image_plane, lost=True)  # xshi change from 0 to 1
        image_beam.set_initial_flux(input_parameters.original_beam.wrapped_beam.get_initial_flux())

        calculation_parameters.set("shadow_oe_end", shadow_oe)
        calculation_parameters.set("image_plane_beam", image_beam)
        calculation_parameters.set("image_plane_beam_lost", image_beam_lo)

        input_parameters.listener.status_message("Projecting beam at HYBRID screen")

        hybrid_screen_beam = shadow_beam_at_image_plane.duplicate(history=False)
        hybrid_screen_beam._beam.rays = hybrid_screen_beam._beam.rays[numpy.where(hybrid_screen_beam._beam.rays[:, 9] == 1)]
        hybrid_screen_beam._beam.retrace(-shadow_oe._oe.T_IMAGE) # hybrid screen is at center

        calculation_parameters.set("screen_plane_beam", hybrid_screen_beam)

        energy     = ShadowPhysics.getEnergyFromShadowK(hybrid_screen_beam._beam.rays[:, 10])  # eV
        wavelength = ShadowPhysics.getWavelengthFromShadowK(hybrid_screen_beam._beam.rays[:, 10])  # Å

        input_parameters.listener.status_message("Using MEAN photon energy [eV]:" + str(numpy.average(energy)))

        xx_screen = hybrid_screen_beam._beam.rays[:, 0]
        zz_screen = hybrid_screen_beam._beam.rays[:, 2]
        xp_screen = hybrid_screen_beam._beam.rays[:, 3]
        yp_screen = hybrid_screen_beam._beam.rays[:, 4]
        zp_screen = hybrid_screen_beam._beam.rays[:, 5]

        x_min   = numpy.min(xx_screen)
        x_max   = numpy.max(xx_screen)
        z_min   = numpy.min(zz_screen)
        z_max   = numpy.max(zz_screen)
        dx_rays = numpy.arctan(xp_screen / yp_screen)  # calculate divergence from direction cosines from SHADOW file  dx = atan(v_x/v_y)
        dz_rays = numpy.arctan(zp_screen / yp_screen)  # calculate divergence from direction cosines from SHADOW file  dz = atan(v_z/v_y)

        to_m = input_parameters.beam.length_units_to_m

        calculation_parameters.energy = numpy.average(energy)
        calculation_parameters.wavelength = numpy.average(wavelength) * 1e-10  # in m
        calculation_parameters.xx_screen = xx_screen * to_m
        calculation_parameters.zz_screen = zz_screen * to_m
        calculation_parameters.xp_screen = xp_screen * to_m
        calculation_parameters.yp_screen = yp_screen * to_m
        calculation_parameters.zp_screen = zp_screen * to_m
        calculation_parameters.x_min = x_min * to_m
        calculation_parameters.x_max = x_max * to_m
        calculation_parameters.z_min = z_min * to_m
        calculation_parameters.z_max = z_max * to_m
        calculation_parameters.dx_rays = dx_rays  # radians
        calculation_parameters.dz_rays = dz_rays  # radians

        return calculation_parameters

    def _check_compound_oe(self, input_parameters: HybridInputParameters, calculation_parameters: AbstractHybridScreen.CalculationParameters):
        calculation_parameters.set("shadow_beam", input_parameters.beam.wrapped_beam)

    def _fix_specific_oe_attributes(self, shadow_oe, original_shadow_oe, screen_index):
        # for all except aperture types
        if shadow_oe._oe.FWRITE > 1 or shadow_oe._oe.F_ANGLE == 0:
            shadow_oe._oe.FWRITE  = 0  # all
            shadow_oe._oe.F_ANGLE = 1  # angles

    def _get_screen_plane_histograms(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters):
        screen_plane_beam = calculation_parameters.get("screen_plane_beam")
        to_m          = input_parameters.beam.length_units_to_m
        to_user_units = 1/to_m

        histogram_s  = None
        bins_s       = None
        histogram_t  = None
        bins_t       = None
        histogram_2D = None

        if input_parameters.diffraction_plane == HybridDiffractionPlane.BOTH_2D:
            ticket = screen_plane_beam._beam.histo2(col_h=1,
                                                    col_v=3,
                                                    nbins_h=int(input_parameters.n_bins_x),
                                                    nbins_v=int(input_parameters.n_bins_z),
                                                    xrange=[calculation_parameters.x_min*to_user_units, calculation_parameters.x_max*to_user_units],
                                                    yrange=[calculation_parameters.z_min*to_user_units, calculation_parameters.z_max*to_user_units],
                                                    nolost=1,
                                                    ref=23)

            histogram_s  = ticket['histogram_h']
            bins_s       = ticket['bin_h_edges']*to_m
            histogram_t  = ticket['histogram_v']
            bins_t       = ticket['bin_v_edges']*to_m
            histogram_2D = ticket['histogram']
        else:
            if input_parameters.diffraction_plane in [HybridDiffractionPlane.SAGITTAL, HybridDiffractionPlane.BOTH_2X1D]:  # 1d in X
                ticket = screen_plane_beam._beam.histo1(1,
                                                        nbins=int(input_parameters.n_bins_x),
                                                        xrange=[calculation_parameters.x_min*to_user_units, calculation_parameters.x_max*to_user_units],
                                                        nolost=1,
                                                        ref=23)

                histogram_s = ticket['histogram']
                bins_s      = ticket['bins']*to_m
            if input_parameters.diffraction_plane in [HybridDiffractionPlane.TANGENTIAL, HybridDiffractionPlane.BOTH_2X1D]:  # 1d in X
                ticket = screen_plane_beam._beam.histo1(3,
                                                        nbins=int(input_parameters.n_bins_z),
                                                        xrange=[calculation_parameters.z_min*to_user_units, calculation_parameters.z_max*to_user_units],
                                                        nolost=1,
                                                        ref=23)

                histogram_t = ticket['histogram']
                bins_t      = ticket['bins']*to_m

        return histogram_s, bins_s, histogram_t, bins_t, histogram_2D

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

    def _apply_convolution_to_rays(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters):
        image_plane_beam      = calculation_parameters.get("image_plane_beam")
        image_plane_beam_lost = calculation_parameters.get("image_plane_beam_lost")
        original_beam_history = calculation_parameters.get("original_beam_history")
        oe_number             = input_parameters.beam.wrapped_beam._oe_number
        to_user_units         = 1/input_parameters.beam.length_units_to_m

        ff_beam = None
        nf_beam = None

        if input_parameters.diffraction_plane == HybridDiffractionPlane.BOTH_2D:
            ff_beam = image_plane_beam.duplicate(history=False)
            ff_beam._oe_number = input_parameters.original_beam.wrapped_beam._oe_number

            angle_num = numpy.sqrt(1 + (numpy.tan(calculation_parameters.dz_convolution)) ** 2 + (numpy.tan(calculation_parameters.dx_convolution)) ** 2)

            ff_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_ff)*to_user_units
            ff_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_ff)*to_user_units
            ff_beam._beam.rays[:, 3] = numpy.tan(calculation_parameters.dx_convolution) / angle_num
            ff_beam._beam.rays[:, 4] = 1 / angle_num
            ff_beam._beam.rays[:, 5] = numpy.tan(calculation_parameters.dz_convolution) / angle_num
        else:
            if input_parameters.diffraction_plane in [HybridDiffractionPlane.SAGITTAL, HybridDiffractionPlane.BOTH_2X1D]:
                # FAR FIELD PROPAGATION
                if input_parameters.propagation_type in [HybridPropagationType.FAR_FIELD, HybridPropagationType.BOTH]:
                    ff_beam = image_plane_beam.duplicate(history=False)
                    ff_beam._oe_number = oe_number

                    angle_perpen = numpy.arctan(calculation_parameters.zp_screen / calculation_parameters.yp_screen)
                    angle_num    = numpy.sqrt(1 + (numpy.tan(angle_perpen)) ** 2 + (numpy.tan(calculation_parameters.dx_convolution)) ** 2)

                    ff_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_ff)*to_user_units
                    ff_beam._beam.rays[:, 3] = numpy.tan(calculation_parameters.dx_convolution) / angle_num
                    ff_beam._beam.rays[:, 4] = 1 / angle_num
                    ff_beam._beam.rays[:, 5] = numpy.tan(angle_perpen) / angle_num

                # NEAR FIELD PROPAGATION
                if input_parameters.propagation_type in [HybridPropagationType.NEAR_FIELD, HybridPropagationType.BOTH]:
                    nf_beam = image_plane_beam.duplicate(history=False)
                    nf_beam._oe_number = oe_number

                    nf_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_nf)*to_user_units

            if input_parameters.diffraction_plane in [HybridDiffractionPlane.TANGENTIAL, HybridDiffractionPlane.BOTH_2X1D]:
                # FAR FIELD PROPAGATION
                if input_parameters.propagation_type in [HybridPropagationType.FAR_FIELD, HybridPropagationType.BOTH]:
                    if ff_beam is None:
                        ff_beam = image_plane_beam.duplicate(history=False)
                        ff_beam._oe_number = oe_number

                    angle_perpen = numpy.arctan(calculation_parameters.xp_screen / calculation_parameters.yp_screen)
                    angle_num    = numpy.sqrt(1 + (numpy.tan(angle_perpen)) ** 2 + (numpy.tan(calculation_parameters.dz_convolution)) ** 2)

                    ff_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_ff)*to_user_units
                    ff_beam._beam.rays[:, 3] = numpy.tan(angle_perpen) / angle_num
                    ff_beam._beam.rays[:, 4] = 1 / angle_num
                    ff_beam._beam.rays[:, 5] = numpy.tan(calculation_parameters.dz_convolution) / angle_num

                    if image_plane_beam_lost.get_number_of_rays() > 0: ff_beam = ShadowBeam.mergeBeams(ff_beam, image_plane_beam_lost, which_flux=1, merge_history=0)

                # NEAR FIELD PROPAGATION
                if input_parameters.propagation_type in [HybridPropagationType.NEAR_FIELD, HybridPropagationType.BOTH]:
                    if nf_beam is None:
                        nf_beam = image_plane_beam.duplicate(history=False)
                        nf_beam._oe_number = oe_number

                    nf_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_nf)*to_user_units

        if input_parameters.propagation_type in [HybridPropagationType.FAR_FIELD, HybridPropagationType.BOTH]:
            if image_plane_beam_lost.get_number_of_rays() > 0: ff_beam = ShadowBeam.mergeBeams(ff_beam, image_plane_beam_lost, which_flux=1, merge_history=0)
            ff_beam.history = original_beam_history

        if input_parameters.propagation_type in [HybridPropagationType.NEAR_FIELD, HybridPropagationType.BOTH]:
            if image_plane_beam_lost.get_number_of_rays() > 0: nf_beam = ShadowBeam.mergeBeams(nf_beam, image_plane_beam_lost, which_flux=1, merge_history=0)
            nf_beam.history = original_beam_history

        calculation_parameters.ff_beam = None if ff_beam is None else ShadowHybridBeam(beam=ff_beam,  length_units=input_parameters.beam.length_units)
        calculation_parameters.nf_beam = None if nf_beam is None else ShadowHybridBeam(beam=nf_beam,  length_units=input_parameters.beam.length_units)

class _ShadowApertureHybridScreen(_ShadowOEHybridScreen):
    def _fix_specific_oe_attributes(self, shadow_oe, original_shadow_oe, screen_index):
        if not (shadow_oe._oe.FMIRR == 5 and \
                shadow_oe._oe.F_CRYSTAL == 0 and \
                shadow_oe._oe.F_REFRAC == 2 and \
                shadow_oe._oe.F_SCREEN==1 and \
                shadow_oe._oe.N_SCREEN==1):
            raise Exception("Connected O.E. is not a Screen-Slit or CRL widget!")

    def _check_oe_displacements(self, input_parameters : HybridInputParameters):
        shadow_oe = input_parameters.optical_element.wrapped_optical_element

        if shadow_oe._oe.F_MOVE == 1: raise Exception("O.E. Movements are not supported for this kind of calculation")

    def _calculate_geometrical_parameters(self, input_parameters: HybridInputParameters):
        geometrical_parameters = ShadowSimpleApertureHybridScreen.GeometricalParameters()

        to_m          = input_parameters.beam.length_units_to_m
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
            geometrical_parameters.max_tangential    = (oe_before._oe.CZ_SLIT[0] + oe_before._oe.RZ_SLIT[0] / 2) * to_m
            geometrical_parameters.min_tangential    = (oe_before._oe.CZ_SLIT[0] - oe_before._oe.RZ_SLIT[0] / 2) * to_m
            geometrical_parameters.max_sagittal      = (oe_before._oe.CX_SLIT[0] + oe_before._oe.RX_SLIT[0] / 2) * to_m
            geometrical_parameters.min_sagittal      = (oe_before._oe.CX_SLIT[0] - oe_before._oe.RX_SLIT[0] / 2) * to_m

            ticket_tangential = beam_at_the_slit._beam.histo1(3, nbins=500, nolost=1, ref=23)
            ticket_sagittal   = beam_at_the_slit._beam.histo1(1, nbins=500, nolost=1, ref=23)

            geometrical_parameters.ticket_tangential = {'histogram' : ticket_tangential["histogram"], 'bins' : ticket_tangential["bin_center"]*to_m}
            geometrical_parameters.ticket_sagittal   = {'histogram' : ticket_sagittal["histogram"],   'bins' : ticket_sagittal["bin_center"]*to_m}

        return geometrical_parameters

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
        geometrical_parameters = AbstractHybridScreen.GeometricalParameters()

        to_m          = input_parameters.beam.length_units_to_m
        beam_after    = input_parameters.beam.wrapped_beam
        history_entry = beam_after.getOEHistory(beam_after._oe_number)

        beam_before = history_entry._input_beam.duplicate()
        oe_before   = history_entry._shadow_oe_start.duplicate()

        if oe_before._oe.FHIT_C == 0:  # infinite
            geometrical_parameters.is_infinite = True
        else:
            str_n_oe = str(input_parameters.beam.wrapped_beam._oe_number)
            if input_parameters.beam.wrapped_beam._oe_number < 10: str_n_oe = "0" + str_n_oe

            beam_before._beam.rays = beam_before._beam.rays[numpy.where(beam_before._beam.rays[:, 9] == 1)]  # GOOD ONLY BEFORE THE BEAM

            oe_before._oe.FWRITE = 1
            oe_before._oe.FHIT_C = 0 # make it infinite to compute the size of the beam
            mirror_beam = ShadowBeam.traceFromOE(beam_before, oe_before, history=False)
            mirror_beam.loadFromFile("mirr." + str_n_oe)
            oe_before._oe.FHIT_C = 1 # restore value

            geometrical_parameters.max_tangential = oe_before._oe.RLEN1 * to_m
            geometrical_parameters.min_tangential = oe_before._oe.RLEN2 * to_m
            geometrical_parameters.max_sagittal   = oe_before._oe.RWIDX1 * to_m
            geometrical_parameters.min_sagittal   = oe_before._oe.RWIDX2 * to_m

            ticket_tangential = mirror_beam._beam.histo1(2, nbins=500, nolost=1, ref=23)
            ticket_sagittal   = mirror_beam._beam.histo1(1, nbins=500, nolost=1, ref=23)

            geometrical_parameters.ticket_tangential = {'histogram' : ticket_tangential["histogram"], 'bins' : ticket_tangential["bin_center"]*to_m}
            geometrical_parameters.ticket_sagittal   = {'histogram' : ticket_sagittal["histogram"],   'bins' : ticket_sagittal["bin_center"]*to_m}

        return geometrical_parameters

    def _fix_specific_oe_attributes(self, shadow_oe, original_shadow_oe, screen_index):
        super(_ShadowOEWithSurfaceHybridScreen, self)._fix_specific_oe_attributes(shadow_oe, original_shadow_oe, screen_index)
        shadow_oe._oe.F_RIPPLE = 0

    def _get_footprint_spatial_coordinates(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> Tuple[numpy.ndarray, numpy.ndarray]:
        mirror_beam = self._read_shadow_file("mirr." + self._get_oe_string(input_parameters))
        to_m        = input_parameters.beam.length_units_to_m

        xx_mirr = mirror_beam._beam.rays[:, 0] * to_m
        yy_mirr = mirror_beam._beam.rays[:, 1] * to_m

        calculation_parameters.set("mirror_beam", mirror_beam)

        return xx_mirr, yy_mirr

    def _get_rays_angles(self, input_parameters: HybridInputParameters, calculation_parameters: AbstractHybridScreen.CalculationParameters) -> Tuple[numpy.ndarray, numpy.ndarray]:
        mirror_beam = calculation_parameters.get("mirror_beam")

        return self._read_shadow_angles("angle." + self._get_oe_string(input_parameters), mirror_beam) # in radians

    def _has_pitch_displacement(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> Tuple[bool, float]:
        shadow_oe = calculation_parameters.get("shadow_oe_end")
        
        return shadow_oe._oe.F_MOVE == 1 and shadow_oe._oe.X_ROT != 0.0, numpy.radians(shadow_oe._oe.X_ROT)

    def _has_roll_displacement(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> Tuple[bool, float]:
        shadow_oe = calculation_parameters.get("shadow_oe_end")

        return shadow_oe._oe.F_MOVE == 1 and shadow_oe._oe.Y_ROT != 0.0, numpy.radians(shadow_oe._oe.Y_ROT)

    def _has_sagittal_offset(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> Tuple[bool, float]:
        shadow_oe = calculation_parameters.get("shadow_oe_end")

        return shadow_oe._oe.F_MOVE == 1 and shadow_oe._oe.OFFX != 0.0, shadow_oe._oe.OFFX * input_parameters.beam.length_units_to_m

    def _has_normal_offset(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> Tuple[bool, float]:
        shadow_oe = calculation_parameters.get("shadow_oe_end")

        return shadow_oe._oe.F_MOVE == 1 and shadow_oe._oe.OFFZ != 0.0, shadow_oe._oe.OFFZ * input_parameters.beam.length_units_to_m

    def _get_optical_element_angles(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> Tuple[float, float]:
        shadow_oe = calculation_parameters.get("shadow_oe_end")
        
        return numpy.radians(90 - shadow_oe._oe.T_INCIDENCE), numpy.radians(90 - shadow_oe._oe.T_REFLECTION)
   
    def _get_optical_element_spatial_limits(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> Tuple[float, float, float, float]:
        shadow_oe = calculation_parameters.get("shadow_oe_end")
        to_m      = input_parameters.beam.length_units_to_m

        return shadow_oe._oe.RWIDX2*to_m, shadow_oe._oe.RWIDX1*to_m, shadow_oe._oe.RLEN2*to_m, shadow_oe._oe.RLEN1*to_m

    def _get_focal_length_from_optical_element(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> float:
        shadow_oe = input_parameters.optical_element.wrapped_optical_element
        to_m      = input_parameters.beam.length_units_to_m

        return shadow_oe._oe.SIMAG * to_m

    @staticmethod
    def _read_shadow_angles(filename, mirror_beam=None) -> Tuple[numpy.ndarray, numpy.ndarray]:
        values    = numpy.loadtxt(congruence.checkFile(filename))
        dimension = len(mirror_beam._beam.rays)

        incidence_angle  = numpy.zeros(dimension)
        reflection_angle = numpy.zeros(dimension)

        ray_index = 0
        for index in range(0, len(values)):
            if values[index, 3] == 1:
                incidence_angle[ray_index] = values[index, 1]
                reflection_angle[ray_index] = values[index, 2]

                ray_index += 1

        incidence_angle  = numpy.radians(90.0 - incidence_angle)
        reflection_angle = numpy.radians(90.0 - reflection_angle)

        #print(numpy.min(1000*(incidence_angle)),  numpy.average(1000*(incidence_angle)),  numpy.max(1000*(incidence_angle)))
        #print(numpy.min(1000*(reflection_angle)), numpy.average(1000*(reflection_angle)), numpy.max(1000*(reflection_angle)))

        return incidence_angle, reflection_angle

class _ShadowOEWithSurfaceAndErrorHybridScreen(_ShadowOEWithSurfaceHybridScreen):
    def _fix_specific_oe_attributes(self, shadow_oe, original_shadow_oe, screen_index):
        super(_ShadowOEWithSurfaceHybridScreen, self)._fix_specific_oe_attributes(shadow_oe, original_shadow_oe, screen_index)
        # disable slope error calculation for OE, must be done by HYBRID!
        if shadow_oe._oe.F_RIPPLE == 1 and shadow_oe._oe.F_G_S == 2: shadow_oe._oe.F_RIPPLE = 0
        else: raise Exception("O.E. has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")

    def _get_error_profile(self, input_parameters: HybridInputParameters, calculation_parameters : AbstractHybridScreen.CalculationParameters) -> ScaledMatrix:
        return self._read_shadow_surface(input_parameters.optical_element.wrapped_optical_element._oe.FILE_RIP, dimension=2, to_m=input_parameters.beam.length_units_to_m)

    def _get_tangential_displacement_index(self, input_parameters: HybridInputParameters, calculation_parameters: AbstractHybridScreen.CalculationParameters):
        shadow_oe     = calculation_parameters.get("shadow_oe_end")
        error_profile = calculation_parameters.get("error_profile")

        return 0.0 if shadow_oe._oe.F_MOVE == 0 else shadow_oe._oe.OFFY*input_parameters.beam.length_units_to_m / error_profile.delta_y()

    def _get_sagittal_displacement_index(self, input_parameters: HybridInputParameters, calculation_parameters: AbstractHybridScreen.CalculationParameters):
        shadow_oe     = calculation_parameters.get("shadow_oe_end")
        error_profile = calculation_parameters.get("error_profile")

        return 0.0 if shadow_oe._oe.F_MOVE == 0 else shadow_oe._oe.OFFX*input_parameters.beam.length_units_to_m / error_profile.delta_x()

    @staticmethod
    def _read_shadow_surface(filename, dimension, to_m):
        if dimension == 1:
            values = numpy.loadtxt(congruence.checkFile(filename))
    
            return ScaledArray(values[:, 1]*to_m, values[:, 0]*to_m)
        elif dimension == 2:
            x_coords, y_coords, z_values = ShadowPreProcessor.read_surface_error_file(filename)
    
            return ScaledMatrix(x_coords*to_m, y_coords*to_m, z_values*to_m)

class _ShadowOELensHybridScreen(_ShadowApertureHybridScreen):
    def _check_oe_displacements(self, input_parameters : HybridInputParameters): pass

    def _calculate_geometrical_parameters(self, input_parameters: HybridInputParameters):
        geometrical_parameters = ShadowSimpleApertureHybridScreen.GeometricalParameters()

        beam_after    = input_parameters.beam.wrapped_beam
        history_entry = beam_after.getOEHistory(beam_after._oe_number)
        beam_before   = history_entry._input_beam
        to_m          = input_parameters.beam.length_units_to_m

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
            geometrical_parameters.max_tangential = numpy.min(max_tangential_list) * to_m
            geometrical_parameters.min_tangential = numpy.max(min_tangential_list) * to_m
            geometrical_parameters.max_sagittal   = numpy.min(max_sagittal_list) * to_m
            geometrical_parameters.min_sagittal   = numpy.max(min_sagittal_list) * to_m

        geometrical_parameters.is_infinite = is_infinite

        ticket_tangential = beam_at_the_slit._beam.histo1(3, nbins=500, nolost=1, ref=23)
        ticket_sagittal   = beam_at_the_slit._beam.histo1(1, nbins=500, nolost=1, ref=23)

        geometrical_parameters.ticket_tangential = {'histogram': ticket_tangential["histogram"], 'bins': ticket_tangential["bin_center"] * to_m}
        geometrical_parameters.ticket_sagittal   = {'histogram': ticket_sagittal["histogram"], 'bins': ticket_sagittal["bin_center"] * to_m}

        return geometrical_parameters

    def _check_compound_oe(self, input_parameters: HybridInputParameters, calculation_parameters: AbstractHybridScreen.CalculationParameters):
        history_entry = input_parameters.beam.wrapped_beam.getOEHistory(input_parameters.beam.wrapped_beam._oe_number)
        compound_oe   = history_entry._shadow_oe_end

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

    def _set_image_distance_from_optical_element(self, input_parameters: HybridInputParameters, calculation_parameters: AbstractHybridScreen.CalculationParameters):
        shadow_oe = input_parameters.optical_element.wrapped_optical_element
        to_m      = input_parameters.beam.length_units_to_m

        calculation_parameters.image_plane_distance = shadow_oe._oe.list[-1].T_IMAGE * to_m

class _ShadowOELensAndErrorHybridScreen(_ShadowOELensHybridScreen):
    def _get_error_profiles(self, input_parameters: HybridInputParameters, calculation_parameters: AbstractHybridScreen.CalculationParameters):
        coords_to_m    = input_parameters.get("crl_coords_to_m")
        thickness_to_m = input_parameters.get("crl_thickness_to_m")

        return [self._read_oasys_surface(thickness_error_file, coords_to_m, thickness_to_m) for thickness_error_file in input_parameters.get("crl_error_profiles")]

    @staticmethod
    def _read_oasys_surface(filename, coords_to_m, thickness_to_m):
        x_coords, y_coords, z_values = read_surface_file(filename)

        return ScaledMatrix(x_coords*coords_to_m, y_coords*coords_to_m, z_values.T*thickness_to_m)

class _ShadowOEKBMirrorHybridScreen():

    def _get_hybrid_beam_instance(self, input_parameters: HybridInputParameters, kb_mirror_input_beam):
        return ShadowHybridBeam(beam=kb_mirror_input_beam, length_units=input_parameters.beam.length_units, history=True)

    def _get_hybrid_oe_instance(self, input_parameters: HybridInputParameters, kb_mirror):
        return ShadowHybridOE(optical_element=kb_mirror, name=input_parameters.beam.wrapped_beam[1].getOEHistory(-1)._widget_class_name)

    def _modify_image_plane_distance_on_kb_1(self, kb_mirror_1: ShadowOpticalElement, kb_mirror_2: ShadowOpticalElement):
        total_image_distance = kb_mirror_1._oe.T_IMAGE + \
                               kb_mirror_2._oe.T_SOURCE + \
                               kb_mirror_2._oe.T_IMAGE

        kb_mirror_1._oe.T_IMAGE = total_image_distance

    def _merge_beams(self, beam_1: ShadowHybridBeam, beam_2: ShadowHybridBeam):
        if beam_1 is None or beam_2 is None: return None

        go_beam_1 = numpy.where(beam_1.wrapped_beam._beam.rays[:, 9] == 1)
        go_beam_2 = numpy.where(beam_2.wrapped_beam._beam.rays[:, 9] == 1)

        if   len(go_beam_2[0]) < len(go_beam_1[0]): go_beam_1 = go_beam_1[0][0 : len(go_beam_2[0])]
        elif len(go_beam_2[0]) > len(go_beam_1[0]): go_beam_2 = go_beam_2[0][0 : len(go_beam_1[0])]

        beam_2.wrapped_beam._beam.rays[go_beam_2, 0] = beam_1.wrapped_beam._beam.rays[go_beam_1, 2] # tangential component 1 becomes the sagittal 2
        beam_2.wrapped_beam._beam.rays[go_beam_2, 3] = beam_1.wrapped_beam._beam.rays[go_beam_1, 5]

        return beam_2

# -------------------------------------------------------------
# HYBRID SCREENS IMPLEMENTATION CLASSES
# -------------------------------------------------------------

class ShadowSimpleApertureHybridScreen(_ShadowApertureHybridScreen, AbstractSimpleApertureHybridScreen):
    def __init__(self, wave_optics_provider : HybridWaveOpticsProvider, **kwargs):
        AbstractSimpleApertureHybridScreen.__init__(self, wave_optics_provider, **kwargs)

class ShadowMirrorOrGratingSizeHybridScreen(_ShadowOEWithSurfaceHybridScreen, AbstractMirrorOrGratingSizeHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider, **kwargs):
        AbstractMirrorOrGratingSizeHybridScreen.__init__(self, wave_optics_provider, **kwargs)

class ShadowMirrorSizeAndErrorHybridScreen(_ShadowOEWithSurfaceAndErrorHybridScreen, AbstractMirrorSizeAndErrorHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider, **kwargs):
        AbstractMirrorSizeAndErrorHybridScreen.__init__(self, wave_optics_provider, **kwargs)

class ShadowGratingSizeAndErrorHybridScreen(_ShadowOEWithSurfaceAndErrorHybridScreen, AbstractGratingSizeAndErrorHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider, **kwargs):
        AbstractGratingSizeAndErrorHybridScreen.__init__(self, wave_optics_provider, **kwargs)

class ShadowCRLSizeHybridScreen(_ShadowOELensHybridScreen, AbstractCRLSizeHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider, **kwargs):
        AbstractCRLSizeHybridScreen.__init__(self, wave_optics_provider, **kwargs)

class ShadowCRLSizeAndErrorHybridScreen(_ShadowOELensAndErrorHybridScreen, AbstractCRLSizeAndErrorHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider, **kwargs):
        AbstractCRLSizeAndErrorHybridScreen.__init__(self, wave_optics_provider, **kwargs)

class ShadowKBMirrorSizeHybridScreen(_ShadowOEKBMirrorHybridScreen, AbstractKBMirrorSizeHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider, implementation: str, **kwargs):
        AbstractKBMirrorSizeHybridScreen.__init__(self, wave_optics_provider, implementation, **kwargs)

class ShadowKBMirrorSizeAndErrorHybridScreen(_ShadowOEKBMirrorHybridScreen, AbstractKBMirrorSizeAndErrorHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider, implementation: str, **kwargs):
        AbstractKBMirrorSizeAndErrorHybridScreen.__init__(self, wave_optics_provider, implementation, **kwargs)


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
    hsm.add_hybrid_screen_class(IMPLEMENTATION, ShadowKBMirrorSizeHybridScreen)
    hsm.add_hybrid_screen_class(IMPLEMENTATION, ShadowKBMirrorSizeAndErrorHybridScreen)
except Exception as e:
    print(e)
