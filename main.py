from ripplex import flow, loop, pmap
import time

def test(time_s: float, message: str) -> float:
    """A simple async function to be tracked within a flow."""
    print(f"Starting test: {message} (will sleep {time_s:.1f}s)")
    time.sleep(time_s)
    print(f"Finished test: {message}")
    return time_s

@flow(debug=True)
def main(query):
    """Main flow orchestrating calls to test."""
    print("--- Starting Flow ---")

    # These will run in parallel
    val = test(0.2, "Task A")
    val2 = test(1.0, "Task B")

    # Simple loop - query is automatically captured!
    items = [1, 2, 3]
    
    @loop(items, debug=True)
    def process_item(item):
        print(f"Processing {item} with query: {query}")
        time.sleep(0.1)  # Simulate work
        return item * 2

    print(f"Results: {process_item}")
    
    # Example with error handling
    numbers = [1, 2, 0, 4]
    
    @loop(numbers, on_error="collect")
    def divide_by(n):
        return 10 / n  # Will error on 0
    
    if not divide_by.all_successful:
        print(f"Had {len(divide_by.errors)} errors: {divide_by.errors}")
    
    # Alternative: use pmap for simple operations
    squared = pmap(lambda x: x ** 2, [1, 2, 3, 4])
    print(f"Squared: {squared}")

    return val + val2

# Run the example
result = main('hello world')
print(f"\nFlow completed with result: {result}")