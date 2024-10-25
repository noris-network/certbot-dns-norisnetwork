"""The setup script."""

import os

from setuptools import find_packages, setup

# read the contents of README file
my_path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(my_path, "README.md")) as readme_file:
    long_description = readme_file.read()

install_requires = [
    "certbot",
    "requests",
]

dev_requirements = [
    "black",
    "bump2version",
    "mypy",
    "pylint",
    "pytest",
    "pytest-cov",
    "types-requests",
]

extras_require = {"dev": [dev_requirements]}

version = os.getenv("BUILD_VERSION", "0.1.0")

setup(
    name="certbot-dns-norisnetwork",
    version=version,
    description="noris network DNS Authenticator Plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/noris-network/certbot-dns-norisnetwork",
    author="Anastasia Skoufa",
    author_email="anastasia.skoufa@noris.gr",
    license="Apache License 2.0",
    install_requires=install_requires,
    extras_require=extras_require,
    packages=find_packages(),
    entry_points={
        "certbot.plugins": [
            "dns-noris = certbot_dns_norisnetwork.dns_noris:Authenticator"
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Security",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    include_package_data=True,
)
