#!/usr/bin/env python3
"""
Script to run performance tests for Microservices architecture using Locust
"""
import subprocess
import time
import requests
import os
from datetime import datetime

# Test configurations
TEST_CONFIGS = {
    "light": {
        "users": 10,
        "spawn_rate": 2,
        "run_time": "2m"
    },
    "medium": {
        "users": 50,
        "spawn_rate": 5,
        "run_time": "5m"
    },
    "heavy": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "10m"
    },
    "custom": {
        "users": None,  # Will be prompted
        "spawn_rate": None,
        "run_time": None
    }
}

def run_locust_test(host, test_name, config):
    """Run Locust test and return results"""
    print(f"\n{'='*60}")
    print(f"Running Performance Test: {test_name}")
    print(f"Host: {host}")
    print(f"Configuration:")
    print(f"  - Users: {config['users']}")
    print(f"  - Spawn Rate: {config['spawn_rate']} users/second")
    print(f"  - Run Time: {config['run_time']}")
    print(f"{'='*60}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"reports/{test_name}_{timestamp}.html"
    csv_prefix = f"reports/{test_name}_{timestamp}"
    
    cmd = [
        "docker", "compose", "run", "--rm",
        "locust",
        "-f", "/mnt/locust/locustfile.py",
        "--host", host,
        "--users", str(config["users"]),
        "--spawn-rate", str(config["spawn_rate"]),
        "--run-time", config["run_time"],
        "--headless",
        "--html", report_file,
        "--csv", csv_prefix,
        "--loglevel", "INFO"
    ]
    
    try:
        print("Starting Locust test...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"\n✓ Test completed successfully!")
        print(f"  Report: {report_file}")
        print(f"  CSV files: {csv_prefix}_*.csv")
        return {
            "success": True,
            "report_file": report_file,
            "csv_prefix": csv_prefix,
            "output": result.stdout
        }
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Test failed!")
        print(f"  Error: {e.stderr}")
        if e.stdout:
            print(f"  Output: {e.stdout}")
        return {
            "success": False,
            "error": e.stderr
        }

def check_service_health(host):
    """Check if API Gateway service is healthy"""
    try:
        print(f"Checking service health at {host}...")
        response = requests.get(f"{host}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Service is healthy")
            return True
        else:
            print(f"⚠ Service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Service health check failed: {e}")
        return False

def get_custom_config():
    """Get custom test configuration from user"""
    print("\nEnter custom test configuration:")
    try:
        users = int(input("Number of users: "))
        spawn_rate = int(input("Spawn rate (users/second): "))
        run_time = input("Run time (e.g., 5m, 10m, 1h): ")
        return {
            "users": users,
            "spawn_rate": spawn_rate,
            "run_time": run_time
        }
    except ValueError:
        print("Invalid input. Using default medium configuration.")
        return TEST_CONFIGS["medium"]

def main():
    """Main function"""
    print("=" * 60)
    print("EduRec Microservices Performance Testing Tool")
    print("=" * 60)
    
    # Check service health
    print("\n[1/3] Checking API Gateway health...")
    api_gateway_url = "http://localhost:5000"
    if not check_service_health(api_gateway_url):
        print("\n⚠ Warning: API Gateway is not healthy or not accessible")
        print("Please ensure the Microservices system is running:")
        print("  docker-compose up -d")
        proceed = input("\nContinue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            print("Exiting...")
            return
    
    # Select test configuration
    print("\n[2/3] Select test configuration:")
    for i, (name, config) in enumerate(TEST_CONFIGS.items(), 1):
        if name == "custom":
            print(f"  {i}. {name.capitalize()} (Custom configuration)")
        else:
            print(f"  {i}. {name.capitalize()} ({config['users']} users, {config['spawn_rate']} spawn rate, {config['run_time']} run time)")
    
    choice = input("\nEnter choice (1-4): ").strip().lower()
    
    config = None
    test_name = "microservices"
    
    if choice == "4" or choice == "custom":
        config = get_custom_config()
        test_name = "microservices_custom"
    elif choice.isdigit() and 1 <= int(choice) <= 3:
        name = list(TEST_CONFIGS.keys())[int(choice) - 1]
        config = TEST_CONFIGS[name]
        test_name = f"microservices_{name}"
    else:
        print("Invalid choice. Using medium configuration.")
        config = TEST_CONFIGS["medium"]
        test_name = "microservices_medium"
    
    # Create reports directory
    os.makedirs("reports", exist_ok=True)
    
    # Run test
    print("\n[3/3] Running performance test...")
    result = run_locust_test(
        "http://api-gateway:5000",
        test_name,
        config
    )
    
    # Summary
    print("\n" + "=" * 60)
    if result.get("success"):
        print("✓ Performance testing completed successfully!")
        print("\nTest Results:")
        print(f"  - Report: {result.get('report_file')}")
        print(f"  - CSV files: {result.get('csv_prefix')}_*.csv")
        print("\nOpen the HTML report in your browser to view detailed statistics:")
        print(f"  file:///{os.path.abspath(result.get('report_file'))}")
    else:
        print("✗ Performance testing failed!")
        print("Please check the error messages above and ensure:")
        print("  - Docker Compose is running")
        print("  - Locust service is configured correctly")
        print("  - API Gateway is accessible")
    print("=" * 60)

if __name__ == "__main__":
    main()

