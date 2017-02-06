# encoding: utf-8
from setuptools import setup, find_packages
from eureka import __version__ as version

setup(
    name = 'python-eureka',
    version = version,
    description = 'A python interface for Netflix Eureka',
    author = u'Keets2012',
    author_email = 'keets1992@gmail.com',
    zip_safe=False,
    include_package_data = True,
    packages = find_packages(exclude=[]),
    install_requires=[
        'dnspython'
    ],
)
