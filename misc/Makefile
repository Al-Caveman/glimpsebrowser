PYTHON = python3
PREFIX ?= /usr/local
ICONSIZES = 16 24 32 48 64 128 256 512
DATAROOTDIR = $(PREFIX)/share
DATADIR ?= $(DATAROOTDIR)
MANDIR ?= $(DATAROOTDIR)/man

ifdef DESTDIR
SETUPTOOLSOPTS = --root="$(DESTDIR)"
endif

all: man
	$(PYTHON) setup.py build

man: doc/glimpsebrowser.1
doc/glimpsebrowser.1: doc/glimpsebrowser.1.asciidoc
	a2x -f manpage $<

install: man
	$(PYTHON) setup.py install --prefix="$(PREFIX)" --optimize=1 $(SETUPTOOLSOPTS)
	install -Dm644 misc/org.glimpsebrowser.glimpsebrowser.appdata.xml \
		"$(DESTDIR)$(DATADIR)/metainfo/org.glimpsebrowser.glimpsebrowser.appdata.xml"
	install -Dm644 doc/glimpsebrowser.1 \
		"$(DESTDIR)$(MANDIR)/man1/glimpsebrowser.1"
	install -Dm644 misc/org.glimpsebrowser.glimpsebrowser.desktop \
		"$(DESTDIR)$(DATADIR)/applications/org.glimpsebrowser.glimpsebrowser.desktop"
	$(foreach i,$(ICONSIZES),install -Dm644 "icons/glimpsebrowser-$(i)x$(i).png" \
			"$(DESTDIR)$(DATADIR)/icons/hicolor/$(i)x$(i)/apps/glimpsebrowser.png";)
	install -Dm644 icons/glimpsebrowser.svg \
		"$(DESTDIR)$(DATADIR)/icons/hicolor/scalable/apps/glimpsebrowser.svg"
	install -Dm755 -t "$(DESTDIR)$(DATADIR)/glimpsebrowser/userscripts/" \
		$(wildcard misc/userscripts/*)
	install -Dm755 -t "$(DESTDIR)$(DATADIR)/glimpsebrowser/scripts/" \
		$(filter-out scripts/__init__.py scripts/__pycache__ scripts/dev \
		  scripts/testbrowser scripts/asciidoc2html.py scripts/setupcommon.py \
			scripts/link_pyqt.py,$(wildcard scripts/*))

.PHONY: all man install
