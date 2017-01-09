__author__ = 'labx'

import sys
import orangecanvas.resources as resources
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from orangewidget import gui, widget
from orangewidget.settings import Setting

from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, EmittingStream

from PyQt4 import QtGui
from PyQt4.QtGui import QImage, QLabel, QPixmap, QWidget, QHBoxLayout, QPalette, QFont, QColor

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow.widgets.special_elements import hybrid_control

from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow

class HybridScreen(AutomaticElement):

    inputs = [("Input Beam", ShadowBeam, "setBeam"),]

    outputs = [{"name":"Output Beam (Far Field)",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam_ff"},]

    name = "Hybrid Screen"
    description = "Shadow HYBRID: Hybrid Screen"
    icon = "icons/hybrid_screen.png"
    maintainer = "Luca Rebuffi and Xianbo Shi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu, xshi(@at@)aps.anl.gov"
    priority = 3
    category = "HYBRID"
    keywords = ["data", "file", "load", "read"]

    want_control_area = 1
    want_main_area = 1

    ghy_diff_plane = Setting(1)
    ghy_calcType = Setting(2)

    focal_length_calc = Setting(0)
    ghy_focallength = Setting(0.0)
    distance_to_image_calc = Setting(0)
    ghy_distance = Setting(0.0)

    ghy_nf = Setting(0)

    ghy_nbins_x = Setting(100)
    ghy_nbins_z = Setting(100)
    ghy_npeak = Setting(10)
    ghy_fftnpts = Setting(1e6)

    file_to_write_out = Setting(0)

    input_beam = None

    TABS_AREA_HEIGHT = 560
    CONTROL_AREA_WIDTH = 405

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 545

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Run Hybrid", self)
        self.runaction.triggered.connect(self.run_hybrid)
        self.addAction(self.runaction)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run HYBRID", callback=self.run_hybrid)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        main_tabs = gui.tabWidget(self.mainArea)
        plot_tab = gui.createTabPage(main_tabs, "Plots")
        out_tab = gui.createTabPage(main_tabs, "Output")

        self.tabs = oasysgui.tabWidget(plot_tab)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Hybrid Setting")

        box_1 = oasysgui.widgetBox(tab_bas, "Calculation Parameters", addSpace=True, orientation="vertical", height=250)

        gui.comboBox(box_1, self, "ghy_diff_plane", label="Diffraction Plane", labelWidth=310,
                     items=["Sagittal", "Tangential", "Both"],
                     callback=self.set_DiffPlane,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(box_1, self, "ghy_calcType", label="Calculation Type", labelWidth=100,
                     items=["Diffraction by Simple Aperture",
                            "Diffraction by Mirror Size",
                            "Diffraction by Mirror Size + Figure Errors",
                            "Diffraction by Lens or C.R.L. Size"],
                     callback=self.set_CalculationType,
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_1, 10)

        self.cb_focal_length_calc = gui.comboBox(box_1, self, "focal_length_calc", label="Focal Length", labelWidth=180,
                     items=["Use O.E. Focal Distance", "Specify Value"],
                     callback=self.set_FocalLengthCalc,
                     sendSelectedValue=False, orientation="horizontal")

        self.le_focal_length = oasysgui.lineEdit(box_1, self, "ghy_focallength", "Focal Length value", labelWidth=260, valueType=float, orientation="horizontal")

        self.cb_distance_to_image_calc = gui.comboBox(box_1, self, "distance_to_image_calc", label="Distance to image", labelWidth=150,
                     items=["Use O.E. Image Plane Distance", "Specify Value"],
                     callback=self.set_DistanceToImageCalc,
                     sendSelectedValue=False, orientation="horizontal")

        self.le_distance_to_image = oasysgui.lineEdit(box_1, self, "ghy_distance", "Distance to Image value", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(box_1)

        self.cb_nf = gui.comboBox(box_1, self, "ghy_nf", label="Near Field Calculation", labelWidth=310,
                                             items=["No", "Yes"],
                                             sendSelectedValue=False, orientation="horizontal")


        box_2 = oasysgui.widgetBox(tab_bas, "Numerical Control Parameters", addSpace=True, orientation="vertical", height=120)

        self.le_nbins_x = oasysgui.lineEdit(box_2, self, "ghy_nbins_x", "Number of bins for I(Sagittal) histogram", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_nbins_z = oasysgui.lineEdit(box_2, self, "ghy_nbins_z", "Number of bins for I(Tangential) histogram", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_npeak   = oasysgui.lineEdit(box_2, self, "ghy_npeak", "Number of diffraction peaks", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_fftnpts = oasysgui.lineEdit(box_2, self, "ghy_fftnpts", "Number of points for FFT", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_DiffPlane()
        self.set_DistanceToImageCalc()
        self.set_CalculationType()

        self.initializeTabs()

        adv_other_box = oasysgui.widgetBox(tab_bas, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=220,
                     items=["None", "Debug (star.xx)"],
                     sendSelectedValue=False,
                     orientation="horizontal")

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        self.shadow_output.setFixedHeight(600)
        self.shadow_output.setFixedWidth(600)

    def after_change_workspace_units(self):
        label = self.le_focal_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_distance_to_image.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def initializeTabs(self):
        self.tabs.clear()

        if self.ghy_diff_plane < 2:
            if self.ghy_nf == 1:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Far Field"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Near Field")
                            ]
            else:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Far Field")
                            ]
        else:
            if self.ghy_nf == 1:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (T)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field (T)"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Near Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Far Field")
                            ]
            else:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (T)"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Far Field")
                            ]

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.plot_canvas = [None, None, None, None, None, None]

    def plot_xy(self, beam_out, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedPlotWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_xy(beam_out._beam, var_x, var_y, title, xtitle, ytitle, xum=xum, yum=yum, conv=self.workspace_units_to_cm)

        self.progressBarSet(progressBarValue)

    def plot_histo(self, beam_out, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle, xum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedHistoWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_histo(beam_out._beam, var, 1, None, 23, title, xtitle, ytitle, xum=xum, conv=self.workspace_units_to_cm)

        self.progressBarSet(progressBarValue)

    def plot_emtpy(self, progressBarValue, plot_canvas_index):
        if self.plot_canvas[plot_canvas_index] is None:
            widget = QWidget()
            widget.setLayout(QHBoxLayout())
            label = QLabel(widget)
            label.setPixmap(QPixmap(QImage(resources.package_dirname("orangecontrib.shadow.widgets.special_elements") +
                                           "/icons/no_result.png")))

            widget.layout().addWidget(label)

            self.plot_canvas[plot_canvas_index] = widget

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])


        self.progressBarSet(progressBarValue)

    def plot_histo_hybrid(self, progressBarValue, scaled_array, plot_canvas_index, title, xtitle, ytitle, var):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = PlotWindow(roi=False, control=False, position=True, plugins=False)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='darkblue')
            self.plot_canvas[plot_canvas_index].setDrawModeEnabled(True, 'rectangle')
            self.plot_canvas[plot_canvas_index].setZoomModeEnabled(True)

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        factor = ShadowPlot.get_factor(var, self.workspace_units_to_cm)

        self.plot_canvas[plot_canvas_index].addCurve(scaled_array.scale*factor, scaled_array.np_array, "crv_"+ytitle, symbol='', color="blue", replace=True) #'+', '^', ','
        self.plot_canvas[plot_canvas_index]._plot.graph.ax.get_yaxis().get_major_formatter().set_useOffset(True)
        self.plot_canvas[plot_canvas_index]._plot.graph.ax.get_yaxis().get_major_formatter().set_scientific(True)
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].setGraphTitle(title)
        self.plot_canvas[plot_canvas_index].replot()

        self.progressBarSet(progressBarValue)

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                if self.is_automatic_run:
                    self.run_hybrid()


    def set_DiffPlane(self):
        self.le_nbins_x.setEnabled(self.ghy_diff_plane == 0 or self.ghy_diff_plane == 2)
        self.le_nbins_z.setEnabled(self.ghy_diff_plane == 1 or self.ghy_diff_plane == 2)

    def set_FocalLengthCalc(self):
         self.le_focal_length.setEnabled(self.focal_length_calc == 1)

    def set_DistanceToImageCalc(self):
         self.le_distance_to_image.setEnabled(self.distance_to_image_calc == 1)

    def set_CalculationType(self):
        self.cb_focal_length_calc.setEnabled(self.ghy_calcType > 0 and self.ghy_calcType < 3)
        self.le_focal_length.setEnabled(self.ghy_calcType > 0 and self.ghy_calcType < 3)
        self.cb_nf.setEnabled(self.ghy_calcType > 0 and self.ghy_calcType < 3)

        if self.ghy_calcType > 0 and self.ghy_calcType < 3:
            self.set_FocalLengthCalc()
        else:
            self.ghy_nf = 0

    def run_hybrid(self):
        try:
            self.setStatusMessage("")
            self.progressBarInit()
            self.initializeTabs()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    sys.stdout = EmittingStream(textWritten=self.write_stdout)

                    self.check_fields()

                    input_parameters = hybrid_control.HybridInputParameters()
                    input_parameters.ghy_lengthunit = self.workspace_units
                    input_parameters.widget = self
                    input_parameters.shadow_beam = self.input_beam
                    input_parameters.ghy_diff_plane = self.ghy_diff_plane + 1
                    input_parameters.ghy_calcType = self.ghy_calcType + 1

                    if self.distance_to_image_calc == 0:
                        input_parameters.ghy_distance = -1
                    else:
                        input_parameters.ghy_distance = self.ghy_distance

                    if self.focal_length_calc == 0:
                        input_parameters.ghy_focallength = -1
                    else:
                        input_parameters.ghy_focallength = self.ghy_focallength

                    if self.ghy_calcType != 0:
                        input_parameters.ghy_nf = self.ghy_nf
                    else:
                        input_parameters.ghy_nf = 0

                    input_parameters.ghy_nbins_x = self.ghy_nbins_x
                    input_parameters.ghy_nbins_z = self.ghy_nbins_z
                    input_parameters.ghy_npeak = self.ghy_npeak
                    input_parameters.ghy_fftnpts = self.ghy_fftnpts
                    input_parameters.file_to_write_out = self.file_to_write_out

                    calculation_parameters = hybrid_control.hy_run(input_parameters)

                    self.ghy_focallength = input_parameters.ghy_focallength
                    self.ghy_distance = input_parameters.ghy_distance
                    self.ghy_nbins_x = input_parameters.ghy_nbins_x
                    self.ghy_nbins_z = input_parameters.ghy_nbins_z
                    self.ghy_npeak   = input_parameters.ghy_npeak
                    self.ghy_fftnpts = input_parameters.ghy_fftnpts

                    if input_parameters.ghy_calcType == 3:
                        do_plot_x = True
                        do_plot_z = True
                    else:
                        do_plot_x = not calculation_parameters.beam_not_cut_in_x
                        do_plot_z = not calculation_parameters.beam_not_cut_in_z

                    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

                    if do_plot_x or do_plot_z:
                        self.setStatusMessage("Plotting Results")

                    if self.ghy_diff_plane == 0:
                        if do_plot_x:
                            if do_nf:
                                self.plot_histo_hybrid(84, calculation_parameters.dif_xp, 0, title=u"\u2206" + "Xp", xtitle=r'$\Delta$Xp [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                                self.plot_histo(calculation_parameters.ff_beam, 88, 1, plot_canvas_index=1, title="X",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                                self.plot_histo_hybrid(92, calculation_parameters.dif_x, 2, title=u"\u2206" + "X", xtitle=r'$\Delta$X [$\mu$m]', ytitle=r'Arbitrary Units', var=1)
                                self.plot_histo(calculation_parameters.nf_beam, 96, 1, plot_canvas_index=3, title="X",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                            else:
                                self.plot_histo_hybrid(88, calculation_parameters.dif_xp, 0, title=u"\u2206" + "Xp", xtitle=r'$\Delta$Xp [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                                self.plot_histo(calculation_parameters.ff_beam, 96, 1, plot_canvas_index=1, title="X",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                        else:
                            if do_nf:
                                self.plot_emtpy(84, 0)
                                self.plot_emtpy(88, 1)
                                self.plot_emtpy(92, 2)
                                self.plot_emtpy(96, 3)
                            else:
                                self.plot_emtpy(88, 0)
                                self.plot_emtpy(96, 1)
                    elif self.ghy_diff_plane == 1:
                        if do_plot_z:
                            if do_nf:
                                self.plot_histo_hybrid(84, calculation_parameters.dif_zp, 0, title=u"\u2206" + "Zp", xtitle=r'$\Delta$Zp [$\mu$rad]', ytitle=r'Arbitrary Units', var=6)
                                self.plot_histo(calculation_parameters.ff_beam, 84, 3, plot_canvas_index=1, title="Z",
                                                xtitle=r'Z [$\mu$m]', ytitle=r'Number of Rays', xum=("Z [" + u"\u03BC" + "m]"))
                                self.plot_histo_hybrid(88, calculation_parameters.dif_z, 2, title=u"\u2206" + "Z", xtitle=r'$\Delta$Z [$\mu$m]', ytitle=r'Arbitrary Units', var=2)
                                self.plot_histo(calculation_parameters.nf_beam, 96, 3, plot_canvas_index=3, title="Z",
                                                xtitle=r'Z [$\mu$m]', ytitle=r'Number of Rays', xum=("Z [" + u"\u03BC" + "m]"))
                            else:
                                self.plot_histo_hybrid(88, calculation_parameters.dif_zp, 0, title=u"\u2206" + "Zp", xtitle=r'$\Delta$Zp [$\mu$rad]', ytitle=r'Arbitrary Units', var=6)
                                self.plot_histo(calculation_parameters.ff_beam, 96, 3, plot_canvas_index=1, title="Z",
                                                xtitle=r'Z [$\mu$m]', ytitle=r'Number of Rays', xum=("Z [" + u"\u03BC" + "m]"))
                        else:
                            if do_nf:
                                self.plot_emtpy(84, 0)
                                self.plot_emtpy(88, 1)
                                self.plot_emtpy(92, 2)
                                self.plot_emtpy(96, 3)
                            else:
                                self.plot_emtpy(88, 0)
                                self.plot_emtpy(96, 1)

                    elif self.ghy_diff_plane == 2:
                        if do_plot_x:
                            if do_nf:
                                self.plot_histo_hybrid(82, calculation_parameters.dif_xp, 0, title=u"\u2206" + "Xp", xtitle=r'$\Delta$Xp [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                                self.plot_histo_hybrid(84, calculation_parameters.dif_x, 1, title=u"\u2206" + "X", xtitle=r'$\Delta$X [$\mu$m]', ytitle=r'Arbitrary Units', var=1)
                            else:
                                self.plot_histo_hybrid(84, calculation_parameters.dif_xp, 0, title=u"\u2206" + "Xp", xtitle=r'$\Delta$Xp [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                        else:
                            if do_nf:
                                self.plot_emtpy(82, 0)
                                self.plot_emtpy(84, 1)
                            else:
                                self.plot_emtpy(84, 0)

                        if do_plot_z:
                            if do_nf:
                                self.plot_histo_hybrid(86, calculation_parameters.dif_zp, 2, title=u"\u2206" + "Zp", xtitle=r'$\Delta$Zp [$\mu$rad]', ytitle=r'Arbitrary Units', var=6)
                                self.plot_histo_hybrid(88, calculation_parameters.dif_z, 3, title=u"\u2206" + "Z", xtitle=r'$\Delta$Z [$\mu$m]', ytitle=r'Arbitrary Units', var=2)
                            else:
                                self.plot_histo_hybrid(88, calculation_parameters.dif_zp, 1, title=u"\u2206" + "Zp", xtitle=r'$\Delta$Zp [$\mu$rad]', ytitle=r'Arbitrary Units', var=6)
                        else:
                            if do_nf:
                                self.plot_emtpy(86, 2)
                                self.plot_emtpy(88, 3)
                            else:
                                self.plot_emtpy(88, 1)

                        if (do_plot_x or do_plot_z):
                            if do_nf:
                                self.plot_xy(calculation_parameters.nf_beam, 94, 1, 3, plot_canvas_index=4, title="X,Z",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
                                self.plot_xy(calculation_parameters.ff_beam, 98, 1, 3, plot_canvas_index=5, title="X,Z",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
                            else:
                                self.plot_xy(calculation_parameters.ff_beam, 96, 1, 3, plot_canvas_index=2, title="X,Z",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
                        else:
                            if do_nf:
                                self.plot_emtpy(94, 4)
                                self.plot_emtpy(98, 5)
                            else:
                                self.plot_emtpy(96, 3)

                    self.send("Output Beam (Far Field)", calculation_parameters.ff_beam)
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")
        except Exception as exception:
            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

            QtGui.QMessageBox.critical(self, "Error", str(exception), QtGui.QMessageBox.Ok)

            #raise exception

        self.setStatusMessage("")
        self.progressBarFinished()

    def check_fields(self):
        if self.focal_length_calc == 1:
            congruence.checkPositiveNumber(self.ghy_focallength, "Focal Length value")

        if self.distance_to_image_calc == 1:
            congruence.checkPositiveNumber(self.ghy_distance, "Distance to image value")

        if self.ghy_diff_plane == 0 or self.ghy_diff_plane == 2:
            congruence.checkStrictlyPositiveNumber(self.ghy_nbins_x, "Number of bins for I(Sagittal) histogram")
        if self.ghy_diff_plane == 1 or self.ghy_diff_plane == 2:
            congruence.checkStrictlyPositiveNumber(self.ghy_nbins_z, "Number of bins for I(Tangential) histogram")

        congruence.checkStrictlyPositiveNumber(self.ghy_npeak, "Number of diffraction peaks")
        congruence.checkStrictlyPositiveNumber(self.ghy_fftnpts, "Number of points for FFT")

    def set_progress_bar(self, value):
        if value >= 100:
            self.progressBarFinished()
        elif value <=0:
            self.progressBarInit()
        else:
            self.progressBarSet(value)

    def status_message(self, message):
        self.setStatusMessage(message)

    def write_stdout(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

