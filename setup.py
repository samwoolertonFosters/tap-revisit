#!/usr/bin/env python

from setuptools import setup

setup(
    name="tap-sitehq",
    version="1.0.0",
    description="Singer.io tap for extracting data from the SiteHQ API",
    author="SiteHQ",
    url="https://sitehq.nz",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_sitehq"],
    install_requires=["singer-python==5.9.0", "aiohttp==3.7.3"],
    extras_require={
        "dev": [
            "pylint",
            "ipdb",
            "nose",
        ]
    },
    entry_points="""
          [console_scripts]
          tap-sitehq=tap_sitehq:main
      """,
    packages=["tap_sitehq"],
    package_data={"tap_sitehq": ["tap_sitehq/schemas/*.json"]},
    include_package_data=True,
)
