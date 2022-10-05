#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------- #
# Copyright (c) 2021, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2021. UChicago Argonne, LLC. This software was produced       #
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

import numpy
from Shadow import OE, IdealLensOE, CompoundOE

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

from oasys.widgets.abstract.beamline_rendering.ow_abstract_beamline_renderer import AbstractBeamlineRenderer, AspectRatioModifier, Orientations, OpticalElementsColors, initialize_arrays, get_height_shift, get_inclinations

class ShadowBeamlineRenderer(AbstractBeamlineRenderer):
    name = "Beamline Renderer"
    description = "Beamline Renderer"
    icon = "icons/renderer.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1000
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    input_beam=None

    def __init__(self):
        super(ShadowBeamlineRenderer, self).__init__(is_using_workspace_units=True)

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                self.render(on_receiving_input=True)

    def get_units_attributes(self):
        return self.workspace_units_label, self.workspace_units_to_mm

    def render_beamline(self):
        if not self.input_beam is None:
            self.figure_canvas.clear_axis()

            number_of_elements=self.input_beam.historySize() + (1 if self.draw_source else 0)

            centers, limits = initialize_arrays(number_of_elements=number_of_elements)

            aspect_ratio_modifier = AspectRatioModifier(element_expansion_factor=[self.element_expansion_factor,
                                                                                  self.element_expansion_factor,
                                                                                  self.element_expansion_factor],
                                                        layout_reduction_factor=[1/self.distance_compression_factor,
                                                                                 1.0,
                                                                                 1,0])
            previous_oe_distance    = 0.0
            previous_image_segment  = 0.0
            previous_image_distance = 0.0
            previous_height = self.initial_height # for better visibility
            previous_shift  = 0.0
            previous_orientation = Orientations.UP
            beam_horizontal_inclination = 0.0
            beam_vertical_inclination   = 0.0

            TODEG = 180.0 / numpy.pi

            for history_element in self.input_beam.getOEHistory():
                if not history_element._shadow_source_end is None:
                    if self.draw_source:
                        source_name = None
                        if not history_element._widget_class_name is None:
                            if "Geometric" in history_element._widget_class_name: source_name = "Geometrical"
                            elif "Bending" in history_element._widget_class_name: source_name = "Bending Magnet"
                            elif "Undulator" in history_element._widget_class_name: source_name = "Undulator"
                            elif "Wiggler" in history_element._widget_class_name: source_name = "Wiggler"

                        self.add_source(centers, limits, length=0.0, height=previous_height, canting=0.0,
                                        aspect_ration_modifier=aspect_ratio_modifier, source_name=source_name)
                elif not history_element._shadow_oe_end is None:
                    oe_number = history_element._oe_number
                    oe_index = oe_number if self.draw_source else (oe_number - 1)
                    oe_end   = history_element._shadow_oe_end._oe
                    oe_start = history_element._shadow_oe_start._oe

                    if (isinstance(oe_start, OE) or isinstance(oe_start, IdealLensOE)):
                        if oe_end.IDUMMY == 0: alpha = int(oe_end.ALPHA)  # oe not changed by shadow, angles in deg changed to rad
                        else:                  alpha = int(oe_end.ALPHA * TODEG)

                        if alpha < 0: alpha = int(360 + alpha)

                        if not alpha in [0, 90, 180, 270]: raise ValueError("Rendering not possible, orientation angle not supported")

                        if previous_orientation == Orientations.UP:
                            if alpha == 0:     orientation = Orientations.UP
                            elif alpha == 90:  orientation = Orientations.LEFT
                            elif alpha == 180: orientation = Orientations.DOWN
                            elif alpha == 270: orientation = Orientations.RIGHT
                        elif previous_orientation == Orientations.DOWN:
                            if alpha == 0:     orientation = Orientations.DOWN
                            elif alpha == 90:  orientation = Orientations.RIGHT
                            elif alpha == 180: orientation = Orientations.UP
                            elif alpha == 270: orientation = Orientations.LEFT
                        elif previous_orientation == Orientations.LEFT:
                            if alpha == 0:     orientation = Orientations.LEFT
                            elif alpha == 90:  orientation = Orientations.DOWN
                            elif alpha == 180: orientation = Orientations.RIGHT
                            elif alpha == 270: orientation = Orientations.UP
                        elif previous_orientation == Orientations.RIGHT:
                            if alpha == 0:     orientation = Orientations.RIGHT
                            elif alpha == 90:  orientation = Orientations.UP
                            elif alpha == 180: orientation = Orientations.LEFT
                            elif alpha == 270: orientation = Orientations.DOWN

                        source_segment = oe_start.T_SOURCE
                        image_segment  = oe_start.T_IMAGE

                        source_distance = source_segment * numpy.cos(beam_vertical_inclination) * numpy.cos(beam_horizontal_inclination)

                        segment_to_oe      = previous_image_segment + source_segment
                        oe_total_distance  = previous_oe_distance + previous_image_distance + source_distance

                        height, shift = get_height_shift(segment_to_oe,
                                                         previous_height,
                                                         previous_shift,
                                                         beam_vertical_inclination,
                                                         beam_horizontal_inclination)

                        if isinstance(oe_start, OE):
                            if oe_end.F_REFRAC == 2: # empty element
                                if not history_element._widget_class_name is None:
                                    if "Slit" in history_element._widget_class_name:
                                        if oe_end.I_ABS[0] == 1: # Filters
                                            self.add_slits_filter(centers, limits, oe_index=oe_index,
                                                                  distance=oe_total_distance, height=height, shift=shift,
                                                                  aperture=None, label="Absorber",
                                                                  aspect_ratio_modifier=aspect_ratio_modifier)
                                        elif oe_end.I_SLIT[0] == 1: # Slits
                                            self.add_slits_filter(centers, limits, oe_index=oe_index,
                                                                  distance=oe_total_distance, height=height, shift=shift,
                                                                  aperture=[oe_end.RX_SLIT[0], oe_end.RZ_SLIT[0]], label="Slits",
                                                                  aspect_ratio_modifier=aspect_ratio_modifier)

                                        else:
                                            self.add_point(centers, limits, oe_index=oe_index,
                                                           distance=oe_total_distance, height=height, shift=shift,
                                                           label=None, aspect_ratio_modifier=aspect_ratio_modifier)
                                    elif "ZonePlate" in history_element._widget_class_name:
                                        length    = 5 / self.workspace_units_to_mm

                                        self.add_non_optical_element(centers, limits, oe_index=oe_index,
                                                                 distance=oe_total_distance, height=height, shift=shift, length=length,
                                                                 color=OpticalElementsColors.LENS, aspect_ration_modifier=aspect_ratio_modifier, label="Zone Plate")
                                    else:
                                        self.add_point(centers, limits, oe_index=oe_index,
                                                       distance=oe_total_distance, height=height, shift=shift,
                                                       label=None, aspect_ratio_modifier=aspect_ratio_modifier)
                                else:
                                    self.add_point(centers, limits, oe_index=oe_index,
                                                   distance=oe_total_distance, height=height, shift=shift,
                                                   label=None, aspect_ratio_modifier=aspect_ratio_modifier)
                            else:
                                if oe_end.F_REFRAC == 0:
                                    if oe_end.IDUMMY == 0:
                                        inclination_in = (90 - oe_end.T_INCIDENCE) / TODEG # oe not changed by shadow, angles in deg changed to rad
                                        inclination_out = (90 - oe_end.T_REFLECTION) / TODEG
                                    else:
                                        inclination_in  = (numpy.pi/2) - oe_end.T_INCIDENCE
                                        inclination_out  = (numpy.pi/2) - oe_end.T_REFLECTION

                                    if oe_end.FHIT_C == 1:
                                        width = oe_start.RWIDX1 + oe_start.RWIDX2
                                        length = oe_start.RLEN1 + oe_start.RLEN2
                                    else:
                                        width = 100 / self.workspace_units_to_mm
                                        length = 100 / self.workspace_units_to_mm

                                    if oe_end.F_CRYSTAL == 1:
                                        color = OpticalElementsColors.CRYSTAL
                                        label = "Crystal"
                                    elif oe_end.F_GRATING == 1:
                                        color = OpticalElementsColors.GRATING
                                        label = "Grating"
                                    else:
                                        color = OpticalElementsColors.MIRROR
                                        label = "Mirror"

                                    absolute_inclination, beam_horizontal_inclination, beam_vertical_inclination = get_inclinations(orientation, inclination_in, inclination_out, beam_vertical_inclination, beam_horizontal_inclination)

                                    self.add_optical_element(centers, limits, oe_index=oe_index,
                                                             distance=oe_total_distance, height=height, shift=shift,
                                                             length=length, width=width, thickness=10/self.workspace_units_to_mm, inclination=absolute_inclination, orientation=orientation,
                                                             color=color, aspect_ration_modifier=aspect_ratio_modifier, label=label)
                                else:
                                    self.add_point(centers, limits, oe_index=oe_index,
                                                   distance=oe_total_distance, height=height, shift=shift,
                                                   label="Refractor", aspect_ratio_modifier=aspect_ratio_modifier)
                        elif isinstance(oe_end, IdealLensOE):
                            self.add_point(centers, limits, oe_index=oe_index,
                                           distance=oe_total_distance, height=height, shift=shift,
                                           label="Ideal Lens", aspect_ratio_modifier=aspect_ratio_modifier)

                        previous_orientation = orientation
                    elif isinstance(oe_start, CompoundOE):
                        n_elements = len(oe_start.list)

                        source_segment = 0.0
                        image_segment  = 0.0

                        for i, oe in enumerate(oe_start.list):
                            oe_type = 'Unknown'
                            if isinstance(oe, OE):
                                if oe.F_REFRAC == 1: oe_type = 'CRLs/Transfocator'
                                elif oe.F_REFRAC == 2:  oe_type = 'Empty'
                                else:
                                    oe_type = 'K-B Mirror' # KB
                                    if oe.F_CRYSTAL == 1: oe_type = 'Double-Crystal Monochromator'
                                    if oe.F_GRATING == 1: oe_type = 'Gratings' # not actually implemented

                            elif isinstance(oe, IdealLensOE): oe_type = 'Ideal Lens'

                            if n_elements == 1:
                                source_segment = oe.T_SOURCE
                                image_segment  = oe.T_IMAGE
                            else:
                                if i < int(n_elements/2): source_segment += (oe.T_SOURCE + oe.T_IMAGE)
                                else:                     image_segment += (oe.T_SOURCE + oe.T_IMAGE)

                        source_distance = source_segment * numpy.cos(beam_vertical_inclination) * numpy.cos(beam_horizontal_inclination)

                        segment_to_oe      = previous_image_segment + source_segment
                        oe_total_distance  = previous_oe_distance + source_distance

                        height, shift = get_height_shift(segment_to_oe,
                                                         previous_height,
                                                         previous_shift,
                                                         beam_vertical_inclination,
                                                         beam_horizontal_inclination)

                        if oe_type in ['Unknown', 'Empty', 'Ideal Lens']:
                            self.add_point(centers, limits, oe_index=oe_index,
                                           distance=oe_total_distance, height=height, shift=shift,
                                           label="Compound OE (" + oe_type + ")", aspect_ratio_modifier=aspect_ratio_modifier)
                        else:
                            if oe_type == 'CRLs/Transfocator':
                                length    = source_segment + image_segment - (oe_start.list[0].T_SOURCE + oe_start.list[-1].T_IMAGE)
                                color     = OpticalElementsColors.LENS
                            else:
                                length    =  100 / self.workspace_units_to_mm

                                if oe_type == 'K-B Mirror': color = OpticalElementsColors.MIRROR
                                elif oe_type == 'Double-Crystal Monochromator': color = OpticalElementsColors.CRYSTAL
                                elif oe_type == 'Gratings': color = OpticalElementsColors.GRATING

                            self.add_non_optical_element(centers, limits, oe_index=oe_index,
                                                         distance=oe_total_distance, height=height, shift=shift, length=length,
                                                         color=color, aspect_ration_modifier=aspect_ratio_modifier, label=oe_type)

                    image_distance          = image_segment * numpy.cos(beam_vertical_inclination) * numpy.cos(beam_horizontal_inclination)  # new direction

                    previous_height         = height
                    previous_shift          = shift
                    previous_oe_distance    = oe_total_distance
                    previous_image_segment  = image_segment
                    previous_image_distance = image_distance

            height, shift = get_height_shift(previous_image_segment,
                                             previous_height,
                                             previous_shift,
                                             beam_vertical_inclination,
                                             beam_horizontal_inclination)

            self.add_point(centers, limits, oe_index=number_of_elements - 1,
                           distance=previous_oe_distance + previous_image_distance,
                           height=height, shift=shift, label="End Point",
                           aspect_ratio_modifier=aspect_ratio_modifier)

            return number_of_elements, centers, limits

