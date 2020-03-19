import copy
import sys
import time

import numpy
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QSettings
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

from Shadow.ShadowLibExtensions import CompoundOE
class PlotXY(AutomaticElement):

    name = "Plot XY"
    description = "Display Data Tools: Plot XY"
    icon = "icons/plot_xy.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    send_footprint_beam = QSettings().value("output/send-footprint", 0, int) == 1

    if send_footprint_beam:
        inputs = [("Input Beam", object, "setBeam")]
    else:
        inputs = [("Input Beam", ShadowBeam, "setBeam")]

    IMAGE_WIDTH = 878
    IMAGE_HEIGHT = 635

    want_main_area=1
    plot_canvas=None
    input_beam=None

    image_plane=Setting(0)
    image_plane_new_position=Setting(10.0)
    image_plane_rel_abs_position=Setting(0)

    x_column_index=Setting(0)
    y_column_index=Setting(2)

    x_range=Setting(0)
    x_range_min=Setting(0.0)
    x_range_max=Setting(0.0)

    y_range=Setting(0)
    y_range_min=Setting(0.0)
    y_range_max=Setting(0.0)

    weight_column_index = Setting(23)
    rays=Setting(1)
    cartesian_axis=Setting(1)

    number_of_bins=Setting(100) # for retrocompatibility: I don't change the name
    number_of_bins_v=Setting(100)

    title=Setting("X,Z")

    autosave = Setting(0)
    autosave_file_name = Setting("autosave_xy_plot.hdf5")

    keep_result=Setting(0)
    autosave_partial_results = Setting(0)

    is_conversion_active = Setting(1)

    cumulated_ticket = None
    plotted_ticket   = None
    autosave_file = None
    autosave_prog_id = 0

    def __init__(self):
        super().__init__()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        gui.button(button_box, self, "Refresh", callback=self.plot_results, height=45)
        gui.button(button_box, self, "Save Current Plot", callback=self.save_results, height=45)

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

        general_box = oasysgui.widgetBox(tab_set, "Variables Settings", addSpace=True, orientation="vertical", height=350)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="H Column",labelWidth=70,
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

        gui.comboBox(general_box, self, "x_range", label="H Range", labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_XRange, sendSelectedValue=False, orientation="horizontal")

        self.xrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.xrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        oasysgui.lineEdit(self.xrange_box, self, "x_range_min", "H min", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.xrange_box, self, "x_range_max", "H max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_XRange()

        self.y_column = gui.comboBox(general_box, self, "y_column_index", label="V Column",labelWidth=70,
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

        gui.comboBox(general_box, self, "y_range", label="V Range",labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_YRange, sendSelectedValue=False, orientation="horizontal")

        self.yrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.yrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        oasysgui.lineEdit(self.yrange_box, self, "y_range_min", "V min", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "y_range_max", "V max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_YRange()

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

        gui.comboBox(general_box, self, "cartesian_axis", label="Cartesian Axis",labelWidth=300,
                                     items=["No",
                                            "Yes"],
                                     sendSelectedValue=False, orientation="horizontal")

        autosave_box = oasysgui.widgetBox(tab_gen, "Autosave", addSpace=True, orientation="vertical", height=85)

        gui.comboBox(autosave_box, self, "autosave", label="Save automatically plot into file", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_autosave)

        self.autosave_box_1 = oasysgui.widgetBox(autosave_box, "", addSpace=False, orientation="horizontal", height=25)
        self.autosave_box_2 = oasysgui.widgetBox(autosave_box, "", addSpace=False, orientation="horizontal", height=25)

        self.le_autosave_file_name = oasysgui.lineEdit(self.autosave_box_1, self, "autosave_file_name", "File Name", labelWidth=100,  valueType=str, orientation="horizontal")

        gui.button(self.autosave_box_1, self, "...", callback=self.selectAutosaveFile)

        incremental_box = oasysgui.widgetBox(tab_gen, "Incremental Result", addSpace=True, orientation="vertical", height=120)

        gui.comboBox(incremental_box, self, "keep_result", label="Keep Result", labelWidth=250,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_autosave)

        self.cb_autosave_partial_results = gui.comboBox(incremental_box, self, "autosave_partial_results", label="Save partial plots into file", labelWidth=250,
                                                        items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.button(incremental_box, self, "Clear", callback=self.clearResults)

        histograms_box = oasysgui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=120)

        oasysgui.lineEdit(histograms_box, self, "number_of_bins", "Number of Bins H", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(histograms_box, self, "number_of_bins_v", "Number of Bins V", labelWidth=250, valueType=int, orientation="horizontal")
        gui.comboBox(histograms_box, self, "is_conversion_active", label="Is U.M. conversion active", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal")

        self.set_autosave()

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        self.image_box = gui.widgetBox(plot_tab, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

    def clearResults(self, interactive=True):
        if not interactive: proceed = True
        else: proceed = ConfirmDialog.confirmed(parent=self)

        if proceed:
            self.input_beam = None
            self.cumulated_ticket = None
            self.plotted_ticket = None
            self.autosave_prog_id = 0
            if not self.autosave_file is None:
                self.autosave_file.close()
                self.autosave_file = None

            if not self.plot_canvas is None:
                self.plot_canvas.clear()

    def set_autosave(self):
        self.autosave_box_1.setVisible(self.autosave==1)
        self.autosave_box_2.setVisible(self.autosave==0)

        self.cb_autosave_partial_results.setEnabled(self.autosave==1 and self.keep_result==1)

    def set_ImagePlane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def set_XRange(self):
        self.xrange_box.setVisible(self.x_range == 1)
        self.xrange_box_empty.setVisible(self.x_range == 0)

    def set_YRange(self):
        self.yrange_box.setVisible(self.y_range == 1)
        self.yrange_box_empty.setVisible(self.y_range == 0)

    def selectAutosaveFile(self):
        self.le_autosave_file_name.setText(oasysgui.selectFileFromDialog(self, self.autosave_file_name, "Select File", file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf)"))

    def replace_fig(self, beam, var_x, var_y,  title, xtitle, ytitle, xrange, yrange, nbins=100, nbins_h=None, nbins_v=None, nolost=0, xum="", yum="", flux=None):
        if self.plot_canvas is None:
            self.plot_canvas = ShadowPlot.DetailedPlotWidget(y_scale_factor=1.14)
            self.image_box.layout().addWidget(self.plot_canvas)

        try:
            if self.autosave == 1:
                if self.autosave_file is None:
                    self.autosave_file = ShadowPlot.PlotXYHdf5File(congruence.checkDir(self.autosave_file_name))
                elif self.autosave_file.filename != congruence.checkFileName(self.autosave_file_name):
                    self.autosave_file.close()
                    self.autosave_file = ShadowPlot.PlotXYHdf5File(congruence.checkDir(self.autosave_file_name))

            if nbins_h is None: nbins_h=nbins
            if nbins_v is None: nbins_v=nbins

            if self.keep_result == 1:
                self.cumulated_ticket, last_ticket = self.plot_canvas.plot_xy(beam, var_x, var_y, title, xtitle, ytitle,
                                                                              xrange=xrange,
                                                                              yrange=yrange,
                                                                              nbins_h=nbins_h,
                                                                              nbins_v=nbins_v,
                                                                              nolost=nolost,
                                                                              xum=xum,
                                                                              yum=yum,
                                                                              conv=self.workspace_units_to_cm,
                                                                              ref=self.weight_column_index,
                                                                              ticket_to_add=self.cumulated_ticket,
                                                                              flux=flux)

                self.plotted_ticket = self.cumulated_ticket

                if self.autosave == 1:
                    self.autosave_prog_id += 1
                    self.autosave_file.write_coordinates(self.cumulated_ticket)
                    dataset_name = self.weight_column.itemText(self.weight_column_index)

                    self.autosave_file.add_plot_xy(self.cumulated_ticket, dataset_name=dataset_name)

                    if self.autosave_partial_results == 1:
                        if last_ticket is None:
                            self.autosave_file.add_plot_xy(self.cumulated_ticket, plot_name="Plot XY #" + str(self.autosave_prog_id), dataset_name=dataset_name)
                        else:
                            self.autosave_file.add_plot_xy(last_ticket, plot_name="Plot X #" + str(self.autosave_prog_id), dataset_name=dataset_name)

                    self.autosave_file.flush()
            else:
                ticket, _ = self.plot_canvas.plot_xy(beam, var_x, var_y, title, xtitle, ytitle,
                                                     xrange=xrange,
                                                     yrange=yrange,
                                                     nbins_h=nbins_h,
                                                     nbins_v=nbins_v,
                                                     nolost=nolost,
                                                     xum=xum,
                                                     yum=yum,
                                                     conv=self.workspace_units_to_cm,
                                                     ref=self.weight_column_index,
                                                     flux=flux)

                self.cumulated_ticket = None
                self.plotted_ticket = ticket

                if self.autosave == 1:
                    self.autosave_prog_id += 1
                    self.autosave_file.write_coordinates(ticket)
                    self.autosave_file.add_plot_xy(ticket, dataset_name=self.weight_column.itemText(self.weight_column_index))
                    self.autosave_file.flush()

        except Exception as e:
            if not self.IS_DEVELOP:
                raise Exception("Data not plottable: No good rays or bad content")
            else:
                raise e

    def plot_xy(self, var_x, var_y, title, xtitle, ytitle, xum, yum):
        beam_to_plot = self.input_beam._beam
        flux         = self.input_beam.get_flux(nolost=self.rays)

        if self.image_plane == 1:
            new_shadow_beam = self.input_beam.duplicate(history=False)

            if self.image_plane_rel_abs_position == 1:  # relative
                dist = self.image_plane_new_position
            else:  # absolute
                if self.input_beam.historySize() == 0:
                    historyItem = None
                else:
                    historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)

                if historyItem is None: image_plane = 0.0
                elif self.input_beam._oe_number == 0: image_plane = 0.0
                else:
                    if isinstance(historyItem._shadow_oe_end._oe, CompoundOE):
                        image_plane = historyItem._shadow_oe_end._oe.list[-1].T_IMAGE
                    else:
                        image_plane = historyItem._shadow_oe_end._oe.T_IMAGE

                dist = self.image_plane_new_position - image_plane

            self.retrace_beam(new_shadow_beam, dist)

            beam_to_plot = new_shadow_beam._beam

        xrange, yrange = self.get_ranges(beam_to_plot, var_x, var_y)

        self.replace_fig(beam_to_plot, var_x, var_y, title, xtitle, ytitle,
                         xrange=xrange,
                         yrange=yrange,
                         nbins_h=int(self.number_of_bins),
                         nbins_v=int(self.number_of_bins_v),
                         nolost=self.rays,
                         xum=xum,
                         yum=yum,
                         flux=flux)

    def get_ranges(self, beam_to_plot, var_x, var_y):
        xrange = None
        yrange = None
        factor1 = ShadowPlot.get_factor(var_x, self.workspace_units_to_cm)
        factor2 = ShadowPlot.get_factor(var_y, self.workspace_units_to_cm)

        if self.x_range == 0 and self.y_range == 0:
            if self.cartesian_axis == 1:
                x_max = 0
                y_max = 0
                x_min = 0
                y_min = 0

                x, y, good_only = beam_to_plot.getshcol((var_x, var_y, 10))

                x_to_plot = copy.deepcopy(x)
                y_to_plot = copy.deepcopy(y)

                go = numpy.where(good_only == 1)
                lo = numpy.where(good_only != 1)

                if self.rays == 0:
                    x_max = numpy.array(x_to_plot[0:], float).max()
                    y_max = numpy.array(y_to_plot[0:], float).max()
                    x_min = numpy.array(x_to_plot[0:], float).min()
                    y_min = numpy.array(y_to_plot[0:], float).min()
                elif self.rays == 1:
                    x_max = numpy.array(x_to_plot[go], float).max()
                    y_max = numpy.array(y_to_plot[go], float).max()
                    x_min = numpy.array(x_to_plot[go], float).min()
                    y_min = numpy.array(y_to_plot[go], float).min()
                elif self.rays == 2:
                    x_max = numpy.array(x_to_plot[lo], float).max()
                    y_max = numpy.array(y_to_plot[lo], float).max()
                    x_min = numpy.array(x_to_plot[lo], float).min()
                    y_min = numpy.array(y_to_plot[lo], float).min()

                xrange = [x_min, x_max]
                yrange = [y_min, y_max]
        else:
            if self.x_range == 1:
                congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")

                xrange = [self.x_range_min / factor1, self.x_range_max / factor1]

            if self.y_range == 1:
                congruence.checkLessThan(self.y_range_min, self.y_range_max, "Y range min", "Y range max")

                yrange = [self.y_range_min / factor2, self.y_range_max / factor2]

        return xrange, yrange

    def save_results(self):
        if not self.plotted_ticket is None:
            try:
                file_name, _ = QFileDialog.getSaveFileName(self, "Save Current Plot", filter="HDF5 Files (*.hdf5 *.h5 *.hdf)")

                if not file_name is None and not file_name.strip()=="":
                    if not (file_name.endswith("hd5") or file_name.endswith("hdf5") or file_name.endswith("hdf")):
                        file_name += ".hdf5"

                    save_file = ShadowPlot.PlotXYHdf5File(congruence.checkDir(file_name))

                    save_file.write_coordinates(self.plotted_ticket)
                    dataset_name = self.weight_column.itemText(self.weight_column_index)

                    save_file.add_plot_xy(self.plotted_ticket, dataset_name=dataset_name)

                    save_file.close()
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception


    def plot_results(self):
        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                ShadowPlot.set_conversion_active(self.getConversionActive())

                self.number_of_bins = congruence.checkStrictlyPositiveNumber(self.number_of_bins, "Number of Bins")

                x, y, auto_x_title, auto_y_title, xum, yum = self.get_titles()

                self.plot_xy(x, y, title=self.title, xtitle=auto_x_title, ytitle=auto_y_title, xum=xum, yum=yum)

                plotted = True
            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

            return False

    def get_titles(self):
        auto_x_title = self.x_column.currentText().split(":", 2)[1]
        auto_y_title = self.y_column.currentText().split(":", 2)[1]
        xum = auto_x_title + " "
        yum = auto_y_title + " "
        self.title = auto_x_title + "," + auto_y_title
        x = self.x_column_index + 1
        if x == 1 or x == 2 or x == 3:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "m]"
                auto_x_title = auto_x_title + " [$\mu$m]"
            else:
                xum = xum + " [" + self.workspace_units_label + "]"
                auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 4 or x == 5 or x == 6:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "rad]"
                auto_x_title = auto_x_title + " [$\mu$rad]"
            else:
                xum = xum + " [rad]"
                auto_x_title = auto_x_title + " [rad]"
        elif x == 11:
            xum = xum + "[eV]"
            auto_x_title = auto_x_title + " [eV]"
        elif x == 13:
            xum = xum + "[" + self.workspace_units_label + "]"
            auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 14:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x == 15:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x == 19:
            xum = xum + "[Å]"
            auto_x_title = auto_x_title + " [Å]"
        elif x == 20:
            xum = xum + "[" + self.workspace_units_label + "]"
            auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 21:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x >= 25 and x <= 28:
            xum = xum + "[Å-1]"
            auto_x_title = auto_x_title + " [Å-1]"
        y = self.y_column_index + 1
        if y == 1 or y == 2 or y == 3:
            if self.getConversionActive():
                yum = yum + "[" + u"\u03BC" + "m]"
                auto_y_title = auto_y_title + " [$\mu$m]"
            else:
                yum = yum + " [" + self.workspace_units_label + "]"
                auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 4 or y == 5 or y == 6:
            if self.getConversionActive():
                yum = yum + "[" + u"\u03BC" + "rad]"
                auto_y_title = auto_y_title + " [$\mu$rad]"
            else:
                yum = yum + " [rad]"
                auto_y_title = auto_y_title + " [rad]"
        elif y == 11:
            yum = yum + "[eV]"
            auto_y_title = auto_y_title + " [eV]"
        elif y == 13:
            yum = yum + "[" + self.workspace_units_label + "]"
            auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 14:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y == 15:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y == 19:
            yum = yum + "[Å]"
            auto_y_title = auto_y_title + " [Å]"
        elif y == 20:
            yum = yum + "[" + self.workspace_units_label + "]"
            auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 21:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y >= 25 and y <= 28:
            yum = yum + "[Å-1]"
            auto_y_title = auto_y_title + " [Å-1]"

        return x, y, auto_x_title, auto_y_title, xum, yum

    def setBeam(self, beam):
        if not beam is None:
            send_footprint_beam = QSettings().value("output/send-footprint", 0, int) == 1

            if send_footprint_beam and isinstance(beam, list):
                footprint_beam = beam[1]

                if ShadowCongruence.checkEmptyBeam(footprint_beam):
                    if ShadowCongruence.checkGoodBeam(footprint_beam):
                        self.input_beam = footprint_beam

                        self.x_column_index = 1
                        self.x_range=0
                        self.y_column_index = 0
                        self.y_range = 0
                        self.image_plane = 0

                        self.set_XRange()
                        self.set_YRange()
                        self.set_ImagePlane()

                        if self.is_automatic_run:
                            self.plot_results()
                    else:
                        QMessageBox.critical(self, "Error",
                                                   "Data not displayable: No good rays, bad content, bad limits or axes",
                                                   QMessageBox.Ok)

            elif isinstance(beam, ShadowBeam):
                if ShadowCongruence.checkEmptyBeam(beam):
                    if ShadowCongruence.checkGoodBeam(beam):
                        self.input_beam = beam

                        if self.is_automatic_run:
                            self.plot_results()
                    else:
                        QMessageBox.critical(self, "Error",
                                                   "Data not displayable: No good rays, bad content, bad limits or axes",
                                                   QMessageBox.Ok)
            else:
                QMessageBox.critical(self, "Error",
                                           "Data not displayable: input type not recognized (must be Shadow Beam or Footprint)",
                                           QMessageBox.Ok)

    def setFootprintBeam(self, footprint):
        if not footprint is None:
            beam = footprint[1]

            if ShadowCongruence.checkEmptyBeam(beam):
                if ShadowCongruence.checkGoodBeam(beam):
                    self.input_beam = beam

                    self.x_column_index = 1
                    self.x_range=0
                    self.y_column_index = 0
                    self.y_range = 0
                    self.image_plane = 0

                    self.set_XRange()
                    self.set_YRange()
                    self.set_ImagePlane()

                    if self.is_automatic_run:
                        self.plot_results()
                else:
                    QMessageBox.critical(self, "Error",
                                               "Data not displayable: No good rays, bad content, bad limits or axes",
                                               QMessageBox.Ok)

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
