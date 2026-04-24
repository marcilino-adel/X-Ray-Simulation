# Beer-Lambert X-Ray Radiography Simulator - Complete Guide

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the simulator
python main.py

# 3. Run tests
python test_physics.py
```

## Project Structure

```
beer-lambert-xray-simulator/
├── main.py                           # Application entry point
├── test_physics.py                   # Physics validation tests
├── requirements.txt                  # Python dependencies
│
├── physics/                          # Core physics engine
│   ├── __init__.py
│   └── beer_lambert.py              # Beer-Lambert simulator implementation
│
└── ui/                              # User interface
    ├── __init__.py
    └── radiography_simulator.py     # PyQt5 GUI
```

---

## Physics Model Overview

### The Forward-Projection Model

This simulator implements a **forward-projection model** of X-ray radiography:

```
X-ray source (point, energy E)
        ↓
    Collimator
        ↓
Digital phantom (tissue with μ(E))
        ↓
    Beer-Lambert attenuation: I = I₀·e^(-μx)
        ↓
Quantum noise (Poisson statistics)
        ↓
    Geometric effects (magnification, penumbra)
        ↓
Detector output (2D radiograph)
```

### Core Equation: Beer-Lambert Law

$$I = I_0 e^{-\mu x}$$

**Components**:

1. **I₀ (Initial Intensity)**: Proportional to radiation dose
   - Related to tube current, exposure time: I₀ ∝ mA·s (mAs)
   - Controls noise level in final image
   - Higher I₀ = more photons = less quantum noise

2. **μ (Linear Attenuation Coefficient)**: Material and energy dependent
   - Units: cm⁻¹
   - **Energy dependence**: μ decreases with higher photon energy
   - **Material dependence**: μ(bone) > μ(soft tissue) > μ(air)

3. **x (Path Length)**: Thickness of material along beam

4. **I (Transmitted Intensity)**: Detected photons
   - Inversely related to attenuation
   - Dark areas = high attenuation (bone, dense tissue)
   - Bright areas = low attenuation (air, soft tissue)

---

## Implementation Details

### 1. Digital Phantom

A **2D array** representing a chest radiograph with:

| Material | ID | μ (80 kVp) | μ (120 kVp) | Anatomy |
|----------|----|-----------|-----------|----|
| Air | 0 | 0.0001 | 0.0001 | Background |
| Soft Tissue | 1 | 0.38 | 0.19 | Main body, lungs |
| Bone | 2 | 1.55 | 0.60 | Spine, ribs |
| Dense | 3 | 2.50 | 1.20 | Pathologies |

**Phantom Structure**:
- Central elliptical region: soft tissue (main body)
- Vertical stripe: spine
- Horizontal stripes: ribs
- Can add pathologies: nodules, fractures, density changes

### 2. Acquisition Simulation

**Algorithm**:
```
1. For each pixel (x,y) in phantom:
   a. Identify material type at this location
   b. Get attenuation coefficient μ for current energy
   c. Path length = 1 unit (simplified 2D projection)
   d. Calculate μx = μ × 1
   e. Apply Beer-Lambert: I(x,y) = I₀ × exp(-μx)

2. Result: 2D array of transmitted intensities
   - One value per detector pixel
   - Bright where attenuation is low
   - Dark where attenuation is high
```

### 3. Dose-Noise Modeling (Poisson Statistics)

Real X-ray detectors count discrete photons. The count follows Poisson distribution:

$$P(N) = \frac{\lambda^N e^{-\lambda}}{N!}$$

Where λ = expected photon count

**Implementation**:
```python
# Convert intensity to photon count
photon_count = I (intensity map)

# Apply Poisson noise
noisy_count = numpy.random.poisson(photon_count)

# Noise characteristics:
# - Mean = I
# - Std Dev = √I
# - SNR = I / √I = √I
```

**Clinical Interpretation**:
- **High dose**: Many photons → small relative noise → high SNR
- **Low dose**: Few photons → large relative noise → low SNR → pathologies may be masked

### 4. Geometric Effects

#### Magnification
Physical setup:
```
Source → Object → Detector
  |         |
  |----d₁---|----d₂----|

