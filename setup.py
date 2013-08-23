#!/usr/bin/python

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "LDPK",
    version = "0.1",
    packages = ['LDPK'],
    package_dir = {'LDPK' : 'src'},
    package_data = {'LDPK' : ['src/classification/*.R',
                              'src/preprocessing/*.R',
                              'src/utilities/*.R']},
    entry_points = {'console_scripts': ['LDPK_preprocess = LDPK.preprocess_image.py:main',
                                        'LDPK_classify = LDPK.classify_image:main',
                                        'LDPK_analyze = LDPK.analyze_classification:main']},
    zip_safe = True,
    install_requires = ['numpy >= 1.7.0',
                        'matplotlib >= 0.98.4',
                        'gdal >= 1.7'],
    author = "Alex Zvoleff",
    author_email = "azvoleff@conservation.org",
    description = "TEAM Landsat Data Processing Kit",
    keywords = "Landsat remote-sensing imagery classification preprocessing land use land cover",
    license = "GPL v3 or later",
    url = "https://github.com/azvoleff/TEAM_Landat",   # project home page, if any
    long_description = ''.join(open('README.rst').readlines()[6:]),
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Image Recognition",
        'Topic :: Utilities',
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7"]
)
