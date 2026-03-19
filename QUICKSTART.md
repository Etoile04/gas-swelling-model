# Quick Start Guide

Get up and running with the Gas Swelling Model in **5 minutes**.

---

## ⏱️ 2-Minute Installation

### Prerequisites

- **Python 3.8+** installed
- Working internet connection

### Option A: pip (Recommended)

```bash
pip install gas-swelling-model[plotting]
```

**Done!** ✓

### Option B: conda

```bash
conda create -n gas-swelling python=3.11 -y
conda activate gas-swelling
conda install -c conda-forge numpy scipy matplotlib -y
pip install gas-swelling-model
```

**Done!** ✓

### Verify Installation

```bash
python -c "from gas_swelling import GasSwellingModel; print('✓ Installation successful!')"
```

---

## 🚀 3-Minute First Simulation

Create a file `my_first_simulation.py`:

```python
from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt

# 1. Setup parameters (default: U-10Zr fuel at 800 K)
params = create_default_parameters()

# 2. Initialize model
model = GasSwellingModel(params)

# 3. Run simulation (100 days of irradiation)
print("Running simulation...")
result = model.solve(t_span=(0, 8.64e6), t_eval=None)

# 4. Print results
print(f"\n✓ Simulation complete!")
print(f"Final swelling: {result['swelling'][-1]:.2%}")
print(f"Final bubble radius: {result['Rcb'][-1]*1e9:.1f} nm")
print(f"Gas release fraction: {result['gas_release'][-1]:.2%}")

# 5. Plot results
plt.figure(figsize=(10, 6))
plt.plot(result['t']/86400, result['swelling']*100, linewidth=2)
plt.xlabel('Time (days)', fontsize=12)
plt.ylabel('Swelling (%)', fontsize=12)
plt.title('Fission Gas Swelling in U-10Zr Fuel at 800 K', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('swelling_curve.png', dpi=150)
print("\n✓ Plot saved as 'swelling_curve.png'")
```

Run it:

```bash
python my_first_simulation.py
```

**Expected output:**
```
Running simulation...

✓ Simulation complete!
Final swelling: 0.15%
Final bubble radius: 12.3 nm
Gas release fraction: 0.08%

✓ Plot saved as 'swelling_curve.png'
```

**Done!** ✓

---

## 🎯 Next Steps

Congratulations! You've successfully:
- ✓ Installed the Gas Swelling Model
- ✓ Run your first simulation
- ✓ Generated a swelling curve plot

### Learn More

- **[📘 INSTALL.md](INSTALL.md)** - Detailed installation options (pip, conda, from source)
- **[📋 Parameter Reference](docs/parameter_reference.md)** - All 40+ parameters explained
- **[🎓 30-Minute Comprehensive Tutorial](docs/tutorials/30minute_quickstart.md)** - Detailed hands-on guide for complete beginners
- **[🐍 quickstart_tutorial.py](examples/quickstart_tutorial.py)** - Detailed step-by-step tutorial
- **[📓 Jupyter Notebook](notebooks/Temperature_Sweep_Example.ipynb)** - Interactive temperature sweep study

### Try Different Conditions

```python
# Higher temperature
params.temperature = 900  # K (vs. default 800 K)

# Different fission rate
params.fission_rate = 5.0e19  # fissions/m³/s (vs. default 4.0e19)

# Use modified Van der Waals EOS
params.eos_model = 'ronchi'  # (vs. default 'ideal')
```

### Troubleshooting

**Import error:**
```bash
pip install --upgrade gas-swelling-model
```

**Plotting not working:**
```bash
pip install matplotlib
```

**Need help?** See [INSTALL.md](INSTALL.md) or [README.md](README.md)

---

**Total time: ~5 minutes** ✓
