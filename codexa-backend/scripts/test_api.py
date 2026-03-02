#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://unidiomatically-ritzier-clarisa.ngrok-free.dev"

def test_api():
    # Login
    print("🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "rajp58425@gmail.com",
            "password": "Test@12345"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    tokens = response.json()
    id_token = tokens['id_token']
    print("✅ Got ID token!")
    print()
    
    # Test /me endpoint
    print("👤 Testing /me endpoint...")
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {id_token}"}
    )
    print(json.dumps(response.json(), indent=2))
    print()
    
    # Test guidance endpoint
    print("💡 Testing guidance endpoint...")
    response = requests.post(
        f"{BASE_URL}/api/guidance",
        headers={
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json"
        },
        json={
            "user_question": "How do I solve Fibonacci?",
            "code_context": "def fib(n):\n    a,b=0,1\n    for _ in range(n):\n        a,b=b,a+b\n    return a",
            "ast_context": {},
            "guidance_level": 1
        }
    )
    print(json.dumps(response.json(), indent=2))
    print()
    
    # Test health endpoint
    print("📊 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), indent=2))
    print()
    
    # Test learning paths
    print("🎓 Testing learning paths...")
    response = requests.get(
        f"{BASE_URL}/api/learning-paths",
        headers={"Authorization": f"Bearer {id_token}"}
    )
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_api()