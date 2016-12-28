from setuptools import setup
import os
from lbrynet import conf

APP_DIR = os.path.join(os.path.dirname(__file__), "unix")
APP_PATH = os.path.join(APP_DIR, 'LBRYURIHandler.py')
DATA_FILES = []
OPTIONS = {'argv_emulation': True,
           'packages': ['jsonrpc'],
           'plist': {
               'LSUIElement': True,
               'CFBundleIdentifier': 'io.lbry.LBRYURIHandler',
               'CFBundleURLTypes': [
                    {
                    'CFBundleURLTypes': 'LBRYURIHandler',
                    'CFBundleURLSchemes': [conf.PROTOCOL_PREFIX]
                    }
               ]
           },
}

setup(
    app=[APP_PATH],
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
