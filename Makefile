# Makefile for Sphinx documentation
#
GH_PAGES_SOURCES = rest_framework_mongoengine 
PYTHONHOME=$(dir $(shell which python))
SPHINXBUILD   = $(PYTHONHOME)/python $(shell which sphinx-build)
SOURCEDIR     = docs
BUILDDIR      = build
SPHINXOPTS   = -E -c .
DJANGO_SETTINGS_MODULE=dumbsettings


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
