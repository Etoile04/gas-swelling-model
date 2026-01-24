"""Setup configuration for gas-swelling CLI package."""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Read requirements from requirements.txt if it exists
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name='gas-swelling',
    version='0.1.0',
    author='Scientific Computing Team',
    author_email='research@example.com',
    description='Command-line interface for Gas Swelling Model simulations',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/example/gas-swelling',
    packages=find_packages(exclude=['tests', 'tests.*', 'examples', 'docs']),
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
    ],
    python_requires='>=3.8',
    install_requires=[
        'click>=8.0.0',
        'pyyaml>=6.0',
        'tqdm>=4.65.0',
        'numpy>=1.20.0',
        'scipy>=1.7.0',
        'pandas>=1.3.0',
        'h5py>=3.0.0',
    ] + read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'matlab': [
            'scipy>=1.7.0',  # For MATLAB file support
        ],
    },
    entry_points={
        'console_scripts': [
            'gas-swelling=cli.main:cli',
        ],
    },
    keywords='gas swelling simulation nuclear fuel fission bubbles cli',
    project_urls={
        'Bug Reports': 'https://github.com/example/gas-swelling/issues',
        'Source': 'https://github.com/example/gas-swelling',
        'Documentation': 'https://gas-swelling.readthedocs.io/',
    },
)
