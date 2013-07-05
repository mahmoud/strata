"""
    strata
    ~~~~~~

    Multi-dimensional, topologically-driven, dependency-resolving
    configuration framework, built to handle the complexities of
    advanced projects.

    :copyright: (c) 2013 by Mahmoud Hashemi
    :license: BSD, see LICENSE for more details.
"""

import sys
from setuptools import setup


__author__ = 'Mahmoud Hashemi'
__version__ = '0.0.0dev'
__contact__ = 'mahmoudrhashemi@gmail.com'
__url__ = 'https://github.com/mahmoud/strata'
__license__ = 'BSD'

desc = ('Multi-dimensional, topologically-driven,'
        ' dependency-resolving configuration framework,'
        ' built to handle the complexities of advanced'
        ' projects.')


if sys.version_info < (2,6):
    raise NotImplementedError("Sorry, strata only supports Python >=2.6")

if sys.version_info >= (3,):
    raise NotImplementedError('strata Python 3 support en'
                              ' route to your location')

setup(name='strata',
      version=__version__,
      description=desc,
      long_description=__doc__,
      author=__author__,
      author_email=__contact__,
      url=__url__,
      packages=['strata'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['argparse>=1.2.1'],
      license=__license__,
      platforms='any',
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries :: Application Frameworks',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7', ]
      )
