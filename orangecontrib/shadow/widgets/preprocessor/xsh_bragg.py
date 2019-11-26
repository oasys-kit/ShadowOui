import os, sys

import numpy, scipy, xraylib, cmath

from PyQt5.QtWidgets import QLabel, QApplication, QMessageBox, QSizePolicy
from PyQt5.QtGui import QTextCursor, QIntValidator, QDoubleValidator, QPixmap
from PyQt5.QtCore import Qt
from Shadow.ShadowPreprocessorsXraylib import bragg

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData

class OWxsh_bragg(OWWidget):
    name = "Bragg"
    id = "xsh_bragg"
    description = "Calculation of crystal diffraction profile"
    icon = "icons/bragg.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 1
    category = ""
    keywords = ["oasys", "bragg"]

    outputs = [{"name":"PreProcessor_Data",
                "type":ShadowPreProcessorData,
                "doc":"PreProcessor Data",
                "id":"PreProcessor_Data"}]

    want_main_area = False

    DESCRIPTOR = Setting(0)
    H_MILLER_INDEX = Setting(1)
    K_MILLER_INDEX = Setting(1)
    L_MILLER_INDEX = Setting(1)
    TEMPERATURE_FACTOR = Setting(1.0)
    E_MIN = Setting(5000.0)
    E_MAX = Setting(15000.0)
    E_STEP = Setting(100.0)
    SHADOW_FILE = Setting("bragg.dat")


    crystals = [
        "Si",
        "Si_NIST",
        "Si2",
        "Ge",
        "Diamond",
        "GaAs",
        "GaSb",
        "GaP",
        "InAs",
        "InP",
        "InSb",
        "SiC",   #11  Up to here they are ZincBlende structure, thus accepred by the preprocessor
        # "NaCl",
        # "CsF",
        # "LiF",
        # "KCl",
        # "CsCl",
        # "Be",
        "Graphite",  # this one is accepted via ad-hoc patch (bragg_new)
        # "PET",
        # "Beryl",
        # "KAP",
        # "RbAP",
        # "TlAP",
        # "Muscovite",
        # "AlphaQuartz",
        # "Copper",
        # "LiNbO3",
        # "Platinum",
        # "Gold",
        # "Sapphire",
        # "LaB6",
        # "LaB6_NIST",
        # "KTP",
        # "AlphaAlumina",
        # "Aluminum",
        # "Iron",
        # "Titanium"
    ]

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "bragg_usage.png")

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(550)
        self.setFixedHeight(550)

        idx = -1 
        
        gui.separator(self.controlArea)

        box0 = oasysgui.widgetBox(self.controlArea, "",orientation="horizontal")
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Help", callback=self.help1)
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Crystal Settings")
        tab_out = oasysgui.createTabPage(tabs_setting, "Output")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)


        #widget index 0
        idx += 1 
        box = oasysgui.widgetBox(tab_bas, "Crystal Parameters", orientation="vertical")
        gui.comboBox(box, self, "DESCRIPTOR",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=self.crystals, sendSelectedValue=False,
                     valueType=int, orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box)
        
        #widget index 1 
        idx += 1 
        box_miller = oasysgui.widgetBox(box, "", orientation = "horizontal")
        oasysgui.lineEdit(box_miller, self, "H_MILLER_INDEX",
                     label="Miller Indices [h k l]", addSpace=True,
                    valueType=int, validator=QIntValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_miller)
        
        #widget index 2 
        idx += 1 
        oasysgui.lineEdit(box_miller, self, "K_MILLER_INDEX", addSpace=True,
                    valueType=int, validator=QIntValidator())
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 3 
        idx += 1 
        oasysgui.lineEdit(box_miller, self, "L_MILLER_INDEX",
                     addSpace=True,
                    valueType=int, validator=QIntValidator(), orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 

        gui.separator(box)

        #widget index 4 
        idx += 1 
        oasysgui.lineEdit(box, self, "TEMPERATURE_FACTOR",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 5 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_MIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 6 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_MAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 7 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_STEP",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 8 
        idx += 1
        box_2 = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal")

        self.le_SHADOW_FILE = oasysgui.lineEdit(box_2, self, "SHADOW_FILE",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=180, orientation="horizontal")

        gui.button(box_2, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=400)
        out_box.layout().addWidget(self.shadow_output)

        self.process_showers()

        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Crystal descriptor','H miller index','K miller index','L miller index','Temperature factor','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]','File name (for SHADOW)']


    def unitFlags(self):
         return ['True','True','True','True','True','True','True','True','True']

    def selectFile(self):
        self.le_SHADOW_FILE.setText(oasysgui.selectFileFromDialog(self, self.SHADOW_FILE, "Select Output File"))

    def compute(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()
            if self.DESCRIPTOR <= 11: # accepted crystals
                tmp = bragg(interactive=False,
                            DESCRIPTOR=self.crystals[self.DESCRIPTOR],
                            H_MILLER_INDEX=self.H_MILLER_INDEX,
                            K_MILLER_INDEX=self.K_MILLER_INDEX,
                            L_MILLER_INDEX=self.L_MILLER_INDEX,
                            TEMPERATURE_FACTOR=self.TEMPERATURE_FACTOR,
                            E_MIN=self.E_MIN,
                            E_MAX=self.E_MAX,
                            E_STEP=self.E_STEP,
                            SHADOW_FILE=congruence.checkFileName(self.SHADOW_FILE))
            elif self.crystals[self.DESCRIPTOR] == "Graphite": # GRAPHITE
                OWxsh_bragg.new_bragg(H_MILLER_INDEX=self.H_MILLER_INDEX,
                                      K_MILLER_INDEX=self.K_MILLER_INDEX,
                                      L_MILLER_INDEX=self.L_MILLER_INDEX,
                                      TEMPERATURE_FACTOR=self.TEMPERATURE_FACTOR,
                                      E_MIN=self.E_MIN,
                                      E_MAX=self.E_MAX,
                                      E_STEP=self.E_STEP,
                                      SHADOW_FILE=congruence.checkFileName(self.SHADOW_FILE))
            else:
                QMessageBox.critical(self, "Error.",
                                     "Crystal %s is not implemented in shadow3"%self.crystals[self.DESCRIPTOR],
                                     QMessageBox.Ok)

            self.send("PreProcessor_Data", ShadowPreProcessorData(bragg_data_file=self.SHADOW_FILE))

        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    @classmethod
    def new_bragg(cls,
                  DESCRIPTOR="Graphite",
                  H_MILLER_INDEX=0,
                  K_MILLER_INDEX=0,
                  L_MILLER_INDEX=2,
                  TEMPERATURE_FACTOR=1.0,
                  E_MIN=5000.0,
                  E_MAX=15000.0,
                  E_STEP=100.0,
                  SHADOW_FILE="bragg.dat"):

        """
         SHADOW preprocessor for crystals - python+xraylib version

         -"""
        # retrieve physical constants needed
        codata = scipy.constants.codata.physical_constants
        codata_e2_mc2, tmp1, tmp2 = codata["classical electron radius"]
        # or, hard-code them
        # In [179]: print("codata_e2_mc2 = %20.11e \n" % codata_e2_mc2 )
        # codata_e2_mc2 =    2.81794032500e-15

        fileout = SHADOW_FILE
        descriptor = DESCRIPTOR

        hh = int(H_MILLER_INDEX)
        kk = int(K_MILLER_INDEX)
        ll = int(L_MILLER_INDEX)

        temper = float(TEMPERATURE_FACTOR)

        emin = float(E_MIN)
        emax = float(E_MAX)
        estep = float(E_STEP)

        #
        # end input section, start calculations
        #

        f = open(fileout, 'wt')

        cryst = xraylib.Crystal_GetCrystal(descriptor)
        volume = cryst['volume']

        #test crystal data - not needed
        itest = 1
        if itest:
            if (cryst == None):
                sys.exit(1)
            print ("  Unit cell dimensions are %f %f %f" % (cryst['a'],cryst['b'],cryst['c']))
            print ("  Unit cell angles are %f %f %f" % (cryst['alpha'],cryst['beta'],cryst['gamma']))
            print ("  Unit cell volume is %f A^3" % volume )
            print ("  Atoms at:")
            print ("     Z  fraction    X        Y        Z")
            for i in range(cryst['n_atom']):
                atom =  cryst['atom'][i]
                print ("    %3i %f %f %f %f" % (atom['Zatom'], atom['fraction'], atom['x'], atom['y'], atom['z']) )
            print ("  ")

        volume = volume*1e-8*1e-8*1e-8 # in cm^3
        #flag Graphite Struecture
        f.write( "%i " % 5)
        #1/V*electronRadius
        f.write( "%e " % ((1e0/volume)*(codata_e2_mc2*1e2)) )
        #dspacing
        dspacing = xraylib.Crystal_dSpacing(cryst, hh, kk, ll)
        f.write( "%e " % (dspacing*1e-8) )
        f.write( "\n")
        #Z's
        atom =  cryst['atom']
        f.write( "%i " % atom[0]["Zatom"] )
        f.write( "%i " % -1 )
        f.write( "%e " % temper ) # temperature parameter
        f.write( "\n")

        ga = (1e0+0j) + cmath.exp(1j*cmath.pi*(hh+kk))  \
                                 + cmath.exp(1j*cmath.pi*(hh+ll))  \
                                 + cmath.exp(1j*cmath.pi*(kk+ll))
        # gb = ga * cmath.exp(1j*cmath.pi*0.5*(hh+kk+ll))
        ga_bar = ga.conjugate()
        # gb_bar = gb.conjugate()


        f.write( "(%20.11e,%20.11e ) \n" % (ga.real, ga.imag) )
        f.write( "(%20.11e,%20.11e ) \n" % (ga_bar.real, ga_bar.imag) )
        f.write( "(%20.11e,%20.11e ) \n" % (0.0, 0.0) )
        f.write( "(%20.11e,%20.11e ) \n" % (0.0, 0.0) )

        zetas = [atom[0]["Zatom"]]
        for zeta in zetas:
            xx01 = 1e0/2e0/dspacing
            xx00 = xx01-0.1
            xx02 = xx01+0.1
            yy00= xraylib.FF_Rayl(int(zeta),xx00)
            yy01= xraylib.FF_Rayl(int(zeta),xx01)
            yy02= xraylib.FF_Rayl(int(zeta),xx02)
            xx = numpy.array([xx00,xx01,xx02])
            yy = numpy.array([yy00,yy01,yy02])
            fit = numpy.polyfit(xx,yy,2)
            #print "zeta: ",zeta
            #print "z,xx,YY: ",zeta,xx,yy
            #print "fit: ",fit[::-1] # reversed coeffs
            #print "fit-tuple: ",(tuple(fit[::-1].tolist())) # reversed coeffs
            #print("fit-tuple: %e %e %e  \n" % (tuple(fit[::-1].tolist())) ) # reversed coeffs
            f.write("%e %e %e  \n" % (tuple(fit[::-1].tolist())) ) # reversed coeffs

        f.write("%e %e %e  \n" % (0.0, 0.0, 0.0))  # reversed coeffs


        npoint  = int( (emax - emin)/estep + 1 )
        f.write( ("%i \n") % npoint)
        for i in range(npoint):
            energy = (emin+estep*i)
            f1a = xraylib.Fi(int(zetas[0]),energy*1e-3)
            f2a = xraylib.Fii(int(zetas[0]),energy*1e-3)
            # f1b = xraylib.Fi(int(zetas[1]),energy*1e-3)
            # f2b = xraylib.Fii(int(zetas[1]),energy*1e-3)
            out = numpy.array([energy,f1a,abs(f2a),1.0, 0.0])
            f.write( ("%20.11e %20.11e %20.11e \n %20.11e %20.11e \n") % ( tuple(out.tolist()) ) )

        f.close()
        print("File written to disk: %s" % fileout)


    def checkFields(self):
        if type(self.DESCRIPTOR) == str: # back compatibility with old version
            try:
                self.DESCRIPTOR = self.crystals.index(self.DESCRIPTOR)
            except:
                self.DESCRIPTOR = 0

        self.H_MILLER_INDEX = congruence.checkNumber(self.H_MILLER_INDEX, "H miller index")
        self.K_MILLER_INDEX = congruence.checkNumber(self.K_MILLER_INDEX, "K miller index")
        self.L_MILLER_INDEX = congruence.checkNumber(self.L_MILLER_INDEX, "L miller index")
        self.TEMPERATURE_FACTOR = congruence.checkNumber(self.TEMPERATURE_FACTOR, "Temperature factor")
        self.E_MIN  = congruence.checkPositiveNumber(self.E_MIN , "Minimum energy")
        self.E_MAX  = congruence.checkStrictlyPositiveNumber(self.E_MAX , "Maximum Energy")
        self.E_STEP = congruence.checkStrictlyPositiveNumber(self.E_STEP, "Energy step")
        congruence.checkLessOrEqualThan(self.E_MIN, self.E_MAX, "From Energy", "To Energy")
        congruence.checkDir(self.SHADOW_FILE)

    def defaults(self):
         self.resetSettings()
         self.compute()
         return

    def help1(self):
        print("help pressed. To be implemented.")

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWxsh_bragg()
    w.show()
    app.exec()
    w.saveSettings()
