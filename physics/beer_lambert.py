"""
Beer-Lambert X-Ray Physics Simulator
Core physics engine for X-ray attenuation simulation
"""

import numpy as np
from scipy import ndimage
from typing import Tuple, Dict, Optional


class BeerLambertSimulator:
    """
    Simulates X-ray attenuation through heterogeneous tissue using Beer-Lambert law.
    I = I₀ * e^(-μx)
    """
    
    # Attenuation coefficients at different energies (cm^-1)
    # Based on typical medical X-ray physics
    ATTENUATION_COEFFICIENTS = {
        'air': {'low': 0.0001, 'high': 0.0001},
        'soft_tissue': {'low': 0.38, 'high': 0.19},
        'bone': {'low': 1.55, 'high': 0.60},
        'dense': {'low': 2.50, 'high': 1.20},  # pathology
        'fracture': {'low': 1.15, 'high': 0.45},  # subtle cortical crack material
    }
    
    def __init__(self, seed: Optional[int] = None):
        self.phantom = None
        self.I0 = 10000  # Initial photon count (dose)
        self.energy = 'high'  # 'low' (80 kVp) or 'high' (120 kVp)
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.voxel_size_cm = 0.1  # 1 mm voxel thickness equivalent
        self.last_dual_weights = (1.0, 1.0)
        self.last_pathology_mask_2d = None

    @staticmethod
    def _ensure_3d(phantom: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Return a 3D view of the phantom and whether original input was 2D."""
        if phantom.ndim == 2:
            return phantom[np.newaxis, ...], True
        if phantom.ndim == 3:
            return phantom, False
        raise ValueError("Phantom must be 2D or 3D")
        
    def create_digital_phantom(self, width: int = 256, height: int = 256, depth: int = 64) -> np.ndarray:
        """
        Create a 3D digital phantom with heterogeneous tissue layers.
        
        Structure:
        - Air: background
        - Soft tissue: main body
        - Bone: structures embedded in soft tissue
        
        Args:
            width: Phantom width in pixels
            height: Phantom height in pixels
            depth: Phantom depth in slices
            
        Returns:
            3D numpy array with shape (depth, height, width)
        """
        print(f"[Physics] Creating {depth}x{height}x{width} digital phantom...")

        phantom = np.zeros((depth, height, width), dtype=np.uint8)

        center_z, center_y, center_x = depth // 2, height // 2, width // 2
        base_radius_y, base_radius_x = height // 3, width // 3

        yy, xx = np.ogrid[:height, :width]

        # Body soft tissue shell with depth-dependent thickness profile
        for z in range(depth):
            z_norm = (z - center_z) / max(center_z, 1)
            depth_scale = np.sqrt(max(0.0, 1.0 - 0.85 * (z_norm ** 2)))
            ry = max(6, int(base_radius_y * depth_scale))
            rx = max(6, int(base_radius_x * depth_scale))
            mask_soft = ((xx - center_x) ** 2 / (rx ** 2) + (yy - center_y) ** 2 / (ry ** 2)) <= 1
            phantom[z][mask_soft] = 1

        # Bone structures through central depth range
        z_start = int(depth * 0.40)  # was 0.25
        z_end = int(depth * 0.60)  # was 0.75
        spine_width = max(8, width // 12)
        phantom[z_start:z_end, center_y - 50:center_y + 50, center_x - spine_width // 2:center_x + spine_width // 2] = 2

        rib_spacing = 40
        rib_height = 12
        x0 = int(center_x - base_radius_x * 0.7)
        x1 = int(center_x + base_radius_x * 0.7)
        for rib_y in range(center_y - 80, center_y + 80, rib_spacing):
            y0 = max(0, rib_y - rib_height // 2)
            y1 = min(height, rib_y + rib_height // 2)
            phantom[z_start:z_end, y0:y1, x0:x1] = 2

        self.phantom = phantom
        print(f"[Physics] Phantom created: {np.unique(phantom, return_counts=True)}")
        return phantom
    
    def add_synthetic_pathology(
        self,
        phantom: np.ndarray,
        pathology_type: str = 'nodule',
        severity: float = 1.0,
        return_mask_2d: bool = False,
    ):
        """
        Add synthetic pathology to phantom for detection studies.
        
        Args:
            phantom: The base phantom
            pathology_type: 'nodule', 'fracture', or 'density'
            severity: Pathology intensity (0-1 scale)
            
        Returns:
            Modified phantom with pathology, and optionally 2D lesion mask
        """
        phantom_with_pathology = phantom.copy()
        severity = float(np.clip(severity, 0.0, 1.0))

        # Ensure 3D representation for modification
        phantom_with_pathology, is_2d = self._ensure_3d(phantom_with_pathology)

        depth, height, width = phantom_with_pathology.shape
        lesion_mask_3d = np.zeros_like(phantom_with_pathology, dtype=bool)

        def sample_from_mask(mask: np.ndarray, fallback_xyz: Tuple[int, int, int]) -> Tuple[int, int, int]:
            coords = np.argwhere(mask)
            if coords.shape[0] == 0:
                return fallback_xyz
            idx = self.rng.integers(0, coords.shape[0])
            z, y, x = coords[idx]
            return int(z), int(y), int(x)

        if pathology_type == 'nodule':
            # Add a dense spherical nodule in soft tissue
            zc, yc, xc = sample_from_mask(
                phantom_with_pathology == 1,
                (depth // 2, height // 2, width // 2)
            )
            radius = max(2, int(3 + 8 * severity))
            zz, yy, xx = np.ogrid[:depth, :height, :width]
            mask = (xx - xc) ** 2 + (yy - yc) ** 2 + (zz - zc) ** 2 <= radius ** 2
            lesion_mask_3d = mask & (phantom_with_pathology == 1)
            phantom_with_pathology[lesion_mask_3d] = 3
            
        elif pathology_type == 'fracture':
            # Add a cortical-like crack that spans multiple depth slices to survive projection.
            zc, yc, xc = sample_from_mask(
                phantom_with_pathology == 2,
                (depth // 2, height // 2, width // 2)
            )
            length = max(8, int(14 + 36 * severity))
            width_px = max(1, int(1 + 2 * severity))
            crack_depth = max(6, int(depth * (0.18 + 0.35 * severity)))
            orientation = 'horizontal' if self.rng.random() < 0.5 else 'vertical'

            z0 = max(0, zc - crack_depth // 2)
            z1 = min(depth, zc + crack_depth // 2 + 1)

            if orientation == 'horizontal':
                y0 = max(0, yc - width_px)
                y1 = min(height, yc + width_px + 1)
                x0 = max(0, xc - length // 2)
                x1 = min(width, xc + length // 2 + 1)
            else:
                y0 = max(0, yc - length // 2)
                y1 = min(height, yc + length // 2 + 1)
                x0 = max(0, xc - width_px)
                x1 = min(width, xc + width_px + 1)

            candidate = np.zeros_like(phantom_with_pathology, dtype=bool)
            candidate[z0:z1, y0:y1, x0:x1] = True
            lesion_mask_3d = candidate & (phantom_with_pathology == 2)
            phantom_with_pathology[lesion_mask_3d] = 4
            
        elif pathology_type == 'density':
            # Add localized increased density patch in soft tissue
            zc, yc, xc = sample_from_mask(
                phantom_with_pathology == 1,
                (depth // 2, int(height * 0.6), int(width * 0.6))
            )
            radius = max(3, int(4 + 10 * severity))
            zz, yy, xx = np.ogrid[:depth, :height, :width]
            mask = (xx - xc) ** 2 + (yy - yc) ** 2 + (zz - zc) ** 2 <= radius ** 2
            lesion_mask_3d = mask & (phantom_with_pathology == 1)
            phantom_with_pathology[lesion_mask_3d] = 2

        lesion_mask_2d = np.any(lesion_mask_3d, axis=0)
        self.last_pathology_mask_2d = lesion_mask_2d

        if is_2d:
            phantom_with_pathology = phantom_with_pathology[0]
        
        print(f"[Physics] Added {pathology_type} pathology (severity: {severity:.2f})")
        if return_mask_2d:
            return phantom_with_pathology, lesion_mask_2d
        return phantom_with_pathology

    def simulate_acquisition(self, phantom: np.ndarray, I0: int = None,
                            energy: str = None) -> np.ndarray:
        """
        Simulate X-ray acquisition using Beer-Lambert law.
        I = I₀ * e^(-μx)

        Args:
            phantom: 3D phantom (material type per voxel)
            I0: Initial photon count (dose). If None, use default.
            energy: 'low' (80 kVp) or 'high' (120 kVp)

        Returns:
            2D radiograph (projected intensity)
        """
        if I0 is not None:
            self.I0 = I0
        if energy is not None:
            self.energy = energy

        print(f"[Physics] Simulating acquisition: I₀={self.I0}, Energy={self.energy} kVp")

        # Ensure 3D representation: (depth, height, width)
        phantom_3d, _ = self._ensure_3d(phantom)

        # Build voxel attenuation map
        mu_volume = np.zeros_like(phantom_3d, dtype=np.float64)

        # Get attenuation coefficients for current energy
        attenuation = {}
        for material, coeff in self.ATTENUATION_COEFFICIENTS.items():
            attenuation[material] = coeff[self.energy]

        # Material index to key mapping
        material_map = {0: 'air', 1: 'soft_tissue', 2: 'bone', 3: 'dense', 4: 'fracture'}


        # Apply Beer-Lambert law
        # μx is the integrated attenuation coefficient times path length
        for mat_id, material_name in material_map.items():
            mu = attenuation[material_name]
            mu_volume[phantom_3d == mat_id] = mu

        # Bone voxel = bone material + embedded soft tissue equivalent
        mu_volume[phantom_3d == 2] = attenuation['bone'] + attenuation['soft_tissue']
        mu_volume[phantom_3d == 3] = attenuation['dense'] + attenuation['soft_tissue']
        mu_volume[phantom_3d == 4] = attenuation['fracture'] + attenuation['soft_tissue']

        # Line integral along beam direction (depth axis)
        mu_x = np.sum(mu_volume, axis=0) * self.voxel_size_cm

        # Apply Beer-Lambert: I = I₀ * e^(-μx)
        intensity = self.I0 * np.exp(-mu_x)

        return intensity
    
    def apply_poisson_noise(self, radiograph: np.ndarray) -> np.ndarray:
        """
        Apply Poisson noise simulating quantum mottle.
        Noise level depends on photon count.
        
        Args:
            radiograph: Intensity map
            
        Returns:
            Noisy radiograph
        """
        print(f"[Physics] Applying Poisson noise (dose-dependent)...")
        
        # Convert intensity to photon counts for Poisson sampling
        # Higher dose = lower noise
        photon_map = np.clip(radiograph, 0, None)
        noisy = self.rng.poisson(photon_map).astype(np.float64)
        
        return noisy

    def compute_rose_detectability(
        self,
        pathology_noisy: np.ndarray,
        lesion_mask_2d: np.ndarray,
        I0: float,
        baseline_ideal: Optional[np.ndarray] = None,
        pathology_ideal: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """
        Compute a practical Rose-style detectability metric in optical-density domain.

        This implementation intentionally models a less-than-ideal human observer:
        - Works in OD domain (log-transformed transmission).
        - Includes local anatomical clutter and small internal observer noise.
        - Uses suboptimal area integration (A^0.25) rather than ideal sqrt(A).
        """
        eps = 1e-6
        lesion_mask = lesion_mask_2d.astype(bool)
        area = int(np.count_nonzero(lesion_mask))
        if area == 0:
            od = -np.log(np.clip(pathology_noisy / (I0 + eps), eps, 1.0))
            return {
                'delta_signal': 0.0,
                'noise_sigma': float(np.std(od)),
                'lesion_area': 0.0,
                'rose_dprime': 0.0,
            }

        # Ring neighborhood around lesion for local background/noise estimate
        ring_outer = ndimage.binary_dilation(lesion_mask, iterations=5)
        ring_inner = ndimage.binary_dilation(lesion_mask, iterations=2)
        ring_mask = ring_outer & (~ring_inner)
        if np.count_nonzero(ring_mask) < 20:
            ring_mask = ~lesion_mask

        # Convert to optical density to suppress pure intensity scaling with dose.
        transmission = np.clip(pathology_noisy / (I0 + eps), eps, 1.0)
        od = -np.log(transmission)

        # Signal term: prefer ideal contrast when available to avoid single-noise-sample bias.
        if baseline_ideal is not None and pathology_ideal is not None:
            base_t = np.clip(baseline_ideal / (I0 + eps), eps, 1.0)
            path_t = np.clip(pathology_ideal / (I0 + eps), eps, 1.0)
            base_od = -np.log(base_t)
            path_od = -np.log(path_t)
            ideal_diff = path_od - base_od
            delta_signal = float(np.mean(np.abs(ideal_diff[lesion_mask])))
        else:
            lesion_mean = float(np.mean(od[lesion_mask]))
            ring_mean = float(np.mean(od[ring_mask]))
            delta_signal = float(abs(lesion_mean - ring_mean))

        # Local quantum noise in OD domain.
        quantum_sigma = float(np.std(od[ring_mask]))

        # Anatomical clutter estimate from low-frequency OD variation.
        od_smooth = ndimage.gaussian_filter(od, sigma=2.0)
        clutter_sigma = float(np.std(od_smooth[ring_mask]))

        # Internal observer noise and non-ideal integration efficiency.
        internal_sigma = 0.01
        total_sigma = float(np.sqrt(quantum_sigma**2 + (0.6 * clutter_sigma)**2 + internal_sigma**2))
        area_gain = float(max(1.0, area) ** 0.25)
        observer_efficiency = 0.85

        rose_dprime = float(observer_efficiency * (delta_signal / (total_sigma + eps)) * area_gain)

        return {
            'delta_signal': delta_signal,
            'noise_sigma': total_sigma,
            'lesion_area': float(area),
            'rose_dprime': rose_dprime,
        }

    def get_projected_material_masks(self, phantom: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Return 2D projected material masks for ROI-based metrics.
        """
        if phantom.ndim == 2:
            phantom_3d = phantom[np.newaxis, ...]
        else:
            phantom_3d = phantom

        return {
            'air': np.any(phantom_3d == 0, axis=0),
            'soft_tissue': np.any(phantom_3d == 1, axis=0),
            'bone': np.any(phantom_3d == 2, axis=0),
            'dense': np.any(phantom_3d == 3, axis=0),
        }

    @staticmethod
    def _center_crop_or_pad(image: np.ndarray, out_shape: Tuple[int, int]) -> np.ndarray:
        """
        Center crop or zero-pad an image to match out_shape.
        """
        target_h, target_w = out_shape
        in_h, in_w = image.shape

        # Crop
        if in_h > target_h:
            start_h = (in_h - target_h) // 2
            image = image[start_h:start_h + target_h, :]
            in_h = target_h
        if in_w > target_w:
            start_w = (in_w - target_w) // 2
            image = image[:, start_w:start_w + target_w]
            in_w = target_w

        # Pad
        if in_h < target_h or in_w < target_w:
            pad_top = (target_h - in_h) // 2
            pad_bottom = target_h - in_h - pad_top
            pad_left = (target_w - in_w) // 2
            pad_right = target_w - in_w - pad_left
            image = np.pad(image, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='constant')

        return image
    

    def apply_geometric_effects(self, radiograph: np.ndarray,
                                SID: float = 100.0,
                                ODD: float = 0.0,
                                focal_spot_size: float = 0.06,
                                apply_magnification: bool = True,
                                apply_penumbra: bool = True) -> np.ndarray:
        """
        Apply geometric effects based on physical X-ray geometry.
        
        Physical setup:
            Source --> [Object] --> [Detector]
            |----SOD----|----ODD----|
            |----------SID---------|
        
        SID is constant (set by user).
        ODD is variable (set by user).
        SOD is automatically calculated as SID - ODD.
    
        Args:
            radiograph          : Input radiograph (2D numpy array)
            SID                 : Source-to-Image Distance in cm (constant, default 100 cm)
            ODD                 : Object-to-Detector Distance in cm (variable, default 0 = no effect)
            focal_spot_size     : Focal spot size in cm (default 0.06 cm = 0.6 mm)
            apply_magnification : Toggle magnification effect ON/OFF
            apply_penumbra      : Toggle penumbra effect ON/OFF
            
        Returns:
            Radiograph with selected geometric effects applied
        """
        result = radiograph.copy()
    
        # ── Step 1: Calculate SOD from SID and ODD ────────────
        # SID is constant, ODD is variable, SOD is calculated
        SOD = SID - ODD
    
        # Safety check
        if SOD <= 0:
            print(f"[Physics] ERROR: SOD must be > 0 (SID={SID}, ODD={ODD})")
            return result
    
        # ── Step 2: Derive Magnification ──────────────────────
        # M = SID / SOD
        magnification = SID / SOD
    
        # ── Step 3: Derive Penumbra from ODD and focal spot ───
        # Penumbra (cm) = focal_spot_size × (ODD / SOD)
        penumbra_cm     = focal_spot_size * (ODD / SOD)
        pixels_per_cm   = 1.0 / self.voxel_size_cm
        penumbra_pixels = penumbra_cm * pixels_per_cm
    
        print(f"[Physics] Geometric Effects:")
        print(f"  SID={SID} cm  (constant)")
        print(f"  ODD={ODD} cm  (variable)")
        print(f"  SOD = SID - ODD = {SID} - {ODD} = {SOD:.1f} cm  (calculated)")
        print(f"  Magnification = SID/SOD = {magnification:.3f}x  → {'ON' if apply_magnification else 'OFF'}")
        print(f"  Penumbra = {penumbra_cm:.4f} cm ({penumbra_pixels:.2f} px)  → {'ON' if apply_penumbra else 'OFF'}")
    
        # ── Step 4: Apply Magnification (if ON) ───────────────
        if apply_magnification and magnification > 1.0:
            print(f"[Physics] Applying magnification: {magnification:.3f}x")
            from scipy.ndimage import zoom
            result = zoom(result, magnification, order=3)  # order=3 = bicubic (more realistic)
            h, w = radiograph.shape
            result = self._center_crop_or_pad(result, (h, w))
        else:
            print(f"[Physics] Magnification skipped (OFF or ODD=0)")
    
        # ── Step 5: Apply Penumbra (if ON) ────────────────────
        if apply_penumbra and penumbra_pixels > 0:
            print(f"[Physics] Applying penumbra blur: {penumbra_pixels:.2f} px")
            sigma = penumbra_pixels / 2.355  # Convert FWHM to sigma
            result = ndimage.gaussian_filter(result, sigma=sigma)
        else:
            print(f"[Physics] Penumbra skipped (OFF or ODD=0)")
    
        return result
    
    def dual_energy_subtraction(self, phantom: np.ndarray, I0_low: int, I0_high: int,
                               tissue_target: str = 'soft_tissue') -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Simulate Dual-Energy X-ray acquisition and subtraction.
        Acquires images at low (80 kVp) and high (120 kVp) energies,
        then performs weighted subtraction to isolate specific tissue.
        
        Args:
            phantom: Digital phantom
            I0_low: Photons for low-energy (80 kVp)
            I0_high: Photons for high-energy (120 kVp)
            tissue_target: 'soft_tissue' or 'bone'
            
        Returns:
            Tuple of (image_low_energy, image_high_energy, subtracted_image)
        """
        print("[Physics] Performing Dual-Energy acquisition...")
        
        # Acquire at low energy
        img_low = self.simulate_acquisition(phantom, I0_low, energy='low')
        img_low_noisy = self.apply_poisson_noise(img_low)
        
        # Acquire at high energy
        img_high = self.simulate_acquisition(phantom, I0_high, energy='high')
        img_high_noisy = self.apply_poisson_noise(img_high)
        

        # ... (بعد الحصول على img_low_noisy و img_high_noisy) ...

        eps = 1e-6
        s_low = -np.log((img_low_noisy + eps) / I0_low)
        s_high = -np.log((img_high_noisy + eps) / I0_high)

        if tissue_target == 'soft_tissue':
            mu_low_bone = self.ATTENUATION_COEFFICIENTS['bone']['low']
            mu_high_bone = self.ATTENUATION_COEFFICIENTS['bone']['high']

            weight = mu_high_bone / mu_low_bone
            subtracted = s_high - (weight * s_low)
            self.last_dual_weights = (weight, 1.0)


        else:
            mu_low_tissue = self.ATTENUATION_COEFFICIENTS['soft_tissue']['low']
            mu_high_tissue = self.ATTENUATION_COEFFICIENTS['soft_tissue']['high']

            weight = mu_low_tissue / mu_high_tissue

            subtracted = s_low - (weight * s_high)
            self.last_dual_weights = (1.0, weight)

        # منع القيم السالبة كما فعلت في كودك السابق
        subtracted = np.clip(subtracted, 0, None)




        return img_low_noisy, img_high_noisy, subtracted
