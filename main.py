"""
Beer-Lambert X-Ray Radiography Simulator
CPU-based 2D radiography simulator demonstrating X-ray physics principles:
- Beer-Lambert attenuation law
- Dose-noise trade-offs with Poisson statistics
- Geometric constraints (magnification, penumbra)
- Dual-Energy Subtraction
- Synthetic pathology detection
"""

import sys
import os

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    from PyQt5.QtWidgets import QApplication
    from ui.radiography_simulator import RadiographySimulator
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("Install dependencies: pip install -r requirements.txt")
    sys.exit(1)


def main():
    try:
        app = QApplication(sys.argv)
        simulator = RadiographySimulator()
        simulator.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"[ERROR] Application startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
