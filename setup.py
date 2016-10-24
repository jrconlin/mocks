import io
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf8') as f:
        README = f.read()
    with io.open(os.path.join(here, 'CHANGELOG.md'), encoding='utf8') as f:
        CHANGES = f.read()
except:
    README = CHANGES = "TBD"

extra_options = {
    "packages": find_packages(),
}


setup(name="MockServers",
      version="0.1",
      description='Mock Bridge Servers',
      long_description=README + '\n\n' + CHANGES,
      classifiers=["Topic :: Internet :: WWW/HTTP",
                   "Programming Language :: Python :: Implementation :: PyPy",
                   'Programming Language :: Python',
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 2.7"
                   ],
      keywords='',
      author="jr conlin",
      author_email="src@jrconlin.com",
      url='http:///',
      license="MPL2",
      test_suite="nose.collector",
      include_package_data=True,
      zip_safe=False,
      tests_require=[
          'nose',
          'coverage',
          'mock>=1.0.1',
          'configargparse==0.11.0',
          'coverage==4.2',
          'cyclone==1.1',
          'service-identity==16.0.0',
          'twisted==16.4.1',
          ],
      entry_points="""
      [console_scripts]
      mock_gcm = mock_gcm.main:main
      [nose.plugins]
      """,
      **extra_options
      )
