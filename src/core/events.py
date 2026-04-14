class EventBus:
    """
    A minimal publish/subscribe event bus for decoupled components.
    
    This acts as the central communication hub. Modules can subscribe to specific
    events (e.g., 'FRAME_READY') and other modules can publish data to them, 
    eliminating tight coupling between core logic and UI renderers.
    """
    def __init__(self):
        self._listeners = {}
        
    def subscribe(self, event_name, callback):
        """
        Register a callback for a specific event.
        
        Args:
            event_name (str): The string identifier of the event (e.g., 'LOG_MESSAGE').
            callback (callable): The function to execute when the event is published.
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        if callback not in self._listeners[event_name]:
            self._listeners[event_name].append(callback)
            
    def unsubscribe(self, event_name, callback):
        """
        Remove a callback from a specific event's listener list.
        Ignores silently if the callback is not found.
        """
        if event_name in self._listeners:
            try:
                self._listeners[event_name].remove(callback)
            except ValueError:
                pass
                
    def publish(self, event_name, data=None):
        """
        Broadcast an event to all registered subscribers.
        
        Args:
            event_name (str): The event identifier to broadcast.
            data: Optional arbitrary payload to pass to the callbacks.
        """
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"[EventBus] Error in callback for {event_name}: {e}")

    def pipeline(self, event_name, data, raw=None):
        """
        Run a sequential, mutable processing pipeline.

        Each subscriber is called with (data, raw) in order of subscription, where:
          - `data`: The current (potentially modified) value from the previous step.
          - `raw`: The original unmodified input — never changes between steps.

        If a subscriber returns a non-None value, it replaces `data` for the
        next subscriber in the chain. Subscribers that return None are treated
        as pass-through (they processed the data but chose not to modify it).

        Args:
            event_name (str): The pipeline identifier (e.g., 'RAW_FRAME_PIPELINE').
            data: The initial data bundle to process.
            raw: Optional reference to the original unmodified root data.

        Returns:
            The final `data` payload after all subscribers have run.
        """
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                try:
                    result = callback(data, raw)
                    if result is not None:
                        data = result
                except Exception as e:
                    print(f"[EventBus] Error in pipeline for {event_name}: {e}")
        return data
