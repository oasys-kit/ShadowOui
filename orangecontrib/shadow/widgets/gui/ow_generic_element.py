import sys

from orangewidget import gui, widget
from orangewidget.settings import Setting

from PyQt4 import QtGui
from PyQt4.QtGui import QApplication

from orangecontrib.shadow.util.shadow_util import ShadowPlot, ShadowGui
from orangecontrib.shadow.widgets.gui import ow_automatic_element

from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow

class GenericElement(ow_automatic_element.AutomaticElement):

    IMAGE_WIDTH = 1100
    IMAGE_HEIGHT = 545

    want_main_area=1
    view_type=Setting(2)

    plotted_beam=None
    tab=[]

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box)

        view_box = ShadowGui.widgetBox(self.mainArea, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = ShadowGui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="Select level of Plotting",
                                            labelWidth=220,
                                            items=["Detailed Plot", "Preview", "None"],
                                            callback=self.set_PlotQuality, sendSelectedValue=False, orientation="horizontal")

        self.tabs = gui.tabWidget(self.mainArea)

        self.initializeTabs()

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = gui.widgetBox(self.mainArea, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        self.shadow_output.setFixedHeight(150)
        self.shadow_output.setFixedWidth(850)

    def initializeTabs(self):
        size = len(self.tab)
        indexes = range(0, size)
        for index in indexes:
            self.tabs.removeTab(size-1-index)

        self.tab = [gui.createTabPage(self.tabs, "X,Z"),
                    gui.createTabPage(self.tabs, "X',Z'"),
                    gui.createTabPage(self.tabs, "X,X'"),
                    gui.createTabPage(self.tabs, "Z,Z'"),
                    gui.createTabPage(self.tabs, "Energy")]

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.plot_canvas = [None, None, None, None, None]
        self.plot_upper_canvas = [None, None, None, None, None]
        self.plot_right_canvas = [None, None, None, None, None]


    def set_PlotQuality(self):
        self.progressBarInit()

        if not self.plotted_beam==None:
            try:
                self.initializeTabs()
                self.plot_results(self.plotted_beam, 80)
            except Exception as exception:
                QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                           str(exception),
                    QtGui.QMessageBox.Ok)

                # CORRELATED TO QScrollArea Bug - see class Orange.canvas.gui.toolbox._ToolBoxScrollArea
                # self.error_id = self.error_id + 1
                # self.error(self.error_id, "Exception occurred: " + str(exception))

        self.progressBarFinished()

    def plot_xy(self, beam_out, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedPlotWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_xy(beam_out.beam, var_x, var_y, title, xtitle, ytitle, xum=xum, yum=yum)

        self.progressBarSet(progressBarValue)

    def plot_xy_fast(self, beam_out, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = PlotWindow(roi=False, control=False, position=False, plugins=False)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(False)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='darkblue')

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        ShadowPlot.plotxy_preview(self.plot_canvas[plot_canvas_index], beam_out.beam, var_x, var_y, nolost=1, title=title, xtitle=xtitle, ytitle=ytitle)

        self.progressBarSet(progressBarValue)

    def plot_histo(self, beam_out, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle, xum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedHistoWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_histo(beam_out.beam, var, 1, None, 23, title, xtitle, ytitle, xum=xum)

        self.progressBarSet(progressBarValue)

    def plot_histo_fast(self, beam_out, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = PlotWindow(roi=False, control=False, position=False, plugins=False)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='darkblue')

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        ShadowPlot.plot_histo_preview(self.plot_canvas[plot_canvas_index], beam_out.beam, var, 1, 23, title, xtitle, ytitle)

        self.progressBarSet(progressBarValue)

    def plot_results(self, beam_out, progressBarValue=80):
        if not self.view_type == 2:
            if ShadowGui.checkEmptyBeam(beam_out):
                if ShadowGui.checkGoodBeam(beam_out):
                    self.view_type_combo.setEnabled(False)

                    try:
                        if self.view_type == 1:
                            self.plot_xy_fast(beam_out, progressBarValue + 4, 1, 3, plot_canvas_index=0, title="X,Z", xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]')
                            self.plot_xy_fast(beam_out, progressBarValue + 8, 4, 6, plot_canvas_index=1, title="X',Z'", xtitle="X' [$\mu$rad]", ytitle="Z' [$\mu$rad]")
                            self.plot_xy_fast(beam_out, progressBarValue + 12, 1, 4, plot_canvas_index=2, title="X,X'", xtitle=r'X [$\mu$m]', ytitle="X' [$\mu$rad]")
                            self.plot_xy_fast(beam_out, progressBarValue + 16, 3, 6, plot_canvas_index=3, title="Z,Z'", xtitle=r'Z [$\mu$m]', ytitle="Z' [$\mu$rad]")
                            self.plot_histo_fast(beam_out, progressBarValue + 20, 11, plot_canvas_index=4, title="Energy", xtitle="Energy [eV]", ytitle="Number of Rays")
                        elif self.view_type == 0:
                            self.plot_xy(beam_out, progressBarValue + 4, 1, 3, plot_canvas_index=0, title="X,Z", xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]',
                                         xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
                            self.plot_xy(beam_out, progressBarValue + 8, 4, 6, plot_canvas_index=1, title="X',Z'", xtitle="X' [$\mu$rad]", ytitle="Z' [$\mu$rad]",
                                         xum="X' [" + u"\u03BC" + "rad]", yum="Z' [" + u"\u03BC" + "rad]")
                            self.plot_xy(beam_out, progressBarValue + 12, 1, 4, plot_canvas_index=2, title="X,X'", xtitle=r'X [$\mu$m]', ytitle="X' [$\mu$rad]",
                                         xum=("X [" + u"\u03BC" + "m]"), yum="X' [" + u"\u03BC" + "rad]")
                            self.plot_xy(beam_out, progressBarValue + 16, 3, 6, plot_canvas_index=3, title="Z,Z'", xtitle=r'Z [$\mu$m]', ytitle="Z' [$\mu$rad]",
                                         xum=("Z [" + u"\u03BC" + "m]"), yum="Z' [" + u"\u03BC" + "rad]")
                            self.plot_histo(beam_out, progressBarValue + 20, 11, plot_canvas_index=4, title="Energy", xtitle="Energy [eV]", ytitle="Number of Rays", xum="[eV]")
                    except Exception:
                        self.view_type_combo.setEnabled(True)

                        raise Exception("Data not plottable: No good rays or bad content")

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

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = GenericElement()
    ow.show()
    a.exec_()
    ow.saveSettings()