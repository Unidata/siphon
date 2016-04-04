from __future__ import print_function
import sys
from setuptools import setup, find_packages, Command
import versioneer


class MakeExamples(Command):
    description = 'Create example scripts from IPython notebooks'
    user_options=[]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import glob
        import os
        import os.path
        from nbconvert.exporters import python
        from traitlets.config import Config
        examples_dir = os.path.join(os.path.dirname(__file__), 'examples')
        script_dir = os.path.join(examples_dir, 'scripts')
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        c = Config({'Exporter': {'template_file': 'examples/python-scripts.tpl'}})
        exporter = python.PythonExporter(config=c)
        for fname in glob.glob(os.path.join(examples_dir, 'notebooks', '*.ipynb')):
            output, _ = exporter.from_filename(fname)
            out_fname = os.path.splitext(os.path.basename(fname))[0]
            out_name = os.path.join(script_dir, out_fname + '.py')
            print(fname, '->', out_name)
            with open(out_name, 'w') as outf:
                outf.write(output)


ver = versioneer.get_version()
commands = versioneer.get_cmdclass()
commands.update(examples=MakeExamples)

# Need to conditionally add enum support for older Python
dependencies = ['numpy>=1.8', 'protobuf>=3.0.0a3', 'requests>=1.2']
if sys.version_info < (3, 4):
    dependencies.append('enum34')

setup(
    name = "siphon",
    version = ver,
    packages = find_packages(),
    cmdclass=commands,
    author = "Unidata Development Team",
    author_email = 'support-python@unidata.ucar.edu',
    license = 'MIT',
    url = "https://github.com/Unidata/siphon",
    description = ("A collection of Python utilities for interacting with the "
                                   "Unidata technology stack."),
    keywords='meteorology weather',
    classifiers=['Development Status :: 3 - Alpha',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Topic :: Scientific/Engineering',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'License :: OSI Approved :: MIT License'],

    install_requires=dependencies,
    extras_require={
        'netcdf': 'netCDF4>=1.1.0',
        'dev': 'ipython[all]>=3.1',
        'test': ['pytest', 'pytest-runner', 'netCDF4>=1.1.0',
                 'vcrpy~=1.5,!=1.7.0,!=1.7.1,!=1.7.2,!=1.7.3', 'xarray>=0.6'],
        'doc': ['sphinx>=1.3', 'nbconvert>=4.0', 'IPython>=4.0'],
        # Need quite a bit of cartopy's "optional" dependencies
        # Need to pin shapely until at least cartopy 0.13.1 is on pypi
        'examples': ['matplotlib>=1.3', 'cartopy>=0.13', 'pillow', 'scipy',
                     'shapely<=1.5.12']
    },

    download_url='https://github.com/Unidata/siphon/archive/v%s.tar.gz' % ver,)
