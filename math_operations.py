def add_numbers(a, b):
    """Add two numbers and return the result."""
    return a + b

def divide_numbers(a, b):
    """Divide two numbers and return the result."""
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b
