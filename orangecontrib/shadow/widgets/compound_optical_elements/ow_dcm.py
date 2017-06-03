import copy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

from orangewidget import gui
from orangewidget.settings import Setting

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData
from orangecontrib.shadow.widgets.gui import ow_compound_optical_element

class DCM(ow_compound_optical_element.CompoundOpticalElement):
    name = "Double-Crystal Monochromator"
    description = "Shadow Compound OE: Double-Crystal Monochromator"
    icon = "icons/dcm.png"
    priority = 5

    NONE_SPECIFIED = "NONE SPECIFIED"

    p = Setting(0.0)
    q = Setting(0.0)
    photon_energy_ev = Setting(14000.0)
    separation = Setting(100.0)
    reflectivity_file = Setting(NONE_SPECIFIED)

    has_finite_dimensions = Setting([0, 0])
    dimensions = Setting([[0.0, 0.0], [0.0, 0.0]])

    def __init__(self):
        super().__init__()

        self.le_p = oasysgui.lineEdit(self.tab_bas, self, "p", "Distance Source - DCM center (P)", labelWidth=280, valueType=float, orientation="horizontal")
        self.le_q = oasysgui.lineEdit(self.tab_bas, self, "q", "Distance DCM center - Image plane (Q)", labelWidth=280, valueType=float, orientation="horizontal")

        self.le_separation = oasysgui.lineEdit(self.tab_bas, self, "separation", "Separation between the Crystals\n(from center of 1st C. to center of 2nd C.)", labelWidth=280, valueType=float,
                           orientation="horizontal")

        oasysgui.lineEdit(self.tab_bas, self, "photon_energy_ev", "Photon Energy [eV]", labelWidth=280, valueType=float, orientation="horizontal")


        file_box = oasysgui.widgetBox(self.tab_bas, "", addSpace=True, orientation="horizontal", height=25)

        self.le_reflectivity_file = oasysgui.lineEdit(file_box, self, "reflectivity_file", "Reflectivity File", labelWidth=150, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectFilePrerefl)

        self.tab_crystals = oasysgui.tabWidget(self.tab_bas)

        tab_first_crystal = oasysgui.createTabPage(self.tab_crystals, "First Crystal")
        tab_second_crystal = oasysgui.createTabPage(self.tab_crystals, "Second Crystal")

        self.crystal_1_box = CrystalBox(dcm=self,
                                        parent=tab_first_crystal,
                                        has_finite_dimensions=self.has_finite_dimensions[0],
                                        dimensions=self.dimensions[0])

        self.crystal_2_box = CrystalBox(dcm=self,
                                        parent=tab_second_crystal,
                                        has_finite_dimensions=self.has_finite_dimensions[1],
                                        dimensions=self.dimensions[1])

    def after_change_workspace_units(self):
        label = self.le_p.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_q.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_separation.parent().layout().itemAt(0).widget()
        label.setText("Separation between the Crystals [" + self.workspace_units_label + "]\n(from center of 1st C. to center of 2nd C.)")

        self.crystal_1_box.after_change_workspace_units()
        self.crystal_2_box.after_change_workspace_units()


    def selectFilePrerefl(self):
        self.le_reflectivity_file.setText(oasysgui.selectFileFromDialog(self, self.reflectivity_file, "Select Reflectivity File", file_extension_filter="Data Files (*.dat)"))

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            self.resetSettings()

            while self.tab_crystals.count() > 0:
                self.tab_crystals.removeTab(0)

            tab_first_crystal = oasysgui.widgetBox(self.tab_crystals, addToLayout=0, margin=4)
            tab_second_crystal = oasysgui.widgetBox(self.tab_crystals, addToLayout=0, margin=4)

            self.crystal_1_box = CrystalBox(dcm=self,
                                            parent=tab_first_crystal,
                                            has_finite_dimensions=self.has_finite_dimensions[0],
                                            dimensions=self.dimensions[0])

            self.crystal_2_box = CrystalBox(dcm=self,
                                            parent=tab_second_crystal,
                                            has_finite_dimensions=self.has_finite_dimensions[1],
                                            dimensions=self.dimensions[1])

            self.tab_crystals.addTab(tab_first_crystal, "First Crystal")
            self.tab_crystals.addTab(tab_second_crystal, "Second Crystal")

            self.setupUI()


    def dumpSettings(self):
        bkp_has_finite_dimensions = copy.deepcopy(self.has_finite_dimensions)
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.has_finite_dimensions = []
            self.dimensions = []

            self.has_finite_dimensions.append(self.crystal_1_box.has_finite_dimensions)
            self.dimensions.append([self.crystal_1_box.mirror_width, self.crystal_1_box.mirror_length])

            self.has_finite_dimensions.append(self.crystal_2_box.has_finite_dimensions)
            self.dimensions.append([self.crystal_2_box.mirror_width, self.crystal_2_box.mirror_length])

        except:
            self.has_finite_dimensions = copy.deepcopy(bkp_has_finite_dimensions)
            self.dimensions = copy.deepcopy(bkp_dimensions)

    ##############################
    # SINGLE FIELDS SIGNALS
    ##############################

    def dump_has_finite_dimensions(self):
        bkp_has_finite_dimensions = copy.deepcopy(self.has_finite_dimensions)

        try:
            self.has_finite_dimensions = []

            self.has_finite_dimensions.append(self.crystal_1_box.has_finite_dimensions)
            self.has_finite_dimensions.append(self.crystal_2_box.has_finite_dimensions)
        except:
            self.has_finite_dimensions = copy.deepcopy(bkp_has_finite_dimensions)

    def dump_dimensions_0(self):
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.dimensions[0] = [self.crystal_1_box.mirror_width, self.crystal_1_box.mirror_length]
        except:
            self.dimensions = copy.deepcopy(bkp_dimensions)

    def dump_dimensions_1(self):
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.dimensions[1] = [self.crystal_2_box.mirror_width, self.crystal_2_box.mirror_length]
        except:
            self.dimensions = copy.deepcopy(bkp_dimensions)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def populateFields(self, shadow_oe):
        self.dumpSettings()

        dimension1_out = self.crystal_1_box.get_dimensions()
        dimension2_out = self.crystal_2_box.get_dimensions()

        shadow_oe._oe.append_monochromator_double_crystal(p0=self.p,
                                                         q0=self.q,
                                                         photon_energy_ev=self.photon_energy_ev,
                                                         separation=self.separation,
                                                         dimensions1=dimension1_out,
                                                         dimensions2=dimension2_out,
                                                         reflectivity_file=bytes(congruence.checkFileName(self.reflectivity_file), 'utf-8'))

    def checkFields(self):
        congruence.checkPositiveNumber(self.p, "Distance Source - KB center")
        congruence.checkPositiveNumber(self.q, "Distance KB center - Image plane")

        congruence.checkPositiveNumber(self.separation, "Separation between the Mirrors")
        congruence.checkStrictlyPositiveNumber(self.photon_energy_ev, "Photon Energy")

        congruence.checkFile(self.reflectivity_file)

        self.crystal_1_box.checkFields()
        self.crystal_2_box.checkFields()

    def setPreProcessorData(self, data):
        if data is not None:
            if data.bragg_data_file != ShadowPreProcessorData.NONE:
                self.reflectivity_file = data.bragg_data_file
                self.le_reflectivity_file.setText(data.bragg_data_file)

            else:
                QtWidgets.QMessageBox.warning(self, "Warning",
                          "Incompatible Preprocessor Data",
                          QtWidgets.QMessageBox.Ok)

    def setupUI(self):
        self.set_use_different_focal_positions()

        self.crystal_1_box.setupUI()
        self.crystal_2_box.setupUI()


