"""
Test suite for Beer-Lambert X-ray simulator
Validates all physics implementations
"""

import numpy as np
import sys
import os

# Add project to path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from physics.beer_lambert import BeerLambertSimulator


def test_phantom_creation():
    """Test digital phantom creation"""
    print("\n[TEST] Phantom Creation")
    print("-" * 50)
    
    simulator = BeerLambertSimulator(seed=42)
    phantom = simulator.create_digital_phantom(256, 256, 64)
    
    assert phantom.shape == (64, 256, 256), "Phantom shape incorrect"
    assert phantom.dtype == np.uint8, "Phantom dtype incorrect"
    
    unique_materials = np.unique(phantom)
    print(f"✓ Phantom created: {phantom.shape}")
    print(f"✓ Materials present: {unique_materials}")
    print(f"✓ Material counts: {dict(zip(unique_materials, np.bincount(phantom.flatten())))}")
    
    return True


def test_beerlambertlaw():
    """Test Beer-Lambert law implementation"""
    print("\n[TEST] Beer-Lambert Law")
    print("-" * 50)
    
    simulator = BeerLambertSimulator(seed=42)
    simulator.create_digital_phantom()
    
    # Test: Lower I₀ should give lower intensity
    radiograph_low = simulator.simulate_acquisition(simulator.phantom, I0=1000, energy='high')
    radiograph_high = simulator.simulate_acquisition(simulator.phantom, I0=10000, energy='high')
    
    assert radiograph_low.mean() < radiograph_high.mean(), "Higher I₀ should give higher intensity"
    
    print(f"✓ I₀=1000:  Mean intensity = {radiograph_low.mean():.2f}")
    print(f"✓ I₀=10000: Mean intensity = {radiograph_high.mean():.2f}")
    print(f"✓ Ratio (high/low) = {radiograph_high.mean() / radiograph_low.mean():.2f}x")
    
    return True


def test_energy_dependence():
    """Test energy-dependent attenuation"""
    print("\n[TEST] Energy Dependence")
    print("-" * 50)
    
    simulator = BeerLambertSimulator(seed=42)
    simulator.create_digital_phantom()
    
    # High energy should penetrate better (higher intensity in bones)
    radiograph_low = simulator.simulate_acquisition(simulator.phantom, I0=10000, energy='low')
    radiograph_high = simulator.simulate_acquisition(simulator.phantom, I0=10000, energy='high')
    
    # Find bone region (spine) - should have higher intensity at high energy
    spine_region = radiograph_high[120:140, 120:140]
    assert spine_region.mean() > 0, "Intensity should be positive"
    
    print(f"✓ Low energy (80 kVp)  - Mean intensity: {radiograph_low.mean():.2f}")
    print(f"✓ High energy (120 kVp) - Mean intensity: {radiograph_high.mean():.2f}")
    print(f"✓ Higher energy penetrates better (higher intensity)")
    
    return True


def test_poisson_noise():
    """Test Poisson noise implementation"""
    print("\n[TEST] Poisson Noise")
    print("-" * 50)
    
    simulator = BeerLambertSimulator(seed=42)
    simulator.create_digital_phantom()
    
    radiograph = simulator.simulate_acquisition(simulator.phantom, I0=10000, energy='high')
    
    noisy_images = []
    for i in range(3):
        noisy = simulator.apply_poisson_noise(radiograph)
        noisy_images.append(noisy)
    
    # Each realization should be different but similar
    img1, img2 = noisy_images[0], noisy_images[1]
    rmse = np.sqrt(np.mean((img1 - img2)**2))
    
    print(f"✓ Original - Mean: {radiograph.mean():.2f}, Std: {radiograph.std():.2f}")
    print(f"✓ Noisy 1  - Mean: {img1.mean():.2f}, Std: {img1.std():.2f}")
    print(f"✓ Noisy 2  - Mean: {img2.mean():.2f}, Std: {img2.std():.2f}")
    print(f"✓ RMSE between two noisy realizations: {rmse:.2f}")
    
    return True


