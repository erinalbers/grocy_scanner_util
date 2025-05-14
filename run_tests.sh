#!/bin/bash

# Run all tests for the barcode scanner application

# Set up environment
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Create test directory if it doesn't exist
mkdir -p tests

# Run individual test files
echo "Running barcode processor tests..."
python -m unittest tests/test_barcode_processor.py

echo "Running grocy client tests..."
python -m unittest tests/test_grocy_client.py

echo "Running config manager tests..."
python -m unittest tests/test_config_manager.py

echo "Running feedback manager tests..."
python -m unittest tests/test_feedback_manager.py

echo "Running barcode scanner tests..."
python -m unittest tests/test_barcode_scanner.py

echo "Running integration tests..."
python -m unittest tests/test_integration.py

# Run all tests with coverage (if installed)
if command -v coverage &> /dev/null; then
    echo "Running tests with coverage..."
    coverage run -m unittest discover -s tests
    coverage report -m
    coverage html -d coverage_html
    echo "Coverage report generated in coverage_html directory"
else
    echo "Coverage not installed. Install with: pip install coverage"
fi

echo "All tests completed!"