class CrystalBox(QtWidgets.QWidget):
    has_finite_dimensions = 0
    mirror_width = 0.0
    mirror_length = 0.0

    dcm = None

    is_on_init = True

    def __init__(self,
                 dcm=None,
                 parent=None,
                 has_finite_dimensions=0,
                 dimensions=[0.0, 0.0]):
        super().__init__(parent)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.dcm = dcm

        self.setFixedWidth(self.dcm.CONTROL_AREA_WIDTH-20)
        self.setFixedHeight(130)

        self.has_finite_dimensions = has_finite_dimensions
        self.mirror_width = dimensions[0]
        self.mirror_length = dimensions[1]

        mirror_box = oasysgui.widgetBox(self, "Crystal Input Parameters", addSpace=False, orientation="vertical", height=120)

        gui.comboBox(mirror_box, self, "has_finite_dimensions", label="Dimensions", labelWidth=260,
                     items=["Finite", "Infinite"], sendSelectedValue=False, orientation="horizontal", callback=self.set_dimensions)

        self.dimension_box = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=50)
        self.dimension_box_empty = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=50)

        self.le_mirror_width = oasysgui.lineEdit(self.dimension_box, self, "mirror_width", "Crystal Width", labelWidth=260, valueType=float, orientation="horizontal",
                           callback=self.dcm.dump_dimensions_0)

        self.le_mirror_length = oasysgui.lineEdit(self.dimension_box, self, "mirror_length", "Crystal Length", labelWidth=260, valueType=float, orientation="horizontal",
                           callback=self.dcm.dump_dimensions_1)

        self.set_dimensions()

        self.is_on_init = False

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def after_change_workspace_units(self):
        label = self.le_mirror_width.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.dcm.workspace_units_label + "]")
        label = self.le_mirror_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.dcm.workspace_units_label + "]")

    def get_dimensions(self):
        if self.has_finite_dimensions == 0:
            return [self.mirror_width, self.mirror_length]
        elif self.has_finite_dimensions == 1:
            return [0.0, 0.0]
        else:
            raise ValueError("Dimensions")

    def set_dimensions(self):
        self.dimension_box.setVisible(self.has_finite_dimensions == 0)
        self.dimension_box_empty.setVisible(self.has_finite_dimensions != 0)

        if not self.is_on_init: self.dcm.dump_has_finite_dimensions()

    def checkFields(self):
        if self.has_finite_dimensions == 0:
            congruence.checkStrictlyPositiveNumber(self.mirror_width, "Mirror Width")
            congruence.checkStrictlyPositiveNumber(self.mirror_length, "Mirror Length")

    def setupUI(self):
        self.set_dimensions()
