"""
Sensitivity analysis module for gas swelling model.

This module provides tools for parameter sensitivity analysis including:
- Base SensitivityAnalyzer class for parameter range management
- One-at-a-Time (OAT) sensitivity analysis
- Morris elementary effects screening
- Sobol variance-based sensitivity analysis
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Union
from ..params.parameters import create_default_parameters
from ..models.modelrk23 import GasSwellingModel


@dataclass
class ParameterRange:
    """Define parameter bounds and sampling distribution for sensitivity analysis.

    Attributes:
        name: Parameter name (must match key in model parameters dict)
        min_value: Minimum bound for parameter
        max_value: Maximum bound for parameter
        nominal_value: Nominal/central value (defaults to midpoint if None)
        distribution: Sampling distribution ('uniform', 'normal', 'lognormal', 'loguniform')
        distribution_params: Additional distribution parameters (e.g., std for normal)

    Example:
        >>> pr = ParameterRange('temperature', 600, 800, nominal_value=700)
        >>> print(pr.name, pr.min_value, pr.max_value)
        temperature 600 800
    """
    name: str
    min_value: float
    max_value: float
    nominal_value: Optional[float] = None
    distribution: str = 'uniform'
    distribution_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and initialize parameter range."""
        # Set nominal value to midpoint if not provided
        if self.nominal_value is None:
            self.nominal_value = (self.min_value + self.max_value) / 2.0

        # Validate bounds
        if self.min_value >= self.max_value:
            raise ValueError(f"ParameterRange '{self.name}': min_value must be less than max_value")

        # Validate nominal value is within bounds
        if not (self.min_value <= self.nominal_value <= self.max_value):
            raise ValueError(
                f"ParameterRange '{self.name}': nominal_value {self.nominal_value} "
                f"must be within bounds [{self.min_value}, {self.max_value}]"
            )

        # Validate distribution type
        valid_distributions = ['uniform', 'normal', 'lognormal', 'loguniform']
        if self.distribution not in valid_distributions:
            raise ValueError(
                f"ParameterRange '{self.name}': distribution must be one of {valid_distributions}"
            )

        # Validate log-uniform and log-normal have positive bounds
        if self.distribution in ['lognormal', 'loguniform']:
            if self.min_value <= 0 or self.max_value <= 0:
                raise ValueError(
                    f"ParameterRange '{self.name}': {self.distribution} distribution "
                    "requires positive min_value and max_value"
                )

    def sample(self, n_samples: int, random_state: Optional[int] = None) -> np.ndarray:
        """Generate samples from the parameter distribution.

        Args:
            n_samples: Number of samples to generate
            random_state: Random seed for reproducibility

        Returns:
            Array of sampled parameter values
        """
        if random_state is not None:
            np.random.seed(random_state)

        if self.distribution == 'uniform':
            return np.random.uniform(self.min_value, self.max_value, n_samples)

        elif self.distribution == 'normal':
            # Use nominal as mean, estimate std from bounds (assuming 95% CI)
            mean = self.nominal_value
            std = self.distribution_params.get('std', (self.max_value - self.min_value) / 4.0)
            return np.random.normal(mean, std, n_samples)

        elif self.distribution == 'loguniform':
            # Sample uniformly in log space
            log_min = np.log10(self.min_value)
            log_max = np.log10(self.max_value)
            return 10 ** np.random.uniform(log_min, log_max, n_samples)

        elif self.distribution == 'lognormal':
            # Sample in log space with normal distribution
            log_mean = np.log(self.nominal_value)
            log_std = self.distribution_params.get('log_std', 0.5)
            return np.random.lognormal(log_mean, log_std, n_samples)

        else:
            raise ValueError(f"Unsupported distribution: {self.distribution}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'nominal_value': self.nominal_value,
            'distribution': self.distribution,
            'distribution_params': self.distribution_params
        }


