
from oasys.widgets import gui as oasysgui, congruence

from PyQt4 import QtGui
from srxraylib.plot import gol
import numpy, sys, os
import xraylib

from orangecontrib.xoppy.util.xoppy_xraylib_util import f1f2_calc

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

#file_name = None
file_name = "/Users/labx/Desktop/AnnaB/efficiencies.asc"

try:
    if file_name is None:
        file_name = oasysgui.selectFileFromDialog(None, None, "Open ASC file")

    congruence.checkFile(file_name)

    data = numpy.loadtxt(file_name, skiprows=1)

    energies = data[:, 0]
    angles = numpy.radians((180-data[:, 3])/2)
    reflectivities = numpy.zeros((energies.size, angles.size))

    density = xraylib.ElementDensity(xraylib.SymbolToAtomicNumber("Au"))

    for i, itheta in enumerate(angles):
        reflectivities[:, i] = f1f2_calc("Au", energies, itheta, F=10,rough=0.0,density=density)

    angles = numpy.degrees(angles)

    file_out = open(os.path.dirname(file_name) + "/reflectivities.out", mode="w")
    rows = ["Energy (eV)  Theta (deg)  Reflectivity\n"]
    for i in range(0, energies.size):
        for j in range(0, angles.size):
            rows.append(str(energies[i]) + "   " + str(angles[j]) + "   " + str(reflectivities[i, j]) + "\n")

    file_out.writelines(rows)
    file_out.close()

    print("File out", os.path.dirname(file_name) + "/reflectivities.out", "written on disk")

    gol.plot_image(reflectivities,
                   energies,
                   angles,
                   xtitle='Energy [eV]',
                   ytitle='Theta [deg]',
                   title='Reflectivity',
                   show=True,
                   aspect='auto')
    '''
    figure = plt.figure()
    figure.patch.set_facecolor('white')

    axis = figure.add_subplot(111, projection='3d')

    x_to_plot, y_to_plot = numpy.meshgrid(energies, numpy.degrees(angles))
    z_to_plot = reflectivities

    axis.plot_surface(x_to_plot, y_to_plot, z_to_plot, rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

    axis.set_xlabel("Energy [eV]")
    axis.set_ylabel("Theta [deg]")
    axis.set_zlabel("Reflectivity")

    axis.set_title("Reflectivity vs E vs Theta")
    axis.mouse_init()

    plt.show()
    '''

except Exception as e:
    print(e)

    raise e

if __name__ == "__main__":
    app.quit()

