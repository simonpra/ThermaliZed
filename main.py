import argparse
from src.gui.app import ThermalApp

def main():
    parser = argparse.ArgumentParser(description='TC001 Thermal Camera Viewer - Tkinter Edition')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    try:
        app = ThermalApp()
        app.mainloop()
    except Exception as e:
        print(f"Failed to start the application: {e}")

if __name__ == '__main__':
    main()
