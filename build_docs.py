#!/usr/bin/env python3
"""Build Sphinx documentation."""
import sys
import os
import site

# Add user site-packages to path
usersite = site.getusersitepackages()
if usersite not in sys.path:
    sys.path.insert(0, usersite)

from sphinx.cmd.build import main as sphinx_build

if __name__ == '__main__':
    # Build from docs directory
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    result = sphinx_build([
        '-b', 'html',
        '-d', os.path.join(docs_dir, '_build/doctrees'),
        docs_dir,  # Source directory
        os.path.join(docs_dir, '_build/html'),  # Output directory
    ])
    sys.exit(result)
