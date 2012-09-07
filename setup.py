import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Add us to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hipmob'))
import importer
import version

path, script = os.path.split(sys.argv[0])
os.chdir(os.path.abspath(path))

# We'll need simplejson
requires = []
try:
  importer.import_json()
except ImportError:
  requires.append('simplejson')

try:
  import json
  _json_loaded = hasattr(json, 'loads')
except ImportError:
  pass

setup(name='hipmob',
      version=version.VERSION,
      description='Hipmob python bindings',
      author='Orthogonal Labs, Inc.',
      author_email='team@hipmob.com',
      url='https://www.hipmob.com/',
      packages=['hipmob'],
      install_requires=requires,
)