Magnification M = (d₁ + d₂) / d₁
ODD = Object-to-Detector Distance = d₂
```

Effect in simulator:
- Scales image by magnification factor
- Increases apparent size (but loses detail due to penumbra)
- Used in portable/bedside radiography (higher magnification)

#### Penumbra (Edge Unsharpness)
Physical cause:
```
Focal spot (size = 0.6 mm typical)
     ⟺
     |
   Object edge
     |
  Detector

Focal spot projects shadow of edge
→ Blurred edge = penumbra
```

Effect in simulator:
- Gaussian blur (simulates focal spot projection)
- Blur radius proportional to focal spot size
- Increases with magnification
- Reduces edge sharpness

### 5. Dual-Energy Subtraction

Principle:
- **Low energy** (80 kVp): Better soft tissue contrast, poor bone penetration
- **High energy** (120 kVp): Poor soft tissue contrast, good bone penetration

Subtraction formula:
$$S = w_L \cdot I_{low} - w_H \cdot I_{high}$$

Where:
- S = subtracted image
- w_L, w_H = energy-specific weights
- For soft tissue isolation: w_L > w_H
- For bone isolation: w_H > w_L

Result:
- **Soft tissue image**: Bone largely suppressed
- **Bone image**: Soft tissue largely suppressed
- Clinical use: Improving diagnostic clarity

---

## Using the Application

### Tab 1: Basic Acquisition

**What it does**: Simulates a single X-ray acquisition

**How to use**:
1. Adjust "Photon Count" slider (I₀ = 100-50,000)
2. Choose energy spectrum (80 or 120 kVp)
3. Toggle "Apply Poisson Noise"
4. Click "Simulate Acquisition"

**What to observe**:
- Brighter image with higher I₀
- Different attenuation patterns at different energies
- Noise becomes visible at low doses

**Example**:
- Set I₀ = 500 → Noisy image
- Set I₀ = 20000 → Clean image
- Same anatomy, different quality

---

### Tab 2: Dose-Noise Analysis

**What it does**: Quantifies the dose-noise trade-off

**How to use**:
1. Set min dose (e.g., 500) and max dose (e.g., 10000)
2. Choose number of steps (e.g., 5)
3. Click "Analyze Dose-Noise Trade-off"

**Output**: Plot showing SNR vs Dose

**Physics insight**:
- SNR increases roughly as √I₀
- Find minimum dose where pathologies are still visible
- Clinical optimization: balance dose and image quality

**Example results**:
```
Dose:    500   2000   5000   10000   20000
SNR:    2.5    5.0    7.9    12.5    17.7
```

---

### Tab 3: Geometric Effects

**What it does**: Shows effect of magnification and focal spot size

**How to use**:
1. Simulate a basic radiograph first (Tab 1)
2. Adjust magnification slider (1.0x - 3.0x)
3. Increase penumbra (0 - 10 pixels)
4. Click "Apply Geometric Effects"

**Observations**:
- Magnification ↑ → Image gets larger but edges blur (penumbra)
- Penumbra ↑ → Edges get softer/blurred
- Trade-off: magnification improves visibility but degrades edge definition

**Clinical example**:
- **Portable radiography**: Limited distance → higher magnification
- **Result**: Worse edge definition (penumbra effect)

---

### Tab 4: Dual-Energy Subtraction

**What it does**: Demonstrates advanced dual-energy imaging

**How to use**:
1. Set doses for low and high energies
2. Choose tissue target (Soft Tissue or Bone)
3. Click "Perform Dual-Energy Subtraction"

**Output**: Three images side-by-side
- Left: Low energy (80 kVp)
- Middle: High energy (120 kVp)
- Right: Subtracted image

**Interpretation**:
- Subtracted image isolates target tissue
- Unwanted tissue largely removed
- Improves diagnostic visibility

**Clinical use**:
- Chest radiography: Suppress ribs for lung pathology detection
- Bone imaging: Suppress soft tissue to see fractures better

---

### Tab 5: Pathology Detection

**What it does**: Tests detectability of pathologies at different doses

**How to use**:
1. Choose pathology type (Nodule, Fracture, or Density)
2. Set severity (0-1 scale)
3. Set dose threshold
4. Click "Analyze Pathology Detection"

**Output**: Three radiographs at different doses showing same pathology

**Analysis**:
- Low dose: Pathology may be masked by quantum noise
- Optimal dose: Pathology clearly visible
- High dose: Excellent visibility but higher radiation

**Clinical relevance**:
- **Low-dose protocols**: Find minimum dose for diagnosis
- **Threshold determination**: At what dose does pathology become invisible?

---

## Key Physics Insights

### 1. Attenuation Coefficient Energy Dependence

```
μ at 80 kVp > μ at 120 kVp

