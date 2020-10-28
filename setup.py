import os
from setuptools import setup

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__)))


def get_requirements():
    if not os.path.exists(os.path.join(ROOT_PATH, 'requerments.txt')):
        return None
    packages = []
    with open(os.path.join(ROOT_PATH, 'requerments.txt'), 'r') as _file:
        for line in _file.readlines():
            packages.append(line.strip())
    return packages


def get_dependency_links():
    if not os.path.exists(os.path.join(ROOT_PATH, 'dependency_links.txt')):
        return None
    links = []
    with open(os.path.join(ROOT_PATH, 'dependency_links.txt'), 'r') as _file:
        for line in _file.readlines():
            links.append(line.strip())
    return links


setup(name='tweb',
      version='0.0.1',
      description='Tronado web imploded router and redis.',
      author='Maco',
      author_email='macohong@hotmail.com',
      license='MIT',
      url='https://github.com/marcohong/tweb',
      keywords=['tornado', 'web', 'imploded'],
      packages=['tweb', 'tweb.utils', 'tweb.database'],
      data_files=[('tweb/fonts', ['tweb/fonts/SourceHanSansSC-Normal.otf'])],
      python_requires='>=3.6',
      dependency_links=get_dependency_links(),
      install_requires=get_requirements(),
      classifiers=[
          'Development Status :: 1 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          "Programming Language :: Python :: Implementation :: CPython",
          'Operating System :: OS Independent',
          'Framework :: AsyncIO',
      ])
