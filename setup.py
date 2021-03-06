from __future__ import absolute_import
from distutils.core import setup
import os


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('starsweb'):
    # Ignore dirnames that start with '.'
    dirnames[:] = [d for d in dirnames if not d.startswith('.')]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[9:]  # Strip "starsweb/" or "starsweb\"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))

setup(
    name='django-starsweb',
    description='',
    version="2.0.0dev",
    author='Jeff Bradberry',
    author_email='jeff.bradberry@gmail.com',
    url='http://github.com/jbradberry/django-starsweb',
    package_dir={'starsweb': 'starsweb'},
    packages=packages,
    package_data={'starsweb': data_files},
    install_requires=['six'],
    entry_points={'turngeneration.plugins': ['starsweb = starsweb.plugins:TurnGeneration']},
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python'
                 'Topic :: Games/Entertainment :: Turn Based Strategy'],
    long_description=read_file('README.rst'),
)
