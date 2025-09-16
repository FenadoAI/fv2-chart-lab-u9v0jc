#!/usr/bin/env python3

import requests
import json
import os
import base64

# API Base URL
API_BASE = "http://localhost:8001/api"

def test_root():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(f"{API_BASE}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)

def test_csv_upload():
    """Test CSV upload endpoint"""
    print("Testing CSV upload...")

    # Read the sample CSV file
    csv_file_path = "/workspace/repo/sample_data.csv"

    if not os.path.exists(csv_file_path):
        print(f"CSV file not found at {csv_file_path}")
        return None

    with open(csv_file_path, 'rb') as f:
        files = {'file': ('sample_data.csv', f, 'text/csv')}
        response = requests.post(f"{API_BASE}/upload-csv", files=files)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Filename: {data['filename']}")
        print(f"Columns: {data['columns']}")
        print(f"Numeric columns: {data['numeric_columns']}")
        print(f"Categorical columns: {data['categorical_columns']}")
        print(f"Rows: {data['row_count']}, Columns: {data['column_count']}")
        print("Preview (first 3 rows):")
        for i, row in enumerate(data['preview'][:3]):
            print(f"  Row {i+1}: {row}")
        print("-" * 50)
        return data
    else:
        print(f"Error: {response.text}")
        print("-" * 50)
        return None

def test_chart_generation(csv_data):
    """Test chart generation endpoint"""
    if not csv_data:
        print("No CSV data available for chart generation")
        return None

    print("Testing chart generation...")

    # Test different chart types
    chart_configs = [
        {
            "chart_type": "bar",
            "x_column": "Department",
            "y_column": "Salary",
            "color_scheme": "viridis",
            "title": "Average Salary by Department",
            "width": 800,
            "height": 600
        },
        {
            "chart_type": "scatter",
            "x_column": "Age",
            "y_column": "Salary",
            "color_scheme": "plasma",
            "title": "Age vs Salary Scatter Plot",
            "width": 800,
            "height": 600
        },
        {
            "chart_type": "histogram",
            "x_column": "Age",
            "color_scheme": "Blues",
            "title": "Age Distribution",
            "width": 800,
            "height": 600
        }
    ]

    charts_created = []

    for i, config in enumerate(chart_configs):
        print(f"\nGenerating {config['chart_type']} chart...")

        chart_request = {
            "filename": csv_data["filename"],
            "data": csv_data["data"],
            "config": config
        }

        response = requests.post(f"{API_BASE}/generate-chart", json=chart_request)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            chart_data = response.json()
            charts_created.append(chart_data)
            print(f"Chart ID: {chart_data['id']}")
            print(f"Message: {chart_data['message']}")
            print(f"Image data length: {len(chart_data['chart_image'])} characters")
        else:
            print(f"Error: {response.text}")

    print("-" * 50)
    return charts_created

def test_get_charts():
    """Test getting all charts"""
    print("Testing get all charts...")
    response = requests.get(f"{API_BASE}/charts")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        charts = response.json()
        print(f"Found {len(charts)} charts")
        for chart in charts:
            print(f"  Chart ID: {chart['id']}, Title: {chart['config']['title']}")
    else:
        print(f"Error: {response.text}")

    print("-" * 50)

def main():
    print("=" * 50)
    print("Data Visualization Playground API Tests")
    print("=" * 50)

    try:
        # Test root endpoint
        test_root()

        # Test CSV upload
        csv_data = test_csv_upload()

        if csv_data:
            # Test chart generation
            charts = test_chart_generation(csv_data)

            # Test getting all charts
            test_get_charts()

        print("All tests completed!")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the backend server is running on http://localhost:8001")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()