import importlib
import pkgutil
import sys
import os

from src.core.events import EventBus
from src.core.camera import ThermalCamera
from src.utils.constants import DEFAULT_PARAMS

class AppContext:
    """
    Central context manager for the Thermal Viewer application.
    
    This class serves as the single source of truth for the application's global
    state. It holds references to registered services, globally shared parameters,
    discovered plugins, and the central EventBus for decoupled communication.
    """
    def __init__(self, root_window):
        """
        Initialize the application context.
        
        Args:
            root_window: The main Tkinter root window instance.
        """
        self.root = root_window
        self.event_bus = EventBus()
        self.state = {
            'params': DEFAULT_PARAMS.copy(),
            'devices': []
        }
        self.services = {}
        self.plugins = []
        
        self.camera = ThermalCamera()
        self.state['devices'] = self.camera.get_device_names()
        self.register_service('camera', self.camera)
        
        # Load components immediately so they can subscribe to events
        self._load_core_components()
        self._load_external_plugins()
        
        # Start camera loop
        self.update_interval = int(1000 / 30) # 30 FPS
        self.root.after(self.update_interval, self._update_loop)

        self.event_bus.publish('LOG_MESSAGE', "System Started. Plugins Loaded.")
        
    def _update_loop(self):
        """
        Main application loop running at a fixed interval (e.g., 30 FPS).
        Fetches the latest frame from the camera service or shared state and 
        broadcasts it to all components via the EventBus 'FRAME_READY' event.
        """
        # Check if we have a frozen frame loaded
        if 'frozen_frame_data' in self.state and self.state['frozen_frame_data'] is not None:
            frame_data = self.state['frozen_frame_data']
            self.event_bus.publish('FRAME_READY', frame_data)
        else:
            # Fetch latest frame
            frame_data = self.camera.get_latest_frame()
            if frame_data:
                self.event_bus.publish('FRAME_READY', frame_data)
        
        self.root.after(self.update_interval, self._update_loop)
        
    def register_service(self, name, service):
        """
        Register a global service (e.g., the camera object) so other plugins 
        and components can retrieve it.
        """
        self.services[name] = service
        self.event_bus.publish('LOG_MESSAGE', f"Registered Service: '{name}'")
        
    def get_service(self, name):
        """Retrieve a registered global service by name."""
        return self.services.get(name)

    def _load_core_components(self):
        """
        Automatically discovers and loads built-in plugins from `src.core.components`.
        These are essential features like basic controls and the main renderer.
        """
        import src.core.components as core_components
        self._load_from_package(core_components)
        
    def _load_external_plugins(self):
        """
        Automatically discovers and loads third-party plugins from the `plugins/` 
        directory in the project root. Fallbacks safely if no plugins are found.
        """
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = sys._MEIPASS
        else:
            # Running in a normal Python environment
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            
        plugins_dir = os.path.join(base_dir, 'plugins')
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            
        if plugins_dir not in sys.path:
            sys.path.insert(0, plugins_dir)

        # Force Python to recognize it as a package if not exists
        init_file = os.path.join(plugins_dir, '__init__.py')
        if not os.path.exists(init_file):
            try:
                with open(init_file, 'w') as f:
                    f.write('')
            except OSError:
                pass # Ignore if running in a read-only PyInstaller MEIPASS bundle
                
        try:
            import plugins
            self._load_from_package(plugins)
        except ImportError as e:
            print(f"Failed to load external plugins directory: {e}")

    def _load_from_package(self, package):
        """
        Internal reflection logic to iterate through a module package and instantiate
        any `PluginClass` object found within child modules.
        
        Args:
            package: The imported Python package module to search through.
        """
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                full_module_name = f"{package.__name__}.{module_name}"
                try:
                    module = importlib.import_module(full_module_name)
                    # We expect a PluginClass inside the __init__.py of the module folder
                    if hasattr(module, 'PluginClass'):
                        plugin_instance = module.PluginClass()
                        plugin_instance.on_load(self)
                        self.plugins.append(plugin_instance)
                        print(f"Loaded Plugin: {module_name}")
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")
