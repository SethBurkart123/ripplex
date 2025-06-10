"""Context management for flow and loop decorators."""
import inspect
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Use contextvars instead of global state for thread safety
_flow_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('flow_context', default=None)

def capture_scope(func) -> Dict[str, Any]:
    """Capture variables from the function's enclosing scope."""
    frame = inspect.currentframe()
    if frame is None:
        return {}
    
    # Go up two frames: capture_scope -> decorator -> actual calling scope
    calling_frame = frame.f_back.f_back
    if calling_frame is None:
        return {}
    
    # Combine locals and globals from the calling scope
    scope = {}
    scope.update(calling_frame.f_globals)
    scope.update(calling_frame.f_locals)
    
    # Filter out built-ins and modules
    filtered_scope = {}
    for name, value in scope.items():
        if not name.startswith('_') and not inspect.ismodule(value) and name not in dir(__builtins__):
            try:
                # Only include serializable values
                import pickle
                pickle.dumps(value)
                filtered_scope[name] = value
            except:
                pass
    
    return filtered_scope

def set_flow_context(context: Dict[str, Any]):
    """Set the current flow context."""
    _flow_context.set(context)

def get_flow_context() -> Dict[str, Any]:
    """Get the current flow context."""
    return _flow_context.get() or {}