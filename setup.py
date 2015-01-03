#!/usr/bin/env python

from distutils.core import setup

setup(name='twsh',
      version='0.1',
      description='Twitter Shell for Python',
      author='7kry',
      author_email='kt@7kry.net',
      url='https://github.com/7kry/twsh',
      packages=['twsh'],
      scripts=['bin/twsh'],
      requires=['yaml', 'dateutil.tz'],
     )
