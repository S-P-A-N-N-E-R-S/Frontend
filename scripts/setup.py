#  This file is part of the OGDF plugin.
#
#  Copyright (C) 2021  Tim Hartmann
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.

from setuptools import setup, Extension
from setuptools.command import build_ext
from pybind11 import *

setup(
	ext_modules = [
		Extension(
			'AStarC', ['models/AStarC.cpp'],
			include_dirs=[get_include()],
			language = 'c++'
		)
	],
	cmdclass={'build_ext':build_ext.build_ext}
)
