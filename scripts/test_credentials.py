#!/usr/bin/env python3
"""
Quick test script to verify HubSpot credentials work
"""

import requests
import sys
from config import get_auth_header, has_credentials, HUBSPOT_ACCESS_TOKEN, HUBSPOT_API_KEY

def test_credentials():
    """Test if credentials are valid"""

    if not has_credentials():
        print("[ERROR] No credentials found in .env file")
        return False

    print("[*] Testing HubSpot API credentials...")

    # Try both authentication methods
    tests = []

    if HUBSPOT_API_KEY:
        print(f"\n[*] Test 1: API Key (hapikey parameter)")
        print(f"[*] Using key: {HUBSPOT_API_KEY[:20]}...")
        url1 = f"https://api.hubapi.com/crm/v3/objects/contacts?limit=1&hapikey={HUBSPOT_API_KEY}"
        tests.append(("API Key (hapikey)", requests.get(url1, timeout=10)))

    if HUBSPOT_ACCESS_TOKEN:
        print(f"\n[*] Test 2: Access Token (Bearer)")
        print(f"[*] Using token: {HUBSPOT_ACCESS_TOKEN[:20]}...")
        url2 = "https://api.hubapi.com/crm/v3/objects/contacts?limit=1"
        headers2 = {'Authorization': f'Bearer {HUBSPOT_ACCESS_TOKEN}'}
        tests.append(("Access Token", requests.get(url2, headers=headers2, timeout=10)))

    if not tests:
        print("[ERROR] No credentials to test")
        return False

    # Test all methods
    for method, response in tests:
        print(f"\n[*] {method} - Status: {response.status_code}")

        if response.status_code == 200:
            print(f"[SUCCESS] {method} works!")
            data = response.json()
            print(f"[*] Found {len(data.get('results', []))} contacts")
            return True
        elif response.status_code == 401:
            print(f"[FAIL] {method} - Invalid/Expired")
        else:
            print(f"[FAIL] {method} - Error: {response.status_code}")

        print(f"[*] Response: {response.text[:150]}")

    print("\n[ERROR] All authentication methods failed")
    return False

if __name__ == '__main__':
    try:
        success = test_credentials()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
