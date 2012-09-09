import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Add us to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hipmob'))
import version

path, script = os.path.split(sys.argv[0])
os.chdir(os.path.abspath(path))

# We'll need simplejson
requires = []
try:
    import json
    if not hasattr(json, 'loads'):
        requires.append('simplejson')
except ImportError:
    requires.append('simplejson')

setup(name='hipmob',
      version=version.VERSION,
      description='Hipmob python bindings',
      author='Orthogonal Labs, Inc.',
      author_email='team@hipmob.com',
      url='https://www.hipmob.com/',
      packages=['hipmob'],
      install_requires=requires,
)
