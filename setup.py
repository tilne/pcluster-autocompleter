import os
from setuptools import find_packages, setup


def readme():
    """Read the README file and use it as long description."""
    with open(os.path.join(os.path.dirname(__file__), "README.md")) as f:
        return f.read()


VERSION = "0.0.0"
REQUIRES = []
DESCRIPTION = (
    "pcluster-autocompleter enables auto completion of the `pcluster` CLI commands for the bash, "
    "zsh, and fish shells. The `pcluster` CLI is used to interact with AWS ParallelCluster, an "
    "AWS supported Open Source cluster management tool to deploy and manage HPC clusters in the "
    "AWS cloud."
)

setup(
    name="pcluster-autocompleter",
    version=VERSION,
    author="Tim Lane",
    description=DESCRIPTION,
    url="https://github.com/tilne/pcluster-autocompleter",
    license="Apache License 2.0",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=REQUIRES,
    entry_points={
        "console_scripts": [
            "pcluster_autocompleter = pcluster_autocompleter.get_pcluster_completion_candidates:main"
        ]
    },
    include_package_data=True,
    zip_safe=False,
    package_data={"": ["examples/config"]},
    long_description=readme(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: Apache Software License",
    ],
)
