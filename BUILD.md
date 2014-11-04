Build
=====

Building requires:

* a build environment (e.g. make, gcc, etc. - the `build-essential` package on Debian-based systems)
* python development files (e.g. the `python-dev` package on Debian-based systems)
* pam development files (e.g. the `libpam0g-dev` package on Debian-based systems)
* the python packages listed in [build-requirements.txt](https://github.com/toopher/toopher-pam/blob/master/build-requirements.txt)

With these in place, the dance should start to look familiar:

Configure the package

	./configure

The script needs a system group to be used for privilege separation.  By default it used `toopher-admin`, but you can specify your own (or `none`) using `--with-admin-group=GROUP`.

Make the PAM module and associated tools

	make

Install (with elevated privileges)

	make install

Experimental
------------

We've been playing around with a docker-based build system that is now publicly available.  If you have docker up and running and want to build RPM/DEB in a snap just run the docker build script:

	./docker-builds.sh