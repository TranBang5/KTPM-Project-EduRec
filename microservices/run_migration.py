#!/usr/bin/env python3
"""
Script to run the migration from Monolith to Microservices
"""
import os
import sys
import subprocess
import time
import requests
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {command}")
            return True
        else:
            print(f"✗ {command}")
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {command}")
        print(f"  Exception: {str(e)}")
        return False

def check_service_health(service_name, url, max_retries=30):
    """Check if a service is healthy"""
    print(f"Checking {service_name} health...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ {service_name} is healthy")
                return True
        except:
            pass
        time.sleep(2)
        print(f"  Retrying {service_name} health check... ({i+1}/{max_retries})")
    
    print(f"✗ {service_name} health check failed")
    return False

def main():
    """Main migration function"""
    print("🚀 Starting Migration from Monolith to Microservices")
    print("=" * 60)
    
    # Change to microservices directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Step 1: Setup services
    print("\n📦 Step 1: Setting up microservices...")
    if not run_command("python setup_services.py"):
        print("❌ Setup failed!")
        return False
    
    # Step 2: Build and start services
    print("\n🐳 Step 2: Building and starting Docker services...")
    if not run_command("docker-compose up -d --build"):
        print("❌ Docker services failed to start!")
        return False
    
    # Step 3: Wait for services to be ready
    print("\n⏳ Step 3: Waiting for services to be ready...")
    services = [
        ("Recommendation Service", "http://localhost:5001"),
        ("Study Plan Service", "http://localhost:5002"),
        ("Feedback Service", "http://localhost:5003"),
        ("API Gateway", "http://localhost:5000")
    ]
    
    all_healthy = True
    for service_name, url in services:
        if not check_service_health(service_name, url):
            all_healthy = False
    
    if not all_healthy:
        print("❌ Some services are not healthy!")
        print("Check logs with: docker-compose logs")
        return False
    
    # Step 4: Backup original app.py
    print("\n💾 Step 4: Backing up original app.py...")
    original_app_path = "../app.py"
    backup_app_path = "../app_monolith_backup.py"
    
    if os.path.exists(original_app_path):
        shutil.copy2(original_app_path, backup_app_path)
        print(f"✓ Original app.py backed up to {backup_app_path}")
    else:
        print("⚠ Original app.py not found")
    
    # Step 5: Replace app.py with migrated version
    print("\n🔄 Step 5: Replacing app.py with migrated version...")
    migrated_app_path = "migrated_app.py"
    
    if os.path.exists(migrated_app_path):
        shutil.copy2(migrated_app_path, original_app_path)
        print("✓ app.py replaced with migrated version")
    else:
        print("❌ migrated_app.py not found!")
        return False
    
    # Step 6: Test the migration
    print("\n🧪 Step 6: Testing the migration...")
    
    # Test API Gateway
    try:
        response = requests.get("http://localhost:5000/health", timeout=10)
        if response.status_code == 200:
            print("✓ API Gateway is responding")
        else:
            print("❌ API Gateway health check failed")
            return False
    except Exception as e:
        print(f"❌ API Gateway test failed: {str(e)}")
        return False
    
    # Test recommendation service through API Gateway
    try:
        test_data = {
            "school": "Test School",
            "current_grade": "10",
            "learning_goals": "Test Goals",
            "favorite_subjects": "Math",
            "preferred_learning_method": "Online"
        }
        response = requests.post("http://localhost:5000/recommendations/generate", 
                               json=test_data, timeout=30)
        if response.status_code == 200:
            print("✓ Recommendation service is working through API Gateway")
        else:
            print(f"⚠ Recommendation service test returned status {response.status_code}")
    except Exception as e:
        print(f"⚠ Recommendation service test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test your application at http://localhost:5000")
    print("2. Monitor services with: docker-compose logs -f")
    print("3. Check service health: curl http://localhost:5000/health")
    print("4. If issues occur, restore from backup: cp app_monolith_backup.py app.py")
    print("\n🔧 Useful commands:")
    print("  docker-compose ps                    # Check service status")
    print("  docker-compose logs -f [service]     # View logs")
    print("  docker-compose restart [service]     # Restart service")
    print("  docker-compose down                  # Stop all services")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
