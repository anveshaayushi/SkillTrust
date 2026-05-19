test_cases = [
    {
        "name": "Copied Code",
        "input": {
            "code": "def add(a,b): return a+b",
            "readme": "simple addition",
            "skills": ["python"]
        }
    },
    {
        "name": "Modified Code",
        "input": {
            "code": "def add_numbers(x, y): return x + y",
            "readme": "adds two numbers",
            "skills": ["python"]
        }
    },
    {
        "name": "Original Code",
        "input": {
            "code": """
def sum_even(nums):
    total = 0
    for n in nums:
        if n % 2 == 0:
            total += n
    return total
""",
            "readme": "sum of even numbers",
            "skills": ["python"]
        }
    }
]