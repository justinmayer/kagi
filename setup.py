#!/usr/bin/env python
import io
import os

from setuptools import setup, find_packages


def read(fname, encoding='utf-8'):
    path = os.path.join(os.path.dirname(__file__), fname)
    with io.open(path, encoding=encoding) as f:
        return f.read()


setup(
    name='kagi',
    version='0.1.0.dev0',
    description="FIDO U2F security token support for Django",
    long_description=read('README.rst'),
    url='https://github.com/justinmayer/kagi',

    packages=find_packages(exclude=['testproj']),
    include_package_data=True,

    install_requires=[
        'python-u2flib-server>=5.0.0',
        'django-sslserver',
        'django',
        'qrcode',
        'webauthn',
    ],
    author='Justin Mayer',
    author_email='gavinwahl@gmail.com',
    license='BSD',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Security',
        'Topic :: Security :: Cryptography',
    ],
)
