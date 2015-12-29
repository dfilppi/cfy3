
from setuptools import setup

# Replace the place holders with values for your project

setup(

    # Do not use underscores in the plugin name.
    name='workflows',

    version='0.1',
    author='dfilppi',
    author_email='dewayne@gigaspaces.com',
    description='resumable install workflow',

    # This must correspond to the actual packages in the plugin.
    packages=['workflows'],

    license='LICENSE',
    zip_safe=False,
    install_requires=[
        # Necessary dependency for developing plugins, do not remove!
        "cloudify-plugins-common>=3.3"
    ],
    test_requires=[
        "cloudify-dsl-parser>=3.3"
        "nose"
    ]
)
