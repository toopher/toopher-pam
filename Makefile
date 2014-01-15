libdir.x86_64 = $(DESTDIR)/lib64
libdir.i686 = $(DESTDIR)/lib

MACHINE := $(shell uname -m)

PAM_LIBDIR ?= $(libdir.$(MACHINE))/security

all: pam_toopher.so

pam_toopher.so: pam_python.c importer.c
	rm -rf build
	CFLAGS="$(WARNINGS)" ./setup.py build
	@#CFLAGS="-O0 $(WARNINGS)" ./setup.py build --debug
	@#CFLAGS="-O0 $(WARNINGS)" Py_DEBUG=1 ./setup.py build --debug
	ln -sf build/lib.*/$@ .

importer.c: bin2c importer.py
	./bin2c importer.py importer.c BUNDLE_IMPORTER

importer.py: pam_toopher.py common.py
	python bundle_importer/create_bundle_importer.py -o importer.py pam_toopher.py
pam_toopher_clean:
	rm -rf pam_toopher.so build bin2c importer.py importer.c

WARNINGS=-Wall -Wextra -Wundef -Wshadow -Wpointer-arith -Wbad-function-cast -Wsign-compare -Waggregate-return -Wstrict-prototypes -Wmissing-prototypes -Wmissing-declarations -Werror
#WARNINGS=-Wunreachable-code 	# Gcc 4.1 .. 4.4 are too buggy to make this useful

pam_python.so: pam_python.c setup.py Makefile
	@rm -f "$@"
	@[ ! -e build -o build/lib.*/$@ -nt setup.py -a build/lib.*/$@ -nt Makefile ] || rm -r build
	CFLAGS="$(WARNINGS)" ./setup.py build
	@#CFLAGS="-O0 $(WARNINGS)" ./setup.py build --debug
	@#CFLAGS="-O0 $(WARNINGS)" Py_DEBUG=1 ./setup.py build --debug
	ln -sf build/lib.*/$@ .

.PHONY: install
install: all
	mkdir -p $(PAM_LIBDIR)
	cp build/lib.*/pam_toopher.so $(PAM_LIBDIR)
	[ -e /etc/security/toopher.conf ] || cp toopher.conf /etc/security/toopher.conf
	[ -e /etc/pam.d/password+toopher-auth ] || cp password+toopher-auth /etc/pam.d/

.PHONY: uninstall
uninstall:
	rm -rf $(PAM_LIBDIR)/pam_toopher.so

.PHONY: clean
clean:
	rm -rf build pam_toopher.so importer.c importer.py bin2c
