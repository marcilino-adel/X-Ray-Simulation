# Beer-Lambert X-Ray Radiography Simulator

## Project Overview

This is a **CPU-based 2D radiography simulator** that demonstrates fundamental X-ray physics principles through interactive simulation and visualization. The simulator models the complete acquisition pipeline from photon emission through detector capture, implementing real physics equations.

## Core Physics Principles

### 1. Beer-Lambert Attenuation Law
$$I = I_0 e^{-\mu x}$$

Where:
- **I** = Transmitted intensity (photons reaching detector)
- **I₀** = Initial photon count (incident dose)
- **μ** = Linear attenuation coefficient (material-dependent)
- **x** = Path length through material

The simulator integrates attenuation coefficients for different tissue types and energies.

### 2. Tissue Attenuation Coefficients
Different tissues and energies have different attenuation responses:

| Tissue | 80 kVp | 120 kVp |
|--------|--------|---------|
| Air | 0.0001 | 0.0001 |
| Soft Tissue | 0.38 | 0.19 |
| Bone | 1.55 | 0.60 |
| Dense/Pathology | 2.50 | 1.20 |

Higher energies penetrate more (lower attenuation).

### 3. Dose-Noise Trade-off (Poisson Statistics)
Quantum noise follows Poisson distribution:
- **Photon count** varies randomly around expected value
- **Lower dose** → More noise → Poisson noise dominates
- **Higher dose** → Less noise → Better visibility but higher radiation

SNR (Signal-to-Noise Ratio) improves with √dose.

### 4. Geometric Effects

#### Magnification
- Determined by **Object-to-Detector Distance (ODD)**
- Magnification factor = Source-to-Detector Distance / Source-to-Object Distance
- Simulated through zoom operation

#### Penumbra (Edge Unsharpness)
- Caused by **finite focal spot size**
- Creates blurred edges at material boundaries
- Applied using Gaussian blur filter
- Inverse relationship with magnification

### 5. Dual-Energy Subtraction
Acquires two images at different energies and performs weighted subtraction:
- **Low Energy (80 kVp)**: Better differentiation of soft tissue
- **High Energy (120 kVp)**: Better penetration, bone less prominent
- **Subtraction**: Eliminates bone, enhances soft tissue (or vice versa)

## Application Features

### Tab 1: Basic Acquisition
**Purpose**: Simulate a single X-ray acquisition

**Controls**:
- **Photon Count (I₀)**: Initial dose (100-50,000 photons)
- **Energy Spectrum**: Low (80 kVp) or High (120 kVp)
- **Apply Poisson Noise**: Enable/disable quantum mottle

**Output**: Single radiograph showing attenuation through digital phantom

### Tab 2: Dose-Noise Analysis
**Purpose**: Quantify dose-noise trade-offs

**Controls**:
- **Min/Max Dose**: Range for analysis
- **Number of Comparisons**: How many doses to compare
- **Analyze Button**: Generates SNR vs Dose plot

**Output**: Graph showing SNR improvement with increasing dose

### Tab 3: Geometric Effects
**Purpose**: Simulate physical constraints of X-ray tubes

**Controls**:
- **Magnification Factor**: 1.0x (no mag) to 3.0x
- **Penumbra (Blur Radius)**: 0-10 pixels focal spot effect

**Output**: Radiograph with geometric distortions applied

### Tab 4: Dual-Energy Subtraction
**Purpose**: Demonstrate advanced imaging technique

**Controls**:
- **Low Energy Dose**: Photons at 80 kVp
- **High Energy Dose**: Photons at 120 kVp
- **Tissue Target**: Isolate 'Soft Tissue' or 'Bone'

**Output**: Three images (Low, High, Subtracted) for comparison

### Tab 5: Pathology Detection
**Purpose**: Analyze at what dose pathologies become invisible

**Controls**:
- **Pathology Type**: Nodule, Fracture, or Density variation
- **Severity**: 0-1 scale (intensity of pathology)
- **Dose Threshold**: Central dose for comparison

