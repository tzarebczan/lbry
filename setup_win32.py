# -*- coding: utf-8 -*-
"""
To create local builds and distributable .msi, run the following command:
python setup_win32.py build bdist_msi
"""
import os
import sys

from cx_Freeze import setup, Executable
import requests.certs
from lbryum import mnemonic

def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        data_dir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        data_dir = os.path.dirname(__file__)
    return os.path.join(data_dir, filename)

shortcut_table = [
    ('DesktopShortcut',  # Shortcut
     'DesktopFolder',  # Directory
     'LBRY',  # Name
     'TARGETDIR',  # Component
     '[TARGETDIR]\LBRY.exe',  # Target
     None,  # Arguments
     None,  # Description
     None,  # Hotkey
     os.path.join('lbrynet', 'lbrynet_gui', 'lbry-dark-icon.ico'),  # Icon
     None,  # IconIndex
     None,  # ShowCmd
     'TARGETDIR',  # WkDir
     ),
    ]

# Now create the table dictionary
msi_data = {'Shortcut': shortcut_table}

bdist_msi_options = {
    'upgrade_code': '{66620F3A-DC3A-11E2-B341-002219E9B01F}',
    'add_to_path': False,
    'initial_target_dir': r'[LocalAppDataFolder]\LBRY',
    'data': msi_data,
    }

electrum_include_files = [(requests.certs.where(), 'cacert.pem')]
path_to_electrum_languages = os.path.join(os.path.dirname(mnemonic.__file__), 'wordlist')
for root, sub_folders, files in os.walk(path_to_electrum_languages):
    for file_in_root in files:
        electrum_include_files.append((os.path.join(root, file_in_root),
                                       os.path.join("wordlist", file_in_root)))

build_exe_options = {
    'include_msvcr': True,
    'includes': [],
    'packages': ['six', 'os', 'twisted', 'miniupnpc', 'unqlite', 'seccure',
                 'requests', 'bitcoinrpc', 'txjsonrpc', 'win32api', 'Crypto',
                 'gmpy', 'yapsy', 'lbryum', 'google.protobuf'],
    'excludes': ['zope.interface._zope_interface_coptimizations'],
    'include_files': [os.path.join('lbrynet', 'lbrynet_gui', 'lbry-dark-icon.ico'),
                      ] + electrum_include_files,
    'namespace_packages': ['zope']}

exe = Executable(
    script=os.path.join('lbrynet', 'lbrynet_daemon', 'LBRYDaemon.py'),
    base='Console',
    icon=os.path.join('lbrynet', 'lbrynet_gui', 'lbry-dark-icon.ico'),
    compress=True,
    shortcutName='LBRY',
    shortcutDir='DesktopFolder',
    targetName='LBRY.exe'
    # targetDir="LocalAppDataFolder"
    )

setup(
    name='LBRY',
    version='0.0.4',
    description='A fully decentralized network for distributing data',
    url='lbry.io',
    author='',
    keywords='LBRY',
    options={'build_exe': build_exe_options,
             'bdist_msi': bdist_msi_options},
    executables=[exe],
    )
