import setuptools

setuptools.setup(
    name="foreman-tools",
    version="0.1.0",
    url="https://github.com/plavjanik/foreman-tools",

    author="Petr Plavjanik",
    author_email="petr.plavjanik@gooddata.com",

    description="Foreman Command Line Tools",
    long_description=open('README.rst').read(),

    packages=setuptools.find_packages(),

    install_requires=[
        "docopt",
        "humanfriendly",
        "requests_kerberos",
    ],

    entry_points={
        "console_scripts": ["foreman=foreman_tools.cli:main"],
    },

    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)
