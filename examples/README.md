# Gas Swelling Model - Examples

This directory contains tutorials and examples demonstrating how to use the Gas Swelling Model for nuclear fuel materials. Each example is designed to help you understand different aspects of the model, from basic simulations to advanced parameter studies.

## Overview

The examples are organized by difficulty and use case:

- **Beginner**: Start here if you're new to the model
- **Intermediate**: Explore specific features and parameter effects
- **Advanced**: Learn optimization techniques and custom workflows

## 📘 Beginner Examples

### [quickstart_tutorial.py](quickstart_tutorial.py)

**Difficulty:** Beginner | **Time:** 15 minutes

A comprehensive, step-by-step tutorial that guides you through your first gas swelling simulation. This script is heavily commented and explains every step of the process.

**What you'll learn:**
- How to set up model parameters
- Running a basic simulation
- Interpreting and visualizing results
- Understanding the 10 state variables
- Calculating swelling and bubble properties

**Key features:**
- Detailed console output explaining each step
- Multi-panel visualization of all key outputs
- Bonus temperature comparison study
- Interactive (can run non-interactively by modifying the script)

**Run it:**
```bash
python examples/quickstart_tutorial.py
```

**Output:**
- `quickstart_results.png` - Comprehensive 6-panel plot of simulation results
- `quickstart_temperature_comparison.png` - Temperature effects comparison (optional)

**Perfect for:**
- First-time users
- Learning the basics of rate theory
- Understanding model outputs
- Teaching and demonstrations

---

## 📓 Intermediate Examples

### [Temperature_Sweep_Example.ipynb](../notebooks/Temperature_Sweep_Example.ipynb)

**Difficulty:** Intermediate | **Time:** 30 minutes

An interactive Jupyter notebook that explores how temperature affects fuel swelling. This notebook provides a hands-on, interactive environment for experimentation.

**What you'll learn:**
- Running multiple simulations with different parameters
- Temperature effects on bubble nucleation and growth
- Interactive data analysis with pandas
- Custom visualization techniques
- Understanding the "swelling peak" phenomenon

**Key features:**
- Interactive code cells
- Real-time plot modification
- Parameter sensitivity analysis
- Export capabilities

**Run it:**
```bash
jupyter notebook notebooks/Temperature_Sweep_Example.ipynb
```

**Or with JupyterLab:**
```bash
jupyter-lab notebooks/Temperature_Sweep_Example.ipynb
```

**Perfect for:**
- Interactive exploration
- Parameter sensitivity studies
- Creating custom visualizations
- Research and analysis workflows

---

## 🔧 Advanced Examples

### [test4_run_rk23.py](../test4_run_rk23.py)

**Difficulty:** Advanced | **Time:** Variable

A comprehensive test and demonstration script showcasing advanced features of the model. This script is used for validation and includes parameter sweep studies.

**What you'll learn:**
- Advanced parameter configuration
- Temperature sweep studies
- Batch simulation workflows
- Custom analysis routines
- Model validation techniques

**Key features:**
- Temperature sweep function
- Publication-quality plotting
- Comparison with experimental data
- Performance benchmarking
- Extensive customization options

**Run it:**
```bash
python test4_run_rk23.py
```

**Perfect for:**
- Model validation and benchmarking
- Generating publication figures
- Batch processing simulations
- Custom analysis workflows
- Advanced users and researchers

---

## Example Comparison

| Example | Format | Interactivity | Difficulty | Best For |
|---------|--------|---------------|------------|----------|
| **quickstart_tutorial.py** | Python script | Low (console output) | Beginner | Learning basics, understanding workflow |
| **Temperature_Sweep_Example.ipynb** | Jupyter notebook | High (interactive cells) | Intermediate | Exploration, experimentation, teaching |
| **test4_run_rk23.py** | Python script | Low (modify code) | Advanced | Validation, batch processing, research |

## How to Choose an Example

