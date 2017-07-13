__author__ = 'labx'

import os, sys

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox
from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.shadow.util.shadow_objects import ShadowTriggerOut, ShadowBeam, ShadowSource, ShadowFile
from orangecontrib.shadow.widgets.gui import ow_generic_element

from syned.widget.widget_decorator import WidgetDecorator

shadow_src_to_copy = None

class Source(ow_generic_element.GenericElement):

    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Trigger", ShadowTriggerOut, "sendNewBeam")]

    WidgetDecorator.append_syned_input_data(inputs)

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    file_to_write_out = Setting(0)

    want_main_area=1

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

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

    def populateFields(self, shadow_src):
        pass

    def deserialize(self, shadow_file):
        pass