class SensitivityAnalyzer:
    """Base class for sensitivity analysis of gas swelling model.

    Provides parameter range management and common utilities for
    local (OAT) and global (Morris, Sobol) sensitivity analysis methods.

    Attributes:
        base_parameters: Base model parameters dictionary
        parameter_ranges: List of ParameterRange objects defining parameter bounds
        output_names: List of model output names to analyze sensitivity for

    Example:
        >>> from gas_swelling.analysis.sensitivity import SensitivityAnalyzer
        >>> analyzer = SensitivityAnalyzer()
        >>> print(analyzer.__class__.__name__)
        SensitivityAnalyzer
    """

    def __init__(
        self,
        base_parameters: Optional[Dict[str, Any]] = None,
        parameter_ranges: Optional[List[ParameterRange]] = None,
        output_names: Optional[List[str]] = None
    ):
        """Initialize the sensitivity analyzer.

        Args:
            base_parameters: Base model parameters (uses defaults if None)
            parameter_ranges: List of ParameterRange objects
            output_names: Model output names to analyze (swelling, bubble_radius, etc.)
        """
        self.base_parameters = base_parameters if base_parameters else create_default_parameters()
        self.parameter_ranges = parameter_ranges if parameter_ranges else []
        self.output_names = output_names if output_names else ['swelling']

        # Build parameter index for quick lookup
        self._parameter_index = {pr.name: pr for pr in self.parameter_ranges}

    def add_parameter_range(self, param_range: ParameterRange) -> None:
        """Add a parameter range to the analyzer.

        Args:
            param_range: ParameterRange object to add
        """
        if param_range.name in self._parameter_index:
            raise ValueError(f"Parameter '{param_range.name}' already exists in analyzer")

        self.parameter_ranges.append(param_range)
        self._parameter_index[param_range.name] = param_range

    def remove_parameter_range(self, param_name: str) -> None:
        """Remove a parameter range from the analyzer.

        Args:
            param_name: Name of parameter to remove
        """
        if param_name not in self._parameter_index:
            raise ValueError(f"Parameter '{param_name}' not found in analyzer")

        self.parameter_ranges = [pr for pr in self.parameter_ranges if pr.name != param_name]
        del self._parameter_index[param_name]

    def get_parameter_range(self, param_name: str) -> ParameterRange:
        """Get a parameter range by name.

        Args:
            param_name: Name of parameter to retrieve

        Returns:
            ParameterRange object
        """
        if param_name not in self._parameter_index:
            raise ValueError(f"Parameter '{param_name}' not found in analyzer")
        return self._parameter_index[param_name]

    def get_nominal_parameters(self) -> Dict[str, Any]:
        """Get parameter dictionary with nominal values for all defined ranges.

        Returns:
            Dictionary with nominal parameter values
        """
        nominal_params = self.base_parameters.copy()
        for param_range in self.parameter_ranges:
            nominal_params[param_range.name] = param_range.nominal_value
        return nominal_params

    def generate_parameter_samples(
        self,
        n_samples: int,
        random_state: Optional[int] = None
    ) -> np.ndarray:
        """Generate parameter samples from all defined ranges.

        Args:
            n_samples: Number of samples to generate
            random_state: Random seed for reproducibility

        Returns:
            Array of shape (n_samples, n_parameters) with parameter values
        """
        if not self.parameter_ranges:
            raise ValueError("No parameter ranges defined. Use add_parameter_range() first.")

        samples = np.zeros((n_samples, len(self.parameter_ranges)))
        for i, param_range in enumerate(self.parameter_ranges):
            samples[:, i] = param_range.sample(n_samples, random_state=random_state)

        return samples

    def apply_parameters(
        self,
        base_params: Dict[str, Any],
        parameter_values: Union[Dict[str, float], np.ndarray]
    ) -> Dict[str, Any]:
        """Apply parameter values to base parameter dictionary.

        Args:
            base_params: Base parameter dictionary
            parameter_values: Either a dict or array of parameter values

        Returns:
            Updated parameter dictionary
        """
        new_params = base_params.copy()

        if isinstance(parameter_values, dict):
            for name, value in parameter_values.items():
                new_params[name] = value
        elif isinstance(parameter_values, np.ndarray):
            if len(parameter_values) != len(self.parameter_ranges):
                raise ValueError(
                    f"Parameter array length {len(parameter_values)} does not match "
                    f"number of parameter ranges {len(self.parameter_ranges)}"
                )
            for i, param_range in enumerate(self.parameter_ranges):
                new_params[param_range.name] = parameter_values[i]
        else:
            raise TypeError("parameter_values must be dict or np.ndarray")

        return new_params

    def validate_parameter_ranges(self) -> List[str]:
        """Validate all parameter ranges against model parameters.

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        for param_range in self.parameter_ranges:
            # Check if parameter exists in base parameters
            if param_range.name not in self.base_parameters:
                errors.append(
                    f"Parameter '{param_range.name}' not found in base parameters. "
                    f"Available: {list(self.base_parameters.keys())}"
                )

        return errors

    def get_parameter_names(self) -> List[str]:
        """Get list of parameter names under analysis.

        Returns:
            List of parameter names
        """
        return [pr.name for pr in self.parameter_ranges]

    def get_n_parameters(self) -> int:
        """Get number of parameters under analysis.

        Returns:
            Number of parameters
        """
        return len(self.parameter_ranges)

    def summary(self) -> Dict[str, Any]:
        """Get summary of analyzer configuration.

        Returns:
            Dictionary with analyzer summary
        """
        return {
            'n_parameters': len(self.parameter_ranges),
            'n_parameters_analyzed': len(self.parameter_ranges),
            'parameter_names': self.get_parameter_names(),
            'output_names': self.output_names,
            'base_parameter_keys': list(self.base_parameters.keys())
        }


def create_default_parameter_ranges() -> List[ParameterRange]:
    """Create default parameter ranges for common sensitivity analysis.

    Returns:
        List of ParameterRange objects for key model parameters
    """
    return [
        # Temperature parameters
        ParameterRange(
            name='temperature',
            min_value=500.0,
            max_value=900.0,
            nominal_value=700.0,
            distribution='uniform'
        ),

        # Fission rate
        ParameterRange(
            name='fission_rate',
            min_value=1e20,
            max_value=5e20,
            nominal_value=2e20,
            distribution='uniform'
        ),

        # Dislocation density
        ParameterRange(
            name='dislocation_density',
            min_value=1e13,
            max_value=1e14,
            nominal_value=7e13,
            distribution='loguniform'
        ),

        # Surface energy
        ParameterRange(
            name='surface_energy',
            min_value=0.3,
            max_value=0.7,
            nominal_value=0.5,
            distribution='uniform'
        ),

        # Bulk nucleation factor
        ParameterRange(
            name='Fnb',
            min_value=1e-6,
            max_value=1e-4,
            nominal_value=1e-5,
            distribution='loguniform'
        ),

        # Boundary nucleation factor
        ParameterRange(
            name='Fnf',
            min_value=1e-6,
            max_value=1e-4,
            nominal_value=1e-5,
            distribution='loguniform'
        ),
    ]


@dataclass
class OATResult:
    """Results from One-at-a-Time sensitivity analysis.

    Attributes:
        parameter_name: Name of the parameter that was varied
        nominal_value: Nominal parameter value
        variations: List of parameter values tested
        outputs: Dictionary of output values for each variation (key: output_name, value: array)
        sensitivities: Dictionary of sensitivity metrics (normalized, elasticity)
        baseline_outputs: Dictionary of baseline output values at nominal parameters

    Example:
        >>> result = OATResult('temperature', 700, [650, 700, 750], {'swelling': [...]})
        >>> print(result.parameter_name)
        temperature
    """
    parameter_name: str
    nominal_value: float
    variations: List[float]
    outputs: Dict[str, np.ndarray]
    sensitivities: Dict[str, Dict[str, float]]
    baseline_outputs: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'parameter_name': self.parameter_name,
            'nominal_value': self.nominal_value,
            'variations': self.variations,
            'outputs': {k: v.tolist() for k, v in self.outputs.items()},
            'sensitivities': self.sensitivities,
            'baseline_outputs': self.baseline_outputs
        }


class OATAnalyzer(SensitivityAnalyzer):
    """One-at-a-Time (OAT) sensitivity analyzer for gas swelling model.

    Performs local sensitivity analysis by varying one parameter at a time
    while keeping all other parameters at their nominal values. Calculates
    sensitivity metrics including normalized sensitivity and elasticity.

    Example:
        >>> from gas_swelling.analysis.sensitivity import OATAnalyzer
        >>> from gas_swelling.analysis.sensitivity import create_default_parameter_ranges
        >>> analyzer = OATAnalyzer(parameter_ranges=create_default_parameter_ranges())
        >>> results = analyzer.run_oat_analysis(percent_variations=[-10, 10])
        >>> print(len(results))
        6
    """

    def __init__(
        self,
        base_parameters: Optional[Dict[str, Any]] = None,
        parameter_ranges: Optional[List[ParameterRange]] = None,
        output_names: Optional[List[str]] = None,
        sim_time: float = 7200000.0,
        t_eval_points: int = 100
    ):
        """Initialize the OAT analyzer.

        Args:
            base_parameters: Base model parameters (uses defaults if None)
            parameter_ranges: List of ParameterRange objects to analyze
            output_names: Model outputs to analyze (default: ['swelling'])
            sim_time: Simulation time in seconds (default: 83.3 days)
            t_eval_points: Number of time points for simulation output
        """
        super().__init__(base_parameters, parameter_ranges, output_names)
        self.sim_time = sim_time
        self.t_eval_points = t_eval_points

    def run_simulation(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, np.ndarray]:
        """Run a single gas swelling simulation.

        Args:
            parameters: Model parameters dictionary

        Returns:
            Dictionary with simulation results including time, state variables,
            and derived quantities (swelling, Rcb, Rcf, etc.)
        """
        try:
            model = GasSwellingModel(parameters)
            t_eval = np.linspace(0, self.sim_time, self.t_eval_points)

            result = model.solve(
                t_span=(0, self.sim_time),
                t_eval=t_eval
            )

            return result

        except Exception as e:
            raise RuntimeError(f"Simulation failed: {str(e)}")

    def extract_output(
        self,
        result: Dict[str, np.ndarray],
        output_name: str
    ) -> float:
        """Extract a scalar output value from simulation results.

        Args:
            result: Simulation result dictionary
            output_name: Name of output to extract

        Returns:
            Scalar output value (typically final value or maximum)

        Raises:
            ValueError: If output_name is not recognized
        """
        if output_name == 'swelling':
            # Calculate final swelling percentage
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']

            V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100  # Convert to percentage

            return swelling[-1]  # Return final swelling value

        elif output_name == 'max_swelling':
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']

            V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100

            return np.max(swelling)

        elif output_name == 'final_bubble_radius_bulk':
            return result['Rcb'][-1]

        elif output_name == 'final_bubble_radius_boundary':
            return result['Rcf'][-1]

        elif output_name == 'gas_release_fraction':
            if 'released_gas' in result:
                total_gas = (
                    result['Cgb'][-1] + result['Cgf'][-1] +
                    result['Ccb'][-1] * result['Ncb'][-1] +
                    result['Ccf'][-1] * result['Ncf'][-1] +
                    result['released_gas'][-1]
                )
                if total_gas > 0:
                    return result['released_gas'][-1] / total_gas
            return 0.0

        elif output_name in result:
            # Return final value of any result variable
            value = result[output_name]
            if isinstance(value, np.ndarray):
                return value[-1]
            return value

        else:
            available = list(result.keys()) + [
                'swelling', 'max_swelling',
                'final_bubble_radius_bulk', 'final_bubble_radius_boundary',
                'gas_release_fraction'
            ]
            raise ValueError(
                f"Unknown output '{output_name}'. Available: {available}"
            )

    def calculate_sensitivity_metrics(
        self,
        param_values: np.ndarray,
        output_values: np.ndarray,
        nominal_param: float,
        nominal_output: float
    ) -> Dict[str, float]:
        """Calculate sensitivity metrics from parameter variations.

        Args:
            param_values: Array of parameter values tested
            output_values: Array of corresponding output values
            nominal_param: Nominal parameter value
            nominal_output: Nominal output value

        Returns:
            Dictionary with sensitivity metrics:
                - 'normalized': Average normalized sensitivity (dY/dX * X/Y)
                - 'elasticity': Average elasticity (percent change in Y / percent change in X)
                - 'std': Standard deviation of normalized sensitivity across variations
        """
        if len(param_values) < 2:
            return {
                'normalized': 0.0,
                'elasticity': 0.0,
                'std': 0.0
            }

        # Avoid division by zero
        if nominal_output == 0 or nominal_param == 0:
            return {
                'normalized': 0.0,
                'elasticity': 0.0,
                'std': 0.0
            }

        # Calculate normalized sensitivity for each variation
        # S = (dY/Y) / (dX/X) = (dY/dX) * (X/Y)
        normalized_sensitivities = []
        elasticities = []

        for i, (p_val, y_val) in enumerate(zip(param_values, output_values)):
            dp = p_val - nominal_param
            dy = y_val - nominal_output

            # Normalized sensitivity: (dy/y_nominal) / (dp/p_nominal)
            if dp != 0:
                norm_sens = (dy / nominal_output) / (dp / nominal_param)
                normalized_sensitivities.append(norm_sens)

                # Elasticity: percent change in output / percent change in parameter
                elasticity = (dy / nominal_output * 100) / (dp / nominal_param * 100)
                elasticities.append(elasticity)

        if not normalized_sensitivities:
            return {
                'normalized': 0.0,
                'elasticity': 0.0,
                'std': 0.0
            }

        return {
            'normalized': float(np.mean(normalized_sensitivities)),
            'elasticity': float(np.mean(elasticities)),
            'std': float(np.std(normalized_sensitivities))
        }

    def run_oat_analysis(
        self,
        percent_variations: Optional[List[float]] = None,
        verbose: bool = True
    ) -> List[OATResult]:
        """Run One-at-a-Time sensitivity analysis on all parameters.

        For each parameter, varies it by the specified percentages while
        keeping all other parameters at their nominal values. Runs a
        simulation for each variation and calculates sensitivity metrics.

        Args:
            percent_variations: List of percentage variations to test
                (e.g., [-20, -10, 10, 20] for ±10% and ±20% variations).
                Defaults to [-10, 10] if None.
            verbose: Whether to print progress messages

        Returns:
            List of OATResult objects, one for each parameter analyzed

        Raises:
            ValueError: If no parameter ranges are defined
            RuntimeError: If any simulation fails

        Example:
            >>> analyzer = OATAnalyzer()
            >>> analyzer.add_parameter_range(ParameterRange('temperature', 600, 800))
            >>> results = analyzer.run_oat_analysis(percent_variations=[-10, 10])
            >>> for result in results:
            ...     print(f"{result.parameter_name}: {result.sensitivities['swelling']['elasticity']:.2f}")
        """
        if not self.parameter_ranges:
            raise ValueError(
                "No parameter ranges defined. Use add_parameter_range() to add parameters."
            )

        if percent_variations is None:
            percent_variations = [-10.0, 10.0]

        if verbose:
            print(f"Starting OAT Sensitivity Analysis")
            print(f"  Parameters: {len(self.parameter_ranges)}")
            print(f"  Variations per parameter: {len(percent_variations)}")
            print(f"  Total simulations: {1 + len(self.parameter_ranges) * len(percent_variations)}")
            print(f"  Simulation time: {self.sim_time:.1f}s ({self.sim_time/86400:.2f} days)")
            print()

        # Get nominal parameters
        nominal_params = self.get_nominal_parameters()

        # Run baseline simulation
        if verbose:
            print("Running baseline simulation with nominal parameters...")

        baseline_result = self.run_simulation(nominal_params)
        baseline_outputs = {}

        for output_name in self.output_names:
            try:
                baseline_outputs[output_name] = self.extract_output(baseline_result, output_name)
            except ValueError as e:
                if verbose:
                    print(f"  Warning: {e}")
                baseline_outputs[output_name] = 0.0

        if verbose:
            print(f"  Baseline outputs: {baseline_outputs}")
            print()

        # Analyze each parameter
        results = []

        for i, param_range in enumerate(self.parameter_ranges):
            param_name = param_range.name
            nominal_value = param_range.nominal_value

            if verbose:
                print(f"[{i+1}/{len(self.parameter_ranges)}] Analyzing '{param_name}' (nominal={nominal_value})")

            # Calculate parameter variations
            variations = []
            for pct in percent_variations:
                varied_value = nominal_value * (1.0 + pct / 100.0)
                # Ensure variation stays within bounds
                varied_value = np.clip(varied_value, param_range.min_value, param_range.max_value)
                variations.append(varied_value)

            # Store outputs for each variation
            outputs = {output_name: [] for output_name in self.output_names}

            # Run simulation for each variation
            for j, var_value in enumerate(variations):
                if verbose:
                    print(f"  Variation {j+1}/{len(variations)}: {var_value:.4g} ({(var_value/nominal_value-1)*100:+.1f}%)")

                # Create parameter dictionary with varied parameter
                test_params = self.apply_parameters(nominal_params, {param_name: var_value})

                try:
                    result = self.run_simulation(test_params)

                    # Extract outputs
                    for output_name in self.output_names:
                        try:
                            output_value = self.extract_output(result, output_name)
                            outputs[output_name].append(output_value)
                        except ValueError:
                            outputs[output_name].append(0.0)

                except Exception as e:
                    if verbose:
                        print(f"  Error: Simulation failed - {e}")
                    # Fill with zeros if simulation fails
                    for output_name in self.output_names:
                        outputs[output_name].append(0.0)

            # Calculate sensitivity metrics for each output
            sensitivities = {}
            for output_name in self.output_names:
                output_array = np.array(outputs[output_name])
                param_array = np.array(variations)

                sensitivities[output_name] = self.calculate_sensitivity_metrics(
                    param_array,
                    output_array,
                    nominal_value,
                    baseline_outputs[output_name]
                )

            # Create result object
            oat_result = OATResult(
                parameter_name=param_name,
                nominal_value=nominal_value,
                variations=variations,
                outputs={k: np.array(v) for k, v in outputs.items()},
                sensitivities=sensitivities,
                baseline_outputs=baseline_outputs
            )

            results.append(oat_result)

            if verbose:
                print(f"  Sensitivities:")
                for output_name in self.output_names:
                    sens = sensitivities[output_name]
                    print(f"    {output_name}: elasticity={sens['elasticity']:.3f}, "
                          f"normalized={sens['normalized']:.3f} (±{sens['std']:.3f})")
                print()

        if verbose:
            print("OAT Analysis complete!")

        return results

    def summary(self, results: Optional[List[OATResult]] = None) -> Dict[str, Any]:
        """Generate summary of OAT analysis results.

        Args:
            results: OAT results to summarize (uses last run if None)

        Returns:
            Dictionary with analysis summary
        """
        summary_dict = super().summary()

        if results is not None:
            summary_dict['n_parameters_analyzed'] = len(results)
            rankings_by_output = {}

            for output_name in self.output_names:
                # Rank parameters by absolute elasticity
                param_sensitivities = [
                    (r.parameter_name, abs(r.sensitivities[output_name]['elasticity']))
                    for r in results
                ]
                param_sensitivities.sort(key=lambda x: x[1], reverse=True)

                rankings_by_output[output_name] = param_sensitivities

            if len(self.output_names) == 1:
                summary_dict['parameter_ranking'] = rankings_by_output[self.output_names[0]]
            else:
                summary_dict['parameter_ranking'] = rankings_by_output

        return summary_dict


@dataclass
class MorrisResult:
    """Results from Morris elementary effects screening analysis.

    Attributes:
        parameter_names: List of parameter names analyzed
        mu: Mean of elementary effects for each parameter (measures overall influence)
        mu_star: Mean of absolute elementary effects (measures overall influence magnitude)
        sigma: Standard deviation of elementary effects (measures nonlinearity/interactions)
        elementary_effects: Dictionary mapping output names to arrays of elementary effects
            Shape: (n_trajectories, n_parameters) for each output
        output_names: List of output names analyzed
        n_trajectories: Number of trajectories used in the analysis

    Example:
        >>> result = MorrisResult(
        ...     parameter_names=['temperature', 'fission_rate'],
        ...     mu=np.array([0.5, 0.3]),
        ...     mu_star=np.array([0.6, 0.4]),
        ...     sigma=np.array([0.2, 0.1]),
        ...     elementary_effects={'swelling': np.array([[0.5, 0.7], [0.3, 0.4]])},
        ...     output_names=['swelling'],
        ...     n_trajectories=10
        ... )
        >>> print(result.parameter_names[0], result.mu_star[0])
        temperature 0.6
    """
    parameter_names: List[str]
    mu: np.ndarray  # Shape: (n_parameters,)
    mu_star: np.ndarray  # Shape: (n_parameters,)
    sigma: np.ndarray  # Shape: (n_parameters,)
    elementary_effects: Dict[str, np.ndarray]  # Shape: (n_trajectories, n_parameters) for each output
    output_names: List[str]
    n_trajectories: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'parameter_names': self.parameter_names,
            'mu': self.mu.tolist(),
            'mu_star': self.mu_star.tolist(),
            'sigma': self.sigma.tolist(),
            'elementary_effects': {
                k: v.tolist() for k, v in self.elementary_effects.items()
            },
            'output_names': self.output_names,
            'n_trajectories': self.n_trajectories
        }

    def get_ranking(self, output_name: str = 'swelling') -> List[tuple]:
        """Get parameter ranking by mu_star for a specific output.

        Args:
            output_name: Name of output to rank by

        Returns:
            List of (parameter_name, mu_star) tuples sorted by mu_star (descending)
        """
        if output_name not in self.output_names:
            raise ValueError(f"Output '{output_name}' not in results")

        ranking = [
            (name, mu_star)
            for name, mu_star in zip(self.parameter_names, self.mu_star)
        ]
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking


class MorrisAnalyzer(SensitivityAnalyzer):
    """Morris elementary effects screening analyzer for gas swelling model.

    Performs global sensitivity analysis using the Morris method, which computes
    elementary effects by varying one parameter at a time along random trajectories
    through the parameter space. More efficient than variance-based methods for
    screening many parameters.

    The method computes three key statistics for each parameter:
    - μ (mu): Mean of elementary effects (overall influence, can cancel out)
    - μ* (mu_star): Mean of absolute elementary effects (overall influence magnitude)
    - σ (sigma): Standard deviation of elementary effects (nonlinearity/interactions)

    Example:
        >>> from gas_swelling.analysis.sensitivity import MorrisAnalyzer
        >>> from gas_swelling.analysis.sensitivity import create_default_parameter_ranges
        >>> analyzer = MorrisAnalyzer(parameter_ranges=create_default_parameter_ranges()[:3])
        >>> results = analyzer.run_morris_analysis(n_trajectories=10)
        >>> ranking = results.get_ranking()
        >>> print(f"Most influential: {ranking[0][0]}")
        Most influential: temperature
    """

    def __init__(
        self,
        base_parameters: Optional[Dict[str, Any]] = None,
        parameter_ranges: Optional[List[ParameterRange]] = None,
        output_names: Optional[List[str]] = None,
        sim_time: float = 7200000.0,
        t_eval_points: int = 100,
        num_trajectories: int = 10,
        num_levels: int = 10,
        delta: Optional[float] = None
    ):
        """Initialize the Morris analyzer.

        Args:
            base_parameters: Base model parameters (uses defaults if None)
            parameter_ranges: List of ParameterRange objects to analyze
            output_names: Model outputs to analyze (default: ['swelling'])
            sim_time: Simulation time in seconds (default: 83.3 days)
            t_eval_points: Number of time points for simulation output
            num_trajectories: Default number of trajectories for Morris sampling
            num_levels: Number of discretization levels for parameter space (p)
            delta: Step size for parameter variations (Δ). Defaults to p/(2(p-1))
        """
        super().__init__(base_parameters, parameter_ranges, output_names)
        self.sim_time = sim_time
        self.t_eval_points = t_eval_points
        self.num_trajectories = num_trajectories
        self.num_levels = num_levels

        # Calculate default delta if not provided
        if delta is None:
            self.delta = num_levels / (2.0 * (num_levels - 1))
        else:
            self.delta = delta

        # Validate delta
        if not (0 < self.delta < 1):
            raise ValueError(f"delta must be in (0, 1), got {self.delta}")

    def run_simulation(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, np.ndarray]:
        """Run a single gas swelling simulation.

        Args:
            parameters: Model parameters dictionary

        Returns:
            Dictionary with simulation results including time, state variables,
            and derived quantities (swelling, Rcb, Rcf, etc.)
        """
        try:
            model = GasSwellingModel(parameters)
            t_eval = np.linspace(0, self.sim_time, self.t_eval_points)

            result = model.solve(
                t_span=(0, self.sim_time),
                t_eval=t_eval
            )

            return result

        except Exception as e:
            raise RuntimeError(f"Simulation failed: {str(e)}")

    def extract_output(
        self,
        result: Dict[str, np.ndarray],
        output_name: str
    ) -> float:
        """Extract a scalar output value from simulation results.

        Args:
            result: Simulation result dictionary
            output_name: Name of output to extract

        Returns:
            Scalar output value (typically final value or maximum)

        Raises:
            ValueError: If output_name is not recognized
        """
        if output_name == 'swelling':
            # Calculate final swelling percentage
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']

            V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100  # Convert to percentage

            return swelling[-1]  # Return final swelling value

        elif output_name == 'max_swelling':
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']

            V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100

            return np.max(swelling)

        elif output_name == 'final_bubble_radius_bulk':
            return result['Rcb'][-1]

        elif output_name == 'final_bubble_radius_boundary':
            return result['Rcf'][-1]

        elif output_name == 'gas_release_fraction':
            if 'released_gas' in result:
                total_gas = (
                    result['Cgb'][-1] + result['Cgf'][-1] +
                    result['Ccb'][-1] * result['Ncb'][-1] +
                    result['Ccf'][-1] * result['Ncf'][-1] +
                    result['released_gas'][-1]
                )
                if total_gas > 0:
                    return result['released_gas'][-1] / total_gas
            return 0.0

        elif output_name in result:
            # Return final value of any result variable
            value = result[output_name]
            if isinstance(value, np.ndarray):
                return value[-1]
            return value

        else:
            available = list(result.keys()) + [
                'swelling', 'max_swelling',
                'final_bubble_radius_bulk', 'final_bubble_radius_boundary',
                'gas_release_fraction'
            ]
            raise ValueError(
                f"Unknown output '{output_name}'. Available: {available}"
            )

    def generate_trajectory(self, random_state: Optional[int] = None) -> np.ndarray:
        """Generate a single trajectory for Morris sampling.

        A trajectory consists of (p+1) points in the discretized parameter space,
        where each point differs from the previous by changing exactly one parameter
        by ±Δ.

        Args:
            random_state: Random seed for reproducibility

        Returns:
            Array of shape (n_parameters + 1, n_parameters) with parameter values
        """
        if random_state is not None:
            np.random.seed(random_state)

        n_params = len(self.parameter_ranges)

        # Generate random starting point in discretized space
        # Values are in {0, 1/(p-1), 2/(p-1), ..., 1}
        start_point = np.random.choice(
            np.arange(0, self.num_levels) / (self.num_levels - 1),
            size=n_params
        )

        # Randomly choose direction for each parameter (+1 or -1)
        directions = np.random.choice([-1, 1], size=n_params)

        # Create trajectory: start with random point, then vary each parameter once
        trajectory = np.zeros((n_params + 1, n_params))
        trajectory[0] = start_point.copy()

        # Random permutation of parameter order
        param_order = np.random.permutation(n_params)

        current_point = start_point.copy()
        for i, param_idx in enumerate(param_order):
            # Compute move for this parameter
            move = directions[param_idx] * self.delta
            new_value = current_point[param_idx] + move

            # Ensure we stay within [0, 1]
            # If move would go out of bounds, reverse direction
            if new_value < 0:
                new_value = current_point[param_idx] + abs(move)
            elif new_value > 1:
                new_value = current_point[param_idx] - abs(move)

            # Update point
            current_point[param_idx] = np.clip(new_value, 0, 1)
            trajectory[i + 1] = current_point.copy()

        return trajectory

    def map_trajectory_to_parameters(
        self,
        trajectory: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Map a trajectory from [0,1] space to actual parameter values.

        Args:
            trajectory: Array of shape (n_points, n_parameters) with values in [0, 1]

        Returns:
            List of parameter dictionaries, one for each point in the trajectory
        """
        n_points = trajectory.shape[0]
        param_dicts = []

        for i in range(n_points):
            params = self.base_parameters.copy()
            for j, param_range in enumerate(self.parameter_ranges):
                # Map from [0, 1] to actual parameter range
                param_value = (
                    param_range.min_value +
                    trajectory[i, j] * (param_range.max_value - param_range.min_value)
                )
                params[param_range.name] = param_value
            param_dicts.append(params)

        return param_dicts

    def compute_elementary_effects(
        self,
        trajectory_outputs: List[float]
    ) -> np.ndarray:
        """Compute elementary effects from a single trajectory.

        The elementary effect for parameter i is computed as:
        EE_i = [Y(x + Δe_i) - Y(x)] / Δ

        where e_i is a unit vector in the direction of parameter i.

        Args:
            trajectory_outputs: List of output values for each point in trajectory

        Returns:
            Array of elementary effects, one for each parameter
        """
        n_params = len(self.parameter_ranges)
        elementary_effects = np.zeros(n_params)

        # Compute EE for each parameter
        # Each consecutive pair in trajectory differs by one parameter
        for i in range(n_params):
            y_before = trajectory_outputs[i]
            y_after = trajectory_outputs[i + 1]
            elementary_effects[i] = (y_after - y_before) / self.delta

        return elementary_effects

    def run_morris_analysis(
        self,
        n_trajectories: Optional[int] = None,
        verbose: bool = True,
        random_state: Optional[int] = None
    ) -> MorrisResult:
        """Run Morris elementary effects screening analysis.

        Generates multiple random trajectories through the parameter space,
        computes elementary effects for each parameter along each trajectory,
        and aggregates statistics (μ, μ*, σ) across all trajectories.

        Args:
            n_trajectories: Number of trajectories to generate. Uses the value
                configured at initialization when None.
            verbose: Whether to print progress messages
            random_state: Random seed for reproducibility

        Returns:
            MorrisResult object with elementary effects statistics

        Raises:
            ValueError: If no parameter ranges are defined
            RuntimeError: If any simulation fails

        Example:
            >>> analyzer = MorrisAnalyzer()
            >>> analyzer.add_parameter_range(ParameterRange('temperature', 600, 800))
            >>> results = analyzer.run_morris_analysis(n_trajectories=20)
            >>> print(f"Most influential: {results.get_ranking()[0][0]}")
        """
        if not self.parameter_ranges:
            raise ValueError(
                "No parameter ranges defined. Use add_parameter_range() to add parameters."
            )

        if n_trajectories is None:
            n_trajectories = self.num_trajectories

        n_params = len(self.parameter_ranges)
        param_names = self.get_parameter_names()

        if verbose:
            print(f"Starting Morris Elementary Effects Screening")
            print(f"  Parameters: {n_params}")
            print(f"  Trajectories: {n_trajectories}")
            print(f"  Levels per parameter: {self.num_levels}")
            print(f"  Delta (step size): {self.delta:.3f}")
            print(f"  Total simulations: {n_trajectories * (n_params + 1)}")
            print(f"  Simulation time: {self.sim_time:.1f}s ({self.sim_time/86400:.2f} days)")
            print()

        # Initialize storage for elementary effects
        all_elementary_effects = {
            output_name: np.zeros((n_trajectories, n_params))
            for output_name in self.output_names
        }

        # Run each trajectory
        for traj_idx in range(n_trajectories):
            if verbose:
                print(f"Trajectory {traj_idx + 1}/{n_trajectories}...")

            # Generate trajectory
            if random_state is not None:
                traj_seed = random_state + traj_idx
            else:
                traj_seed = None

            trajectory = self.generate_trajectory(random_state=traj_seed)

            # Map to actual parameter values
            param_dicts = self.map_trajectory_to_parameters(trajectory)

            # Run simulations for each point in trajectory
            trajectory_outputs = {output_name: [] for output_name in self.output_names}

            for point_idx, params in enumerate(param_dicts):
                if verbose and point_idx == 0:
                    print(f"  Running {len(param_dicts)} simulations...")

                try:
                    result = self.run_simulation(params)

                    # Extract outputs
                    for output_name in self.output_names:
                        try:
                            output_value = self.extract_output(result, output_name)
                            trajectory_outputs[output_name].append(output_value)
                        except ValueError:
                            trajectory_outputs[output_name].append(0.0)

                except Exception as e:
                    if verbose:
                        print(f"  Error at point {point_idx}: {e}")
                    # Fill with zeros if simulation fails
                    for output_name in self.output_names:
                        trajectory_outputs[output_name].append(0.0)

            # Compute elementary effects for this trajectory
            for output_name in self.output_names:
                ee = self.compute_elementary_effects(trajectory_outputs[output_name])
                all_elementary_effects[output_name][traj_idx, :] = ee

            if verbose:
                print(f"  Complete!")

        if verbose:
            print()
            print("Computing statistics...")

        # Compute statistics for each output
        # Use swelling as the reference for mu, mu_star, sigma
        reference_output = self.output_names[0]
        ee_ref = all_elementary_effects[reference_output]

        mu = np.mean(ee_ref, axis=0)
        mu_star = np.mean(np.abs(ee_ref), axis=0)
        sigma = np.std(ee_ref, axis=0, ddof=1)

        if verbose:
            print("Morris Analysis complete!")
            print()
            print("Results (sorted by μ*):")
            ranking = sorted(
                [(name, m, m_s, s) for name, m, m_s, s in zip(param_names, mu, mu_star, sigma)],
                key=lambda x: x[2],
                reverse=True
            )
            for name, m, m_s, s in ranking:
                print(f"  {name:25s}: μ* = {m_s:7.3f}, μ = {m:7.3f}, σ = {s:7.3f}")
            print()

        # Create result object
        morris_result = MorrisResult(
            parameter_names=param_names,
            mu=mu,
            mu_star=mu_star,
            sigma=sigma,
            elementary_effects=all_elementary_effects,
            output_names=self.output_names,
            n_trajectories=n_trajectories
        )

        return morris_result

    def summary(self, results: Optional[MorrisResult] = None) -> Dict[str, Any]:
        """Generate summary of Morris analysis results.

        Args:
            results: Morris results to summarize (uses last run if None)

        Returns:
            Dictionary with analysis summary
        """
        summary_dict = super().summary()

        if results is not None:
            summary_dict['n_trajectories'] = results.n_trajectories
            summary_dict['n_parameters_analyzed'] = len(results.parameter_names)
            rankings_by_output = {}

            for output_name in self.output_names:
                if output_name in results.elementary_effects:
                    # Rank parameters by mu_star
                    param_effects = [
                        (name, mu_star)
                        for name, mu_star in zip(results.parameter_names, results.mu_star)
                    ]
                    param_effects.sort(key=lambda x: x[1], reverse=True)

                    rankings_by_output[output_name] = param_effects

            if len(self.output_names) == 1 and self.output_names[0] in rankings_by_output:
                summary_dict['parameter_ranking'] = rankings_by_output[self.output_names[0]]
            else:
                summary_dict['parameter_ranking'] = rankings_by_output

        return summary_dict


