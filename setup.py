#!/usr/bin/env python

version_str = '0.6.1'
languages = ['pt', 'nl', 'ja', 'en', 'fi', 'ko', 'fr', 'ar', 'it', 'es', 'hu', 'zh', 'mblem']
packages=['csc_utils', 'csc', 'csc.conceptnet', 'csc.conceptnet4',
          'csc.concepttools', 'csc.corpus', 'csc.divisi2', 'csc.divisi2.algorithms',
          'csc.django_settings', 'csc.lib', 'csc.nl',
          'csc.pseudo_auth', 'csc.util', 'csc.webapi'] + ['csc.nl.'+lang for lang in languages]

try:
    from setuptools import setup, Extension, find_packages

    # Verify the list of packages.
    setuptools_packages = find_packages(exclude=[])
    if set(packages) != set(setuptools_packages):
        import sys
        print >>sys.stderr, 'Missing or extraneous packages found.'
        print >>sys.stderr, 'Extraneous:', list(set(packages) - set(setuptools_packages))
        print >>sys.stderr, 'Missing:', list(set(setuptools_packages) - set(packages))
        sys.exit(1)

except ImportError:
    from distutils.core import setup, Extension
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

README_contents = open(os.path.join(os.path.dirname(__file__), 'README.txt')).read()
doclines = README_contents.split("\n")

setup(
    name="csc-utils",
    version=version_str,
    maintainer='MIT Media Lab, Software Agents group',
    maintainer_email='conceptnet@media.mit.edu',     
    url='http://csc.media.mit.edu/',
    download_url='http://divisi.media.mit.edu/dist/csc-util-%s.tar.gz' % version_str,
    license = "http://www.gnu.org/copyleft/gpl.html",
    platforms = ["any"],
    description = doclines[0],
    classifiers = classifiers,
    long_description = "\n".join(doclines[2:]),
    packages=packages,
    namespace_packages=['csc'],
)
