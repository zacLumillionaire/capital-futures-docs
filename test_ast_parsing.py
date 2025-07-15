#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test to verify AST parsing works correctly.
"""

import ast
import os

# Test with a simple Python file
test_code = """
def test_function(group_id, position_id):
    return group_id + position_id

group_id = 123
position_id = 456
"""

try:
    tree = ast.parse(test_code)
    print("AST parsing successful!")
    print(f"AST dump: {ast.dump(tree)[:200]}...")
except Exception as e:
    print(f"AST parsing failed: {e}")

# Test with a real file from the project
test_file = os.path.join("Capital_Official_Framework", "main.py")
if os.path.exists(test_file):
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=test_file)
        print(f"Successfully parsed {test_file}")
    except Exception as e:
        print(f"Failed to parse {test_file}: {e}")
else:
    print(f"Test file {test_file} not found")