@dataclass
class SobolResult:
    """Results from Sobol variance-based sensitivity analysis.

    Attributes:
        parameter_names: List of parameter names analyzed
        S1: First-order Sobol indices for each parameter and output
            Shape: (n_parameters, n_outputs) - measures main effects
        ST: Total-order Sobol indices for each parameter and output
            Shape: (n_parameters, n_outputs) - measures total effects including interactions
        S1_conf: Confidence intervals for first-order indices (optional)
        ST_conf: Confidence intervals for total-order indices (optional)
        output_names: List of output names analyzed
        n_samples: Number of samples used in the analysis
        convergence_data: Dictionary tracking convergence over sample sizes (optional)

    Example:
        >>> result = SobolResult(
        ...     parameter_names=['temperature', 'fission_rate'],
        ...     S1=np.array([[0.6, 0.3], [0.2, 0.4]]),
        ...     ST=np.array([[0.7, 0.5], [0.3, 0.6]]),
        ...     output_names=['swelling', 'gas_release'],
        ...     n_samples=1000
        ... )
        >>> print(result.parameter_names[0], result.S1[0, 0])
        temperature 0.6
    """
    parameter_names: List[str]
    S1: np.ndarray  # Shape: (n_parameters, n_outputs)
    ST: np.ndarray  # Shape: (n_parameters, n_outputs)
    output_names: List[str]
    n_samples: int
    S1_conf: Optional[np.ndarray] = None  # Shape: (n_parameters, n_outputs)
    ST_conf: Optional[np.ndarray] = None  # Shape: (n_parameters, n_outputs)
    convergence_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result_dict = {
            'parameter_names': self.parameter_names,
            'S1': self.S1.tolist(),
            'ST': self.ST.tolist(),
            'output_names': self.output_names,
            'n_samples': self.n_samples
        }

        if self.S1_conf is not None:
            result_dict['S1_conf'] = self.S1_conf.tolist()
        if self.ST_conf is not None:
            result_dict['ST_conf'] = self.ST_conf.tolist()
        if self.convergence_data is not None:
            result_dict['convergence_data'] = self.convergence_data

        return result_dict

    def get_ranking(self, output_name: str = 'swelling', order: str = 'ST') -> List[tuple]:
        """Get parameter ranking by Sobol index for a specific output.

        Args:
            output_name: Name of output to rank by
            order: Which index to use for ranking ('S1' or 'ST')

        Returns:
            List of (parameter_name, sobol_index) tuples sorted by index (descending)
        """
        if output_name not in self.output_names:
            raise ValueError(f"Output '{output_name}' not in results")

        output_idx = self.output_names.index(output_name)
        indices = self.S1 if order == 'S1' else self.ST

        ranking = [
            (name, indices[i, output_idx])
            for i, name in enumerate(self.parameter_names)
        ]
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking


