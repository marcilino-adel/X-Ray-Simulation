# Beer-Lambert X-Ray Radiography Simulator - File Index

## Application Files

### Entry Point
- **main.py** - Application launcher
  - Initializes PyQt5 app
  - Creates simulator window
  - Error handling

### Core Physics Engine

**Directory**: `physics/`

- **physics/__init__.py** - Module initialization
- **physics/beer_lambert.py** (350+ lines)
  - BeerLambertSimulator class
  - Digital phantom creation
  - Beer-Lambert attenuation simulation
  - Poisson noise application
  - Geometric effects (magnification, penumbra)
  - Dual-energy acquisition
  - Synthetic pathology generation

### User Interface

**Directory**: `ui/`

- **ui/__init__.py** - Module initialization
- **ui/radiography_simulator.py** (600+ lines)
  - RadiographySimulator class (main window)
  - 5 operation tabs:
    1. Basic Acquisition
    2. Dose-Noise Analysis
    3. Geometric Effects
    4. Dual-Energy Subtraction
    5. Pathology Detection
  - Matplotlib integration
  - Real-time visualization

---

## Testing & Validation

- **test_physics.py** (300+ lines)
  - 8 comprehensive test functions
  - Physics validation
  - Results reporting
  - Run with: `python test_physics.py`

---

## Documentation

### Quick Reference
- **BEERLAMBERTREADME.md**
  - Physics overview
  - Equations and principles
  - Clinical relevance
  - Feature descriptions
  - Key algorithms
  - Example workflows

- **SIMULATOR_GUIDE.md**
  - Complete user manual
  - Tab-by-tab walkthroughs
  - Physics insights
  - Expected results
  - Validation procedures
  - Troubleshooting

- **COMPLETION_SUMMARY.md** (this file)
  - Project status
  - Deliverables checklist
  - Implementation details
  - Demo workflows

---

## Configuration & Dependencies

- **requirements.txt**
  - PyQt5>=5.15.0
  - numpy>=1.19.0
  - scipy>=1.5.0
  - matplotlib>=3.3.0

- **config.py** (if present)
  - Configuration constants
  - Default parameters

---

## File Statistics

| Component | Lines | Files | Purpose |
|-----------|-------|-------|---------|
| Physics Engine | 350+ | 1 | Core simulation |
| GUI | 600+ | 1 | User interface |
| Tests | 300+ | 1 | Validation |
| Documentation | 1500+ | 3 | Guidance |
| **Total** | **2750+** | **9** | **Complete system** |

---

## How to Navigate

### For Users (Want to Run Simulation)
1. Read: **BEERLAMBERTREADME.md** (5 min - physics overview)
2. Run: `python main.py`
3. Refer to: **SIMULATOR_GUIDE.md** (as needed - per tab)

### For Developers (Want to Understand Code)
1. Read: **physics/beer_lambert.py** docstrings
2. Read: **ui/radiography_simulator.py** docstrings
3. Study: **test_physics.py** for usage examples
4. Run tests: `python test_physics.py`

### For Validation (Want to Verify Physics)
1. Run: `python test_physics.py`
2. Check output against **SIMULATOR_GUIDE.md** "Expected Results"
3. Run **Tab 2: Dose-Noise Analysis** in app
4. Compare plot with theory

---

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the simulator
python main.py

# Run validation tests
python test_physics.py

# Check Python version (must be 3.6+)
python --version
```

---

## Project Structure Visualization

```
beer-lambert-simulator/
│
├── main.py ............................ Entry point
├── test_physics.py ................... Validation tests
├── requirements.txt ................... Dependencies
│
├── physics/
│   ├── __init__.py
│   └── beer_lambert.py ............... Physics engine (350+ lines)
│
├── ui/
│   ├── __init__.py
│   └── radiography_simulator.py ....... GUI (600+ lines)
│
└── Documentation/
    ├── BEERLAMBERTREADME.md .......... Physics principles
    ├── SIMULATOR_GUIDE.md ............ User guide
    └── COMPLETION_SUMMARY.md ......... Status & deliverables
```

---

## Features by File

### physics/beer_lambert.py
- Digital phantom generation
- Beer-Lambert attenuation
- Energy-dependent modeling
- Poisson noise
- Magnification simulation
- Penumbra modeling
- Dual-energy subtraction
- Pathology generation

### ui/radiography_simulator.py
- 5-tab interface
- Real-time controls
- Matplotlib integration
- Status reporting
- Interactive visualization

### test_physics.py
- Phantom validation
- Law of attenuation verification
- Energy dependence testing
- Noise statistics validation
- Dose-SNR relationship
- Geometric effect testing
- Dual-energy validation
- Pathology testing

---

## Key Classes

### BeerLambertSimulator (physics/beer_lambert.py)
Main physics engine with methods:
- `create_digital_phantom()`
- `simulate_acquisition()`
- `apply_poisson_noise()`
- `apply_geometric_effects()`
- `dual_energy_subtraction()`
- `add_synthetic_pathology()`

### RadiographySimulator (ui/radiography_simulator.py)
Main GUI window with methods:
- `create_basic_tab()`
- `create_dose_noise_tab()`
- `create_geometric_tab()`
- `create_dualenergy_tab()`
- `create_pathology_tab()`
- `simulate_basic()`
- `analyze_dose_noise()`
- `perform_dual_energy()`
- `analyze_pathology()`

---

## Constants & Parameters

### Attenuation Coefficients (cm⁻¹)
```python
ATTENUATION_COEFFICIENTS = {
    'air': {'low': 0.0001, 'high': 0.0001},
    'soft_tissue': {'low': 0.38, 'high': 0.19},
    'bone': {'low': 1.55, 'high': 0.60},
    'dense': {'low': 2.50, 'high': 1.20},
}
```

### Default Parameters
- Phantom size: 256×256 pixels
- Default I₀: 10,000 photons
- Energy options: 80 kVp ('low'), 120 kVp ('high')
- Magnification range: 1.0x - 3.0x
- Penumbra range: 0 - 10 pixels

---

## Contact & Support

For questions or issues:
1. Check **SIMULATOR_GUIDE.md** troubleshooting section
2. Run `python test_physics.py` to validate setup
3. Review inline code comments
4. Consult **BEERLAMBERTREADME.md** for physics questions

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Apr 24, 2026 | Initial release - all features complete |

---

**Status**: ✅ COMPLETE  
**Last Updated**: April 24, 2026  
**All Systems**: OPERATIONAL

