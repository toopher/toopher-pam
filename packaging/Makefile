.PHONY: deb

UPSTREAM_TARBALL=$(PACKAGE)_$(VERSION).orig.tar.gz

deb: clean-build-dir
	mv $(DIST_ARCHIVES) $(UPSTREAM_TARBALL)
	tar xzvf $(UPSTREAM_TARBALL)
	cp -r deb $(distdir)/debian
	cd $(distdir) && dpkg-buildpackage -uc -us

clean-build-dir:
	rm -rf $(distdir)
