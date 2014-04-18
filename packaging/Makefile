.PHONY: deb rpm dontrunmebro

dontrunmebro:
	@test "$(RECURSIVE_MAKE)" = "true" || (echo "This Makefile is intended to be invoked recursively" && exit 1)

deb rpm: dontrunmebro

UPSTREAM_TARBALL=$(PACKAGE)_$(VERSION).orig.tar.gz

deb: clean-build-dir
	mv $(DIST_ARCHIVES) $(UPSTREAM_TARBALL)
	tar xzvf $(UPSTREAM_TARBALL)
	cp -r deb $(distdir)/debian
	cd $(distdir) && dpkg-buildpackage -uc -us

clean-build-dir:
	rm -rf $(distdir)

rpm:
	mkdir -p rpm/SOURCES
	mv $(DIST_ARCHIVES) rpm/SOURCES
	rpmbuild -ba --define "_topdir $(shell pwd)/rpm" --define "autoconfversion $(VERSION)" --define "distarchives $(DIST_ARCHIVES)" rpm/pam_toopher.spec
