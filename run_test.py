#!/usr/bin/env python3
"""
Minimal test runner to verify test_oat_workflow logic
"""
import sys
sys.path.insert(0, '.')

print("Testing OAT workflow logic...")

# Import required modules
import numpy as np
from gas_swelling.analysis.sensitivity import (
    OATAnalyzer,
    ParameterRange
)

# Test the workflow step by step
print("\n1. Creating parameter ranges...")
param_ranges = [
    ParameterRange('temperature', 650, 750, nominal_value=700),
    ParameterRange('fission_rate', 1.5e20, 2.5e20, nominal_value=2e20)
]
print(f"   Created {len(param_ranges)} parameter ranges")

print("\n2. Creating OAT analyzer...")
analyzer = OATAnalyzer(
    parameter_ranges=param_ranges,
    output_names=['swelling'],
    sim_time=3600000.0,
    t_eval_points=50
)
print(f"   Analyzer created with {analyzer.get_n_parameters()} parameters")

print("\n3. Running OAT analysis (this may take a moment)...")
try:
    results = analyzer.run_oat_analysis(
        percent_variations=[-10, 10],
        verbose=False
    )
    print(f"   ✓ Analysis completed successfully")
    print(f"   Got {len(results)} results")

    print("\n4. Verifying results structure...")
    assert isinstance(results, list), "Results should be a list"
    assert len(results) == 2, "Should have 2 parameter results"
    print("   ✓ Results structure is correct")

    print("\n5. Verifying first result (temperature)...")
    temp_result = results[0]
    assert temp_result.parameter_name == 'temperature', "First parameter should be temperature"
    assert temp_result.nominal_value == 700, "Nominal value should be 700"
    assert len(temp_result.variations) == 2, "Should have 2 variations"
    assert 'swelling' in temp_result.outputs, "Should have swelling output"
    assert 'swelling' in temp_result.sensitivities, "Should have swelling sensitivities"
    assert 'swelling' in temp_result.baseline_outputs, "Should have swelling baseline"
    print("   ✓ Temperature result is correct")

    print("\n6. Verifying sensitivity metrics...")
    sens = temp_result.sensitivities['swelling']
    assert 'normalized' in sens, "Should have normalized sensitivity"
    assert 'elasticity' in sens, "Should have elasticity"
    assert 'std' in sens, "Should have std"
    assert isinstance(sens['normalized'], (int, float)), "Normalized should be numeric"
    assert isinstance(sens['elasticity'], (int, float)), "Elasticity should be numeric"
    assert isinstance(sens['std'], (int, float)), "Std should be numeric"
    print("   ✓ Sensitivity metrics are correct")

    print("\n7. Verifying second result (fission_rate)...")
    fission_result = results[1]
    assert fission_result.parameter_name == 'fission_rate', "Second parameter should be fission_rate"
    assert fission_result.nominal_value == 2e20, "Nominal value should be 2e20"
    print("   ✓ Fission rate result is correct")

    print("\n✓✓✓ All test_oat_workflow verifications passed! ✓✓✓")

except Exception as e:
    print(f"\n✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nThe test_oat_workflow test is correctly structured and working!")
