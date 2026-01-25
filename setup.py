"""
setup.py for gas-swelling-model

This file provides backward compatibility for older pip versions and build tools
that don't fully support pyproject.toml. Most metadata is read from pyproject.toml.
"""

import os
from setuptools import setup

# Read the contents of README file (if it exists)
this_directory = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(this_directory, 'README.md')
long_description = "A scientific computing package for modeling fission gas bubble evolution and void swelling behavior in irradiated metallic fuels"
if os.path.exists(readme_path):
    with open(readme_path, encoding='utf-8') as f:
        long_description = f.read()

# Package metadata - should match pyproject.toml
setup(
    name="gas-swelling-model",
    version="0.1.0",
    description="A scientific computing package for modeling fission gas bubble evolution and void swelling behavior in irradiated metallic fuels",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Gas Swelling Model Contributors",
    author_email="",
    url="https://github.com/yourusername/gas-swelling-model",
    project_urls={
        "Homepage": "https://github.com/yourusername/gas-swelling-model",
        "Documentation": "https://github.com/yourusername/gas-swelling-model/blob/main/README.md",
        "Repository": "https://github.com/yourusername/gas-swelling-model",
        "Issues": "https://github.com/yourusername/gas-swelling-model/issues",
    },
    packages=['gas_swelling', 'gas_swelling.models', 'gas_swelling.params', 'gas_swelling.physics', 'gas_swelling.ode', 'gas_swelling.solvers', 'gas_swelling.io'],
    python_requires='>=3.8',
    install_requires=[
        'numpy>=1.20.0',
        'scipy>=1.7.0',
    ],
    extras_require={
        'plotting': ['matplotlib>=3.3.0'],
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'build>=0.10.0',
            'twine>=4.0.0',
        ],
        'all': ['gas-swelling-model[plotting,dev]'],
    },
    keywords=[
        'nuclear',
        'fuel',
        'swelling',
        'fission-gas',
        'metallic-fuel',
        'u-zr',
        'u-pu-zr',
        'rate-theory',
        'scientific-computing',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    license='MIT',
    include_package_data=True,
    zip_safe=False,
)
