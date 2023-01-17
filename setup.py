#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.md').read()
requirements = open('requirements/base.txt').readlines()
require_select2 = open('requirements/select2.txt').readlines()
require_all = requirements + require_select2

setup(
    name='django-org',
    version='0.2.0',
    description='Base classes for enterprise modeling',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Sergei Pikhovkin',
    author_email='s@pikhovkin.ru',
    url='https://github.com/pikhovkin/django-org',
    packages=['django_org'],
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'all': require_all,
        'select2': require_select2,
    },
    python_requires='>=3.9.*, <4.2.*',
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords=[
        'django',
        'enterprise',
        'organization',
        'regime',
        'shift',
        'work mode',
        'work regime',
        'work shift',
    ]
)
