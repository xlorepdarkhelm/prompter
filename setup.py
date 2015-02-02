#!/usr/bin/env python3

import os
import gzip

from codecs import open
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
import appdirs

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()


prompter_path = os.path.join(here, 'prompter')

copyright_year = 2015
copyright_owner = 'Clifford Hill'


def install_config():
    def make_hier(path):
        if path != '/':
            make_hier(os.path.dirname(path))

        if not os.path.exists(path):
            os.mkdir(path)

    dst_base = appdirs.site_config_dir('prompter')
    make_hier(dst_base)

    src_base = os.path.join(prompter_path, 'default')
    for src_path, dst_path, dirs, files in (
        (path, ''.join([dst_base, path[len(src_base):]]), dirs, files)
        for path, dirs, files in os.walk(src_base)
    ):
        if not os.path.exists(dst_path):
            os.mkdir(dst_path)

        for filename in files:
            basename, ext = os.path.splitext(filename)
            if ext.casefold() == '.yaml':
                gz_filename = '.'.join([filename, 'gz'])
                src_filepath = os.path.join(src_path, filename)
                dst_filepath = os.path.join(dst_path, gz_filename)

                if not os.path.exists(dst_filepath):
                    with open(src_filepath) as src, \
                            gzip.open(dst_filepath, 'wb') as dst:
                        dst.write(src.read())


class CustomDevelopCommand(develop):
    def run(self):
        develop.run(self)
        install_config()


class CustomInstallCommand(install):
    def run(self):
        install.run(self)
        install_config()


setup(
    name='prompter',

    version='0.1.dev3',

    description='The pythonic way to make shell prompts.',

    long_description=long_description,

    author='Cliff Hill',
    author_email='xlorep@darkhelm.org',

    url='',

    license='GPLv3',

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: System :: Shells',
    ],

    keywords='shell prompt generator bash',

    packages=find_packages(exclude=['test*']),

    package_data={
        'prompter': [
            os.path.join(path[len(prompter_path) + 1:], filename)
            for path, dirs, files in os.walk(os.path.join(
                prompter_path,
                'config'
            ))
            for filename in files
        ] + [
            os.path.join(path[len(prompter_path) + 1:], filename)
            for path, dirs, files in os.walk(os.path.join(
                prompter_path,
                'default'
            ))
            for filename in files
        ]
    },

    install_requires=[
        'PyYAML>=3.10',
        'appdirs>=1.4',
        'psutil>=2.2',
    ],

    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand,
    },

    entry_points={
        'console_scripts': [
            'prompter = prompter.make_prompt:Prompt.get_prompt',
        ]
    },
)