### Start with `quickstart_tutorial.py` if:
- ✅ You're using the model for the first time
- ✅ You want detailed explanations of each step
- ✅ You prefer running scripts rather than notebooks
- ✅ You want to understand the fundamentals

### Use `Temperature_Sweep_Example.ipynb` if:
- ✅ You want to explore parameter effects interactively
- ✅ You're familiar with Jupyter notebooks
- ✅ You need to iterate quickly on different parameters
- ✅ You want to create custom visualizations

### Use `test4_run_rk23.py` if:
- ✅ You need to run parameter sweeps
- ✅ You're validating the model
- ✅ You want publication-quality figures
- ✅ You're working on a research project

## Common Workflows

### Workflow 1: Learning the Model

1. Read the [main README](../README.md) for project overview
2. Run `quickstart_tutorial.py` to see a complete simulation
3. Explore the [Parameter Reference](../docs/parameter_reference.md)
4. Modify parameters in the tutorial and re-run

### Workflow 2: Parameter Study

1. Start with `Temperature_Sweep_Example.ipynb`
2. Modify the temperature range or other parameters
3. Add your own analysis in new notebook cells
4. Export results for reports or publications

### Workflow 3: Research Project

1. Complete the quickstart tutorial
2. Study `test4_run_rk23.py` for advanced patterns
3. Create your own analysis script based on these examples
4. Use the [Jupyter notebook](../notebooks/Temperature_Sweep_Example.ipynb) for exploratory analysis
5. Implement production code in Python scripts

## Modifying Examples

All examples are designed to be modified! Here are some common modifications:

### Change Simulation Time

In any example, modify the simulation time:
```python
# Simulate 200 days instead of 100
simulation_time_days = 200
simulation_time_seconds = simulation_time_days * 24 * 3600
```

### Modify Temperature

```python
# Try different temperatures
params['temperature'] = 950  # K
```

### Change Fission Rate

```python
# Higher fission rate
params['fission_rate'] = 6.0e19  # fissions/(m³·s)
```

### Custom Plots

The visualization code in all examples can be customized. For example, to add a new plot:
```python
# Add gas pressure plot
fig, ax = plt.subplots()
ax.plot(time_days, result['Pg']/1e6, 'b-', linewidth=2)
ax.set_xlabel('Time (days)')
ax.set_ylabel('Gas pressure (MPa)')
ax.set_title('Bubble Internal Pressure')
ax.grid(True, alpha=0.3)
plt.show()
```

## Tips for Running Examples

### Performance

- Use fewer time points for faster initial runs: `t_eval = np.linspace(0, sim_time, 50)`
- Increase time points for smoother plots: `t_eval = np.linspace(0, sim_time, 500)`
- Longer simulations require more computation time

### Visualization

- All examples save plots to PNG files
- Increase DPI for publication-quality figures: `plt.savefig('output.png', dpi=600)`
- Use vector formats for scalability: `plt.savefig('output.pdf')`

### Debugging

- If simulations fail, check parameter values are physically reasonable
- Use the console output to track simulation progress
- The model includes error handling for common issues

## Next Steps

After running the examples:

1. **Explore Parameters**: Read the [Parameter Reference](../docs/parameter_reference.md)
2. **Understand the Physics**: See [model_design.md](../model_design.md) (Chinese)
3. **Advanced Usage**: Check [CLAUDE.md](../CLAUDE.md) for developer documentation
4. **Custom Analysis**: Create your own scripts based on these examples

## Getting Help

- **Documentation**: See [docs/](../docs/) for detailed guides
- **Issues**: Report bugs or request features via the project issue tracker
- **Physics Questions**: Refer to [model_design.md](../model_design.md) and the original paper

## Contributing Examples

Have you created a useful example? We'd love to include it!

Good example contributions:
- Clear, well-commented code
- Focuses on a specific use case
- Includes documentation
- Demonstrates a unique feature or application

---

**Happy Simulating! 🚀**

For the complete project documentation, see the [main README](../README.md).