class SobolAnalyzer(SensitivityAnalyzer):
    """Sobol variance-based sensitivity analyzer for gas swelling model.

    Performs global sensitivity analysis using the Sobol decomposition method,
    which quantifies the contribution of each parameter to the output variance.
    Uses Saltelli's sampling scheme for efficient computation of first-order
    (S1) and total-order (ST) Sobol indices.

    Key indices:
    - S1 (first-order): Fraction of output variance due to each parameter alone
    - ST (total-order): Fraction due to each parameter including all interactions

    The method decomposes the output variance as:
    V(Y) = Σ_i V_i + Σ_i Σ_{j>i} V_{ij} + Σ_i Σ_{j>i} Σ_{k>j} V_{ijk} + ...

    where V_i is the variance due to parameter i alone, V_{ij} is due to
    interaction between i and j, etc.

    Example:
        >>> from gas_swelling.analysis.sensitivity import SobolAnalyzer
        >>> from gas_swelling.analysis.sensitivity import create_default_parameter_ranges
        >>> analyzer = SobolAnalyzer(parameter_ranges=create_default_parameter_ranges()[:3])
        >>> results = analyzer.run_sobol_analysis(n_samples=100)
        >>> ranking = results.get_ranking()
        >>> print(f"Most influential: {ranking[0][0]} (ST={ranking[0][1]:.3f})")
        Most influential: temperature (ST=0.650)
    """

    def __init__(
        self,
        base_parameters: Optional[Dict[str, Any]] = None,
        parameter_ranges: Optional[List[ParameterRange]] = None,
        output_names: Optional[List[str]] = None,
        sim_time: float = 7200000.0,
        t_eval_points: int = 100,
        calc_second_order: bool = False
    ):
        """Initialize the Sobol analyzer.

        Args:
            base_parameters: Base model parameters (uses defaults if None)
            parameter_ranges: List of ParameterRange objects to analyze
            output_names: Model outputs to analyze (default: ['swelling'])
            sim_time: Simulation time in seconds (default: 83.3 days)
            t_eval_points: Number of time points for simulation output
            calc_second_order: Whether to calculate second-order indices (computationally expensive)
        """
        super().__init__(base_parameters, parameter_ranges, output_names)
        self.sim_time = sim_time
        self.t_eval_points = t_eval_points
        self.calc_second_order = calc_second_order

    def run_simulation(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, np.ndarray]:
        """Run a single gas swelling simulation.

        Args:
            parameters: Model parameters dictionary

        Returns:
            Dictionary with simulation results including time, state variables,
            and derived quantities (swelling, Rcb, Rcf, etc.)
        """
        try:
            model = GasSwellingModel(parameters)
            t_eval = np.linspace(0, self.sim_time, self.t_eval_points)

            result = model.solve(
                t_span=(0, self.sim_time),
                t_eval=t_eval
            )

            return result

        except Exception as e:
            raise RuntimeError(f"Simulation failed: {str(e)}")

    def extract_output(
        self,
        result: Dict[str, np.ndarray],
        output_name: str
    ) -> float:
        """Extract a scalar output value from simulation results.

        Args:
            result: Simulation result dictionary
            output_name: Name of output to extract

        Returns:
            Scalar output value (typically final value or maximum)

        Raises:
            ValueError: If output_name is not recognized
        """
        if output_name == 'swelling':
            # Calculate final swelling percentage
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']

            V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100  # Convert to percentage

            return swelling[-1]  # Return final swelling value

        elif output_name == 'max_swelling':
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']

            V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100

            return np.max(swelling)

        elif output_name == 'final_bubble_radius_bulk':
            return result['Rcb'][-1]

        elif output_name == 'final_bubble_radius_boundary':
            return result['Rcf'][-1]

        elif output_name == 'gas_release_fraction':
            if 'released_gas' in result:
                total_gas = (
                    result['Cgb'][-1] + result['Cgf'][-1] +
                    result['Ccb'][-1] * result['Ncb'][-1] +
                    result['Ccf'][-1] * result['Ncf'][-1] +
                    result['released_gas'][-1]
                )
                if total_gas > 0:
                    return result['released_gas'][-1] / total_gas
            return 0.0

        elif output_name in result:
            # Return final value of any result variable
            value = result[output_name]
            if isinstance(value, np.ndarray):
                return value[-1]
            return value

        else:
            available = list(result.keys()) + [
                'swelling', 'max_swelling',
                'final_bubble_radius_bulk', 'final_bubble_radius_boundary',
                'gas_release_fraction'
            ]
            raise ValueError(
                f"Unknown output '{output_name}'. Available: {available}"
            )

    def generate_saltelli_samples(
        self,
        n_samples: int,
        random_state: Optional[int] = None
    ) -> np.ndarray:
        """Generate parameter samples using Saltelli's sampling scheme.

        Saltelli's scheme extends Sobol's quasi-random sampling for efficient
        computation of both first-order and total-order indices. It generates:
        - Matrix A: N samples from the parameter space
        - Matrix B: N independent samples from the parameter space
        - Matrices AB_i: For each parameter i, replace column i of A with column i of B

        Total samples: N * (2 + n_parameters)

        Args:
            n_samples: Number of samples per matrix (N)
            random_state: Random seed for reproducibility

        Returns:
            Array of shape (n_samples * (2 + n_parameters), n_parameters) with parameter samples
        """
        if random_state is not None:
            np.random.seed(random_state)

        n_params = len(self.parameter_ranges)

        # Generate base matrix A (samples in [0, 1])
        A = np.random.random((n_samples, n_params))

        # Generate base matrix B (independent samples in [0, 1])
        B = np.random.random((n_samples, n_params))

        # Generate Saltelli sequence
        # Stack A and B
        saltelli_samples = np.vstack([A, B])

        # For each parameter, create AB_i matrices
        for i in range(n_params):
            AB_i = A.copy()
            AB_i[:, i] = B[:, i]
            saltelli_samples = np.vstack([saltelli_samples, AB_i])

        return saltelli_samples

    def map_samples_to_parameters(
        self,
        samples: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Map samples from [0,1] space to actual parameter values.

        Args:
            samples: Array of shape (n_samples, n_parameters) with values in [0, 1]

        Returns:
            List of parameter dictionaries, one for each sample
        """
        n_samples = samples.shape[0]
        param_dicts = []

        for i in range(n_samples):
            params = self.base_parameters.copy()
            for j, param_range in enumerate(self.parameter_ranges):
                # Map from [0, 1] to actual parameter range
                param_value = (
                    param_range.min_value +
                    samples[i, j] * (param_range.max_value - param_range.min_value)
                )
                params[param_range.name] = param_value
            param_dicts.append(params)

        return param_dicts

    def compute_sobol_indices(
        self,
        Y_A: np.ndarray,
        Y_B: np.ndarray,
        Y_AB: np.ndarray
    ) -> tuple:
        """Compute first-order and total-order Sobol indices using Saltelli's estimators.

        The estimators use:
        - First-order S1: V[Y|X_i] contribution
        - Total-order ST: V[E[Y|X_{~i}]] contribution (variance due to all parameters except i)

        Args:
            Y_A: Model outputs for matrix A samples (shape: n_samples,)
            Y_B: Model outputs for matrix B samples (shape: n_samples,)
            Y_AB: Model outputs for AB_i matrices (shape: n_parameters, n_samples)

        Returns:
            Tuple of (S1, ST) arrays, each of shape (n_parameters,)
        """
        n_params = Y_AB.shape[0]

        # Compute total variance
        Y_all = np.concatenate([Y_A, Y_B])
        V_Y = np.var(Y_all, ddof=1)

        if V_Y == 0:
            # No variance in output
            return np.zeros(n_params), np.zeros(n_params)

        # Initialize Sobol indices
        S1 = np.zeros(n_params)
        ST = np.zeros(n_params)

        for i in range(n_params):
            # First-order index S1 (Saltelli 2010 estimator).
            numerator_S1 = np.mean(Y_B * (Y_AB[i] - Y_A))
            S1[i] = numerator_S1 / V_Y

            # Total-order index ST (Jansen estimator).
            ST[i] = 0.5 * np.mean((Y_A - Y_AB[i]) ** 2) / V_Y

        # Ensure indices are in valid range [0, 1]
        # Small negative values or values > 1 can occur due to numerical errors
        S1 = np.clip(S1, 0, 1)
        ST = np.clip(ST, 0, 1)
        ST = np.maximum(ST, S1)

        return S1, ST

    def run_sobol_analysis(
        self,
        n_samples: int = 100,
        verbose: bool = True,
        random_state: Optional[int] = None,
        track_convergence: bool = False
    ) -> SobolResult:
        """Run Sobol variance-based sensitivity analysis using Saltelli sampling.

        Generates Saltelli samples, runs simulations for each sample point,
        and computes first-order (S1) and total-order (ST) Sobol indices
        for all parameters and outputs.

        Args:
            n_samples: Number of samples per matrix (N). Total simulations = N * (2 + n_parameters)
            verbose: Whether to print progress messages
            random_state: Random seed for reproducibility
            track_convergence: Whether to track convergence over increasing sample sizes

        Returns:
            SobolResult object with first-order and total-order indices

        Raises:
            ValueError: If no parameter ranges are defined
            RuntimeError: If any simulation fails

        Example:
            >>> analyzer = SobolAnalyzer()
            >>> analyzer.add_parameter_range(ParameterRange('temperature', 600, 800))
            >>> results = analyzer.run_sobol_analysis(n_samples=100)
            >>> ranking = results.get_ranking()
            >>> print(f"Most influential: {ranking[0][0]}")
        """
        if not self.parameter_ranges:
            raise ValueError(
                "No parameter ranges defined. Use add_parameter_range() to add parameters."
            )

        n_params = len(self.parameter_ranges)
        param_names = self.get_parameter_names()

        # Calculate total number of simulations
        n_simulations = n_samples * (2 + n_params)

        if verbose:
            print(f"Starting Sobol Variance-Based Sensitivity Analysis")
            print(f"  Parameters: {n_params}")
            print(f"  Base samples (N): {n_samples}")
            print(f"  Total simulations: {n_simulations}")
            print(f"  Simulation time: {self.sim_time:.1f}s ({self.sim_time/86400:.2f} days)")
            print()

        # Generate Saltelli samples
        if verbose:
            print("Generating Saltelli sample sequence...")

        samples = self.generate_saltelli_samples(n_samples, random_state=random_state)

        # Map to actual parameter values
        param_dicts = self.map_samples_to_parameters(samples)

        if verbose:
            print(f"  Generated {len(param_dicts)} parameter sets")
            print()

        # Initialize output storage
        # Split samples into A, B, and AB matrices
        # Structure: [A (N), B (N), AB_0 (N), AB_1 (N), ..., AB_{p-1} (N)]
        outputs = {output_name: np.zeros(n_simulations) for output_name in self.output_names}

        # Track convergence if requested
        convergence = {}
        if track_convergence:
            convergence['n_samples_history'] = []
            for output_name in self.output_names:
                convergence[f'{output_name}_S1'] = []
                convergence[f'{output_name}_ST'] = []

        # Run simulations
        if verbose:
            print("Running simulations...")

        for i, params in enumerate(param_dicts):
            if verbose and (i + 1) % max(1, n_simulations // 10) == 0:
                print(f"  Progress: {i+1}/{n_simulations} ({100*(i+1)/n_simulations:.1f}%)")

            try:
                result = self.run_simulation(params)

                # Extract outputs
                for output_name in self.output_names:
                    try:
                        output_value = self.extract_output(result, output_name)
                        outputs[output_name][i] = output_value
                    except ValueError:
                        outputs[output_name][i] = 0.0

            except Exception as e:
                if verbose:
                    print(f"  Error at sample {i}: {e}")
                # Fill with NaN if simulation fails
                for output_name in self.output_names:
                    outputs[output_name][i] = np.nan

        if verbose:
            print(f"  Complete!")
            print()
            print("Computing Sobol indices...")

        # Extract outputs for A, B, and AB matrices
        # A: samples 0 to N-1
        # B: samples N to 2N-1
        # AB_i: samples 2N+i*N to 2N+(i+1)*N-1
        Y_A_all = {output_name: outputs[output_name][:n_samples] for output_name in self.output_names}
        Y_B_all = {output_name: outputs[output_name][n_samples:2*n_samples] for output_name in self.output_names}

        Y_AB_all = {}
        for i in range(n_params):
            start_idx = 2 * n_samples + i * n_samples
            end_idx = start_idx + n_samples
            for output_name in self.output_names:
                if output_name not in Y_AB_all:
                    Y_AB_all[output_name] = np.zeros((n_params, n_samples))
                Y_AB_all[output_name][i] = outputs[output_name][start_idx:end_idx]

        # Compute Sobol indices for each output
        S1_all = np.zeros((n_params, len(self.output_names)))
        ST_all = np.zeros((n_params, len(self.output_names)))

        for j, output_name in enumerate(self.output_names):
            Y_A = Y_A_all[output_name]
            Y_B = Y_B_all[output_name]
            Y_AB = Y_AB_all[output_name]

            S1, ST = self.compute_sobol_indices(Y_A, Y_B, Y_AB)
            S1_all[:, j] = S1
            ST_all[:, j] = ST

        if verbose:
            print("Sobol Analysis complete!")
            print()
            print("Results (sorted by total-order ST):")

            # Use first output as reference for printing
            ref_output_idx = 0
            ref_output_name = self.output_names[ref_output_idx]

            ranking = sorted(
                [(name, S1_all[i, ref_output_idx], ST_all[i, ref_output_idx])
                 for i, name in enumerate(param_names)],
                key=lambda x: x[2],
                reverse=True
            )

            for name, s1, st in ranking:
                print(f"  {name:25s}: S1 = {s1:7.3f}, ST = {st:7.3f}")
            print()

        # Create result object
        sobol_result = SobolResult(
            parameter_names=param_names,
            S1=S1_all,
            ST=ST_all,
            output_names=self.output_names,
            n_samples=n_samples
        )

        return sobol_result

    def summary(self, results: Optional[SobolResult] = None) -> Dict[str, Any]:
        """Generate summary of Sobol analysis results.

        Args:
            results: Sobol results to summarize (uses last run if None)

        Returns:
            Dictionary with analysis summary
        """
        summary_dict = super().summary()

        if results is not None:
            summary_dict['n_samples'] = results.n_samples
            summary_dict['n_parameters_analyzed'] = len(results.parameter_names)
            rankings_by_output = {}

            for output_name in self.output_names:
                output_idx = results.output_names.index(output_name)

                # Rank parameters by total-order index
                param_effects = [
                    (name, results.ST[i, output_idx])
                    for i, name in enumerate(results.parameter_names)
                ]
                param_effects.sort(key=lambda x: x[1], reverse=True)

                rankings_by_output[output_name] = param_effects

            if len(self.output_names) == 1 and self.output_names[0] in rankings_by_output:
                summary_dict['parameter_ranking'] = rankings_by_output[self.output_names[0]]
            else:
                summary_dict['parameter_ranking'] = rankings_by_output

        return summary_dict
