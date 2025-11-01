#!/usr/bin/env python3
"""
Script to set up microservices by copying necessary files
"""
import os
import shutil
import sys
from pathlib import Path

def copy_file_if_exists(src, dst):
    """Copy file if source exists"""
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"✓ Copied {src} to {dst}")
    else:
        print(f"⚠ Source file not found: {src}")

def copy_directory_if_exists(src, dst):
    """Copy directory if source exists"""
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"✓ Copied directory {src} to {dst}")
    else:
        print(f"⚠ Source directory not found: {src}")

def setup_recommendation_service():
    """Set up recommendation service with necessary files"""
    print("Setting up Recommendation Service...")
    
    # Copy models directory
    copy_directory_if_exists("../models", "recommendation_service/models")
    
    # Copy data directory
    copy_directory_if_exists("../data", "recommendation_service/data")
    
    # Copy checkpoints if exists
    copy_directory_if_exists("../checkpoints", "recommendation_service/checkpoints")
    
    # Copy bruteforce data if exists
    copy_file_if_exists("../bruteforce_data.npz", "recommendation_service/bruteforce_data.npz")
    
    print("Recommendation Service setup complete!")

def setup_study_plan_service():
    """Set up study plan service"""
    print("Setting up Study Plan Service...")
    print("Study Plan Service setup complete!")

def setup_feedback_service():
    """Set up feedback service"""
    print("Setting up Feedback Service...")
    print("Feedback Service setup complete!")

def setup_api_gateway():
    """Set up API gateway"""
    print("Setting up API Gateway...")
    print("API Gateway setup complete!")

def main():
    """Main setup function"""
    print("🚀 Setting up Microservices...")
    print("=" * 50)
    
    # Change to microservices directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Set up each service
    setup_recommendation_service()
    print()
    setup_study_plan_service()
    print()
    setup_feedback_service()
    print()
    setup_api_gateway()
    print()
    
    print("=" * 50)
    print("✅ All microservices setup complete!")
    print()
    print("To start the services, run:")
    print("  docker-compose up --build")
    print()
    print("To start in background:")
    print("  docker-compose up -d --build")

if __name__ == "__main__":
    main()
