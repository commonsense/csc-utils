#!/usr/bin/env python

"""A set of utility functions for Python and Django that the Commonsense Computing project uses in multiple projects.

Includes:

* A `foreach` with progress reporting (also Status.reporter)
* A `cached` decorator for Django
* A generator for the "sampling sequence" (binary van der Corput sequence),
  useful for incremental resolution on graphs.
* A dictionary that stores its items as pickles in a directory. Features
  lazy loading and lazy evaluation.

Plus a few more odds and ends."""

version_str = '0.4.3'

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils import setup, Extension
import os.path, sys
from stat import ST_MTIME

classifiers=[
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: MacOS',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Programming Language :: C',
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development',
    'Topic :: Text Processing :: Linguistic',]

doclines = __doc__.split("\n")

setup(
    name="csc-utils",
    version=version_str,
    maintainer='MIT Media Lab, Software Agents group',
    maintainer_email='conceptnet@media.mit.edu',     
    url='http://divisi.media.mit.edu/',
    download_url='http://divisi.media.mit.edu/dist/csc-util-%s.tar.gz' % version_str,
    license = "http://www.gnu.org/copyleft/gpl.html",
    platforms = ["any"],
    description = doclines[0],
    classifiers = classifiers,
    long_description = "\n".join(doclines[2:]),
    packages=['csc', 'csc.util'],
    namespace_packages = ['csc'],
)
