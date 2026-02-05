"""
Validation scripts for reproducing figures from the reference paper.

This module contains scripts to reproduce Figures 6, 7, 9, and 10 from:
"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase
of irradiated U-Zr and U-Pu-Zr fuel"

Available scripts:
- reproduce_figure6: U-10Zr swelling vs burnup
- reproduce_figure7: U-19Pu-10Zr swelling vs burnup
- reproduce_figure9_10: High-purity uranium swelling

Usage:
    python -m gas_swelling.validation.scripts.reproduce_figure6 --help
"""

from .reproduce_figure6 import main as main_figure6

__all__ = ['main_figure6']
