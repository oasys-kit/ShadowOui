__author__ = 'labx'

import os, sys

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSettings
from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import TriggerIn, TriggerOut


from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowSource, ShadowFile
from orangecontrib.shadow.widgets.gui import ow_generic_element

from syned.widget.widget_decorator import WidgetDecorator

shadow_src_to_copy = None

class Source(ow_generic_element.GenericElement):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Trigger", TriggerOut, "sendNewBeam")]

    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    file_to_write_out = Setting(0)

    want_main_area=1

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

    number_of_rays=Setting(5000)
    seed=Setting(5676561)

    scanning_data = None

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box)

        self.runaction = widget.OWAction("Copy Source Parameters", self)
        self.runaction.triggered.connect(self.copy_src_parameters)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Paste Source Parameters", self)
        self.runaction.triggered.connect(self.paste_src_parameters)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Run Shadow/Source", self)
        self.runaction.triggered.connect(self.runShadowSource)
        self.addAction(self.runaction)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow/Source", callback=self.runShadowSource)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

    def initializeTabs(self):
        current_tab = self.tabs.currentIndex()

        enabled = self.isFootprintEnabled()

        size = len(self.tab)
        indexes = range(0, size)
        for index in indexes:
            self.tabs.removeTab(size-1-index)

        show_effective_source_size = QSettings().value("output/show-effective-source-size", 0, int) == 1

        titles = self.getTitles()

        if show_effective_source_size:
            self.tab = [oasysgui.createTabPage(self.tabs, titles[0]),
                        oasysgui.createTabPage(self.tabs, titles[1]),
                        oasysgui.createTabPage(self.tabs, titles[2]),
                        oasysgui.createTabPage(self.tabs, titles[3]),
                        oasysgui.createTabPage(self.tabs, titles[4]),
                        oasysgui.createTabPage(self.tabs, titles[5]),
            ]

            self.plot_canvas = [None, None, None, None, None, None]
        else:
            self.tab = [oasysgui.createTabPage(self.tabs, titles[0]),
                        oasysgui.createTabPage(self.tabs, titles[1]),
                        oasysgui.createTabPage(self.tabs, titles[2]),
                        oasysgui.createTabPage(self.tabs, titles[3]),
                        oasysgui.createTabPage(self.tabs, titles[4]),
            ]

            self.plot_canvas = [None, None, None, None, None]

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.enableFootprint(enabled)

        self.tabs.setCurrentIndex(min(current_tab, len(self.tab)-1))

    def isFootprintEnabled(self):
        return False

    def enableFootprint(self, enabled=False):
        pass

    def get_write_file_options(self):
        write_begin_file = 0
        write_start_file = 0
        write_end_file = 0

        if self.file_to_write_out == 1:
            write_begin_file = 1
        if self.file_to_write_out == 2:
            write_begin_file = 1

            if sys.platform == 'linux':
                QMessageBox.warning(self, "Warning", "Debug Mode is not yet available for sources in Linux platforms", QMessageBox.Ok)
            else:
                write_start_file = 1
                write_end_file = 1

        return write_begin_file, write_start_file, write_end_file

    def copy_src_parameters(self):
        global shadow_src_to_copy

        shadow_src_to_copy = ShadowSource.create_src()

        self.populateFields(shadow_src_to_copy)

        shadow_src_to_copy.set_source_type(self.__class__.__name__)

    def paste_src_parameters(self):
        global shadow_src_to_copy

        if not shadow_src_to_copy is None:
            try:
                if "BendingMagnet" in shadow_src_to_copy.source_type and not "BendingMagnet" in str(self.__class__):
                    raise Exception("Paste Parameters not allowed:\nDestination Source is not a BendingMagnet")
                elif "Undulator" in shadow_src_to_copy.source_type and not "Undulator" in str(self.__class__):
                    raise Exception("Paste Parameters not allowed:\nDestination Source is not an Undulator")
                elif "Geometrical" in shadow_src_to_copy.source_type and not "Geometrical" in str(self.__class__):
                    raise Exception("Paste Parameters not allowed:\nDestination Source is not a Geometrical Source")
                elif "Wiggler" in shadow_src_to_copy.source_type and not "Wiggler" in str(self.__class__):
                    raise Exception("Paste Parameters not allowed:\nDestination Source is not a Wiggler")

                if QMessageBox.information(self, "Confirm Operation",
                                              "Confirm Paste Operation?",
                                              QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                    shadow_temp_file = congruence.checkFileName("tmp_src_buffer.dat")
                    shadow_src_to_copy.src.write(shadow_temp_file)

                    shadow_file, type = ShadowFile.readShadowFile(shadow_temp_file)

                    self.deserialize(shadow_file)

            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

    def sendNewBeam(self, trigger):
        self.scanning_data = None

        if trigger and trigger.new_object == True:
            if trigger.has_additional_parameter("seed_increment"):
                self.seed += trigger.get_additional_parameter("seed_increment")
            elif trigger.has_additional_parameter("variable_name") and self.is_scanning_enabled():
                variable_name = trigger.get_additional_parameter("variable_name").strip()
                variable_display_name = trigger.get_additional_parameter("variable_display_name").strip()
                variable_value = trigger.get_additional_parameter("variable_value")
                variable_um = trigger.get_additional_parameter("variable_um")

                def check_number(x):
                    try:    return float(x)
                    except: return x

                if "," in variable_name:
                    variable_names = variable_name.split(",")

                    if isinstance(variable_value, str) and "," in variable_value:
                        variable_values = variable_value.split(",")
                        for variable_name, variable_value in zip(variable_names, variable_values):
                            setattr(self, variable_name.strip(), check_number(variable_value))
                            self.check_source_options(variable_name)
                    else:
                        for variable_name in variable_names:
                            setattr(self, variable_name.strip(), check_number(variable_value))
                            self.check_source_options(variable_name)
                else:
                    setattr(self, variable_name, check_number(variable_value))
                    self.check_source_options(variable_name)

                self.scanning_data=ShadowBeam.ScanningData(variable_name, variable_value, variable_display_name, variable_um)

            self.runShadowSource()

    def is_scanning_enabled(self):
        return False

    def check_source_options(self, variable_name):
        pass

    def populateFields(self, shadow_src):
        pass

    def deserialize(self, shadow_file):
        pass

    def plot_results(self, beam_out, footprint_beam=None, progressBarValue=80):
        show_effective_source_size = QSettings().value("output/show-effective-source-size", 0, int) == 1

        if show_effective_source_size:
            if len(self.tab)==5: self.initializeTabs()
        else:
            if len(self.tab)==6: self.initializeTabs()

        super().plot_results(beam_out, footprint_beam, progressBarValue)

        if show_effective_source_size and not self.view_type == 2:
            effective_source_size_beam = beam_out.duplicate(history=False)
            effective_source_size_beam._beam.retrace(0)

            variables = self.getVariablestoPlot()
            titles = self.getTitles()
            xtitles = self.getXTitles()
            ytitles = self.getYTitles()
            xums = self.getXUM()
            yums = self.getYUM()

            if self.view_type == 1:
                self.plot_xy_fast(effective_source_size_beam, 100,  variables[0][0], variables[0][1], plot_canvas_index=5, title=titles[0], xtitle=xtitles[0], ytitle=ytitles[0])
            elif self.view_type == 0:
                self.plot_xy(effective_source_size_beam, 100,  variables[0][0], variables[0][1], plot_canvas_index=5, title=titles[0], xtitle=xtitles[0], ytitle=ytitles[0], xum=xums[0], yum=yums[0])

    def runShadowSource(self):
        raise NotImplementedError("This method is abstract")

    def getTitles(self):
        return ["X,Z", "X',Z'", "X,X'", "Z,Z'", "Energy", "Effective Source Size"]
