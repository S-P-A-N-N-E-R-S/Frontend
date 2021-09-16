from setuptools import setup, Extension
from setuptools.command import build_ext
from pybind11 import *

setup(
	ext_modules = [
		Extension(
			'AStarC', ['AStarC.cpp'],
			include_dirs=[get_include()],
			language = 'c++'
		)
	],
	cmdclass={'build_ext':build_ext.build_ext}
)