Example - Bone:
- 80 kVp:  μ = 1.55 cm⁻¹
- 120 kVp: μ = 0.60 cm⁻¹

Higher energy photons interact less with matter
→ Better penetration
→ Lower attenuation
→ Brighter image
```

### 2. SNR vs Dose Relationship

Theory:
$$SNR = \sqrt{I_0} \propto \sqrt{\text{dose}}$$

Practical implication:
- Double dose → SNR increases by √2 ≈ 1.41x
- To double SNR → Need 4x dose
- Non-linear relationship favors low-dose imaging when possible

### 3. Penumbra vs Magnification Trade-off

Geometry:
```
Penumbra ∝ Focal Spot Size × ODD
         = Focal Spot Size × (SDD - SOD)

Higher magnification requires higher ODD
→ Higher ODD → Higher penumbra
→ Sharpness degradation

Result: Can't infinitely magnify (geometry limits detail)
```

### 4. Dual-Energy Physics

Why it works:
- μ(E) curves for different materials cross at certain energies
- Weighted subtraction exploits these curves
- Selective tissue removal possible

Example:
```
μ_bone(80 kVp)  = 1.55
μ_bone(120 kVp) = 0.60
Difference = 0.95 ← Good separation

μ_soft(80 kVp)  = 0.38
μ_soft(120 kVp) = 0.19
Difference = 0.19 ← Poor separation

→ Bone shows more energy dependence
→ Can suppress bone by weighting high-energy image more heavily
```

---

## Validation & Testing

Run the test suite to validate physics:

```bash
python test_physics.py
```

**Tests**:
1. ✓ Phantom creation
2. ✓ Beer-Lambert law
3. ✓ Energy dependence
4. ✓ Poisson noise
5. ✓ Dose-noise relationship
6. ✓ Geometric effects
7. ✓ Dual-energy subtraction
8. ✓ Synthetic pathology

---

## Expected Results (Validation)

### Test 1: Dose Impact
```
Dose 500:  Noisy appearance, low SNR
Dose 5000:  Intermediate
Dose 20000: Clean, high SNR
```

### Test 2: Energy Impact
```
80 kVp (low):   Darker image, higher attenuation
120 kVp (high): Brighter image, lower attenuation
```

### Test 3: Magnification
```
1.0x: Sharp edges
2.0x: Edges start to blur
3.0x: Significant blur (penumbra effect)
```

---

## Advanced Topics

### 1. SNR Calculation
$$SNR = \frac{\text{Mean Intensity}}{\text{Std Dev Noise}}$$

With Poisson noise:
$$SNR = \frac{I}{\sqrt{I}} = \sqrt{I}$$

### 2. Contrast
$$\text{Contrast} = \frac{I_{bone} - I_{soft}}{I_{soft}}$$

Changes with dose (improves with √dose).

### 3. MTF (Modulation Transfer Function)
Affected by:
- Penumbra (reduces high-frequency response)
- Detector resolution
- Motion blur

---

## References & Further Reading

1. **Bushberg, J. T., et al.** (2011). "The Essential Physics of Medical Imaging"
2. **Cherry, S. R., et al.** (2012). "Physics in Nuclear Medicine"
3. **Hendee, W. R., & Ritenour, E. R.** (2002). "Medical Imaging Physics"

---

## Technical Support

**Common Issues**:

1. **App won't start**
   - Check Python version (3.6+)
   - Install dependencies: `pip install -r requirements.txt`

2. **Slow performance**
   - Reduce phantom size
   - Use fewer dose comparison points

3. **Questions about physics**
   - See BEERLAMBERTREADME.md for physics details
   - Run test_physics.py for validation

---

**Version**: 1.0  
**Last Updated**: April 2026  
**Authors**: Medical Physics Team

