from setuptools import setup

setup(
  name = "grabpod",
  version = "1.0.0",
  author = "John Baber-Lucero",
  author_email = "pypi@frundle.com",
  description = ("Elementary CLI podcatcher"),
  license = "GPLv3",
  url = "https://github.com/jbaber/grabpod",
  packages = ['grabpod'],
  install_requires = ['docopt', 'beautifulsoup4', 'lxml', ],
  entry_points = {
    'console_scripts': ['grabpod=grabpod.grabpod:main'],
  }
)
