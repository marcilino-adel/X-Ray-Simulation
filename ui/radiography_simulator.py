"""
Main Radiography Simulator Window
PyQt5 GUI for Beer-Lambert X-ray simulator
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QLabel, QSlider, QSpinBox, QPushButton,
                            QGroupBox, QGridLayout, QComboBox, QCheckBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from physics.beer_lambert import BeerLambertSimulator


class RadiographySimulator(QMainWindow):
    """Main window for Beer-Lambert X-ray radiography simulator"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beer-Lambert X-Ray Radiography Simulator")
        self.setGeometry(100, 100, 1400, 900)
        
        # Physics engine
        self.physics = BeerLambertSimulator()
        self.phantom = None
        self.current_radiograph = None
        
        # Create UI
        self.init_ui()
        self.create_phantom()
        
    def init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel: Controls
        left_panel = QVBoxLayout()
        
        # Tabs for different simulation modes
        self.tabs = QTabWidget()
        
        # Tab 1: Basic Acquisition
        self.tabs.addTab(self.create_basic_tab(), "Basic Acquisition")
        
        # Tab 2: Dose-Noise Analysis
        self.tabs.addTab(self.create_dose_noise_tab(), "Dose-Noise Analysis")
        
        # Tab 3: Geometric Effects
        self.tabs.addTab(self.create_geometric_tab(), "Geometric Effects")
        
        # Tab 4: Dual-Energy
        self.tabs.addTab(self.create_dualenergy_tab(), "Dual-Energy")
        
        # Tab 5: Pathology Detection
        self.tabs.addTab(self.create_pathology_tab(), "Pathology Detection")
        
        left_panel.addWidget(self.tabs)
        main_layout.addLayout(left_panel, 1)
        
        # Right panel: Image Display
        right_panel = self.create_display_panel()
        main_layout.addLayout(right_panel, 2)
        
    def create_basic_tab(self) -> QWidget:
        """Create Basic Acquisition tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Dose control
        dose_group = QGroupBox("Dose Control (I₀)")
        dose_layout = QGridLayout()
        
        dose_label = QLabel("Photon Count:")
        self.dose_spinbox = QSpinBox()
        self.dose_spinbox.setRange(100, 50000)
        self.dose_spinbox.setValue(10000)
        self.dose_spinbox.setSingleStep(1000)
        dose_layout.addWidget(dose_label, 0, 0)
        dose_layout.addWidget(self.dose_spinbox, 0, 1)
        
        dose_group.setLayout(dose_layout)
        layout.addWidget(dose_group)
        
        # Energy selection
        energy_group = QGroupBox("X-Ray Energy Spectrum")
        energy_layout = QGridLayout()
        
        energy_label = QLabel("Energy (kVp):")
        self.energy_combo = QComboBox()
        self.energy_combo.addItems(["Low (80 kVp)", "High (120 kVp)"])
        energy_layout.addWidget(energy_label, 0, 0)
        energy_layout.addWidget(self.energy_combo, 0, 1)
        
        energy_group.setLayout(energy_layout)
        layout.addWidget(energy_group)
        
        # Noise checkbox
        self.noise_checkbox = QCheckBox("Apply Poisson Noise (Quantum Mottle)")
        self.noise_checkbox.setChecked(True)
        layout.addWidget(self.noise_checkbox)

        # Display mode
        self.show_phantom_checkbox = QCheckBox("Show Phantom Materials beside Radiograph")
        self.show_phantom_checkbox.setChecked(True)
        layout.addWidget(self.show_phantom_checkbox)
        
        # Simulate button
        simulate_btn = QPushButton("Simulate Acquisition")
        simulate_btn.clicked.connect(self.simulate_basic)
        layout.addWidget(simulate_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_dose_noise_tab(self) -> QWidget:
        """Create Dose-Noise Analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Dose range
        dose_range_group = QGroupBox("Dose Range Study")
        dose_range_layout = QGridLayout()
        
        dose_min_label = QLabel("Min Dose (I₀):")
        self.dose_min_spinbox = QSpinBox()
        self.dose_min_spinbox.setRange(10, 10000)
        self.dose_min_spinbox.setValue(500)
        dose_range_layout.addWidget(dose_min_label, 0, 0)
        dose_range_layout.addWidget(self.dose_min_spinbox, 0, 1)
        
        dose_max_label = QLabel("Max Dose (I₀):")
        self.dose_max_spinbox = QSpinBox()
        self.dose_max_spinbox.setRange(1000, 50000)
        self.dose_max_spinbox.setValue(20000)
        dose_range_layout.addWidget(dose_max_label, 1, 0)
        dose_range_layout.addWidget(self.dose_max_spinbox, 1, 1)
        
        dose_range_group.setLayout(dose_range_layout)
        layout.addWidget(dose_range_group)
        
        # Number of steps
        steps_label = QLabel("Number of Comparisons:")
        self.steps_spinbox = QSpinBox()
        self.steps_spinbox.setRange(2, 10)
        self.steps_spinbox.setValue(5)
        layout.addWidget(steps_label)
        layout.addWidget(self.steps_spinbox)

        repeats_label = QLabel("Noise Realizations per Dose:")
        self.repeats_spinbox = QSpinBox()
        self.repeats_spinbox.setRange(1, 20)
        self.repeats_spinbox.setValue(3)
        layout.addWidget(repeats_label)
        layout.addWidget(self.repeats_spinbox)
        
        # Analyze button
        analyze_btn = QPushButton("Analyze Dose-Noise Trade-off")
        analyze_btn.clicked.connect(self.analyze_dose_noise)
        layout.addWidget(analyze_btn)
        
        # SNR calculation
        snr_label = QLabel("SNR Analysis:")
        self.snr_label = QLabel("Ready for analysis")
        layout.addWidget(snr_label)
        layout.addWidget(self.snr_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_geometric_tab(self) -> QWidget:
        """Create Geometric Effects tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Magnification
        mag_group = QGroupBox("Magnification (Object-to-Detector Distance)")
        mag_layout = QGridLayout()
        
        mag_label = QLabel("Magnification Factor:")
        self.mag_slider = QSlider(Qt.Horizontal)
        self.mag_slider.setRange(100, 300)  # 1.0x to 3.0x
        self.mag_slider.setValue(100)
        self.mag_value_label = QLabel("1.0x")
        self.mag_slider.valueChanged.connect(
            lambda: self.mag_value_label.setText(f"{self.mag_slider.value()/100:.2f}x")
        )
        mag_layout.addWidget(mag_label, 0, 0)
        mag_layout.addWidget(self.mag_slider, 0, 1)
        mag_layout.addWidget(self.mag_value_label, 0, 2)
        
        mag_group.setLayout(mag_layout)
        layout.addWidget(mag_group)
        
        # Penumbra (edge unsharpness)
        penumbra_group = QGroupBox("Penumbra (Focal Spot Effect)")
        penumbra_layout = QGridLayout()
        
        penumbra_label = QLabel("Blur Radius (pixels):")
        self.penumbra_slider = QSlider(Qt.Horizontal)
        self.penumbra_slider.setRange(0, 100)  # 0 to 10 pixels
        self.penumbra_slider.setValue(0)
        self.penumbra_value_label = QLabel("0.0px")
        self.penumbra_slider.valueChanged.connect(
            lambda: self.penumbra_value_label.setText(f"{self.penumbra_slider.value()/10:.1f}px")
        )
        penumbra_layout.addWidget(penumbra_label, 0, 0)
        penumbra_layout.addWidget(self.penumbra_slider, 0, 1)
        penumbra_layout.addWidget(self.penumbra_value_label, 0, 2)
        
        penumbra_group.setLayout(penumbra_layout)
        layout.addWidget(penumbra_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Geometric Effects")
        apply_btn.clicked.connect(self.apply_geometric_effects)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_dualenergy_tab(self) -> QWidget:
        """Create Dual-Energy Subtraction tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Dose for each energy
        dose_group = QGroupBox("Dual-Energy Acquisition")
        dose_layout = QGridLayout()
        
        dose_low_label = QLabel("Low Energy (80 kVp) Dose:")
        self.dose_low_spinbox = QSpinBox()
        self.dose_low_spinbox.setRange(100, 50000)
        self.dose_low_spinbox.setValue(8000)
        dose_layout.addWidget(dose_low_label, 0, 0)
        dose_layout.addWidget(self.dose_low_spinbox, 0, 1)
        
        dose_high_label = QLabel("High Energy (120 kVp) Dose:")
        self.dose_high_spinbox = QSpinBox()
        self.dose_high_spinbox.setRange(100, 50000)
        self.dose_high_spinbox.setValue(8000)
        dose_layout.addWidget(dose_high_label, 1, 0)
        dose_layout.addWidget(self.dose_high_spinbox, 1, 1)
        
        dose_group.setLayout(dose_layout)
        layout.addWidget(dose_group)
        
        # Tissue target
        tissue_label = QLabel("Tissue Target for Isolation:")
        self.tissue_combo = QComboBox()
        self.tissue_combo.addItems(["Soft Tissue", "Bone"])
        layout.addWidget(tissue_label)
        layout.addWidget(self.tissue_combo)
        
        # Perform subtraction
        deacq_btn = QPushButton("Perform Dual-Energy Subtraction")
        deacq_btn.clicked.connect(self.perform_dual_energy)
        layout.addWidget(deacq_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_pathology_tab(self) -> QWidget:
        """Create Pathology Detection tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Pathology type
        pathology_group = QGroupBox("Synthetic Pathology Generation")
        pathology_layout = QGridLayout()
        
        type_label = QLabel("Pathology Type:")
        self.pathology_combo = QComboBox()
        self.pathology_combo.addItems(["Nodule", "Fracture", "Density"])
        pathology_layout.addWidget(type_label, 0, 0)
        pathology_layout.addWidget(self.pathology_combo, 0, 1)
        
        severity_label = QLabel("Severity (0-1):")
        self.severity_slider = QSlider(Qt.Horizontal)
        self.severity_slider.setRange(0, 100)
        self.severity_slider.setValue(50)
        self.severity_value_label = QLabel("0.5")
        self.severity_slider.valueChanged.connect(
            lambda: self.severity_value_label.setText(f"{self.severity_slider.value()/100:.2f}")
        )
        pathology_layout.addWidget(severity_label, 1, 0)
        pathology_layout.addWidget(self.severity_slider, 1, 1)
        pathology_layout.addWidget(self.severity_value_label, 1, 2)
        
        pathology_group.setLayout(pathology_layout)
        layout.addWidget(pathology_group)
        
        # Dose threshold study
        threshold_label = QLabel("Detection Threshold:")
        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setRange(100, 50000)
        self.threshold_spinbox.setValue(5000)
        layout.addWidget(threshold_label)
        layout.addWidget(self.threshold_spinbox)
        
        # Analyze button
        analyze_btn = QPushButton("Analyze Pathology Detection")
        analyze_btn.clicked.connect(self.analyze_pathology)
        layout.addWidget(analyze_btn)

        self.pathology_outline_checkbox = QCheckBox("Show lesion outline")
        self.pathology_outline_checkbox.setChecked(False)
        layout.addWidget(self.pathology_outline_checkbox)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_display_panel(self) -> QVBoxLayout:
        """Create image display panel"""
        layout = QVBoxLayout()
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        return layout
    
    def create_phantom(self):
        """Create initial phantom"""
        self.physics.create_digital_phantom(256, 256)
        self.phantom = self.physics.phantom
        print("[UI] Phantom created")

    @staticmethod
    def _to_bone_white_display(radiograph: np.ndarray) -> np.ndarray:
        """Map transmission image to display where bone is white and air is dark."""
        radiograph_norm = (radiograph - radiograph.min()) / (radiograph.max() - radiograph.min() + 1e-6)
        return 1.0 - radiograph_norm
    
    def simulate_basic(self):
        """Simulate basic acquisition"""
        try:
            dose = self.dose_spinbox.value()
            energy = 'low' if 'Low' in self.energy_combo.currentText() else 'high'
            apply_noise = self.noise_checkbox.isChecked()
            
            # Simulate
            radiograph = self.physics.simulate_acquisition(self.phantom, dose, energy)
            
            if apply_noise:
                radiograph = self.physics.apply_poisson_noise(radiograph)
            
            self.current_radiograph = radiograph
            if self.show_phantom_checkbox.isChecked():
                self.display_phantom_and_radiograph(radiograph, f"Radiograph (I₀={dose}, {energy})")
            else:
                self.display_radiograph(radiograph, f"Radiograph (I₀={dose}, {energy})")
            self.status_label.setText(f"✓ Simulation complete: I₀={dose}, Energy={energy}, Noise={apply_noise}")
            
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            print(f"[ERROR] {e}")
    
    def analyze_dose_noise(self):
        """Analyze dose-noise trade-off"""
        try:
            min_dose = self.dose_min_spinbox.value()
            max_dose = self.dose_max_spinbox.value()
            steps = self.steps_spinbox.value()
            repeats = self.repeats_spinbox.value()

            if min_dose >= max_dose:
                self.status_label.setText("✗ Min dose must be less than max dose")
                return
            
            doses = np.linspace(min_dose, max_dose, steps, dtype=int)
            snr_means = []
            snr_stds = []
            cnr_means = []

            masks = self.physics.get_projected_material_masks(self.phantom)
            signal_mask = masks['soft_tissue'] & ~masks['bone']
            noise_mask = masks['air'] & ~masks['soft_tissue']

            # Fallback masks if anatomy overlap removes too many pixels
            if np.count_nonzero(signal_mask) < 50:
                signal_mask = masks['soft_tissue']
            if np.count_nonzero(noise_mask) < 50:
                noise_mask = masks['air']
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            for dose in doses:
                snr_rep = []
                cnr_rep = []

                for _ in range(repeats):
                    radiograph = self.physics.simulate_acquisition(self.phantom, dose, 'high')
                    radiograph = self.physics.apply_poisson_noise(radiograph)

                    signal_values = radiograph[signal_mask]
                    noise_values = radiograph[noise_mask]

                    mean_signal = float(np.mean(signal_values))
                    std_signal = float(np.std(signal_values))
                    mean_noise = float(np.mean(noise_values))
                    std_noise = float(np.std(noise_values))

                    snr = mean_signal / (std_signal + 1e-6)
                    cnr = abs(mean_signal - mean_noise) / (std_noise + 1e-6)
                    snr_rep.append(snr)
                    cnr_rep.append(cnr)

                snr_means.append(float(np.mean(snr_rep)))
                snr_stds.append(float(np.std(snr_rep)))
                cnr_means.append(float(np.mean(cnr_rep)))
            
            # Plot
            ax.errorbar(
                doses,
                snr_means,
                yerr=snr_stds,
                fmt='o-',
                linewidth=2,
                markersize=6,
                capsize=3,
                label='ROI SNR (mean ± std)'
            )
            ax.plot(doses, cnr_means, 's--', linewidth=2, markersize=5, label='ROI CNR')
            ax.set_xlabel('Dose (I₀)')
            ax.set_ylabel('Quality Metric')
            ax.set_title('Dose-Noise Trade-off (ROI-based SNR/CNR)')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            self.canvas.draw()
            
            snr_text = (
                f"SNR: {min(snr_means):.2f}→{max(snr_means):.2f} | "
                f"CNR: {min(cnr_means):.2f}→{max(cnr_means):.2f}"
            )
            self.snr_label.setText(snr_text)
            self.status_label.setText(f"✓ Dose-noise analysis complete ({repeats} realizations/dose)")
            
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            print(f"[ERROR] {e}")
    
    def apply_geometric_effects(self):
        """Apply geometric effects to current radiograph"""
        try:
            if self.current_radiograph is None:
                self.status_label.setText("✗ No radiograph loaded. Simulate first.")
                return
            
            mag = self.mag_slider.value() / 100.0
            penumbra = self.penumbra_slider.value() / 10.0
            
            radiograph = self.physics.apply_geometric_effects(
                self.current_radiograph, mag, penumbra
            )
            
            self.current_radiograph = radiograph
            self.display_radiograph(radiograph, f"Radiograph (Mag={mag:.2f}x, Penumbra={penumbra:.1f}px)")
            self.status_label.setText(f"✓ Geometric effects applied")
            
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            print(f"[ERROR] {e}")
    
    def perform_dual_energy(self):
        """Perform dual-energy subtraction"""
        try:
            dose_low = self.dose_low_spinbox.value()
            dose_high = self.dose_high_spinbox.value()
            tissue = 'soft_tissue' if 'Soft' in self.tissue_combo.currentText() else 'bone'
            
            img_low, img_high, subtracted = self.physics.dual_energy_subtraction(
                self.phantom, dose_low, dose_high, tissue
            )
            
            # Display all three
            self.figure.clear()
            
            ax1 = self.figure.add_subplot(131)
            im1 = ax1.imshow(self._to_bone_white_display(img_low), cmap='gray', vmin=0, vmax=1)
            ax1.set_title(f'Low Energy (80 kVp)\nI₀={dose_low}')
            ax1.axis('off')
            
            ax2 = self.figure.add_subplot(132)
            im2 = ax2.imshow(self._to_bone_white_display(img_high), cmap='gray', vmin=0, vmax=1)
            ax2.set_title(f'High Energy (120 kVp)\nI₀={dose_high}')
            ax2.axis('off')
            
            ax3 = self.figure.add_subplot(133)
            im3 = ax3.imshow(subtracted, cmap='seismic')
            ax3.set_title(f'Subtracted\n(Target: {tissue})')
            ax3.axis('off')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            w_low, w_high = self.physics.last_dual_weights
            self.status_label.setText(
                f"✓ Dual-Energy subtraction complete (w_low={w_low:.3f}, w_high={w_high:.3f})"
            )
            
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            print(f"[ERROR] {e}")
    
    def analyze_pathology(self):
        """Analyze pathology detection"""
        try:
            pathology_type = self.pathology_combo.currentText().lower()
            severity = self.severity_slider.value() / 100.0
            threshold_dose = self.threshold_spinbox.value()
            
            # Create phantom with pathology and projected lesion mask
            phantom_with_path, lesion_mask_2d = self.physics.add_synthetic_pathology(
                self.phantom, pathology_type, severity, return_mask_2d=True
            )
            
            # Simulate different doses
            doses = np.array([threshold_dose // 2, threshold_dose, threshold_dose * 2])
            pathology_radiographs = []
            od_radiographs = []
            rose_values = []
            rose_stds = []
            repeats = 10
            
            for dose in doses:
                baseline_ideal = self.physics.simulate_acquisition(self.phantom, dose)
                pathology_ideal = self.physics.simulate_acquisition(phantom_with_path, dose)
                dprime_rep = []
                selected_noisy = None
                selected_od = None

                for rep in range(repeats):
                    pathology_noisy = self.physics.apply_poisson_noise(pathology_ideal)
                    transmission = np.clip(pathology_noisy / (dose + 1e-6), 1e-6, 1.0)
                    pathology_od = -np.log(transmission)

                    rose = self.physics.compute_rose_detectability(
                        pathology_noisy,
                        lesion_mask_2d,
                        I0=float(dose),
                        baseline_ideal=baseline_ideal,
                        pathology_ideal=pathology_ideal,
                    )
                    dprime_rep.append(rose['rose_dprime'])

                    if rep == 0:
                        selected_noisy = pathology_noisy
                        selected_od = pathology_od

                pathology_radiographs.append(selected_noisy)
                od_radiographs.append(selected_od)
                rose_values.append(float(np.mean(dprime_rep)))
                rose_stds.append(float(np.std(dprime_rep)))
            
            # Display comparison: top row = OD images (dose-normalized), bottom row = ideal contrast map
            self.figure.clear()

            if od_radiographs:
                od_min = float(min(np.percentile(img, 1) for img in od_radiographs))
                od_max = float(max(np.percentile(img, 99) for img in od_radiographs))
            else:
                od_min, od_max = 0.0, 1.0

            for i, (rad_od, dose, dprime, dstd) in enumerate(zip(od_radiographs, doses, rose_values, rose_stds)):
                ax = self.figure.add_subplot(2, 3, i + 1)
                od_norm = (rad_od - od_min) / (od_max - od_min + 1e-6)
                ax.imshow(od_norm, cmap='gray', vmin=0, vmax=1)
                if self.pathology_outline_checkbox.isChecked() and np.count_nonzero(lesion_mask_2d) > 0:
                    ax.contour(lesion_mask_2d.astype(float), levels=[0.5], colors='red', linewidths=0.6)
                ax.set_title(f'Dose={dose}\nd\'={dprime:.2f}±{dstd:.2f}')
                ax.axis('off')

                # Contrast map relative to baseline at same dose
                baseline_ideal = self.physics.simulate_acquisition(self.phantom, dose)
                pathology_ideal = self.physics.simulate_acquisition(phantom_with_path, dose)
                diff = pathology_ideal - baseline_ideal

                ax_diff = self.figure.add_subplot(2, 3, i + 4)
                vmax = np.max(np.abs(diff)) + 1e-6
                ax_diff.imshow(diff, cmap='seismic', vmin=-vmax, vmax=vmax)
                if self.pathology_outline_checkbox.isChecked() and np.count_nonzero(lesion_mask_2d) > 0:
                    ax_diff.contour(lesion_mask_2d.astype(float), levels=[0.5], colors='black', linewidths=0.5)
                ax_diff.set_title('Ideal contrast map')
                ax_diff.axis('off')
            
            self.figure.tight_layout()
            self.canvas.draw()

            max_dprime = max(rose_values) if rose_values else 0.0
            rose_state = "detectable" if max_dprime >= 5.0 else "sub-threshold"
            self.status_label.setText(
                f"✓ Pathology analysis complete ({pathology_type}, severity={severity:.2f}) | max d'={max_dprime:.2f} ({rose_state}), averaged over {repeats} realizations"
            )
            
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            print(f"[ERROR] {e}")
    
    def display_radiograph(self, radiograph: np.ndarray, title: str):
        """Display a single radiograph"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        display = self._to_bone_white_display(radiograph)
        im = ax.imshow(display, cmap='gray', vmin=0, vmax=1)
        ax.set_title(title)
        ax.axis('off')
        self.figure.colorbar(im, ax=ax, label='Radiographic opacity (bone-white)')
        self.figure.tight_layout()
        self.canvas.draw()

    def display_phantom_and_radiograph(self, radiograph: np.ndarray, title: str):
        """Display projected phantom materials and radiograph side-by-side."""
        self.figure.clear()

        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)

        # Project 3D phantom to 2D material map (priority by material id)
        if self.phantom is None:
            phantom_proj = np.zeros_like(radiograph, dtype=np.uint8)
        elif self.phantom.ndim == 3:
            phantom_proj = np.max(self.phantom, axis=0)
        else:
            phantom_proj = self.phantom

        im1 = ax1.imshow(phantom_proj, cmap='tab10', vmin=0, vmax=3)
        ax1.set_title('Projected Phantom Materials')
        ax1.axis('off')
        cbar1 = self.figure.colorbar(im1, ax=ax1, ticks=[0, 1, 2, 3], fraction=0.046, pad=0.04)
        cbar1.ax.set_yticklabels(['Air', 'Soft', 'Bone', 'Dense'])

        display = self._to_bone_white_display(radiograph)
        im2 = ax2.imshow(display, cmap='gray', vmin=0, vmax=1)
        ax2.set_title(title)
        ax2.axis('off')
        self.figure.colorbar(im2, ax=ax2, label='Radiographic opacity (bone-white)', fraction=0.046, pad=0.04)

        self.figure.tight_layout()
        self.canvas.draw()
