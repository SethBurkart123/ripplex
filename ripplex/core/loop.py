"""Simplified loop decorator for parallel execution."""
import inspect
from typing import Callable, Iterable, TypeVar, Union, Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, Future
from functools import wraps
from .context import capture_scope, get_flow_context
from .debug import LoopDebugger

T = TypeVar("T")
R = TypeVar("R")

class LoopResult(List[R]):
    """Enhanced list that tracks errors from loop execution."""
    def __init__(self, results: List[R], errors: Dict[int, Exception]):
        super().__init__(results)
        self.errors = errors
        self.success_count = len(results) - len(errors)
        self.total_count = len(results)
    
    @property
    def all_successful(self) -> bool:
        return len(self.errors) == 0

def loop(
    iterable: Union[int, Iterable[T]],
    *,
    workers: Optional[int] = None,
    debug: bool = False,
    on_error: str = "continue"  # "continue", "raise", or "collect"
) -> Callable[[Callable[..., R]], LoopResult[R]]:
    """
    Execute a function over an iterable in parallel using threads.
    
    Automatically captures variables from the enclosing scope.
    
    Args:
        iterable: An iterable or integer (converted to range)
        workers: Number of worker threads (defaults to number of items)
        debug: Show progress visualization
        on_error: How to handle errors:
            - "continue": Continue processing, None for failed items
            - "raise": Stop and raise first error encountered
            - "collect": Continue processing, collect all errors
    
    Usage:
        items = [1, 2, 3]
        multiplier = 10
        
        @loop(items)
        def process(item):
            return item * multiplier  # multiplier is auto-captured!
        
        # process is now a list of results: [10, 20, 30]
    """
    def decorator(fn: Callable[..., R]) -> LoopResult[R]:
        # Convert integer to range if needed
        if isinstance(iterable, int):
            items: List[T] = list(range(iterable))  # type: ignore
        else:
            items = list(iterable)
        
        if len(items) == 0:
            return LoopResult([], {})
        
        # Capture variables from enclosing scope
        captured_scope = capture_scope(fn)
        
        # Also get any flow context if we're inside a @flow
        flow_context = get_flow_context()
        
        # Merge contexts (flow context takes precedence)
        context = {**captured_scope, **flow_context}
        
        # Extract function signature to know what to pass
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        
        # Prepare debugger if needed
        debugger = LoopDebugger(len(items), desc=f"Processing {fn.__name__}") if debug else None
        if debugger:
            debugger.start()
        
        errors: Dict[int, Exception] = {}
        results: List[Optional[R]] = [None] * len(items)
        
        def execute_item(idx: int, item: T) -> Optional[R]:
            try:
                # Build kwargs based on function signature
                kwargs = {}
                for param in params[1:]:  # Skip first param (the item)
                    if param in context:
                        kwargs[param] = context[param]
                
                result = fn(item, **kwargs)
                results[idx] = result
                
                if debugger:
                    debugger.update(success=True)
                
                return result
            except Exception as e:
                errors[idx] = e
                
                if debugger:
                    debugger.update(success=False)
                
                if on_error == "raise":
                    raise
                elif on_error == "collect":
                    results[idx] = None
                    return None
                else:  # continue
                    results[idx] = None
                    return None
        
        # Execute in parallel
        max_workers = workers or min(len(items), 32)  # Cap at 32 threads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures: List[Future] = []
            for idx, item in enumerate(items):
                future = executor.submit(execute_item, idx, item)
                futures.append(future)
            
            # Wait for all to complete (they handle errors internally)
            for future in futures:
                try:
                    future.result()
                except Exception:
                    if on_error == "raise":
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        raise
        
        if debugger:
            debugger.stop()
        
        # Filter out None results if we're in continue mode
        if on_error == "continue":
            filtered_results = [r for r in results if r is not None]
            return LoopResult(filtered_results, errors)
        else:
            return LoopResult(results, errors)  # type: ignore
    
    # Allow using @loop without parentheses for simple cases
    if callable(iterable):
        # This means it was used as @loop without arguments
        # In this case, iterable is actually the function
        # We'll return a function that expects the iterable
        fn = iterable
        
        @wraps(fn)
        def wrapper(iter_arg: Union[int, Iterable], **kwargs):
            return loop(iter_arg, **kwargs)(fn)
        
        return wrapper  # type: ignore
    
    return decorator

# Convenience function for simple map operations
def pmap(fn: Callable[[T], R], iterable: Iterable[T], **kwargs) -> List[R]:
    """
    Parallel map - simpler alternative to @loop decorator.
    
    Usage:
        results = pmap(lambda x: x * 2, [1, 2, 3])
        # returns [2, 4, 6]
    """
    @loop(iterable, **kwargs)
    def _mapped(item):
        return fn(item)
    
    return _mapped