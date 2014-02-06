pamdir = $(PAMDIR)

EXTRA_DIST =
CLEANFILES = 

# Configuration files
#  We define our own install rule that ensures existing config files aren't clobbered (and permissions are correct)
toopherconfdir = $(TOOPHER_CONF_DIR)
dist_toopherconf_DATA = config-files/config config-files/credentials
install-dist_toopherconfDATA: $(dist_toopherconf_DATA)
		@if [ ! -d $(DESTDIR)$(toopherconfdir) ]; then \
			test -z "$(toopherconfdir)" || $(MKDIR_P) "$(DESTDIR)$(toopherconfdir)"; \
			list='$(dist_toopherconf_DATA)'; test -n "$(toopherconfdir)" || list=; \
			for p in $$list; do \
			  if test -f "$$p"; then d=; else d="$(srcdir)/"; fi; \
			  echo "$$d$$p"; \
			done | $(am__base_list) | \
			while read files; do \
			  echo " $(INSTALL_DATA) $$files '$(DESTDIR)$(toopherconfdir)'"; \
			  $(INSTALL_DATA) $$files "$(DESTDIR)$(toopherconfdir)" || exit $$?; \
			done; \
			echo "NOTICE: Fill in the credential configuration in "$(DESTDIR)$(toopherconfdir)/credentials" to enable Toopher functionality"; \
		else \
			echo "NOTICE: Skipping config file install because Toopher config directory already exists ($(DESTDIR)$(toopherconfdir))"; \
		fi
		test ${ADMINGROUP} = none || chgrp ${ADMINGROUP} ${DESTDIR}${toopherconfdir}/credentials
		chmod o-rwx ${DESTDIR}${toopherconfdir}/credentials

# PAModule
pam_LTLIBRARIES = pam_toopher.la
pam_toopher_la_SOURCES = pam_python.c pam_toopher.py common.py
nodist_pam_toopher_la_SOURCES = config.py
pam_toopher_la_CFLAGS = @PYTHON_CSPEC@
pam_toopher_la_LDFLAGS = @PYTHON_LSPEC@ -module -shared -no-undefined -avoid-version -export-symbols-regex 'pam_sm.*'

# Importer bundle
nodist_pam_toopher_la_SOURCES += importer.c
BUILT_SOURCES = importer.c importer.py
EXTRA_DIST += bin2c.c bundle_importer
CLEANFILES += importer.c importer.py bin2c
importer.c: importer.py bin2c
	$(builddir)/bin2c $< $@ BUNDLED_IMPORTER
importer.py: pam_toopher.py common.py config.py
	python $(srcdir)/bundle_importer/create_bundle_importer.py --outfile $@ $^

# Helper utilities
bin_SCRIPTS = toopher-pair toopher-api-helper 
EXTRA_DIST += toopher-pair.py toopher-api-helper.py
CLEANFILES += $(bin_SCRIPTS) toopher-pair.spec toopher-api-helper.spec 

toopher-%: toopher-%.py common.py config.py
	pyinstaller --onefile --distpath=$(builddir) --additional-hooks-dir=$(srcdir)/pyinstaller-hooks $<

install-exec-hook:
	test ${ADMINGROUP} = none || \
		chgrp ${ADMINGROUP} ${DESTDIR}${bindir}/toopher-api-helper && \
		chmod g+s ${DESTDIR}${bindir}/toopher-api-helper

# Clean-up after pyinstaller
clean-local:
	rm -rf build

# Installing a PAModule as typically expected requires elevated privileges and
# thus bends the GNU rules a bit.  To pass the dist-check we need to unbend
# them by specifying compliant install locations
DISTCHECK_CONFIGURE_FLAGS = --enable-gnu-compliance --with-admin-group=none

# libtool hides the libraries - add convenience link (thanks @umlaute from SO)
.PHONY: convenience-link clean-convenience-link

convenience-link: $(pam_LTLIBRARIES)
	@for soname in `echo | $(EGREP) "^dlname=" $^ | $(SED) -e "s|^dlname='\(.*\)'|\1|"`; do  \
		echo "$$soname: creating convenience link from $(abs_builddir)/.libs to $(top_builddir)"; \
		rm -f $(top_builddir)/$$soname ; \
		test -e $(abs_builddir)/.libs/$$soname && \
		cd $(top_builddir) && \
		$(LN_S) $(abs_builddir)/.libs/$$soname $$soname || true;\
		done 

clean-convenience-link:
	@for soname in `echo | $(EGREP) "^dlname=" $(lib_LTLIBRARIES) | $(SED) -e "s|^dlname='\(.*\)'|\1|"`; do  \
		echo "$$soname: cleaning convenience links"; \
		test -L $(top_builddir)/$$soname && rm -f $(top_builddir)/$$soname || true; \
		done 

all-local: convenience-link

clean-local: clean-convenience-link
