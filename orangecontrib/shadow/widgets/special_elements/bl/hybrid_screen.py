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
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement

from hybrid_methods.coherence.hybrid_screen import *

IMPLEMENTATION = "SHADOW3"

# -------------------------------------------------------------
# RAY-TRACING WRAPPERS
# -------------------------------------------------------------

class ShadowHybridBeam(HybridBeamWrapper):
    def __init__(self, beam : ShadowBeam, length_units):
        super(ShadowHybridBeam, self).__init__(beam, length_units)

    def duplicate(self): return self._beam.duplicate()

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

# -------------------------------------------------------------
# HYBRID SCREENS HELPER CLASSES
# -------------------------------------------------------------

class _ShadowOEHybridScreen():

    def _no_lost_rays_from_oe(self, input_parameters : HybridInputParameters):
        shadow_beam   = input_parameters.beam.wrapped_beam
        history_entry = shadow_beam.getOEHistory(shadow_beam._oe_number)

        beam_after = shadow_beam
        beam_before = history_entry._input_beam

        number_of_good_rays_before = len(beam_before._beam.rays[numpy.where(beam_before._beam.rays[:, 9] == 1)])
        number_of_good_rays_after = len(beam_after._beam.rays[numpy.where(beam_after._beam.rays[:, 9] == 1)])

        return number_of_good_rays_before == number_of_good_rays_after

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
            str_n_oe = str(input_parameters.shadow_beam._oe_number)
            if input_parameters.shadow_beam._oe_number < 10: str_n_oe = "0" + str_n_oe

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

class _ShadowOELensHybridScreen(_ShadowOEHybridScreen):
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

# -------------------------------------------------------------
# HYBRID SCREENS IMPLEMENTATION CLASSES
# -------------------------------------------------------------

class ShadowSimpleApertureHybridScreen(AbstractSimpleApertureHybridScreen, _ShadowOEHybridScreen):
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

class ShadowMirrorOrGratingSizeHybridScreen(AbstractMirrorOrGratingSizeHybridScreen, _ShadowOEWithSurfaceHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractMirrorOrGratingSizeHybridScreen.__init__(self, wave_optics_provider)

class ShadowMirrorSizeAndErrorHybridScreen(AbstractMirrorSizeAndErrorHybridScreen, _ShadowOEWithSurfaceHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractMirrorSizeAndErrorHybridScreen.__init__(self, wave_optics_provider)

class ShadowGratingSizeAndErrorHybridScreen(AbstractGratingSizeAndErrorHybridScreen, _ShadowOEWithSurfaceHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractGratingSizeAndErrorHybridScreen.__init__(self, wave_optics_provider)

class ShadowCRLSizeHybridScreen(AbstractCRLSizeHybridScreen, _ShadowOELensHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractCRLSizeHybridScreen.__init__(self, wave_optics_provider)

class ShadowCRLSizeAndErrorHybridScreen(AbstractCRLSizeAndErrorHybridScreen, _ShadowOELensHybridScreen):
    def __init__(self, wave_optics_provider: HybridWaveOpticsProvider):
        AbstractCRLSizeAndErrorHybridScreen.__init__(self, wave_optics_provider)

# -------------------------------------------------------------
# FACTORY METHOD INITIALIZATION
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



if __name__=="__main__":
    hsm = HybridScreenManager.Instance()

    hm = hsm.create_hybrid_screen_manager(IMPLEMENTATION, HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE)

    hm.run_hybrid_method(None)