**Output**: Comparison of same pathology at different doses

## Digital Phantom Structure

The simulator uses a **2D digital phantom** representing a chest radiograph:

```
Air (background)
  ↓
Soft Tissue (main body/lungs)
  ├─ Bone (spine - vertical structure)
  └─ Ribs (horizontal structures)
```

Each voxel has an attenuation coefficient based on material type. The acquisition process integrates attenuation along the beam path.

## Key Algorithms

### 1. Phantom Creation
- 256×256 pixel 2D array
- Material types: Air (0), Soft Tissue (1), Bone (2), Dense (3)
- Anatomical structures: elliptical main body, spine, ribs

### 2. Attenuation Simulation
```python
# For each pixel (x,y):
# 1. Identify material
# 2. Get attenuation coefficient μ for current energy
# 3. Assume unit path length through that material
# 4. Accumulate: μx = Σ(μ_i * thickness_i)
# 5. Apply Beer-Lambert: I = I₀ * exp(-μx)
```

### 3. Noise Application
```python
# Poisson-distributed photon count
# photon_count = I (intensity map)
# noisy_image = Poisson(photon_count)
# Higher I₀ → Lower variance → Better SNR
```

### 4. Geometric Effects
```python
# Magnification: Zoom operation (interpolation)
# Penumbra: Gaussian blur with σ = penumbra/2.355
```

## Physics Validation

### Expected Behaviors
1. ✓ **Dose increases SNR**: SNR ∝ √dose
2. ✓ **Magnification degrades detail**: Blurring increases with mag
3. ✓ **Higher energy penetrates bone better**: Lower attenuation at 120 kVp
4. ✓ **Pathology visibility** depends on dose and severity
5. ✓ **Dual-Energy** can isolate tissue types

## Example Workflows

### Workflow 1: Optimize for Low-Dose Imaging
1. Go to **Dose-Noise Analysis**
2. Set range: 500 - 5000 photons
3. Analyze trade-off
4. Find minimum dose where pathologies still visible

### Workflow 2: Demonstrate Dual-Energy
1. Go to **Dual-Energy** tab
2. Set low dose: 8000, high dose: 8000
3. Target: Soft Tissue
4. Compare three images to see bone suppression

### Workflow 3: Geometric Constraints Study
1. Go to **Geometric Effects** tab
2. First simulate basic radiograph in tab 1
3. Increase magnification to 2.0x
4. Add penumbra to 3.0px
5. Observe edge unsharpness

## Clinical Relevance

- **Chest radiography**: Primary use case for this simulator
- **Dose optimization**: Finding minimum dose for diagnosis
- **Dual-Energy Chest X-ray**: Emerging technique for improving contrast
- **Quantum noise**: Fundamental limit in low-dose imaging
- **Geometric magnification**: Important in portable/bedside radiography

## Technical Implementation

**Language**: Python 3

**Libraries**:
- `numpy`: Matrix operations
- `scipy`: Filtering, interpolation
- `PyQt5`: GUI framework
- `matplotlib`: Visualization

**Architecture**:
- `physics/beer_lambert.py`: Physics engine
- `ui/radiography_simulator.py`: PyQt5 GUI

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run simulator
python main.py
```

## Key Equations Reference

### Beer-Lambert Law
$$I = I_0 e^{-\mu x}$$

### SNR (Signal-to-Noise Ratio)
$$SNR = \frac{\mu_{signal}}{\sigma_{noise}}$$

### Magnification
$$M = \frac{SDD}{SOD}$$
Where SDD=Source-to-Detector, SOD=Source-to-Object

### Poisson Standard Deviation
$$\sigma = \sqrt{I}$$

## Future Enhancements

1. 3D phantom acquisition (cone-beam geometry)
2. Monte Carlo validation
3. Different phantom geometries
4. Scatter simulation
5. Detector response modeling
6. Real DICOM input/output

