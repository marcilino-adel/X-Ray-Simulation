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
        self.current_radiograph = None   # modified result (display only)
        self.base_radiograph = None      # original simulation output (never overwritten)
        
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
        # self.tabs.addTab(self.create_geometric_tab(), "Geometric Effects")
        
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
        """Create Dose-Noise Analysis tab (Modified Version)"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # --- Top Section: Dashboard (Controls + Metrics Side-by-Side) ---
        dashboard_layout = QHBoxLayout()
        
        # 1. Left Side of Tab: Controls
        controls_group = QGroupBox("Dose & Phantom Controls")
        controls_layout = QVBoxLayout()
        
        controls_layout.addWidget(QLabel("Select Phantom Anatomy:"))
        self.dn_phantom_combo = QComboBox()
        self.dn_phantom_combo.addItems(["Chest Phantom (Complete)", "Bone Only Phantom", "Soft Tissue Only Phantom"])
        controls_layout.addWidget(self.dn_phantom_combo)
        
        self.btn_gen_dn_phantom = QPushButton("Generate New Phantom")
        self.btn_gen_dn_phantom.clicked.connect(self.analyze_dose_noise)
        self.btn_gen_dn_phantom.setStyleSheet("background-color: #2C3E50; color: white; font-weight: bold;")
        controls_layout.addWidget(self.btn_gen_dn_phantom)
        
        controls_layout.addSpacing(15)
        
        controls_layout.addWidget(QLabel("Dose Intensity (I₀):"))
        self.dn_dose_slider = QSlider(Qt.Horizontal)
        self.dn_dose_slider.setRange(100, 50000)
        self.dn_dose_slider.setValue(10000)
        self.dn_dose_slider.setTickPosition(QSlider.TicksBelow)
        self.dn_dose_slider.setTickInterval(5000)
        controls_layout.addWidget(self.dn_dose_slider)
        
        self.dn_dose_val_label = QLabel("I₀ = 10000")
        self.dn_dose_val_label.setStyleSheet("font-weight: bold; color: #2980B9;")
        self.dn_dose_slider.valueChanged.connect(
            lambda: self.dn_dose_val_label.setText(f"I₀ = {self.dn_dose_slider.value()}")
        )
        controls_layout.addWidget(self.dn_dose_val_label)
        
        controls_layout.addSpacing(15)
        
        self.btn_analyze_dn = QPushButton("Apply Dose & Analyze Quality")
        self.btn_analyze_dn.clicked.connect(self.analyze_dose_noise)
        self.btn_analyze_dn.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 10px;")
        controls_layout.addWidget(self.btn_analyze_dn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        dashboard_layout.addWidget(controls_group, stretch=1)
        
        # 2. Right Side of Tab: Live Metrics View
        metrics_group = QGroupBox("Live Diagnostic Metrics")
        metrics_layout = QVBoxLayout()
        
        self.dn_metric_snr = QLabel("SNR: --")
        self.dn_metric_snr.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.dn_metric_cnr = QLabel("CNR: --")
        self.dn_metric_cnr.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.dn_metric_status = QLabel("Status: Waiting to apply dose...")
        self.dn_metric_status.setStyleSheet("font-size: 14px; font-weight: bold; color: gray;")
        self.dn_metric_status.setWordWrap(True)
        
        metrics_layout.addWidget(self.dn_metric_snr)
        metrics_layout.addWidget(self.dn_metric_cnr)
        metrics_layout.addSpacing(10)
        metrics_layout.addWidget(self.dn_metric_status)
        metrics_layout.addStretch()
        
        metrics_group.setLayout(metrics_layout)
        dashboard_layout.addWidget(metrics_group, stretch=1)
        
        layout.addLayout(dashboard_layout)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _update_geo_labels(self):
        """Update live preview labels when SID/ODD/focal spot changes."""
        SID   = self.sid_spinbox.value()
        ODD   = float(self.odd_slider.value())
        focal = self.focal_spinbox.value()

        # ── Update ODD slider max to match SID ────────────────
        # ODD must always be between 0 and SID
        self.odd_slider.setMaximum(int(SID))

        # Clamp ODD if it exceeds new SID value
        if ODD > SID:
            self.odd_slider.setValue(int(SID) - 1)
            ODD = float(self.odd_slider.value())

        # ── Core Logic ────────────────────────────────────────
        # SID is constant, ODD is variable, SOD is calculated
        SOD = SID - ODD

        # Safety check
        if SOD <= 0:
            self.odd_value_label.setText(f"{ODD:.0f} cm")
            self.sod_result_label.setText("⚠ ODD must be less than SID!")
            self.mag_result_label.setText("Magnification: N/A")
            self.penumbra_result_label.setText("Penumbra: N/A")
            return

        magnification = SID / SOD
        penumbra_cm   = focal * (ODD / SOD)
        penumbra_px   = penumbra_cm / self.physics.voxel_size_cm

        # Update all labels
        self.odd_value_label.setText(f"{ODD:.0f} cm")
        self.sod_result_label.setText(
            f"SOD = SID - ODD = {SID:.1f} - {ODD:.1f} = {SOD:.1f} cm"
        )
        self.mag_result_label.setText(f"Magnification: {magnification:.3f}x")
        self.penumbra_result_label.setText(
            f"Penumbra: {penumbra_cm:.4f} cm ({penumbra_px:.2f} px)"
        )   
    
    def create_dualenergy_tab(self) -> QWidget:
        """Create Dual-Energy Subtraction tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Dose for each energy
        dose_group = QGroupBox("Dual-Energy Acquisition")
        dose_layout = QGridLayout()
        
        dose_low_label = QLabel("Low Energy (80 kVp) Dose:")
        self.dose_low_spinbox = QSpinBox()
        self.dose_low_spinbox.setRange(100, 1000000)
        self.dose_low_spinbox.setValue(8000)
        dose_layout.addWidget(dose_low_label, 0, 0)
        dose_layout.addWidget(self.dose_low_spinbox, 0, 1)
        
        dose_high_label = QLabel("High Energy (120 kVp) Dose:")
        self.dose_high_spinbox = QSpinBox()
        self.dose_high_spinbox.setRange(100, 1000000)
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
            self.base_radiograph = radiograph.copy()   # save original
            if self.show_phantom_checkbox.isChecked():
                self.display_phantom_and_radiograph(radiograph, f"Radiograph (I₀={dose}, {energy})")
            else:
                self.display_radiograph(radiograph, f"Radiograph (I₀={dose}, {energy})")
            self.status_label.setText(f"✓ Simulation complete: I₀={dose}, Energy={energy}, Noise={apply_noise}")
            
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            print(f"[ERROR] {e}")
    
    def analyze_dose_noise(self):
        """Simulate single dose on selected phantom and update global canvas"""
        try:
            self.status_label.setText("Simulating dose application...")
            
            # 1. Generate and Filter Phantom based on selection
            # We generate a fresh base phantom so we don't permanently corrupt the original
            base_phantom = self.physics.create_digital_phantom(256, 256, 64)
            self.physics.add_synthetic_pathology(base_phantom, 'nodule', severity=1.0)
            
            selection = self.dn_phantom_combo.currentIndex()
            if selection == 1:
                # Bone Only: Convert Soft Tissue (1) to Air (0)
                base_phantom[base_phantom == 1] = 0
            elif selection == 2:
                # Soft Tissue Only: Convert Bone (2) to Soft Tissue (1)
                base_phantom[base_phantom == 2] = 1
                
            self.phantom = base_phantom # Update the global phantom for consistency

            dose = self.dn_dose_slider.value()
            
            # 2. Simulate physics
            ideal = self.physics.simulate_acquisition(self.phantom, dose, 'high')
            noisy = self.physics.apply_poisson_noise(ideal)
            
            # 3. Extract masks for metrics
            masks = self.physics.get_projected_material_masks(self.phantom)
            signal_mask = masks['soft_tissue'] & ~masks['bone']
            noise_mask = masks['air'] & ~masks['soft_tissue']
            
            # Fallback if strict masks are empty due to filtering
            if np.count_nonzero(signal_mask) < 50:
                signal_mask = masks['soft_tissue'] if np.count_nonzero(masks['soft_tissue']) > 0 else np.ones_like(ideal, dtype=bool)
            if np.count_nonzero(noise_mask) < 50:
                noise_mask = masks['air'] if np.count_nonzero(masks['air']) > 0 else np.ones_like(ideal, dtype=bool)
                
            # 4. Calculate SNR and CNR
            signal_vals = noisy[signal_mask]
            noise_vals = noisy[noise_mask]
            
            mean_sig = float(np.mean(signal_vals))
            std_sig = float(np.std(signal_vals))
            mean_noise = float(np.mean(noise_vals))
            std_noise = float(np.std(noise_vals))
            
            snr = mean_sig / (std_sig + 1e-6)
            cnr = abs(mean_sig - mean_noise) / (std_noise + 1e-6)
            
            # 5. Update Metrics inside the Tab
            self.dn_metric_snr.setText(f"SNR: {snr:.2f}")
            self.dn_metric_cnr.setText(f"CNR: {cnr:.2f}")
            
            if snr > 15:
                status_text = "Diagnostic Quality: EXCELLENT\nHigh clarity, minimal quantum mottle."
                self.dn_metric_status.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
            elif snr > 7:
                status_text = "Diagnostic Quality: ACCEPTABLE\nVisible noise, but structures are distinguishable."
                self.dn_metric_status.setStyleSheet("font-size: 14px; font-weight: bold; color: orange;")
            else:
                status_text = "Diagnostic Quality: POOR\nHeavy quantum noise obscures critical details."
                self.dn_metric_status.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
                
            self.dn_metric_status.setText(status_text)
            
            # 6. Update the GLOBAL right-side Canvas
            self.figure.clear()
            
            # Plot 1: Visual Image Quality
            ax1 = self.figure.add_subplot(121)
            im = ax1.imshow(noisy, cmap='gray', vmin=0, vmax=dose)
            ax1.set_title(f"Simulated Clinical Radiograph\n(Dose I₀ = {dose})")
            ax1.axis('off')
            
            # Plot 2: Quantitative Metrics Bar Chart
            ax2 = self.figure.add_subplot(122)
            ax2.bar(['SNR', 'CNR'], [snr, cnr], color=['#2980B9', '#27AE60'])
            ax2.set_title("Quantitative Quality Scores")
            ax2.set_ylabel("Metric Score")
            ax2.grid(True, axis='y', alpha=0.3)
            
            # Add an indicative line for minimum diagnostic SNR
            ax2.axhline(7, color='red', linestyle='--', alpha=0.7, label='Diagnostic Threshold (SNR=7)')
            ax2.legend()
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            self.status_label.setText(f"✓ Dose analysis complete. SNR = {snr:.2f}")
            
        except Exception as e:
            self.status_label.setText(f"✗ Error during analysis: {str(e)}")
            print(f"[ERROR] {e}")
    
    def apply_geometric_effects(self):
        try:
            if self.base_radiograph is None:      # ← check base not current
                self.status_label.setText("✗ No radiograph loaded. Simulate first (Tab 1).")
                return
    
            # Read physical parameters from UI
            SID             = self.sid_spinbox.value()
            ODD             = float(self.odd_slider.value())
            focal_spot_size = self.focal_spinbox.value()
    
            # Calculate SOD from SID and ODD
            SOD = SID - ODD
    
            # Safety check
            if SOD <= 0:
                self.status_label.setText("✗ ODD must be less than SID!")
                return
    
            # Calculate derived values for display
            magnification = SID / SOD
            penumbra_cm   = focal_spot_size * (ODD / SOD)
            penumbra_px   = penumbra_cm / self.physics.voxel_size_cm
    
            # Read toggles from UI
            apply_magnification = self.magnification_checkbox.isChecked()
            apply_penumbra      = self.penumbra_checkbox.isChecked()
    
            # Apply physics
            radiograph = self.physics.apply_geometric_effects(
                self.base_radiograph,
                SID=SID,
                ODD=ODD,
                focal_spot_size=focal_spot_size,
                apply_magnification=apply_magnification,
                apply_penumbra=apply_penumbra
            )
    
            self.current_radiograph = radiograph  # ← update current for display only
            self.display_radiograph(
                radiograph,
                f"Geometric Effects | SID={SID}cm  ODD={ODD}cm  SOD={SOD:.1f}cm\n"
                f"Magnification={magnification:.3f}x | Penumbra={penumbra_cm:.4f}cm ({penumbra_px:.2f}px)"
            )
            self.status_label.setText(
                f"✓ Geometric effects applied | "
                f"SOD={SOD:.1f}cm | ODD={ODD:.1f}cm | "
                f"M={magnification:.3f}x | "
                f"Penumbra={penumbra_cm:.4f}cm ({penumbra_px:.2f}px)"
            )
    
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
            im3 = ax3.imshow(subtracted, cmap='bone')
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
