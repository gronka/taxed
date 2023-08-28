#!/usr/bin/env python
import os
from setuptools import setup, find_packages
from urllib.parse import urlparse, parse_qs


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as fp:
        return fp.read()


def parse_requires_from_url(url):
    fragment = parse_qs(url.fragment)
    egg_info = fragment.get('egg', [''])
    package = egg_info[-1].rsplit('-', 1)

    if len(package) == 1:
        return package[0]
    else:
        return '{0}=={1}'.format(*package)


def parse_requirements_file(filename):
    install_requires = []
    dependency_links = []

    for link in [line.strip() for line in read(filename).strip().split('\n')]:
        if not link:
            continue

        url = urlparse(link)

        if url.scheme:
            dependency_links.append(link)
            req = parse_requires_from_url(url)
        else:
            req = link

        if req:
            install_requires.append(req)

    return {'install_requires': install_requires,
            'dependency_links': dependency_links}


pkg = {}
exec(read('src/taxed/__pkg__.py'), pkg)

readme = read('README.rst')
changelog = read('CHANGELOG.rst')
requirements = parse_requirements_file('requirements.txt')
entry_points = {
    'console_scripts': [
        'taxed = taxed.cli:app'
    ]
}


setup(
    name=pkg['__package_name__'],
    version=pkg['__version__'],
    url=pkg['__url__'],
    license=pkg['__license__'],
    author=pkg['__author__'],
    author_email=pkg['__email__'],
    description=pkg['__description__'],
    long_description=readme + '\n\n' + changelog,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=requirements['install_requires'],
    dependency_links=requirements['dependency_links'],
    entry_points=entry_points,
    keywords='taxed',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Filesystems',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ]
)
