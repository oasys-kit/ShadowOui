import sys
import numpy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import TriggerIn

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowPlot, ShadowCongruence
from orangecontrib.shadow.widgets.gui import ow_automatic_element

class GenericElement(ow_automatic_element.AutomaticElement):

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 545

    want_main_area=1
    view_type=Setting(2)

    plotted_beam=None
    footprint_beam=None

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box)

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        view_box = oasysgui.widgetBox(plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="Select level of Plotting",
                                            labelWidth=220,
                                            items=["Detailed Plot", "Preview", "None"],
                                            callback=self.set_PlotQuality, sendSelectedValue=False, orientation="horizontal")
        self.tab = []
        self.tabs = oasysgui.tabWidget(plot_tab)

        self.initializeTabs()

        self.enableFootprint(False)

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

    def initializeTabs(self):
        current_tab = self.tabs.currentIndex()

        enabled = self.isFootprintEnabled()

        size = len(self.tab)
        indexes = range(0, size)
        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = self.getTitles()
        self.plot_canvas = [None]*len(titles)
        self.tab = []

        for title in titles:
            self.tab.append(oasysgui.createTabPage(self.tabs, title))

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.enableFootprint(enabled)

        self.tabs.setCurrentIndex(current_tab)

    def check_not_interactive_conditions(self, input_beam):
        not_interactive = False

        if not input_beam is None:
            if not input_beam.scanned_variable_data is None:
                not_interactive = input_beam.scanned_variable_data.has_additional_parameter("total_power")

        return not_interactive

    def sendEmptyBeam(self):
        empty_beam = self.input_beam.duplicate()
        empty_beam._beam.rays = numpy.array([])
        empty_beam._oe_number += 1

        self.send("Beam", empty_beam)
        self.send("Trigger", TriggerIn(new_object=True))

    def isFootprintEnabled(self):
        return self.tabs.count() == 6

    def enableFootprint(self, enabled=False):
        if enabled:
            if self.tabs.count() == 5:
                self.tab.append(gui.createTabPage(self.tabs, "Footprint"))
                self.plot_canvas.append(None)
        else:
            if self.tabs.count() == 6:
                self.tabs.removeTab(5)
                self.tab = [self.tab[0],
                            self.tab[1],
                            self.tab[2],
                            self.tab[3],
                            self.tab[4],]
                self.plot_canvas = [self.plot_canvas[0],
                                    self.plot_canvas[1],
                                    self.plot_canvas[2],
                                    self.plot_canvas[3],
                                    self.plot_canvas[4],]

    def set_PlotQuality(self):
        self.progressBarInit()

        if not self.plotted_beam is None:
            try:
                self.initializeTabs()

                self.plot_results(self.plotted_beam, progressBarValue=80)
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

    def plot_xy(self, beam_out, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum="", is_footprint=False):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedPlotWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_xy(beam_out._beam, var_x, var_y, title, xtitle, ytitle, xum=xum, yum=yum, conv=self.workspace_units_to_cm, is_footprint=is_footprint, flux=beam_out.get_flux())

        self.progressBarSet(progressBarValue)

    def plot_xy_fast(self, beam_out, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, is_footprint=False):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(roi=False, control=False, position=True)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(False)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        ShadowPlot.plotxy_preview(self.plot_canvas[plot_canvas_index], beam_out._beam, var_x, var_y, nolost=1, title=title, xtitle=xtitle, ytitle=ytitle, conv=self.workspace_units_to_cm, is_footprint=is_footprint)

        self.progressBarSet(progressBarValue)

    def plot_histo(self, beam_out, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle, xum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedHistoWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_histo(beam_out._beam, var, 1, None, 23, title, xtitle, ytitle, xum=xum, conv=self.workspace_units_to_cm, flux=beam_out.get_flux())

        self.progressBarSet(progressBarValue)

    def plot_histo_fast(self, beam_out, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(roi=False, control=False, position=True)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        ShadowPlot.plot_histo_preview(self.plot_canvas[plot_canvas_index], beam_out._beam, var, 1, 23, title, xtitle, ytitle, conv=self.workspace_units_to_cm)

        self.progressBarSet(progressBarValue)

    def plot_results(self, beam_out, footprint_beam=None, progressBarValue=80):
        if not self.view_type == 2:
            if ShadowCongruence.checkEmptyBeam(beam_out):
                if ShadowCongruence.checkGoodBeam(beam_out):
                    self.view_type_combo.setEnabled(False)

                    ShadowPlot.set_conversion_active(self.getConversionActive())

                    if self.isFootprintEnabled() and footprint_beam is None:
                            footprint_beam = ShadowBeam()
                            if beam_out._oe_number < 10:
                                footprint_beam.loadFromFile(file_name="mirr.0" + str(beam_out._oe_number))
                            else:
                                footprint_beam.loadFromFile(file_name="mirr." + str(beam_out._oe_number))

                    variables = self.getVariablestoPlot()
                    titles = self.getTitles()
                    xtitles = self.getXTitles()
                    ytitles = self.getYTitles()
                    xums = self.getXUM()
                    yums = self.getYUM()

                    try:
                        if self.view_type == 1:
                            self.plot_xy_fast(beam_out, progressBarValue + 4,  variables[0][0], variables[0][1], plot_canvas_index=0, title=titles[0], xtitle=xtitles[0], ytitle=ytitles[0])
                            self.plot_xy_fast(beam_out, progressBarValue + 8,  variables[1][0], variables[1][1], plot_canvas_index=1, title=titles[1], xtitle=xtitles[1], ytitle=ytitles[1])
                            self.plot_xy_fast(beam_out, progressBarValue + 12, variables[2][0], variables[2][1], plot_canvas_index=2, title=titles[2], xtitle=xtitles[2], ytitle=ytitles[2])
                            self.plot_xy_fast(beam_out, progressBarValue + 16, variables[3][0], variables[3][1], plot_canvas_index=3, title=titles[3], xtitle=xtitles[3], ytitle=ytitles[3])
                            self.plot_histo_fast(beam_out, progressBarValue + 20, variables[4],                  plot_canvas_index=4, title=titles[4], xtitle=xtitles[4], ytitle=ytitles[4])

                            if self.isFootprintEnabled():
                                self.plot_xy_fast(footprint_beam, progressBarValue + 20, 2, 1, plot_canvas_index=5, title="Footprint", xtitle="Y [" + self.workspace_units_label +"]", ytitle="X [" + self.workspace_units_label +"]", is_footprint=True)


                        elif self.view_type == 0:
                            self.plot_xy(beam_out, progressBarValue + 4,  variables[0][0], variables[0][1], plot_canvas_index=0, title=titles[0], xtitle=xtitles[0], ytitle=ytitles[0], xum=xums[0], yum=yums[0])
                            self.plot_xy(beam_out, progressBarValue + 8,  variables[1][0], variables[1][1], plot_canvas_index=1, title=titles[1], xtitle=xtitles[1], ytitle=ytitles[1], xum=xums[1], yum=yums[1])
                            self.plot_xy(beam_out, progressBarValue + 12, variables[2][0], variables[2][1], plot_canvas_index=2, title=titles[2], xtitle=xtitles[2], ytitle=ytitles[2], xum=xums[2], yum=yums[2])
                            self.plot_xy(beam_out, progressBarValue + 16, variables[3][0], variables[3][1], plot_canvas_index=3, title=titles[3], xtitle=xtitles[3], ytitle=ytitles[3], xum=xums[3], yum=yums[3])
                            self.plot_histo(beam_out, progressBarValue + 20, variables[4],                  plot_canvas_index=4, title=titles[4], xtitle=xtitles[4], ytitle=ytitles[4], xum=xums[4] )

                            if self.isFootprintEnabled():
                                self.plot_xy(footprint_beam, progressBarValue + 20, 2, 1, plot_canvas_index=5, title="Footprint", xtitle="Y [" + self.workspace_units_label +"]", ytitle="X [" + self.workspace_units_label +"]",
                                             xum=("Y [" + self.workspace_units_label +"]"), yum=("X [" + self.workspace_units_label +"]"), is_footprint=True)

                    except Exception as e:
                        self.view_type_combo.setEnabled(True)

                        raise Exception("Data not plottable: No good rays or bad content\nexception: " + str(e))

                    self.view_type_combo.setEnabled(True)
                else:
                    raise Exception("Beam with no good rays")
            else:
                raise Exception("Empty Beam")

        self.plotted_beam = beam_out

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def onReceivingInput(self):
        self.initializeTabs()

    def deserialize(self, shadow_file):
        pass

    def getVariablestoPlot(self):
        return [[1, 3], [4, 6], [1, 4], [3, 6], 11]

    def getTitles(self):
        return ["X,Z", "X',Z'", "X,X'", "Z,Z'", "Energy"]

    def getXTitles(self):
        return [r'X [$\mu$m]', "X' [$\mu$rad]", r'X [$\mu$m]', r'Z [$\mu$m]', "Energy [eV]"]

    def getYTitles(self):
        return [r'Z [$\mu$m]', "Z' [$\mu$rad]", "X' [$\mu$rad]", "Z' [$\mu$rad]", "Number of Rays"]

    def getXUM(self):
        return ["X [" + u"\u03BC" + "m]", "X' [" + u"\u03BC" + "rad]", "X [" + u"\u03BC" + "m]", "Z [" + u"\u03BC" + "m]", "[eV]"]

    def getYUM(self):
        return ["Z [" + u"\u03BC" + "m]", "Z' [" + u"\u03BC" + "rad]", "X' [" + u"\u03BC" + "rad]", "Z' [" + u"\u03BC" + "rad]", None]

    def getConversionActive(self):
        return True

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = GenericElement()
    ow.show()
    a.exec_()
    ow.saveSettings()
