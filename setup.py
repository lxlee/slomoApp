import os
import sys
try:
    from setuptools import setup, find_packages
    setuptools_available = True
except ImportError:
    from distutils.core import setup, Command
    setuptools_available = False
from distutils.spawn import spawn

VERSION = "1.0.0"
DESCRIPTION = 'Super-Slomo gui'
LONG_DESCRIPTION = 'Super-Slomo simple gui wrapper program'

if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
    try:
        import py2exe

        py2exe_options = {
            'bundle_files': 1,
            'compressed': 1,
            'optimize': 2,
            'dist_dir': '.',
            'dll_excludes': ['w9xpopen.exe', 'crypt32.dll'],
        }

        py2exe_console = [{
            'script': './slomo/__main__.py',
            'dest_base': 'slomo',
            'version': VERSION,
            'description': DESCRIPTION,
            'comments': LONG_DESCRIPTION,
            'product_name': 'youtube-dl',
            'product_version': VERSION,
        }]

        py2exe_params = {
            'console': py2exe_console,
            'options': {'py2exe': py2exe_options},
            'zipfile': None
        }

        params = py2exe_params
    except ImportError as error:
        print(error)
        sys.exit(1)
else:
    params = {}

    root = os.path.dirname(os.path.abspath(__file__))
    print("setuptools_available : ", setuptools_available)
    if setuptools_available:
        params['entry_points'] = {'console_scripts': ['slomo = slomo:main']}
        params['scripts'] = ['bin/slomoCMD']
    else:
        params['scripts'] = ['bin/slomoCMD', 'bin/slomo']

setup(
    name = "Slomo",
    version = VERSION,
    author = "lxlong",
    author_email = "lxiaolong@wisionai.com",
    description = DESCRIPTION,
    long_description = LONG_DESCRIPTION,

    packages = ["slomo"],
    include_package_data = True,

    install_requires = [
        'torch >= 2.0.1',
        'torchvision',
        'svg.path',
        'pypotrace',
        'scipy',
        'numpy',
        'CairoSVG',
        'pillow',
        'customtkinter',
        'CTkMessagebox',
        'click'
    ],

    **params
)