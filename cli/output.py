"""
Output Module

This module handles exporting simulation results to various formats.
Supported formats include CSV, JSON, HDF5, and MATLAB.

Functions:
    export_csv: Export results to CSV format
    export_json: Export results to JSON format with metadata
    export_hdf5: Export results to HDF5 format with compression and metadata
    export_matlab: Export results to MATLAB .mat file format with metadata

All exporters follow consistent patterns:
- Create parent directories automatically
- Validate input data
- Support optional metadata
- Provide clear error messages
- Handle numpy arrays and scientific computing data types
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


def _convert_to_json_serializable(obj: Any) -> Any:
    """
    Convert numpy types and other non-serializable objects to JSON-serializable types.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable version of the object
    """
    # Handle numpy arrays
    if hasattr(obj, 'tolist'):
        return obj.tolist()

    # Handle numpy scalars
    if hasattr(obj, 'item'):
        return obj.item()

    # Handle dictionaries recursively
    if isinstance(obj, dict):
        return {key: _convert_to_json_serializable(value) for key, value in obj.items()}

    # Handle lists and tuples recursively
    if isinstance(obj, (list, tuple)):
        return [_convert_to_json_serializable(item) for item in obj]

    # Return as-is if already serializable (int, float, str, bool, None)
    return obj



def export_csv(data: Dict[str, List[Any]], output_path: str) -> None:
    """
    Export simulation results to CSV format.

    Args:
        data: Dictionary with column names as keys and data lists as values
        output_path: Path where CSV file will be saved

    Raises:
        IOError: If file cannot be written
        ValueError: If data is empty or lists have inconsistent lengths

    This will be fully implemented in subtask-4-1.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        raise ValueError("No data to export")

    # Get keys and ensure all lists have same length
    keys = list(data.keys())
    num_rows = len(data[keys[0]])

    # Validate all lists have same length
    for key in keys:
        if len(data[key]) != num_rows:
            raise ValueError(f"Inconsistent data lengths: '{keys[0]}' has {num_rows} elements, '{key}' has {len(data[key])}")

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()

        for i in range(num_rows):
            row = {key: data[key][i] for key in keys}
            writer.writerow(row)


