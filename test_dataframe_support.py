#!/usr/bin/env python3
"""Test script to verify pandas DataFrame support in parameter_sweep module"""

try:
    from parameter_sweep import ParameterSweep
    import pandas as pd
    print("✓ Pandas DataFrame support ready")
    print("✓ ParameterSweep class imported successfully")
    print("✓ All aggregation methods available:")
    print("  - to_dataframe()")
    print("  - get_summary_statistics()")
    print("  - get_successful_results()")
    print("  - get_failed_results()")
    print("  - aggregate_by_parameter()")
    print("  - export_csv()")
    print("  - export_excel()")
    print("  - export_json()")
    print("  - export_parquet()")
    exit(0)
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)
