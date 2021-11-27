#/***************************************************************************
# OGDFPlugin
#
# Prototype Plugin for Project Group Theoretical Computer Science. Creates Graphs from VectorLayers.
#							 -------------------
#		begin				: 2021-05-07
#		copyright			: (C) 2021 by Jwittker
#		email				: jwittker@uos.de
# ***************************************************************************/
#
#/***************************************************************************
# *																		 *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or	 *
# *   (at your option) any later version.								   *
# *																		 *
# ***************************************************************************/

#################################################
# Edit the following to match your sources lists
#################################################


#Add iso code for any locales you want to support here (space separated)
# default is no locales
LOCALES = de

# If locales are enabled, set the name of the lrelease binary on your system. If
# you have trouble compiling the translations, you may have to specify the full path to
# lrelease
LRELEASE = lrelease
#LRELEASE = lrelease-qt4


# translation
SOURCES = \
	__init__.py \
	mainPlugin.py

PLUGINNAME = ogdf_plugin

PY_FILES = __init__.py mainPlugin.py helperFunctions.py exceptions.py
DIRECTORIES = controllers lib models resources views network i18n
EXTRAS = metadata.txt

# COMPILED_RESOURCE_FILES = resources.py

PEP8EXCLUDE=pydev,resources.py,conf.py,third_party,ui

# QGISDIR points to the location where your plugin should be installed.
# This varies by platform, relative to your HOME directory:
#	* Linux:
#	  .local/share/QGIS/QGIS3/profiles/default/python/plugins/
#	* Mac OS X:
#	  Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins
#	* Windows:
#	  AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins

QGISDIR=.local/share/QGIS/QGIS3/profiles/default/python/plugins/

#################################################
# Normally you would not need to edit below here
#################################################

# RESOURCE_SRC=$(shell grep '^ *<file' resources.qrc | sed 's@</file>@@g;s/.*>//g' | tr '\n' ' ')

.PHONY: default
default:
	@echo While you can use make to build and deploy your plugin, pb_tool
	@echo is a much better solution.
	@echo A Python script, pb_tool provides platform independent management of
	@echo your plugins and runs anywhere.
	@echo You can install pb_tool using: pip install pb_tool
	@echo See https://g-sherman.github.io/plugin_build_tool/ for info.

# compile: $(COMPILED_RESOURCE_FILES)

#%.py : %.qrc $(RESOURCES_SRC)
#	pyrcc5 -o $*.py  $<

%.qm : %.ts
	$(LRELEASE) $<

deploy: transcompile proto pybind_build
	@echo
	@echo "------------------------------------------"
	@echo "Deploying plugin to your .qgis2 directory."
	@echo "------------------------------------------"
	# The deploy  target only works on unix like operating system where
	# the Python plugin directory is located at:
	# $HOME/$(QGISDIR)
	mkdir -p $(HOME)/$(QGISDIR)/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/$(QGISDIR)/$(PLUGINNAME)
	$(foreach dir, $(DIRECTORIES), if [ -d "$(dir)" ]; then cp -vfr $(dir) $(HOME)/$(QGISDIR)/$(PLUGINNAME); fi;)
	cp -vf $(EXTRAS) $(HOME)/$(QGISDIR)/$(PLUGINNAME)
	#cp -vfr i18n $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) 			# Translation files
	#cp -vfr $(HELP) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/help
	# Copy extra directories if any
	#(foreach EXTRA_DIR,(EXTRA_DIRS), cp -R (EXTRA_DIR) (HOME)/(QGISDIR)/python/plugins/(PLUGINNAME)/;)
	unzip resources/Graph_Collection.zip -d resources/


derase:
	@echo
	@echo "-------------------------"
	@echo "Removing deployed plugin."
	@echo "-------------------------"
	rm -Rf $(HOME)/$(QGISDIR)/$(PLUGINNAME)

proto:
	mkdir -p network/protocol/build
	protoc --proto_path=network/protocol/protos/ --python_out=network/protocol/build/ network/protocol/protos/*.proto network/protocol/protos/handlers/*.proto
	sed -i 's/^\(import.*pb2\)/from . \1/g' network/protocol/build/*.py
	sed -i 's/^\(import.*pb2\)/from .. \1/g' network/protocol/build/handlers/*.py

clean_proto:
	rm -Rf network/protocol/build

pybind_build:
	echo "Script to build shared object with pybind"
	echo "Start build"
	echo "Execute setup.py"
	python3 scripts/setup.py build_ext --build-lib models/
	echo "Remove build folder"
	rm -rf build
	echo "End pybind build"

zip:
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	rm -f $(PLUGINNAME).zip
	rm -fr temp_zip
	mkdir -p temp_zip/$(PLUGINNAME)
	cp -vf $(PY_FILES)  temp_zip/$(PLUGINNAME)
	$(foreach dir, $(DIRECTORIES), if [ -d "$(dir)" ]; then cp -vfr $(dir) temp_zip/$(PLUGINNAME); fi;)
	cp -vf $(EXTRAS) temp_zip/$(PLUGINNAME)
	cd temp_zip; zip $(CURDIR)/$(PLUGINNAME).zip -r $(PLUGINNAME)
	rm -fr temp_zip

package:
	# Create a zip package of the plugin named $(PLUGINNAME).zip.
	# This requires use of git (your plugin development directory must be a
	# git repository).
	# To use, pass a valid commit or tag as follows:
	#   make package VERSION=Version_0.3.2
	@echo
	@echo "------------------------------------"
	@echo "Exporting plugin to zip package.	"
	@echo "------------------------------------"
	rm -f $(PLUGINNAME).zip
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip HEAD
	echo "Created package: $(PLUGINNAME).zip"

transup:
	@echo
	@echo "------------------------------------------------"
	@echo "Updating translation files with any new strings."
	@echo "------------------------------------------------"
	@chmod +x scripts/update-strings.sh
	@scripts/update-strings.sh $(LOCALES)

transcompile:
	@echo
	@echo "----------------------------------------"
	@echo "Compiled translation files to .qm files."
	@echo "----------------------------------------"
	@chmod +x scripts/compile-strings.sh
	@scripts/compile-strings.sh $(LRELEASE) $(LOCALES)


transclean:
	@echo
	@echo "------------------------------------"
	@echo "Removing compiled translation files."
	@echo "------------------------------------"
	rm -f i18n/*.qm

pylint:
	@echo
	@echo "-----------------"
	@echo "Pylint violations"
	@echo "-----------------"
	@pylint --reports=n --rcfile=pylintrc . || true
	@echo
	@echo "----------------------"
	@echo "If you get a 'no module named qgis.core' error, try sourcing"
	@echo "the helper script we have provided first then run make pylint."
	@echo "e.g. source run-env-linux.sh <path to qgis install>; make pylint"
	@echo "----------------------"


# Run pep8 style checking
#http://pypi.python.org/pypi/pep8
pep8:
	@echo
	@echo "-----------"
	@echo "PEP8 issues"
	@echo "-----------"
	@pep8 --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128 --exclude $(PEP8EXCLUDE) . || true
	@echo "-----------"
	@echo "Ignored in PEP8 check:"
	@echo $(PEP8EXCLUDE)

test:
	@echo
	@echo "----------------------"
	@echo "Tests"
	@echo "----------------------"
	@-export PYTHONPATH=`pwd`:$(PYTHONPATH); export QGIS_DEBUG=0; export QGIS_LOG_FILE=/dev/null; \
		python -m unittest discover -s tests -t .. -v || true
