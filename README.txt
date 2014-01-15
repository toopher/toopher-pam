pam_python
==========

  pam_python is a PAM module that runs the Python interpreter
  and so allows PAM modules to be written in Python.

  The home page is:
    http://www.stuart.id.au/russell/files/pam_python


Requirements
------------

  Python >= 2.2
  pam >= 0.76


Installing
----------

  To build you require the Python development system
  and the libpam development files.  The command
  to build the entire system is:

	make

  To install:

	make install

  To run the test suite you to be root or be able to sudo
  to root.  The command is:

	make test


Documentation
-------------

  After installing the documentation it available in HTML
  format in:

    /usr/share/doc/pam_python/html/pam_python.html

  Example files are here:

    /usr/share/doc/pam_python/examples


License
-------

  Copyright (c) 2007,2009,2010,2011,2012 Russell Stuart.
  All rights reserved. This program and the accompanying materials
  are made available under the terms of the Eclipse Public License v1.0
  which accompanies this distribution, and is available at
  http://www.eclipse.org/legal/epl-v10.html



--
Russell Stuart
2009-August-05
