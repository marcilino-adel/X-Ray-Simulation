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
    }
    
    def __init__(self, seed: Optional[int] = None):
        self.phantom = None
        self.I0 = 10000  # Initial photon count (dose)
        self.energy = 'high'  # 'low' (80 kVp) or 'high' (120 kVp)
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.voxel_size_cm = 0.1  # 1 mm voxel thickness equivalent
        self.last_dual_weights = (1.0, 1.0)
        
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
        z_start = int(depth * 0.25)
        z_end = int(depth * 0.75)
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
    
    def add_synthetic_pathology(self, phantom: np.ndarray, pathology_type: str = 'nodule', 
                               severity: float = 1.0) -> np.ndarray:
        """
        Add synthetic pathology to phantom for detection studies.
        
        Args:
            phantom: The base phantom
            pathology_type: 'nodule', 'fracture', or 'density'
            severity: Pathology intensity (0-1 scale)
            
        Returns:
            Modified phantom with pathology
        """
        phantom_with_pathology = phantom.copy()
        severity = float(np.clip(severity, 0.0, 1.0))

        # Ensure 3D representation for modification
        is_2d = phantom_with_pathology.ndim == 2
        if is_2d:
            phantom_with_pathology = phantom_with_pathology[np.newaxis, ...]

        depth, height, width = phantom_with_pathology.shape

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
            phantom_with_pathology[mask & (phantom_with_pathology == 1)] = 3
            
        elif pathology_type == 'fracture':
            # Add a micro-fracture in bone as a thin low-density streak
            zc, yc, xc = sample_from_mask(
                phantom_with_pathology == 2,
                (depth // 2, height // 2, width // 2)
            )
            length = max(4, int(8 + 20 * severity))
            thickness = max(1, int(1 + 2 * severity))
            y0 = max(0, yc - length // 2)
            y1 = min(height, yc + length // 2)
            z0 = max(0, zc - thickness)
            z1 = min(depth, zc + thickness + 1)
            x0 = max(0, xc - thickness)
            x1 = min(width, xc + thickness + 1)
            bone_region = phantom_with_pathology[z0:z1, y0:y1, x0:x1] == 2
            phantom_with_pathology[z0:z1, y0:y1, x0:x1][bone_region] = 1
            
        elif pathology_type == 'density':
            # Add localized increased density patch in soft tissue
            zc, yc, xc = sample_from_mask(
                phantom_with_pathology == 1,
                (depth // 2, int(height * 0.6), int(width * 0.6))
            )
            radius = max(3, int(4 + 10 * severity))
            zz, yy, xx = np.ogrid[:depth, :height, :width]
            mask = (xx - xc) ** 2 + (yy - yc) ** 2 + (zz - zc) ** 2 <= radius ** 2
            phantom_with_pathology[mask & (phantom_with_pathology == 1)] = 2

        if is_2d:
            phantom_with_pathology = phantom_with_pathology[0]
        
        print(f"[Physics] Added {pathology_type} pathology (severity: {severity:.2f})")
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
        if phantom.ndim == 2:
            phantom_3d = phantom[np.newaxis, ...]
        elif phantom.ndim == 3:
            phantom_3d = phantom
        else:
            raise ValueError("Phantom must be 2D or 3D")

        # Build voxel attenuation map
        mu_volume = np.zeros_like(phantom_3d, dtype=np.float64)
        
        # Get attenuation coefficients for current energy
        attenuation = {}
        for material, coeff in self.ATTENUATION_COEFFICIENTS.items():
            attenuation[material] = coeff[self.energy]
        
        # Material index to key mapping
        material_map = {0: 'air', 1: 'soft_tissue', 2: 'bone', 3: 'dense'}
        
        # Apply Beer-Lambert law
        # μx is the integrated attenuation coefficient times path length
        for mat_id, material_name in material_map.items():
            mu = attenuation[material_name]
            mu_volume[phantom_3d == mat_id] = mu

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
                               magnification: float = 1.0,
                               penumbra: float = 0.0) -> np.ndarray:
        """
        Apply geometric effects:
        - Magnification: Object-to-Detector Distance (ODD)
        - Penumbra (edge unsharpness): focal spot size effect
        
        Args:
            radiograph: Input radiograph
            magnification: Linear magnification factor (1.0 = no magnification)
            penumbra: Penumbra blur radius (pixels)
            
        Returns:
            Radiograph with geometric effects applied
        """
        result = radiograph.copy()
        
        # Apply magnification with centered crop/pad
        if magnification != 1.0:
            print(f"[Physics] Applying magnification: {magnification:.2f}x")
            from scipy.ndimage import zoom
            result = zoom(result, magnification, order=1)
            h, w = radiograph.shape
            result = self._center_crop_or_pad(result, (h, w))
        
        # Apply penumbra (focal spot blurring)
        if penumbra > 0:
            print(f"[Physics] Applying penumbra: {penumbra:.2f}px")
            sigma = penumbra / 2.355  # Convert FWHM to sigma
            result = ndimage.gaussian_filter(result, sigma=sigma)
        
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
        
        masks = self.get_projected_material_masks(phantom)

        # Calibrate subtraction weights from suppression ROI
        eps = 1e-6
        if tissue_target == 'soft_tissue':
            suppress_mask = masks['bone']
            k = float(np.mean(img_low_noisy[suppress_mask]) / (np.mean(img_high_noisy[suppress_mask]) + eps))
            weight_low, weight_high = 1.0, k
            subtracted = (weight_low * img_low_noisy) - (weight_high * img_high_noisy)
        else:
            suppress_mask = masks['soft_tissue']
            k = float(np.mean(img_high_noisy[suppress_mask]) / (np.mean(img_low_noisy[suppress_mask]) + eps))
            weight_low, weight_high = k, 1.0
            subtracted = (weight_high * img_high_noisy) - (weight_low * img_low_noisy)

        self.last_dual_weights = (weight_low, weight_high)
        
        print(f"[Physics] Dual-Energy subtraction complete (target: {tissue_target})")
        
        return img_low_noisy, img_high_noisy, subtracted
