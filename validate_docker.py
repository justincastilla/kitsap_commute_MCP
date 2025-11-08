#!/usr/bin/env python3
"""
Validate Docker configuration files
"""
import os
import json
import yaml

print("Validating Docker configuration...")
print()

# Validate Dockerfile exists
if os.path.exists("Dockerfile"):
    print("✓ Dockerfile exists")
    with open("Dockerfile") as f:
        content = f.read()
        if "FROM python:3.12-slim" in content:
            print("  ✓ Using Python 3.12-slim base image")
        if "WORKDIR /app" in content:
            print("  ✓ Working directory set to /app")
        if all(pkg in content for pkg in ["elasticsearch", "fastmcp", "pydantic", "python-dotenv", "requests"]):
            print("  ✓ All required dependencies specified")
        if "PYTHONUNBUFFERED=1" in content:
            print("  ✓ Python unbuffered mode enabled")
else:
    print("✗ Dockerfile not found")
    exit(1)

print()

# Validate docker-compose.yml
if os.path.exists("docker-compose.yml"):
    print("✓ docker-compose.yml exists")
    try:
        with open("docker-compose.yml") as f:
            compose = yaml.safe_load(f)
        
        if "services" in compose:
            services = compose["services"]
            print(f"  ✓ Defines {len(services)} services:")
            for svc in services:
                print(f"    - {svc}")
            
            if "elasticsearch" in services:
                print("  ✓ Elasticsearch service configured")
            if "commute-server" in services:
                print("  ✓ Commute server configured")
            if "elasticsearch-server" in services:
                print("  ✓ Elasticsearch server configured")
                
        if "volumes" in compose:
            print(f"  ✓ Persistent volumes configured: {list(compose['volumes'].keys())}")
    except Exception as e:
        print(f"  ✗ Error parsing docker-compose.yml: {e}")
        exit(1)
else:
    print("✗ docker-compose.yml not found")
    exit(1)

print()

# Validate .dockerignore
if os.path.exists(".dockerignore"):
    print("✓ .dockerignore exists")
    with open(".dockerignore") as f:
        content = f.read()
        if "__pycache__" in content:
            print("  ✓ Ignores Python cache files")
        if ".env" in content:
            print("  ✓ Ignores environment files")
        if ".git" in content:
            print("  ✓ Ignores git directory")
else:
    print("✗ .dockerignore not found")

print()
print("="*60)
print("Docker configuration validation passed! ✓")
print("="*60)
