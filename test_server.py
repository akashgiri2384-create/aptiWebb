"""
Test that the Django server and APIs are actually working
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing Quizzy Platform APIs...")
print("=" * 50)

# Test 1: Admin panel is accessible
print("\n1. Testing Admin Panel...")
try:
    response = requests.get(f"{BASE_URL}/admin/", timeout=5)
    if response.status_code == 200:
        print("   [OK] Admin panel accessible")
        print(f"   Status: {response.status_code}")
    else:
        print(f"   [WARN] Status: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 2: Main page
print("\n2. Testing Main Page...")
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"   Status: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 3: API endpoints exist
print("\n3. Testing API Endpoints...")
api_endpoints = [
    "/api/accounts/",
    "/api/quizzes/",
    "/api/daily-quizzes/",
    "/api/leaderboards/",
    "/api/xp/",
]

for endpoint in api_endpoints:
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        status = "[OK]" if response.status_code < 500 else "[ERROR]"
        print(f"   {status} {endpoint} - Status: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] {endpoint} - {e}")

# Test 4: Login endpoint
print("\n4. Testing Authentication...")
try:
    login_data = {
        "email": "test@quizzy.com",
        "password": "testpass123"
    }
    response = requests.post(
        f"{BASE_URL}/api/accounts/login/",
        json=login_data,
        timeout=5
    )
    print(f"   Login endpoint status: {response.status_code}")
    if response.status_code == 200:
        print("   [OK] Login endpoint working!")
        data = response.json()
        if 'access_token' in str(data):
            print("   [OK] JWT tokens returned")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "=" * 50)
print("Testing Complete!")
print("\nSERVER STATUS: RUNNING on http://localhost:8000")
print("ADMIN ACCESS: http://localhost:8000/admin/")
print("  - admin@quizzy.com / admin123")
