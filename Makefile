libdir.x86_64 = $(DESTDIR)/lib64
libdir.i686 = $(DESTDIR)/lib

MACHINE := $(shell uname -m)

PAM_LIBDIR ?= $(libdir.$(MACHINE))/security
HOOKSDIR := ./pyinstaller-hooks

WARNINGS=-Wall -Wextra -Wundef -Wshadow -Wpointer-arith -Wbad-function-cast -Wsign-compare -Waggregate-return -Wstrict-prototypes -Wmissing-prototypes -Wmissing-declarations -Werror
#WARNINGS=-Wunreachable-code 	# Gcc 4.1 .. 4.4 are too buggy to make this useful

.PHONY: all
all: pam_toopher.so toopher-pair toopher-api-helper

.PHONY: clean
clean: clean_pam_toopher.so clean_toopher-pair clean_toopher-api-helper
	rm -rf build

pam_toopher.so: pam_python.c setup.py importer.c
	rm -rf build
	CFLAGS="$(WARNINGS)" ./setup.py build
	@#CFLAGS="-O0 $(WARNINGS)" ./setup.py build --debug
	@#CFLAGS="-O0 $(WARNINGS)" Py_DEBUG=1 ./setup.py build --debug
	ln -sf build/lib.*/$@ .

importer.c: bin2c importer.py
	./bin2c importer.py importer.c BUNDLE_IMPORTER

importer.py: pam_toopher.py common.py
	python bundle_importer/create_bundle_importer.py -o importer.py pam_toopher.py

.PHONY: clean_pam_toopher.so
clean_pam_toopher.so:
	rm -rf pam_toopher.so importer.c importer.py *.pyc bin2c


toopher-pair: toopher-pair.py common.py $(HOOKSDIR)/*.py
	pyinstaller --onefile --additional-hooks-dir=$(HOOKSDIR) toopher-pair.py
	ln -sf ./dist/toopher-pair

.PHONY:
clean_toopher-pair:
	rm -rf toopher-pair toopher-pair.spec dist


toopher-api-helper: toopher-api-helper.py common.py $(HOOKSDIR)/*.py
	pyinstaller --onefile --additional-hooks-dir=$(HOOKSDIR) toopher-api-helper.py
	ln -sf ./dist/toopher-api-helper

.PHONY:
clean_toopher-api-helper:
	rm -rf toopher-api-helper toopher-api-helper.spec dist


.PHONY: install
install: all
	install -D pam_toopher.so $(PAM_LIBDIR)
	install -D toopher-pair /usr/bin
	install -D --group=toopher-admin --mode=u+rwx,g+rxs,o+rx toopher-api-helper /usr/bin

	install -d /etc/security/toopher
	[ -e /etc/security/toopher/config ] || install -T config-files/toopher.conf /etc/security/toopher/config
	[ -e /etc/security/toopher/credentials ] || install -T --group=toopher-admin --mode=u+rwx,g+rx,o-rwx config-files/credentials.conf /etc/security/toopher/credentials

	[ -e /etc/pam.d/password+toopher-auth ] || install -D config-files/password+toopher-auth /etc/pam.d/

.PHONY: uninstall
uninstall:
	rm -rf $(PAM_LIBDIR)/pam_toopher.so
	rm -rf /usr/bin/toopher-pair
	rm -rf /usr/bin/toopher-api-helper

