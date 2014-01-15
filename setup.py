#!/usr/bin/python -W default
import warnings; warnings.simplefilter('default')
try:
  from setuptools import setup, Extension
except ImportError:
  from distutils.core import setup, Extension

import sys
import os 

long_description = """\
Embeds the Python interpreter into PAM \
so PAM modules can be written in Python"""

classifiers = [
  "Development Status :: 4 - Beta",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: EPL",
  "Natural Language :: English",
  "Operating System :: Unix",
  "Programming Language :: C",
  "Programming Language :: Python",
  "Topic :: Software Development :: Libraries :: Python Modules",
  "Topic :: System :: Systems Administration :: Authentication/Directory"]

if not os.environ.has_key("Py_DEBUG"):
  Py_DEBUG = []
else:
  Py_DEBUG = [('Py_DEBUG',1)]

libpython_so = ('libpython%d.%d.so.1') % sys.version_info[:2]
ext_modules = [
    Extension(
      "pam_python",
      sources=["pam_python.c"],
      include_dirs = [],
      library_dirs=[],
      define_macros=[('LIBPYTHON_SO','"'+libpython_so+'"')] + Py_DEBUG,
      libraries=["pam","python%d.%d" % sys.version_info[:2]],
    ), ]

setup(
  name="pam_python",
  version="1.0.2",
  description="Enabled PAM Modules to be written in Python",
  keywords="pam,embed,authentication,security",
  platforms="Unix",
  long_description=long_description,
  author="Russell Stuart",
  author_email="russell-pampython@stuart.id.au",
  url="http://www.stuart.id.au/russell/files/pam_python",
  license="EPL",
  classifiers=classifiers,
  ext_modules=ext_modules,
)
