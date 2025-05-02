import codecs
import os.path

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    # Basic package information
    name="netbox-ipamtree",
    version=get_version("ipamtree/version.py"),
    description="NetBox IPAM Tree plugin",
    keywords=["netbox", "netbox-plugin"],
    # Project URLs and documentation
    url="https://github.com/Snoo-py/netbox-ipamtree",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # Package configuration
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    python_requires=">=3.9",
    # Classifiers
    classifiers=[
        "Intended Audience :: Developers",
        "Framework :: Django",
        "Framework :: Django :: 5.0",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)