def export_json(data: Dict[str, Any], output_path: str, metadata: Dict[str, Any] = None) -> None:
    """
    Export simulation results to JSON format with metadata.

    Args:
        data: Dictionary containing simulation results
        output_path: Path where JSON file will be saved
        metadata: Optional metadata to include in the JSON

    Raises:
        IOError: If file cannot be written
        ValueError: If data is empty
        TypeError: If data contains non-JSON-serializable types

    This will be fully implemented in subtask-4-2.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        raise ValueError("No data to export")

    # Prepare metadata with timestamp if not provided
    enhanced_metadata = metadata.copy() if metadata else {}
    if 'timestamp' not in enhanced_metadata:
        enhanced_metadata['timestamp'] = datetime.now().isoformat()
    if 'version' not in enhanced_metadata:
        enhanced_metadata['version'] = '1.0'

    # Convert data to JSON-serializable format (handles numpy arrays, etc.)
    serializable_data = _convert_to_json_serializable(data)
    serializable_metadata = _convert_to_json_serializable(enhanced_metadata)

    output_data = {
        'results': serializable_data,
        'metadata': serializable_metadata
    }

    try:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
    except (TypeError, ValueError) as e:
        raise TypeError(f"Data contains non-JSON-serializable types: {e}")
    except IOError as e:
        raise IOError(f"Failed to write JSON file: {e}")


def export_hdf5(data: Dict[str, Any], output_path: str, metadata: Dict[str, Any] = None) -> None:
    """
    Export simulation results to HDF5 format.

    HDF5 format provides efficient storage for large numerical datasets and
    supports hierarchical data organization. This function creates datasets
    for array-like data and attributes for scalar metadata.

    Args:
        data: Dictionary containing simulation results (keys are dataset names,
              values are arrays or lists of data)
        output_path: Path where HDF5 file will be saved
        metadata: Optional metadata to store as HDF5 attributes

    Raises:
        ImportError: If h5py is not installed
        ValueError: If data is empty
        IOError: If file cannot be written

    Example:
        >>> export_hdf5({'time': [0, 1, 2], 'Rcb': [1e-9, 2e-9, 3e-9]},
        ...             'results.h5',
        ...             metadata={'temperature': 650, 'version': '1.0'})
    """
    try:
        import h5py
        import numpy as np
    except ImportError as e:
        module = 'h5py' if 'h5py' in str(e) else 'numpy'
        raise ImportError(f"{module} is required for HDF5 export. "
                        f"Install with: pip install {module}")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        raise ValueError("No data to export")

    try:
        with h5py.File(output_file, 'w') as f:
            # Create datasets for each key in data
            for key, value in data.items():
                # Convert lists and numpy arrays to numpy arrays for HDF5
                if isinstance(value, list):
                    value = np.array(value)
                elif not isinstance(value, np.ndarray):
                    # Convert scalars to single-element arrays
                    value = np.array([value])

                # Create dataset with compression for efficiency
                f.create_dataset(key, data=value, compression='gzip')

            # Store metadata as attributes if provided
            if metadata:
                for meta_key, meta_value in metadata.items():
                    # Convert to JSON-serializable types
                    meta_value = _convert_to_json_serializable(meta_value)
                    if isinstance(meta_value, (list, dict)):
                        # Store complex types as JSON strings
                        f.attrs[meta_key] = json.dumps(meta_value)
                    else:
                        f.attrs[meta_key] = meta_value

                # Add timestamp if not already in metadata
                if 'timestamp' not in metadata:
                    f.attrs['timestamp'] = datetime.now().isoformat()

    except (IOError, OSError) as e:
        raise IOError(f"Failed to write HDF5 file: {e}")
    except Exception as e:
        raise IOError(f"Unexpected error writing HDF5 file: {e}")


def export_matlab(data: Dict[str, Any], output_path: str, metadata: Dict[str, Any] = None) -> None:
    """
    Export simulation results to MATLAB .mat file format.

    MATLAB .mat files can be loaded directly in MATLAB or Octave for
    further analysis and visualization.

    Args:
        data: Dictionary containing simulation results (keys become variable names
              in MATLAB workspace)
        output_path: Path where .mat file will be saved
        metadata: Optional metadata (will be stored as variable '__metadata__')

    Raises:
        ImportError: If scipy is not installed
        ValueError: If data is empty
        IOError: If file cannot be written

    Example:
        >>> export_matlab({'time': [0, 1, 2], 'Rcb': [1e-9, 2e-9, 3e-9]},
        ...              'results.mat',
        ...              metadata={'temperature': 650, 'version': '1.0'})
    """
    try:
        from scipy.io import savemat
        import numpy as np
    except ImportError as e:
        module = 'scipy' if 'scipy' in str(e) else 'numpy'
        raise ImportError(f"{module} is required for MATLAB export. "
                        f"Install with: pip install {module}")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        raise ValueError("No data to export")

    try:
        # Convert data to MATLAB-compatible format
        matlab_data = {}
        for key, value in data.items():
            # Convert lists to numpy arrays for MATLAB compatibility
            if isinstance(value, list):
                matlab_data[key] = np.array(value)
            elif isinstance(value, np.ndarray):
                matlab_data[key] = value
            else:
                # Scalars
                matlab_data[key] = value

        # Add metadata as a special variable if provided
        if metadata:
            enhanced_metadata = metadata.copy()
            if 'timestamp' not in enhanced_metadata:
                enhanced_metadata['timestamp'] = datetime.now().isoformat()
            if 'version' not in enhanced_metadata:
                enhanced_metadata['version'] = '1.0'

            # Convert metadata to JSON-serializable format
            matlab_data['__metadata__'] = _convert_to_json_serializable(enhanced_metadata)

        # Save to .mat file (use -v7.1 format for better compatibility)
        savemat(output_file, matlab_data, format='5', do_compression=True, oned_as='column')

    except (IOError, OSError) as e:
        raise IOError(f"Failed to write MATLAB file: {e}")
    except Exception as e:
        raise IOError(f"Unexpected error writing MATLAB file: {e}")
