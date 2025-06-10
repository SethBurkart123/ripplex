# Ripplex

A Python framework for parallel execution with automatic dependency resolution and variable capture.

## Features

- **@flow decorator**: Automatically parallelize function execution based on dependencies
- **@loop decorator**: Simple parallel loops with automatic variable capture
- **Visual debugging**: See execution progress in real-time
- **Error handling**: Multiple strategies for dealing with failures
- **Zero-config**: Works out of the box with sensible defaults

## Installation

```bash
pip install ripplex
```

## Quick Start

### Simple Parallel Loop

```python
from ripplex import loop

items = [1, 2, 3, 4, 5]
multiplier = 10

@loop(items)
def process(item):
    # 'multiplier' is automatically captured from the outer scope!
    return item * multiplier

print(process)  # [10, 20, 30, 40, 50]
```

### Automatic Parallelization with @flow

```python
from ripplex import flow
import time

@flow(debug=True)
def data_pipeline():
    # These run in parallel automatically
    data1 = fetch_source_1()
    data2 = fetch_source_2()
    
    # This waits for both to complete
    combined = merge(data1, data2)
    
    # These transformations run in parallel
    result1 = transform_a(combined)
    result2 = transform_b(combined)
    
    return result1, result2
```

### Error Handling

```python
@loop(items, on_error="collect")
def safe_process(item):
    return risky_operation(item)

if not safe_process.all_successful:
    print(f"Failed items: {safe_process.errors}")
```

### Progress Tracking

```python
@loop(large_list, debug=True)
def slow_operation(item):
    # Progress bar shows automatically
    return expensive_computation(item)
```

## API Reference

### @flow(debug=False)

Decorator that analyzes function dependencies and runs independent operations in parallel.

- `debug`: Show visual execution timeline

### @loop(iterable, *, workers=None, debug=False, on_error="continue")

Decorator for parallel loops with automatic variable capture.

- `iterable`: Items to process (or an int for range)
- `workers`: Number of threads (default: number of items, max 32)
- `debug`: Show progress bar
- `on_error`: How to handle errors
  - `"continue"`: Skip failed items (default)
  - `"raise"`: Stop on first error
  - `"collect"`: Continue but keep None for failed items

### pmap(fn, iterable, **kwargs)

Functional alternative to @loop decorator.

```python
from ripplex import pmap

results = pmap(lambda x: x ** 2, [1, 2, 3, 4])
```

## Advanced Features

### Nested Loops in Flows

```python
@flow(debug=True)
def complex_pipeline():
    categories = fetch_categories()
    
    @loop(categories)
    def process_category(cat):
        items = fetch_items(cat)
        
        @loop(items)
        def process_item(item):
            # Both 'cat' and 'item' are available
            return transform(item, cat)
        
        return summarize(process_item)
    
    return process_category
```

### Custom Worker Pools

```python
# Limit parallelism for resource-intensive tasks
@loop(items, workers=4)
def gpu_operation(item):
    return heavy_compute(item)
```

## Debugging

Both decorators support visual debugging:

- `@flow(debug=True)`: Shows execution DAG and timing
- `@loop(items, debug=True)`: Shows progress bar with success/error counts

## Contributing

PRs welcome! Please include tests for new features.

## License

MIT