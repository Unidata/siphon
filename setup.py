from __future__ import print_function
from setuptools import setup, find_packages, Command
import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'siphon/_version.py'
versioneer.versionfile_build = 'siphon/_version.py'
versioneer.tag_prefix = 'v'
versioneer.parentdir_prefix = 'siphon-'


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
        from IPython.nbconvert.exporters import python
        from IPython.config import Config
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


setup(
    name = "siphon",
    version = ver,
    packages = find_packages(),
    cmdclass=commands,
    author = "Unidata Development Team",
    author_email = 'support-python@unidata.ucar.edu',
    license = 'MIT',
    url = "https://github.com/Unidata/siphon",
    test_suite = "nose.collector",
    description = ("A collection of Python utilities for interacting with the "
                                   "Unidata technology stack."),
    keywords='meteorology weather',
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Topic :: Scientific/Engineering',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'License :: OSI Approved :: MIT License'],

    install_requires=['numpy>=1.8', 'protobuf>=3.0.0a3', 'requests>=1.2',
                      'netCDF4>=1.1.0'],
    extras_require={
        'dev': ['ipython[all]>=3.1'],
        'doc': ['sphinx>=1.3', 'ipython[all]>=3.1'],
        'test': ['nosetest', 'vcrpy>=1.5,<1.7']
    },

    download_url='https://github.com/Unidata/siphon/archive/v%s.tar.gz' % ver,)
