# Makefile for Sphinx documentation
#
GH_PAGES_SOURCES = rest_framework_mongoengine 

# You can set these variables from the command line.
SPHINXBUILD   = sphinx-build
SOURCEDIR     = docs
BUILDDIR      = build
SPHINXOPTS   = -d $(BUILDDIR)/doctrees -c .
export DJANGO_SETTINGS_MODULE=dumbsettings

# User-friendly check for sphinx-build
ifeq ($(shell which $(SPHINXBUILD) >/dev/null 2>&1; echo $$?), 1)
$(error The '$(SPHINXBUILD)' command was not found. Make sure you have Sphinx installed, then set the SPHINXBUILD environment variable to point to the full path of the '$(SPHINXBUILD)' executable. Alternatively you can add the directory with the executable to your PATH. If you don't have Sphinx installed, grab it from http://sphinx-doc.org/)
endif


.PHONY: clean html checkout pages

clean:
	rm -rf $(BUILDDIR)
	rm -rf *.html *.inv *.js _static _sources

html:
	$(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)

checkout:
	git checkout master $(GH_PAGES_SOURCES)
	git reset HEAD

pages: clean html
	rm -rf $(BUILDDIR)/doctrees
	mv -fv $(BUILDDIR)/* ./
