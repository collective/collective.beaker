from setuptools import setup, find_packages

version = '1.0b4.dev0'

setup(
    name='collective.beaker',
    version=version,
    description="Beaker integration for Zope and Plone",
    long_description=(open("README.rst").read() + "\n" +
                      open("CHANGES.rst").read()),
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='beaker zope plone caching sessions',
    author='Martin Aspeli',
    author_email='optilude@gmail.com',
    url='https://github.com/collective/collective.beaker',
    license='BSD',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['collective'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Beaker',
        'zope.interface',
        'zope.component',
        'Zope2',
        'zope.publisher',
    ],
    extras_require={
        'Zope2.10': ['ZPublisherEventsBackport'],
        'tests': ['Products.PloneTestCase', 'collective.testcaselayer']
    },
    entry_points="""
    """,
)
