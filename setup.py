import io
import os

from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with io.open("README.md", encoding="utf-8") as readme:
    README = readme.read()

with open("requirements.txt") as requirements:
    REQUIRES = requirements.read().splitlines()

setup(
    name="calsum",
    version="0.1",
    packages=["sum_calculator"],
    include_package_data=True,
    description=(
        "A list sum calculator"
    ),
    long_description=README,
    long_description_content_type="text/x-rst",
    license="GPLv3+",
    author="Hao Hu",
    author_email="hao.hu.fr@gmail.com",
    install_requires=REQUIRES,
    zip_safe=False,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Tornado",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Personal Website",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    entry_points={"console_scripts": ["calsum = sum_calculator.server:main"]},
)