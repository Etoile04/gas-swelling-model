"""
Gas Swelling Model Wrapper (气体肿胀模型包装器)

This module provides backward compatibility by wrapping the refactored model.
The actual implementation has been moved to refactored_model.py.

此模块通过包装重构后的模型提供向后兼容性。
实际实现已移至 refactored_model.py。

DEPRECATED: For new code, please use:
    from gas_swelling.models.refactored_model import RefactoredGasSwellingModel

已弃用：对于新代码，请使用：
    from gas_swelling.models.refactored_model import RefactoredGasSwellingModel

使用示例 (Usage Example):
    >>> from gas_swelling.models.modelrk23 import GasSwellingModel
    >>> from gas_swelling.params.parameters import create_default_parameters
    >>>
    >>> # Create model with custom parameters
    >>> params = create_default_parameters()
    >>> params['temperature'] = 773.15  # 500°C in Kelvin
    >>> model = GasSwellingModel(params)
    >>>
    >>> # Solve simulation
    >>> results = model.solve(t_span=(0, 8640000), t_eval=time_points)
"""

# Import the refactored model and provide backward-compatible alias
from .refactored_model import RefactoredGasSwellingModel as GasSwellingModel

# Export the main class
__all__ = ['GasSwellingModel']
