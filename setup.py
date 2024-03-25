# -*- coding: utf-8 -*-
import sys
import os.path
from setuptools import setup

PKG_NAME = "PythonForWindows"
VERSION  = "0.6.0"

# Load long description from README.md
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

setup(
    name = PKG_NAME,
    version = VERSION,
    author = 'Hakril',
    author_email = 'pfw@hakril.net',
    description = 'A codebase aimed to make interaction with Windows and native execution easier',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license = 'BSD',
    keywords = 'windows python',
    url = 'https://github.com/hakril/PythonForWindows',
    packages = ['pfw_windows',
                'pfw_windows.crypto',
                'pfw_windows.debug',
                'pfw_windows.generated_def',
                'pfw_windows.native_exec',
                'pfw_windows.rpc',
                'pfw_windows.utils',
                'pfw_windows.winobject',
                'pfw_windows.winproxy',
                'pfw_windows.winproxy.apis'],
    classifiers = ['Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 2.7']
)