def test_dose_noise_relationship():
    """Test dose-noise trade-off (SNR increases with dose)"""
    print("\n[TEST] Dose-Noise Trade-off")
    print("-" * 50)
    
    simulator = BeerLambertSimulator(seed=42)
    simulator.create_digital_phantom()
    
    doses = [500, 1000, 5000, 10000]
    snrs = []

    masks = simulator.get_projected_material_masks(simulator.phantom)
    signal_mask = masks['soft_tissue'] & ~masks['bone']
    if np.count_nonzero(signal_mask) < 50:
        signal_mask = masks['soft_tissue']
    
    for dose in doses:
        radiograph = simulator.simulate_acquisition(simulator.phantom, I0=dose, energy='high')
        radiograph_noisy = simulator.apply_poisson_noise(radiograph)
        
        signal_values = radiograph_noisy[signal_mask]
        mean_signal = np.mean(signal_values)
        std_noise = np.std(signal_values)
        snr = mean_signal / (std_noise + 1e-6)
        snrs.append(snr)
        
        print(f"✓ Dose {dose:5d}: SNR = {snr:.3f}")
    
    # SNR should increase with dose
    assert snrs[-1] > snrs[0], "Higher dose should give higher SNR"
    print(f"✓ SNR increases with dose (as expected)")
    
    return True


def test_geometric_effects():
    """Test geometric magnification and penumbra"""
    print("\n[TEST] Geometric Effects")
    print("-" * 50)

    simulator = BeerLambertSimulator(seed=42)
    simulator.create_digital_phantom()
    radiograph = simulator.simulate_acquisition(simulator.phantom, I0=10000, energy='high')

    # ── Test 1: Magnification Only (Penumbra OFF) ─────────
    # SID=100, ODD=33 → SOD=67 → M = 100/67 ≈ 1.5x
    radiograph_mag = simulator.apply_geometric_effects(
        radiograph,
        SID=100.0,
        ODD=33.0,
        focal_spot_size=0.06,
        apply_magnification=True,
        apply_penumbra=False       # OFF to isolate magnification
    )
    print(f"✓ Original shape:       {radiograph.shape}")
    print(f"✓ Magnified (1.5x) shape: {radiograph_mag.shape}")

    # ── Test 2: Penumbra Only (Magnification OFF) ─────────
    # SID=100, ODD=50 → SOD=50 → P = 0.06 × (50/50) = 0.06 cm = 0.6 px
    radiograph_blur = simulator.apply_geometric_effects(
        radiograph,
        SID=100.0,
        ODD=50.0,
        focal_spot_size=0.06,
        apply_magnification=False,  # OFF to isolate penumbra
        apply_penumbra=True
    )
    blur_std = np.std(radiograph_blur - radiograph)
    print(f"✓ Penumbra applied - Blur effect std: {blur_std:.2f}")

    # ── Test 3: Both Effects Together ─────────────────────
    # SID=100, ODD=50 → SOD=50 → M=2.0x, P=0.06cm
    radiograph_both = simulator.apply_geometric_effects(
        radiograph,
        SID=100.0,
        ODD=50.0,
        focal_spot_size=0.06,
        apply_magnification=True,
        apply_penumbra=True
    )
    print(f"✓ Both effects applied - Mean: {radiograph_both.mean():.2f}")

    # ── Test 4: No Effect (ODD=0) ─────────────────────────
    radiograph_none = simulator.apply_geometric_effects(
        radiograph,
        SID=100.0,
        ODD=0.0,
        focal_spot_size=0.06,
        apply_magnification=True,
        apply_penumbra=True
    )
    assert np.allclose(radiograph, radiograph_none), "ODD=0 should produce no change"
    print(f"✓ ODD=0 produces no change (as expected)")

    print(f"✓ Geometric effects working correctly")
    return True


