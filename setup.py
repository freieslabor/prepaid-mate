#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

__name__ == '__main__' and setup(name='prepaid-mate',
    version='0.0',
    author='Bastian Krause, Bayden',
    url='https://github.com/freieslabor/prepaid-mate/',
    author_email='basti@freieslabor.org',
    install_requires=[
        'requests',
        'evdev',
        'Flask'
    ],
    python_requires='>=3.5',
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'scanner-client = prepaid_mate.scanner_client:main',
            'prepaid-mate-reset-pw = prepaid_mate.reset_password:main',
            'prepaid-mate-new-drink = prepaid_mate.add_drink:main',
            'prepaid-mate-manage-django = prepaid_mate._django.manage:main',
        ]
    })
