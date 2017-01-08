#!/usr/bin/env python

import os
from setuptools import setup
from lbrynet import conf
from pip import req as pip_req, download as pip_download
from distutils.sysconfig import get_python_lib

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macos")
APP_PATH = os.path.join(APP_DIR, "main.py")
requirements_path = os.path.join(APP_DIR, "requirements.txt")
site_packages = get_python_lib()

DATA_FILES = [os.path.join(APP_DIR, 'app.icns')]

_requirements = pip_req.parse_requirements(requirements_path, session=pip_download.PipSession())
requirements = []
for item in _requirements:
    if item.req:
        requirements.append(str(item.req))
    if getattr(item, 'markers', None):
        if item.markers is not None:
            # remove OS specific requirements
            if getattr(item.markers, 'evaluate', None):
                if not item.markers.evaluate():
                    requirements.remove(str(item.req))
            else:
                print "Don't know how to process markers: %s" % str(item.markers)

OPTIONS = {
    'iconfile': conf.ICON_PATH,
    'plist': {
        'CFBundleIdentifier': 'io.lbry.LBRY',
        'LSUIElement': True,
    },
    'includes': ['zope.interface', 'PyObjCTools'],
    'packages': requirements,
}

setup(
    name=conf.APP_NAME,
    app=[APP_PATH],
    options={'py2app': OPTIONS},
    data_files=DATA_FILES,
    setup_requires=['py2app'],
)
