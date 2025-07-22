# Ripplex
A pythonic parallel computing library that just works

## Installation

```bash
pip install ripplex
```

## Two Simple Features

### 1. `@flow` - Automatic Parallelization

Add `@flow` to any function and Ripplex automatically runs independent operations in parallel.

```python
from ripplex import flow

@flow
def get_user_profile(user_id):
    # These three calls run in PARALLEL automatically
    user = fetch_user_data(user_id)      # 1.0s
    posts = fetch_user_posts(user_id)    # 1.5s  
    friends = fetch_user_friends(user_id) # 0.8s
    
    # This waits for all three to finish, then runs
    return {
        "user": user,
        "posts": posts,
        "friends": friends
    }

# Sequential: 3.3 seconds
# With @flow: 1.5 seconds
result = get_user_profile(123)
```

**Zero refactoring required.** Just add the decorator.

### 2. `@loop` - Parallel Processing

Process lists in parallel with automatic variable capture.

```python
from ripplex import loop

# Variables from outer scope are automatically available
API_KEY = "secret-key"
BASE_URL = "https://api.example.com"

user_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

@loop(user_ids)
def fetch_user(user_id):
    # API_KEY and BASE_URL automatically available!
    url = f"{BASE_URL}/users/{user_id}?key={API_KEY}"
    return requests.get(url).json()

# The decorated function becomes a list of results!
print(f"Fetched {len(fetch_user)} users in parallel")
print(fetch_user[0])  # First user's data
```

**No setup needed.** Outer variables just work.

## Working with @loop Results

The `@loop` decorator returns a special `LoopResult` object that acts like a list but includes extra metadata:

```python
@loop([1, 2, 0, 4, 0, 6], on_error="collect")
def divide(n):
    return 100 / n

# It's a list!
print(divide)            # [100, 50, None, 25, None, 16.67]
print(divide[0])         # 100
print(len(divide))       # 6

# But with extras!
print(divide.success_count)    # 4 successful
print(divide.total_count)      # 6 total attempts
print(divide.all_successful)   # False
print(divide.errors)           # {2: ZeroDivisionError(...), 4: ZeroDivisionError(...)}
```

## Error Handling Options

The `@loop` decorator provides three strategies for handling errors:

```python
data = [1, 2, 0, 4, 0, 6]  # Zeros will cause division errors

# Option 1: "continue" (default) - Skip failures, only return successes
@loop(data, on_error="continue")
def divide_continue(n):
    return 100 / n
# Returns: [100, 50, 25, 16.67] - failed items removed

# Option 2: "raise" - Stop on first error
@loop(data, on_error="raise")
def divide_raise(n):
    return 100 / n
# Raises: ZeroDivisionError (and cancels remaining)

# Option 3: "collect" - Keep None for failures, preserve positions
@loop(data, on_error="collect")
def divide_collect(n):
    return 100 / n
# Returns: [100, 50, None, 25, None, 16.67] - preserves list structure
```

## More Ways to Parallelize

### Functional API - No Decorators Needed

```python
from ripplex import pmap, execute, quick_map

# One-liner parallel map
squared = pmap(lambda x: x**2, range(100))

# Execute with options
results = execute(process_item, items, workers=8, on_error="collect")

# Super quick for prototyping
doubled = quick_map(lambda x: x * 2, [1,2,3,4,5])
```

### Convenience Aliases

```python
import ripplex as rx

# Use short aliases for less typing
@rx.f  # Instead of @flow
def complex_pipeline():
    data = fetch_data()
    processed = transform(data)
    return processed

@rx.l(items)  # Instead of @loop  
def process(item):
    return item * 2

# Ultra-short parallel map
results = rx.p(lambda x: x**2, range(10))
```

## Complete Example

Here's a real-world data pipeline using both features:

```python
from ripplex import flow, loop

@flow  
def process_sales_data():
    # Step 1: Fetch data in parallel
    sales = fetch_sales_data()        # 2s
    customers = fetch_customers()     # 1.5s
    products = fetch_products()       # 1s
    
    # Step 2: Process each sale in parallel  
    @loop(sales, workers=8)
    def enrich_sale(sale):
        # customers and products automatically available!
        customer = customers[sale['customer_id']]
        product = products[sale['product_id']]
        
        return {
            **sale,
            'customer_name': customer['name'],
            'product_name': product['name'],
            'profit': sale['price'] - product['cost']
        }
    
    # Step 3: Generate reports in parallel
    summary = generate_summary(enrich_sale)
    insights = analyze_trends(enrich_sale)
    
    return {'sales': enrich_sale, 'summary': summary, 'insights': insights}

# Sequential: ~15 seconds
# With Ripplex: ~6 seconds  
result = process_sales_data()
```

## Debugging

Add `debug=True` to see what's happening:

```python
@flow(debug=True)
def my_function():
    # Shows execution timeline
    pass

@loop(items, debug=True) 
def process_item(item):
    # Shows progress bar
    pass
```

## API Reference

### Decorators

#### `@flow(debug=False)`
Automatically parallelizes independent operations in a function by analyzing dependencies.

#### `@loop(iterable, workers=None, on_error="continue", debug=False)`
Processes items in parallel with automatic variable capture.

**Parameters:**
- `iterable`: Items to process (or an integer for `range(n)`)
- `workers`: Number of threads (default: smart auto-detection)
- `on_error`: Error handling strategy:
  - `"continue"`: Skip errors, return only successes
  - `"raise"`: Stop on first error
  - `"collect"`: Include `None` for failures, preserve list positions
- `debug`: Show progress bar and timing

**Returns:** `LoopResult` - an enhanced list with error tracking

### Functions

#### `pmap(function, iterable, **kwargs)`
Functional parallel map for one-liners:
```python
results = pmap(lambda x: x**2, [1,2,3,4])  # [1,4,9,16]
```

#### `execute(function, items, **kwargs)`
Execute a function in parallel without decorators:
```python
results = execute(process_item, items, workers=10, on_error="collect")
```

#### `quick_map(function, items)`
Simplest parallel map with defaults:
```python
results = quick_map(lambda x: x * 2, items)
```

#### `summary(loop_result)`
Get a human-readable summary of loop execution:
```python
from ripplex import summary

@loop(items, on_error="collect")
def process(item):
    return risky_operation(item)

print(summary(process))
# 📊 Execution Summary:
#    Total items: 100
#    Successful: 95
#    Failed: 5
#    Success rate: 95.0%
```

## Performance Tips

- **I/O heavy**: Use more workers (`workers=20`)
- **CPU heavy**: Use fewer workers (`workers=4`) 
- **Start with**: `debug=True` to see what's happening
- **Error handling**: Use `on_error="collect"` to see which items failed

## Gotchas and Tips

1. **@flow analyzes code**: Each parallelizable operation must be an assignment that creates a new variable
2. **Thread-based**: Best for I/O-bound tasks (API calls, file operations, database queries)
3. **Auto-captures variables**: Inner functions automatically see outer scope - no need to pass everything
4. **Smart defaults**: Worker count auto-scales based on workload
5. **Not for CPU-bound**: Use `multiprocessing` for heavy computation

**Ready to supercharge your Python code?** Start with `@flow` on your existing functions and watch them run in parallel!
