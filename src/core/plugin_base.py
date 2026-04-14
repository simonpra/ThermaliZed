class SystemComponent:
    """
    Abstract base class for all plugins and built-in components.
    
    This establishes the contract for integrating new features into the Thermal Viewer.
    Any class inheriting from this and discovered by `AppContext` will automatically
    have its UI injected and its events wired up.
    """
    
    def on_load(self, context):
        """
        Lifecycle hook: Called automatically when the component is discovered.
        
        Args:
            context: The global `AppContext` instance. Use this to subscribe to
                     EventBus events, register services, or store component state.
        """
        pass
        
    def get_ui(self, parent_widget, zone):
        """
        Lifecycle hook: Called during application layout building to inject visual elements.
        
        Args:
            parent_widget: The Tkinter container to mount inside.
            zone (str): The string identifier of the current layout zone being built.
                        Available zones typically include: 'left_sidebar', 'main_content', 'bottom_bar'.
                        
        Returns:
            A Tkinter widget (usually a `ttk.Frame`) to be immediately `.pack()`ed into the zone.
            Return `None` if this component does not provide UI for the given zone.
        """
        return None
        
    def on_unload(self, context):
        """
        Lifecycle hook: Called when the application is shutting down.
        Perform any necessary cleanup here (e.g., closing file handles, stopping threads).
        """
        pass
