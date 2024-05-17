import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md'),
          'r',
          encoding='utf-8') as fh:
    readme = fh.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='cloudreve',
    version='1.0.5',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    include_package_data=True,
    license='GPLv3',
    description='Python SDK for Cloudreve sites',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/yxzlwz/cloudreve-sdk',
    author='yxzlwz',
    author_email='yxzlwz@gmail.com',
    install_requires=[
        'requests',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
)