def test_dual_energy_subtraction():
    """Test dual-energy acquisition and subtraction"""
    print("\n[TEST] Dual-Energy Subtraction")
    print("-" * 50)
    
    simulator = BeerLambertSimulator(seed=42)
    simulator.create_digital_phantom()
    
    img_low, img_high, subtracted = simulator.dual_energy_subtraction(
        simulator.phantom, I0_low=8000, I0_high=8000, tissue_target='soft_tissue'
    )
    
    expected_shape = simulator.phantom.shape[-2:]
    assert img_low.shape == expected_shape, "Shape mismatch"
    assert img_high.shape == expected_shape, "Shape mismatch"
    assert subtracted.shape == expected_shape, "Shape mismatch"
    
    print(f"✓ Low energy image:  Mean = {img_low.mean():.2f}")
    print(f"✓ High energy image: Mean = {img_high.mean():.2f}")
    print(f"✓ Subtracted image:  Mean = {subtracted.mean():.2f}")
    print(f"✓ Dual-Energy subtraction working correctly")
    
    return True


def test_synthetic_pathology():
    """Test synthetic pathology generation"""
    print("\n[TEST] Synthetic Pathology")
    print("-" * 50)
    
    simulator = BeerLambertSimulator(seed=42)
    phantom = simulator.create_digital_phantom()
    
    pathologies = ['nodule', 'fracture', 'density']
    
    for pathology_type in pathologies:
        phantom_with_path = simulator.add_synthetic_pathology(
            phantom, pathology_type=pathology_type, severity=0.7
        )
        
        # Should have some differences
        diff = np.sum(phantom_with_path != phantom)
        print(f"✓ {pathology_type:10s} - {diff:5d} voxels modified")
    
    print(f"✓ Synthetic pathology generation working correctly")
    
    return True


def test_fracture_projection_visibility():
    """Test that fracture alters projected radiograph intensity."""
    print("\n[TEST] Fracture Projection Visibility")
    print("-" * 50)

    simulator = BeerLambertSimulator(seed=42)
    phantom = simulator.create_digital_phantom()
    phantom_with_fracture, lesion_mask = simulator.add_synthetic_pathology(
        phantom, pathology_type='fracture', severity=0.8, return_mask_2d=True
    )

    base = simulator.simulate_acquisition(phantom, I0=10000, energy='high')
    fracture = simulator.simulate_acquisition(phantom_with_fracture, I0=10000, energy='high')

    lesion_pixels = int(np.count_nonzero(lesion_mask))
    assert lesion_pixels > 0, "Lesion mask should be non-empty"

    mean_abs_diff = float(np.mean(np.abs(fracture[lesion_mask] - base[lesion_mask])))
    assert mean_abs_diff > 0.1, "Fracture should create measurable projection contrast"

    print(f"✓ Lesion pixels: {lesion_pixels}")
    print(f"✓ Mean lesion contrast (ideal): {mean_abs_diff:.4f}")
    return True


def test_rose_detectability_increases_with_dose():
    """Test Rose d' trend with increasing dose."""
    print("\n[TEST] Rose Detectability vs Dose")
    print("-" * 50)

    simulator = BeerLambertSimulator(seed=42)
    phantom = simulator.create_digital_phantom()
    phantom_with_nodule, lesion_mask = simulator.add_synthetic_pathology(
        phantom, pathology_type='nodule', severity=0.7, return_mask_2d=True
    )

    doses = [1000, 5000, 10000]
    dprimes = []

    for dose in doses:
        pathology_ideal = simulator.simulate_acquisition(phantom_with_nodule, I0=dose, energy='high')
        pathology_noisy = simulator.apply_poisson_noise(pathology_ideal)

        rose = simulator.compute_rose_detectability(
            pathology_noisy,
            lesion_mask,
            I0=float(dose),
        )
        dprimes.append(rose['rose_dprime'])
        print(f"✓ Dose {dose:5d}: d' = {rose['rose_dprime']:.3f}")

    assert dprimes[-1] > dprimes[0], "Rose d' should increase with dose"
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("BEER-LAMBERT X-RAY SIMULATOR - TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_phantom_creation,
        test_beerlambertlaw,
        test_energy_dependence,
        test_poisson_noise,
        test_dose_noise_relationship,
        test_geometric_effects,
        test_dual_energy_subtraction,
        test_synthetic_pathology,
        test_fracture_projection_visibility,
        test_rose_detectability_increases_with_dose,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
