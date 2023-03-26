"""
A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import os
import sys

from setuptools import setup, find_packages

# pylint: disable=redefined-builtin

setup(
    name="dance-runaway-desktop",
    # Don't forget to update the version in __init__.py and CHANGELOG.rst!
    version="0.0.1",
    description="Run away dancing the mat.",
    url="https://github.com/mristin/dance-runaway-desktop",
    author="Marko Ristin",
    author_email="marko@ristin.ch",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
    ],
    license="License :: OSI Approved :: MIT License",
    keywords="dance pad run away",
    install_requires=[
        "icontract>=2.6.1,<3",
        "pygame>=2,<3",
    ],
    extras_require={
        "dev": [
            "black==23.1.0",
            "mypy==1.1.1",
            "pylint==2.17.1",
            "coverage>=6.5.0,<7",
            "twine",
            "pyinstaller>=5,<6",
            "pillow>=9,<10",
            "requests>=2,<3",
        ],
    },
    py_modules=["dancerunaway"],
    packages=find_packages(exclude=["tests", "continuous_integration", "dev_scripts"]),
    package_data={
        "dancerunaway": [
            "media/images/*",
            "media/sfx/*",
        ]
    },
    entry_points={
        "console_scripts": [
            "dance-runaway-desktop=dancerunaway.main:entry_point",
        ]
    },
)
