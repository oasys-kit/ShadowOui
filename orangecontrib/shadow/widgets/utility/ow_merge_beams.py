from PyQt4 import QtGui
from PyQt4.QtCore import QRect
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QPalette, QColor, QFont

from orangewidget import widget, gui
from oasys.widgets import gui as oasysgui

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

class MergeBeams(widget.OWWidget):

    name = "Merge Shadow Beam"
    description = "Display Data: Merge Shadow Beam"
    icon = "icons/merge.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 4
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam # 1" , ShadowBeam, "setBeam1" ),
              ("Input Beam # 2" , ShadowBeam, "setBeam2" ),
              ("Input Beam # 3" , ShadowBeam, "setBeam3" ),
              ("Input Beam # 4" , ShadowBeam, "setBeam4" ),
              ("Input Beam # 5" , ShadowBeam, "setBeam5" ),
              ("Input Beam # 6" , ShadowBeam, "setBeam6" ),
              ("Input Beam # 7" , ShadowBeam, "setBeam7" ),
              ("Input Beam # 8" , ShadowBeam, "setBeam8" ),
              ("Input Beam # 9" , ShadowBeam, "setBeam9" ),
              ("Input Beam # 10", ShadowBeam, "setBeam10"),]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    WIDGET_WIDTH = 250
    WIDGET_HEIGHT = 150

    want_main_area=0
    want_control_area = 1

    input_beam1=None
    input_beam2=None
    input_beam3=None
    input_beam4=None
    input_beam5=None
    input_beam6=None
    input_beam7=None
    input_beam8=None
    input_beam9=None
    input_beam10=None

    def __init__(self, show_automatic_box=True):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height()*0.95, self.WIDGET_HEIGHT))))


        gen_box = gui.widgetBox(self.controlArea, "Merge Shadow Beams", addSpace=True, orientation="horizontal")

        button_box = oasysgui.widgetBox(gen_box, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Merge Beams and Send", callback=self.merge_beams)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

    def setBeam1(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam1 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #1 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam2(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam2 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #2 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam3(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam3 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #3 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam4(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam4 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #4 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam5(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam5 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #5 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam6(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam6 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #6 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam7(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam7 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #7 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam8(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam8 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #8 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam9(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam9 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #9 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam10(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam10 = beam
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #10 not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def merge_beams(self):
        merged_beam = None

        if not self.input_beam1 is None:
            merged_beam = self.input_beam1

        for index in range(2, 11):

            if not getattr(self, "input_beam" + str(index)) is None:
                if merged_beam is None: merged_beam = getattr(self, "input_beam" + str(index))
                else: merged_beam = ShadowBeam.mergeBeams(merged_beam, getattr(self, "input_beam" + str(index)))

        self.send("Beam", merged_beam)