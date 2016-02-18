#! /usr/bin/env python3

import os

from setuptools import find_packages, setup

NAME = 'ShadowOui'
VERSION = '1.3.12'
ISRELEASED = False

DESCRIPTION = 'Shadow, Ray-tracing simulation software'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.txt')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Luca Rebuffi, Manuel Sanchez del Rio and Bioinformatics Laboratory, FRI UL'
AUTHOR_EMAIL = 'luca.rebuffi@elettra.eu'
URL = 'http://github.com/lucarebuffi/ShadowOui'
DOWNLOAD_URL = 'http://github.com/lucarebuffi/ShadowOui'
LICENSE = 'GPLv3'

KEYWORDS = (
    'ray-tracing',
    'simulator',
    'oasys',
)

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
)

SETUP_REQUIRES = (
    'setuptools',
)

INSTALL_REQUIRES = (
    'setuptools',
    'numpy',
    'scipy',
    'matplotlib==1.4.3', #problems found with 1.5.0
    'srxraylib>=1.0.1',
    'orange-widget-core>=0.0.2',
    'oasys>=0.1.11',
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.shadow.widgets.gui":["misc/*.*"],
    "orangecontrib.shadow.widgets.experimental_elements":["icons/*.png", "icons/*.jpg", "misc/*.*", "data/*.*"],
    "orangecontrib.shadow.widgets.optical_elements":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow.widgets.special_elements":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow.widgets.compound_optical_elements": ["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow.widgets.loop_management":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow.widgets.plots":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow.widgets.preprocessor":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow.widgets.sources":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow.widgets.utility":["icons/*.png", "icons/*.jpg"],
}

NAMESPACE_PACAKGES = ["orangecontrib", "orangecontrib.shadow", "orangecontrib.shadow.widgets"]

ENTRY_POINTS = {
    'oasys.addons' : ("shadow = orangecontrib.shadow", ),
    'oasys.widgets' : (
        "Shadow Experiments = orangecontrib.shadow.widgets.experimental_elements",
        "Shadow Loop Management = orangecontrib.shadow.widgets.loop_management",
        "Shadow Optical Elements = orangecontrib.shadow.widgets.optical_elements",
        "Shadow Compound Optical Elements = orangecontrib.shadow.widgets.compound_optical_elements",
        "Shadow Special Elements = orangecontrib.shadow.widgets.special_elements",
        "Shadow PostProcessor = orangecontrib.shadow.widgets.plots",
        "Shadow PreProcessor = orangecontrib.shadow.widgets.preprocessor",
        "Shadow Sources = orangecontrib.shadow.widgets.sources",
        "Shadow Utility = orangecontrib.shadow.widgets.utility",
    ),
    'oasys.menus' : ("shadowmenu = orangecontrib.shadow.menu",)
}

import site, shutil, sys, platform

if __name__ == '__main__':
    setup(
          name = NAME,
          version = VERSION,
          description = DESCRIPTION,
          long_description = LONG_DESCRIPTION,
          author = AUTHOR,
          author_email = AUTHOR_EMAIL,
          url = URL,
          download_url = DOWNLOAD_URL,
          license = LICENSE,
          keywords = KEYWORDS,
          classifiers = CLASSIFIERS,
          packages = PACKAGES,
          package_data = PACKAGE_DATA,
          #          py_modules = PY_MODULES,
          setup_requires = SETUP_REQUIRES,
          install_requires = INSTALL_REQUIRES,
          #extras_require = EXTRAS_REQUIRE,
          #dependency_links = DEPENDENCY_LINKS,
          entry_points = ENTRY_POINTS,
          namespace_packages=NAMESPACE_PACAKGES,
          include_package_data = True,
          zip_safe = False,
          )

    try:
        is_install = False
        is_develop = False

        for arg in sys.argv:
            if arg == 'install': is_install = True
            if arg == 'develop': is_develop = True

        if is_install and not is_develop:
            site_packages_dir = None

            for directory in site.getsitepackages():
                if os.path.exists(directory + "/oasys"):
                    site_packages_dir = directory  + "/"
                    break

            if not site_packages_dir is None:
                if platform.system()== 'Darwin':
                    version, _ , _ = platform.mac_ver()
                    version_data = version.split('.')

                    if int(version_data[0]) < 10 or int(version_data[1]) < 8: raise Exception("MacOSX version not supported (>= 10.8)")
                    if int(version_data[1]) < 10: version_dir = "10.8"
                    else: version_dir = "10.10"
                    
                    libraries_dir = "libraries/darwin/"
                    libraries_version_dir = libraries_dir + version_dir + "/"

                    if not os.path.exists(site_packages_dir + "xrayhelp.py"):
                        shutil.copyfile(libraries_dir + "xrayhelp.py", site_packages_dir + "xrayhelp.py")
                    if not os.path.exists(site_packages_dir + "xraylib.py"):
                        shutil.copyfile(libraries_dir + "xraylib.py", site_packages_dir + "xraylib.py")
                    if not os.path.exists(site_packages_dir + "xraymessages.py"):
                        shutil.copyfile(libraries_dir + "xraymessages.py", site_packages_dir + "xraymessages.py")
                    if not os.path.exists(site_packages_dir + "_xraylib.la"):
                        shutil.copyfile(libraries_version_dir + "_xraylib.la", site_packages_dir + "_xraylib.la")
                    if not os.path.exists(site_packages_dir + "_xraylib.so"):
                        shutil.copyfile(libraries_version_dir + "_xraylib.so", site_packages_dir + "_xraylib.so")
                    if not os.path.exists(site_packages_dir + "xraylib_np.la"):
                        shutil.copyfile(libraries_version_dir + "xraylib_np.la", site_packages_dir + "xraylib_np.la")
                    if not os.path.exists(site_packages_dir + "xraylib_np.so"):
                        shutil.copyfile(libraries_version_dir + "xraylib_np.so", site_packages_dir + "xraylib_np.so")
                elif platform.system() == 'Linux':
                    pass
    except Exception as exception:
        raise exception
        print(str(exception))