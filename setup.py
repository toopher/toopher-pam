#!/usr/bin/python -W default
import warnings; warnings.simplefilter('default')
try:
  from setuptools import setup, Extension
except ImportError:
  from distutils.core import setup, Extension

import sys
import os 

from ctypes.util import find_library

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

libpython_so = find_library("python%d.%d" % sys.version_info[:2])
if not libpython_so:
    "libpython%d.%d.so.1" % sys.version_info[:2]

ext_modules = [
    Extension(
      "pam_toopher",
      sources=["pam_python.c", "importer.c"],
      include_dirs = [],
      library_dirs=[],
      define_macros=[('LIBPYTHON_SO','"'+libpython_so+'"')] + Py_DEBUG,
      libraries=["pam","python%d.%d" % sys.version_info[:2]],
    ), ]

setup(
  name="pam_toopher",
  version="1.0.2",
  description="Toopher PAM module",
  keywords="pam,embed,authentication,security",
  platforms="Unix",
  long_description=long_description,
  author="Toopher",
  author_email="dev@toopher.com",
  url="https://github.com/toopher/toopher-pam/",
  license="EPL",
  classifiers=classifiers,
  ext_modules=ext_modules,
)
