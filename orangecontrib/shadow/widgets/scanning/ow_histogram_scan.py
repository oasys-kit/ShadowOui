#!/usr/bin/env python
# -*- coding: utf-8 -*-
# #########################################################################
# Copyright (c) 2018, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2018. UChicago Argonne, LLC. This software was produced       #
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

import sys
import os
import time
import copy
import numpy

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog
from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui import ow_automatic_element

from oasys.util.scanning_gui import StatisticalDataCollection, HistogramDataCollection, DoublePlotWidget, write_histo_and_stats_file_hdf5, write_histo_and_stats_file
from orangecontrib.shadow.util.scanning_gui import ScanHistoWidget, Scan3DHistoWidget

class Histogram(ow_automatic_element.AutomaticElement):

    name = "Scanning Variable Histogram"
    description = "Display Data Tools: Histogram"
    icon = "icons/histogram.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 7
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    IMAGE_WIDTH = 878
    IMAGE_HEIGHT = 635

    want_main_area=1
    plot_canvas=None
    plot_scan_canvas=None

    input_beam=None

    image_plane=Setting(0)
    image_plane_new_position=Setting(10.0)
    image_plane_rel_abs_position=Setting(0)

    x_column_index=Setting(10)

    x_range=Setting(0)
    x_range_min=Setting(0.0)
    x_range_max=Setting(0.0)

    weight_column_index = Setting(23)
    rays=Setting(1)

    number_of_bins=Setting(100)

    title=Setting("Energy")

    iterative_mode = Setting(0)

    last_ticket=None

    is_conversion_active = Setting(1)

    current_histo_data = None
    current_stats = None
    last_histo_data = None
    histo_index = -1

    plot_type = Setting(1)
    add_labels=Setting(0)
    has_colormap=Setting(1)
    plot_type_3D = Setting(0)
    sigma_fwhm_size = Setting(0)
    peak_integral_intensity = Setting(0)
    absolute_relative_intensity = Setting(0)

    def __init__(self):
        super().__init__()

        self.refresh_button = gui.button(self.controlArea, self, "Refresh", callback=self.plot_results, height=45)
        gui.separator(self.controlArea, 10)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        # graph tab
        tab_set = oasysgui.createTabPage(self.tabs_setting, "Plot Settings")
        tab_gen = oasysgui.createTabPage(self.tabs_setting, "Histogram Settings")

        screen_box = oasysgui.widgetBox(tab_set, "Screen Position Settings", addSpace=True, orientation="vertical", height=120)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                            items=["On Image Plane", "Retraced"], labelWidth=260,
                                            callback=self.set_ImagePlane, sendSelectedValue=False, orientation="horizontal")

        self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=50)
        self.image_plane_box_empty = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=50)

        oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "Image Plane new Position", labelWidth=220, valueType=float, orientation="horizontal")

        gui.comboBox(self.image_plane_box, self, "image_plane_rel_abs_position", label="Position Type", labelWidth=250,
                     items=["Absolute", "Relative"], sendSelectedValue=False, orientation="horizontal")

        self.set_ImagePlane()

        general_box = oasysgui.widgetBox(tab_set, "General Settings", addSpace=True, orientation="vertical", height=250)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="Column", labelWidth=70,
                                     items=["1: X",
                                            "2: Y",
                                            "3: Z",
                                            "4: X'",
                                            "5: Y'",
                                            "6: Z'",
                                            "7: E\u03c3 X",
                                            "8: E\u03c3 Y",
                                            "9: E\u03c3 Z",
                                            "10: Ray Flag",
                                            "11: Energy",
                                            "12: Ray Index",
                                            "13: Optical Path",
                                            "14: Phase \u03c3",
                                            "15: Phase \u03c0",
                                            "16: E\u03c0 X",
                                            "17: E\u03c0 Y",
                                            "18: E\u03c0 Z",
                                            "19: Wavelength",
                                            "20: R = sqrt(X\u00b2 + Y\u00b2 + Z\u00b2)",
                                            "21: Theta (angle from Y axis)",
                                            "22: Magnitude = |E\u03c3| + |E\u03c0|",
                                            "23: Total Intensity = |E\u03c3|\u00b2 + |E\u03c0|\u00b2",
                                            "24: \u03a3 Intensity = |E\u03c3|\u00b2",
                                            "25: \u03a0 Intensity = |E\u03c0|\u00b2",
                                            "26: |K|",
                                            "27: K X",
                                            "28: K Y",
                                            "29: K Z",
                                            "30: S0-stokes = |E\u03c0|\u00b2 + |E\u03c3|\u00b2",
                                            "31: S1-stokes = |E\u03c0|\u00b2 - |E\u03c3|\u00b2",
                                            "32: S2-stokes = 2|E\u03c3||E\u03c0|cos(Phase \u03c3-Phase \u03c0)",
                                            "33: S3-stokes = 2|E\u03c3||E\u03c0|sin(Phase \u03c3-Phase \u03c0)",
                                            "34: Power = Intensity * Energy",
                                     ],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "x_range", label="X Range", labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_XRange, sendSelectedValue=False, orientation="horizontal")

        self.xrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.xrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        oasysgui.lineEdit(self.xrange_box, self, "x_range_min", "X min", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.xrange_box, self, "x_range_max", "X max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_XRange()

        self.weight_column = gui.comboBox(general_box, self, "weight_column_index", label="Weight", labelWidth=70,
                                         items=["0: No Weight",
                                                "1: X",
                                                "2: Y",
                                                "3: Z",
                                                "4: X'",
                                                "5: Y'",
                                                "6: Z'",
                                                "7: E\u03c3 X",
                                                "8: E\u03c3 Y",
                                                "9: E\u03c3 Z",
                                                "10: Ray Flag",
                                                "11: Energy",
                                                "12: Ray Index",
                                                "13: Optical Path",
                                                "14: Phase \u03c3",
                                                "15: Phase \u03c0",
                                                "16: E\u03c0 X",
                                                "17: E\u03c0 Y",
                                                "18: E\u03c0 Z",
                                                "19: Wavelength",
                                                "20: R = sqrt(X\u00b2 + Y\u00b2 + Z\u00b2)",
                                                "21: Theta (angle from Y axis)",
                                                "22: Magnitude = |E\u03c3| + |E\u03c0|",
                                                "23: Total Intensity = |E\u03c3|\u00b2 + |E\u03c0|\u00b2",
                                                "24: \u03a3 Intensity = |E\u03c3|\u00b2",
                                                "25: \u03a0 Intensity = |E\u03c0|\u00b2",
                                                "26: |K|",
                                                "27: K X",
                                                "28: K Y",
                                                "29: K Z",
                                                "30: S0-stokes = |E\u03c0|\u00b2 + |E\u03c3|\u00b2",
                                                "31: S1-stokes = |E\u03c0|\u00b2 - |E\u03c3|\u00b2",
                                                "32: S2-stokes = 2|E\u03c3||E\u03c0|cos(Phase \u03c3-Phase \u03c0)",
                                                "33: S3-stokes = 2|E\u03c3||E\u03c0|sin(Phase \u03c3-Phase \u03c0)",
                                                "34: Power = Intensity * Energy",
                                         ],
                                         sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "rays", label="Rays", labelWidth=250,
                                     items=["All rays",
                                            "Good Only",
                                            "Lost Only"],
                                     sendSelectedValue=False, orientation="horizontal")

        incremental_box = oasysgui.widgetBox(tab_gen, "Incremental Result", addSpace=True, orientation="vertical", height=320)

        gui.button(incremental_box, self, "Clear Stored Data", callback=self.clearResults, height=30)
        gui.separator(incremental_box)

        gui.comboBox(incremental_box, self, "iterative_mode", label="Iterative Mode", labelWidth=250,
                                         items=["None", "Accumulating", "Scanning"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_IterativeMode)

        self.box_scan_empty = oasysgui.widgetBox(incremental_box, "", addSpace=False, orientation="vertical")
        self.box_scan = oasysgui.widgetBox(incremental_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.box_scan, self, "plot_type", label="Plot Type", labelWidth=310,
                     items=["2D", "3D"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_PlotType)

        self.box_pt_1 = oasysgui.widgetBox(self.box_scan, "", addSpace=False, orientation="vertical", height=25)

        gui.comboBox(self.box_pt_1, self, "add_labels", label="Add Labels (Variable Name/Value)", labelWidth=310,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")

        self.box_pt_2 = oasysgui.widgetBox(self.box_scan, "", addSpace=False, orientation="vertical", height=25)

        gui.comboBox(self.box_pt_2, self, "plot_type_3D", label="3D Plot Aspect", labelWidth=310,
                     items=["Lines", "Surface"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.box_scan, self, "has_colormap", label="Colormap", labelWidth=310,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.box_scan)

        gui.comboBox(self.box_scan, self, "sigma_fwhm_size", label="Stats: Spot Attribute", labelWidth=310,
                     items=["Sigma", "FWHM", "Centroid"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.box_scan, self, "peak_integral_intensity", label="Stats: Intensity (1)", labelWidth=310,
                     items=["Peak", "Integral"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.box_scan, self, "absolute_relative_intensity", label="Stats: Intensity (2)", labelWidth=310,
                     items=["Relative", "Absolute"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.button(self.box_scan, self, "Export Scanning Results/Stats", callback=self.export_scanning_stats_analysis, height=30)

        self.set_IterativeMode()

        histograms_box = oasysgui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=90)

        oasysgui.lineEdit(histograms_box, self, "number_of_bins", "Number of Bins", labelWidth=250, valueType=int, orientation="horizontal")

        gui.comboBox(histograms_box, self, "is_conversion_active", label="Is U.M. conversion active", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal")

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        plot_tab_stats = oasysgui.createTabPage(self.main_tabs, "Stats")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        self.image_box = gui.widgetBox(plot_tab, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.image_box_stats = gui.widgetBox(plot_tab_stats, "Stats Result", addSpace=True, orientation="vertical")
        self.image_box_stats.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box_stats.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

    def clearResults(self, interactive=True):
        if not interactive: proceed = True
        else: proceed = ConfirmDialog.confirmed(parent=self)

        if proceed:
            self.clear_data()

    def clear_data(self):
        self.input_beam = None
        self.last_ticket = None
        self.current_stats = None
        self.current_histo_data = None
        self.last_histo_data = None

        self.histo_index = -1

        if not self.plot_canvas is None:
            self.main_tabs.removeTab(1)
            self.main_tabs.removeTab(0)

            plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

            self.image_box = gui.widgetBox(plot_tab, "Plot Result", addSpace=True, orientation="vertical")
            self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
            self.image_box.setFixedWidth(self.IMAGE_WIDTH)

            plot_tab_stats = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

            self.image_box_stats = gui.widgetBox(plot_tab_stats, "Stats Result", addSpace=True, orientation="vertical")
            self.image_box_stats.setFixedHeight(self.IMAGE_HEIGHT)
            self.image_box_stats.setFixedWidth(self.IMAGE_WIDTH)

            self.main_tabs.insertTab(0, plot_tab_stats, "TEMP")
            self.main_tabs.setTabText(0, "Stats")
            self.main_tabs.insertTab(0, plot_tab, "TEMP")
            self.main_tabs.setTabText(0, "Plots")
            self.main_tabs.setCurrentIndex(0)

            self.plot_canvas = None
            self.plot_canvas_stats = None

    def set_IterativeMode(self):
        self.box_scan_empty.setVisible(self.iterative_mode<2)
        if self.iterative_mode==2:
            self.box_scan.setVisible(True)
            self.refresh_button.setEnabled(False)
            self.set_PlotType()
        else:
            self.box_scan.setVisible(False)
            self.refresh_button.setEnabled(True)

        self.clear_data()

    def set_PlotType(self):
        self.plot_canvas = None
        self.plot_canvas_stats = None

        self.box_pt_1.setVisible(self.plot_type==0)
        self.box_pt_2.setVisible(self.plot_type==1)

    def set_XRange(self):
        self.xrange_box.setVisible(self.x_range == 1)
        self.xrange_box_empty.setVisible(self.x_range == 0)

    def set_ImagePlane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def replace_fig(self, beam, var, xrange, title, xtitle, ytitle, xum):
        if self.plot_canvas is None:
            if self.iterative_mode < 2:
                self.plot_canvas = ShadowPlot.DetailedHistoWidget(y_scale_factor=1.14)
            else:
                if self.plot_type == 0:
                    self.plot_canvas = ScanHistoWidget(self.workspace_units_to_cm)
                elif self.plot_type==1:
                    self.plot_canvas = Scan3DHistoWidget(self.workspace_units_to_cm,
                                                         type=Scan3DHistoWidget.PlotType.LINES if self.plot_type_3D==0 else Scan3DHistoWidget.PlotType.SURFACE)

                self.plot_canvas_stats = DoublePlotWidget(parent=None)
                self.image_box_stats.layout().addWidget(self.plot_canvas_stats)

            self.image_box.layout().addWidget(self.plot_canvas)

        if self.iterative_mode==0:
            self.last_ticket = None
            self.current_histo_data = None
            self.current_stats = None
            self.last_histo_data = None
            self.histo_index = -1
            self.plot_canvas.plot_histo(beam._beam, var, self.rays, xrange,
                                        self.weight_column_index, title, xtitle, ytitle,
                                        nbins=self.number_of_bins, xum=xum, conv=self.workspace_units_to_cm)

        elif self.iterative_mode == 1:
            self.current_histo_data = None
            self.current_stats = None
            self.last_histo_data = None
            self.histo_index = -1
            self.last_ticket = self.plot_canvas.plot_histo(beam._beam, var, self.rays, xrange,
                                                           self.weight_column_index, title, xtitle, ytitle,
                                                           nbins=self.number_of_bins, xum=xum, conv=self.workspace_units_to_cm,
                                                           ticket_to_add=self.last_ticket)
        else:
            if not beam.scanned_variable_data is None:
                self.last_ticket = None
                self.histo_index += 1

                um = beam.scanned_variable_data.get_scanned_variable_um()
                um = " " + um if um.strip() == "" else " [" + um + "]"

                histo_data = self.plot_canvas.plot_histo(beam=beam,
                                                         col=var,
                                                         ref=self.weight_column_index,
                                                         nbins=self.number_of_bins,
                                                         title=title,
                                                         xtitle=xtitle,
                                                         ytitle=ytitle,
                                                         histo_index=self.histo_index,
                                                         scan_variable_name=beam.scanned_variable_data.get_scanned_variable_display_name() + um,
                                                         scan_variable_value=beam.scanned_variable_data.get_scanned_variable_value(),
                                                         offset=0.0 if self.last_histo_data is None else self.last_histo_data.offset,
                                                         xrange=xrange,
                                                         show_reference=False,
                                                         add_labels=self.add_labels==1,
                                                         has_colormap=self.has_colormap==1
                                                         )
                scanned_variable_value = beam.scanned_variable_data.get_scanned_variable_value()

                if isinstance(scanned_variable_value, str):
                    histo_data.scan_value = self.histo_index + 1
                else:
                    histo_data.scan_value=beam.scanned_variable_data.get_scanned_variable_value()

                if not histo_data.bins is None:
                    if self.current_histo_data is None:
                        self.current_histo_data = HistogramDataCollection(histo_data)
                    else:
                        self.current_histo_data.add_histogram_data(histo_data)

                if self.current_stats is None:
                    self.current_stats = StatisticalDataCollection(histo_data)
                else:
                    self.current_stats.add_statistical_data(histo_data)

                self.last_histo_data = histo_data

                if self.sigma_fwhm_size==0: # sigma
                    sizes = self.current_stats.get_sigmas()
                    label_size = "Sigma " + xum
                elif self.sigma_fwhm_size==1: # FWHM
                    sizes = self.current_stats.get_fwhms()
                    label_size = "FWHM " + xum
                else: # centroid
                    sizes = self.current_stats.get_centroids()
                    label_size = "Centroid " + xum

                if self.absolute_relative_intensity == 0: #relative
                    if self.peak_integral_intensity==0: # peak
                        intensities =  self.current_stats.get_relative_peak_intensities()
                        label_intensity = "Relative Peak Intensity"
                    else:
                        intensities = self.current_stats.get_relative_integral_intensities()
                        label_intensity = "Relative Integral Intensity"
                else:
                    if self.peak_integral_intensity==0: # peak
                        intensities =  self.current_stats.get_absolute_peak_intensities()
                        label_intensity = "Absolute Peak Intensity"
                    else:
                        intensities = self.current_stats.get_absolute_integral_intensities()
                        label_intensity = "Absolute Integral Intensity"

                self.plot_canvas_stats.plotCurves(self.current_stats.get_scan_values(),
                                                  sizes,
                                                  intensities,
                                                  "Statistics",
                                                  beam.scanned_variable_data.get_scanned_variable_display_name() + um,
                                                  label_size,
                                                  label_intensity)


    def plot_histo(self, var_x, title, xtitle, ytitle, xum):
        beam_to_plot = self.input_beam

        if self.image_plane == 1:
            new_shadow_beam = self.input_beam.duplicate(history=False)
            dist = 0.0

            if self.image_plane_rel_abs_position == 1:  # relative
                dist = self.image_plane_new_position
            else:  # absolute
                if self.input_beam.historySize() == 0:
                    historyItem = None
                else:
                    historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)

                if historyItem is None: image_plane = 0.0
                elif self.input_beam._oe_number == 0: image_plane = 0.0
                else: image_plane = historyItem._shadow_oe_end._oe.T_IMAGE

                dist = self.image_plane_new_position - image_plane

            self.retrace_beam(new_shadow_beam, dist)

            beam_to_plot = new_shadow_beam

        xrange = self.get_range(beam_to_plot._beam, var_x)

        self.replace_fig(beam_to_plot, var_x, xrange, title, xtitle, ytitle, xum)

    def get_range(self, beam_to_plot, var_x):
        if self.x_range == 0 :
            x_max = 0
            x_min = 0

            x, good_only = beam_to_plot.getshcol((var_x, 10))

            x_to_plot = copy.deepcopy(x)

            go = numpy.where(good_only == 1)
            lo = numpy.where(good_only != 1)

            if self.rays == 0:
                x_max = numpy.array(x_to_plot[0:], float).max()
                x_min = numpy.array(x_to_plot[0:], float).min()
            elif self.rays == 1:
                x_max = numpy.array(x_to_plot[go], float).max()
                x_min = numpy.array(x_to_plot[go], float).min()
            elif self.rays == 2:
                x_max = numpy.array(x_to_plot[lo], float).max()
                x_min = numpy.array(x_to_plot[lo], float).min()

            xrange = [x_min, x_max]
        else:
            congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")

            factor1 = ShadowPlot.get_factor(var_x, self.workspace_units_to_cm)

            xrange = [self.x_range_min / factor1, self.x_range_max / factor1]

        return xrange

    def plot_results(self):
        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                ShadowPlot.set_conversion_active(self.getConversionActive())

                self.number_of_bins = congruence.checkPositiveNumber(self.number_of_bins, "Number of Bins")

                x, auto_title, xum = self.get_titles()

                self.plot_histo(x, title=self.title, xtitle=auto_title, ytitle="Number of Rays", xum=xum)

                plotted = True
            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

            return False

    def get_titles(self):
        auto_title = self.x_column.currentText().split(":", 2)[1]

        xum = auto_title + " "
        self.title = auto_title
        x = self.x_column_index + 1

        if x == 1 or x == 2 or x == 3:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "m]"
                auto_title = auto_title + " [$\mu$m]"
            else:
                xum = xum + " [" + self.workspace_units_label + "]"
                auto_title = auto_title + " [" + self.workspace_units_label + "]"
        elif x == 4 or x == 5 or x == 6:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "rad]"
                auto_title = auto_title + " [$\mu$rad]"
            else:
                xum = xum + " [rad]"
                auto_title = auto_title + " [rad]"
        elif x == 11:
            xum = xum + "[eV]"
            auto_title = auto_title + " [eV]"
        elif x == 13:
            xum = xum + " [" + self.workspace_units_label + "]"
            auto_title = auto_title + " [" + self.workspace_units_label + "]"
        elif x == 14:
            xum = xum + "[rad]"
            auto_title = auto_title + " [rad]"
        elif x == 15:
            xum = xum + "[rad]"
            auto_title = auto_title + " [rad]"
        elif x == 19:
            xum = xum + "[Å]"
            auto_title = auto_title + " [Å]"
        elif x == 20:
            xum = xum + " [" + self.workspace_units_label + "]"
            auto_title = auto_title + " [" + self.workspace_units_label + "]"
        elif x == 21:
            xum = xum + "[rad]"
            auto_title = auto_title + " [rad]"
        elif x >= 25 and x <= 28:
            xum = xum + "[Å-1]"
            auto_title = auto_title + " [Å-1]"

        return x, auto_title, xum

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                if self.is_automatic_run:
                    self.plot_results()
            else:
                QMessageBox.critical(self, "Error", "Data not displayable: No good rays or bad content", QMessageBox.Ok)


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def retrace_beam(self, new_shadow_beam, dist):
            new_shadow_beam._beam.retrace(dist)

    def getConversionActive(self):
        return self.is_conversion_active==1

    def export_scanning_stats_analysis(self):
        output_folder = QFileDialog.getExistingDirectory(self, "Select Output Directory", directory=os.curdir)

        if output_folder:
            if not self.current_histo_data is None:
                items = ("Hdf5 only", "Text only", "Hdf5 and Text")

                item, ok = QInputDialog.getItem(self, "Select Output Format", "Formats: ", items, 2, False)

                if ok and item:
                    if item == "Hdf5 only" or item == "Hdf5 and Text":
                        write_histo_and_stats_file_hdf5(histo_data=self.current_histo_data,
                                                        stats=self.current_stats,
                                                        suffix="",
                                                        output_folder=output_folder)
                    if item == "Text only" or item == "Hdf5 and Text":
                        write_histo_and_stats_file(histo_data=self.current_histo_data,
                                                   stats=self.current_stats,
                                                   suffix="",
                                                   output_folder=output_folder)

                    QMessageBox.information(self, "Export Scanning Results & Stats", "Data saved into directory: " + output_folder, QMessageBox.Ok)
