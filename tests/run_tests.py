import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tests.test_cases import test_cases
from main import evaluate

for case in test_cases:
    print(f"\n--- {case['name']} ---")
    
    try:
        result = evaluate(case["input"])
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("ERROR:", str(e))