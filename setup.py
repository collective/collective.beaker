from setuptools import find_namespace_packages
from setuptools import setup


version = "1.0b4.dev0"

setup(
    name="collective.beaker",
    version=version,
    description="Beaker integration for Zope and Plone",
    long_description=(open("README.rst").read() + "\n" + open("CHANGES.rst").read()),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.2",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="beaker zope plone caching sessions",
    author="Martin Aspeli",
    author_email="optilude@gmail.com",
    url="https://github.com/collective/collective.beaker",
    license="BSD",
    packages=find_namespace_packages("src", include=["collective.*"]),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "setuptools",
        "Beaker",
        "zope.interface",
        "zope.component",
        "Zope2",
        "zope.publisher",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
        ],
    },
    entry_points="""
    """,
)
