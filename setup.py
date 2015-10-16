#! /usr/bin/env python3

import os

from setuptools import find_packages, setup


NAME = 'ShadowOui'
VERSION = '1.2.20'
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
    'matplotlib',
    'srxraylib',
    'orange-widget-core>=0.0.2',
    'oasys>=0.1',
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.shadow.widgets.gui":["misc/*.*"],
    "orangecontrib.shadow.widgets.experimental_elements":["icons/*.png", "icons/*.jpg", "misc/*.*", "data/*.*"],
    "orangecontrib.shadow.widgets.optical_elements":["icons/*.png", "icons/*.jpg"],
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
        "Shadow Visualization = orangecontrib.shadow.widgets.plots",
        "Shadow PreProcessor = orangecontrib.shadow.widgets.preprocessor",
        "Shadow Sources = orangecontrib.shadow.widgets.sources",
        "Shadow Utility = orangecontrib.shadow.widgets.utility",
    ),
    'oasys.menus' : ("Menu = orangecontrib.shadow.menu",)
}

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
