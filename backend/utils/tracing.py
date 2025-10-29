"""X-Ray distributed tracing for Aegis platform."""

from functools import wraps
from typing import Callable, Any
try:
    from aws_xray_sdk.core import xray_recorder
    XRAY_AVAILABLE = True
except ImportError:
    XRAY_AVAILABLE = False
    xray_recorder = None

def trace_operation(operation_name: str):
    """Decorator to trace operations with X-Ray."""
    def decorator(func: Callable) -> Callable:
        if not XRAY_AVAILABLE:
            return func
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                with xray_recorder.capture(operation_name):
                    result = await func(*args, **kwargs)
                    return result
            except Exception as e:
                # If X-Ray fails, just execute the function without tracing
                if "cannot find the current segment" in str(e):
                    result = await func(*args, **kwargs)
                    return result
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                with xray_recorder.capture(operation_name):
                    result = func(*args, **kwargs)
                    return result
            except Exception as e:
                # If X-Ray fails, just execute the function without tracing
                if "cannot find the current segment" in str(e):
                    result = func(*args, **kwargs)
                    return result
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def add_trace_metadata(key: str, value: Any):
    """Add metadata to current X-Ray trace."""
    if XRAY_AVAILABLE and xray_recorder:
        try:
            xray_recorder.put_metadata(key, value)
        except Exception:
            pass

def add_trace_annotation(key: str, value: str):
    """Add annotation to current X-Ray trace."""
    if XRAY_AVAILABLE and xray_recorder:
        try:
            xray_recorder.put_annotation(key, value)
        except Exception:
            pass



