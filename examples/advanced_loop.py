"""Advanced examples of using the @loop decorator."""
from ripplex import loop, flow
import time
import random

# Example 1: Automatic variable capture
def example_auto_capture():
    """Show how @loop automatically captures variables from scope."""
    base_url = "https://api.example.com"
    api_key = "secret123"
    multiplier = 10
    
    @loop([1, 2, 3, 4, 5])
    def fetch_and_process(item_id):
        # All these variables are automatically available!
        url = f"{base_url}/items/{item_id}?key={api_key}"
        print(f"Would fetch: {url}")
        return item_id * multiplier
    
    print(f"Results: {fetch_and_process}")

# Example 2: Error handling modes
def example_error_handling():
    """Demonstrate different error handling strategies."""
    data = [10, 20, 0, 30, 0, 40]
    
    print("\n1. Continue on error (default):")
    @loop(data, on_error="continue")
    def safe_divide(n):
        return 100 / n
    
    print(f"Results: {safe_divide}")
    print(f"Errors: {safe_divide.errors}")
    
    print("\n2. Collect errors:")
    @loop(data, on_error="collect")
    def collect_divide(n):
        return 100 / n
    
    print(f"Results (with None for errors): {collect_divide}")
    print(f"Success rate: {collect_divide.success_count}/{collect_divide.total_count}")

# Example 3: Nested loops in a flow
@flow(debug=True)
def example_nested_loops():
    """Show how loops work within flows."""
    categories = ["electronics", "books", "clothing"]
    
    @loop(categories)
    def process_category(category):
        # Simulate fetching items for category
        items = list(range(3))
        
        @loop(items)
        def process_item(item_id):
            # Both category and item_id are available!
            time.sleep(0.1)
            return f"{category}-{item_id}"
        
        return process_item
    
    return process_category

# Example 4: Progress tracking
def example_progress():
    """Show progress tracking for long-running operations."""
    
    @loop(range(20), debug=True, workers=4)
    def slow_operation(i):
        time.sleep(random.uniform(0.1, 0.3))
        return i ** 2
    
    print(f"Completed: {slow_operation}")

# Example 5: Worker control
def example_workers():
    """Control parallelism with worker threads."""
    
    # Limit to 2 workers for resource-intensive tasks
    @loop(range(10), workers=2)
    def resource_intensive(i):
        print(f"Processing {i} on thread")
        time.sleep(0.5)
        return i * 100
    
    return resource_intensive

if __name__ == "__main__":
    print("=== Auto Capture Example ===")
    example_auto_capture()
    
    print("\n=== Error Handling Example ===")
    example_error_handling()
    
    print("\n=== Nested Loops Example ===")
    result = example_nested_loops()
    print(f"Nested results: {result}")
    
    print("\n=== Progress Tracking Example ===")
    example_progress()
    
    print("\n=== Worker Control Example ===")
    results = example_workers()
    print(f"Worker results: {results}")