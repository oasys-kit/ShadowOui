import sys
from PyQt4.QtGui import QTextEdit, QTextCursor, QIntValidator, QDoubleValidator, QApplication
from oasys.widgets import widget
from orangewidget import gui
from orangewidget.settings import Setting
from Shadow.ShadowPreprocessorsXraylib import pre_mlayer

try:
    from ..tools.xoppy_calc import xoppy_doc
except ImportError:
    #print("Error importing: xoppy_doc")
    #raise
    pass
except SystemError:
    pass

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, EmittingStream
from orangecontrib.shadow.util.shadow_util import ShadowGui

class OWxsh_pre_mlayer(widget.OWWidget):
    name = "xsh_pre_mlayer"
    id = "xsh_pre_mlayer"
    description = "xoppy application to compute..."
    icon = "icons/premlayer.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 10
    category = ""
    keywords = ["xoppy", "xsh_pre_mlayer"]

    outputs = [{"name":"PreProcessor_Data",
                "type":ShadowPreProcessorData,
                "doc":"PreProcessor Data",
                "id":"PreProcessor_Data"}]

    want_main_area = False

    FILE = Setting("mlayer.dat")
    E_MIN = Setting(5000.0)
    E_MAX = Setting(20000.0)
    S_DENSITY = Setting("2.33")
    S_MATERIAL = Setting("Si")
    E_DENSITY = Setting("2.40")
    E_MATERIAL = Setting("B4C")
    O_DENSITY = Setting("9.40")
    O_MATERIAL = Setting("Ru")
    GRADE_DEPTH = Setting(0)
    N_PAIRS = Setting(70)
    THICKNESS = Setting(33.1)
    GAMMA = Setting(0.483)
    ROUGHNESS_EVEN = Setting(3.3)
    ROUGHNESS_ODD = Setting(3.1)
    FILE_DEPTH = Setting("myfile_depth.dat")
    GRADE_SURFACE = Setting(0)
    FILE_SHADOW = Setting("mlayer1.sha")
    FILE_THICKNESS = Setting("mythick.dat")
    FILE_GAMMA = Setting("mygamma.dat")
    AA0 = Setting(1.0)
    AA1 = Setting(0.0)
    AA2 = Setting(0.0)


    def __init__(self):
        super().__init__()

        self.setFixedWidth(800)
        self.setFixedHeight(930)

        box = gui.widgetBox(self.controlArea, "Multilayer Parameters",orientation="vertical")

        idx = -1 
        
        #widget index 0 
        idx += 1 
        ShadowGui.lineEdit(box, self, "FILE",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 1
        idx += 1
        ShadowGui.lineEdit(box, self, "E_MIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 2
        idx += 1
        ShadowGui.lineEdit(box, self, "E_MAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 3
        idx += 1
        ShadowGui.lineEdit(box, self, "S_DENSITY",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 4
        idx += 1
        ShadowGui.lineEdit(box, self, "S_MATERIAL",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 5
        idx += 1
        ShadowGui.lineEdit(box, self, "E_DENSITY",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 6
        idx += 1
        ShadowGui.lineEdit(box, self, "E_MATERIAL",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 7
        idx += 1
        ShadowGui.lineEdit(box, self, "O_DENSITY",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 8
        idx += 1
        ShadowGui.lineEdit(box, self, "O_MATERIAL",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 9
        idx += 1
        gui.comboBox(box, self, "GRADE_DEPTH",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=['No (Constant)', 'thicknesses,gamma,rough_even and rough_off from file '],
                     valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)


        box_2 = gui.widgetBox(box, "",orientation="vertical")

        #widget index 10
        idx += 1
        ShadowGui.lineEdit(box_2, self, "N_PAIRS",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=int, validator=QIntValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 11
        idx += 1
        ShadowGui.lineEdit(box_2, self, "THICKNESS",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 12
        idx += 1
        ShadowGui.lineEdit(box_2, self, "GAMMA",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 13
        idx += 1
        ShadowGui.lineEdit(box_2, self, "ROUGHNESS_EVEN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 14
        idx += 1
        ShadowGui.lineEdit(box_2, self, "ROUGHNESS_ODD",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 15
        idx += 1
        ShadowGui.lineEdit(box_2, self, "FILE_DEPTH",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=450, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 16
        idx += 1
        gui.comboBox(box, self, "GRADE_SURFACE",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=['No (Constant)', 'thick and gamma graded (from spline files)', 'thickness graded (from quadratic fit)'],
                     valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        box_3 = gui.widgetBox(box, "",orientation="vertical")

        #widget index 17
        idx += 1
        ShadowGui.lineEdit(box_3, self, "FILE_SHADOW",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_3)

        #widget index 18
        idx += 1
        ShadowGui.lineEdit(box_3, self, "FILE_THICKNESS",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_3)

        #widget index 19
        idx += 1
        ShadowGui.lineEdit(box_3, self, "FILE_GAMMA",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_3)

        box_4 = gui.widgetBox(box, "",orientation="vertical")

        #widget index 20
        idx += 1
        ShadowGui.lineEdit(box_4, self, "AA0",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_4)

        #widget index 21
        idx += 1
        ShadowGui.lineEdit(box_4, self, "AA1",
                     label=self.unitLabels()[idx], addSpace=True,
                     valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_4)

        #widget index 22
        idx += 1
        ShadowGui.lineEdit(box_4, self, "AA2",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_4)

        self.process_showers()

        self.shadow_output = QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = ShadowGui.widgetBox(self.controlArea, "System Output", addSpace=True, orientation="horizontal", height=150)
        out_box.layout().addWidget(self.shadow_output)

        box0 = gui.widgetBox(self.controlArea, "",orientation="horizontal")
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Help", callback=self.help1)
        button.setFixedHeight(45)


        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Output file (for SHADOW/trace): ',
                 'Min Energy [eV]','Max Energy [eV]',
                 'Density (substrate) [g/cm3]',
                 'Material (substrate) (element or formula)',
                 'Density (even "bottom" sublayer) [g/cm3]',
                 'Material (even sublayer) (element or formula)',
                 'Density (odd "top" sublayer) [g/cm3]',
                 'Material (odd sublayer) (element or formula)',
                 'Bilayer thicknesses graded along the depth? ',
                 'Number of bilayers ',
                 'bilayer thickness t [A]',
                 'gamma ratio [t_even/(t_odd+t_even)]',
                 'Roughness even layer [A]',
                 'Roughness odd layer [A]',
                 'File with list of t_bilayer,gamma,roughness_even,roughness_odd:',
                 'Bilayer thicknesses/gamma graded along the surface? ',
                 'Output binary file (for SHADOW) with splines',
                 'File with bilayer thicknesses versus surface (PRESURFACE format)',
                 'File with bilayer gamma versus surface (PRESURFACE format)',
                 'Fit bilayer t(y)/t(y=0) vs y: zero-order coefficient (constant)',
                 'Fit bilayer t(y)/t(y=0) vs y: linear coefficient (slope)',
                 'Fit bilayer t(y)/t(y=0) vs y: 2nd degree coefficient']


    def unitFlags(self):
         return ['True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  1',
                 'True',
                 'self.GRADE_SURFACE  ==  1',
                 'self.GRADE_SURFACE  ==  1',
                 'self.GRADE_SURFACE  ==  1',
                 'self.GRADE_SURFACE  ==  2',
                 'self.GRADE_SURFACE  ==  2',
                 'self.GRADE_SURFACE  ==  2']

    def compute(self):
        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        tmp = pre_mlayer(interactive=False,
                         FILE=self.FILE,
                         E_MIN=self.E_MIN,
                         E_MAX=self.E_MAX,
                         S_DENSITY=self.S_DENSITY,
                         S_MATERIAL=self.S_MATERIAL,
                         E_DENSITY=self.E_DENSITY,
                         E_MATERIAL=self.E_MATERIAL,
                         O_DENSITY=self.O_DENSITY,
                         O_MATERIAL=self.O_MATERIAL,
                         GRADE_DEPTH=self.GRADE_DEPTH,
                         N_PAIRS=self.N_PAIRS,
                         THICKNESS=self.THICKNESS,
                         GAMMA=self.GAMMA,
                         ROUGHNESS_EVEN=self.ROUGHNESS_EVEN,
                         ROUGHNESS_ODD=self.ROUGHNESS_ODD,
                         FILE_DEPTH=self.FILE_DEPTH,
                         GRADE_SURFACE=self.GRADE_SURFACE,
                         FILE_SHADOW=self.FILE_SHADOW,
                         FILE_THICKNESS=self.FILE_THICKNESS,
                         FILE_GAMMA=self.FILE_GAMMA,
                         AA0=self.AA0,
                         AA1=self.AA1,
                         AA2=self.AA2)

        self.send("PreProcessor_Data", ShadowPreProcessorData(m_layer_data_file_dat=self.FILE, m_layer_data_file_sha=self.FILE_SHADOW))

    def defaults(self):
         self.resetSettings()
         #self.compute()
         return

    def help1(self):
        print("help pressed.")
        try:
            xoppy_doc('xsh_pre_mlayer')
        except:
            pass

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWxsh_pre_mlayer()
    w.show()
    app.exec()
    w.saveSettings()
