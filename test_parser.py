"""
Test script for YAMLParser class.
Demonstrates parsing various YAML configuration files.
"""

import json
from engine.YAMLParser import YAMLParser


def print_separator(title):
    """Print a formatted separator."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_parser(file_path, description):
    """Test the parser with a specific file."""
    print_separator(description)
    print(f"File: {file_path}\n")
    
    try:
        parser = YAMLParser(file_path)
        result = parser.parse()
        
        # Pretty print the result
        print(json.dumps(result, indent=2))
        
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    # Test all the YAML files
    
    test_files = [
        ("engine/test/test1.yml", "Test 1: Sequential workflow with 2 agents"),
        ("engine/test/test2.yml", "Test 2: Parallel workflow with branches"),
        ("engine/test/test3.yml", "Test 3: Sequential workflow with tools"),
        ("engine/test/test4.yml", "Test 4: Dict-based agents with models section"),
        ("engine/examples/config_sequential.yml", "Example: Full sequential config"),
    ]
    
    for file_path, description in test_files:
        test_parser(file_path, description)
    
    print_separator("All Tests Complete")
