#!/usr/bin/env python3
"""
List all portals accessible to this account
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

csrf = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES).group(1) if 'hubspotapi-csrf=' in SESSION_COOKIES else ''

print("="*80)
print("Listing Accessible Portals")
print("="*80)

headers_session = {
    'Cookie': SESSION_COOKIES,
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://app.hubspot.com/',
    'Origin': 'https://app.hubspot.com',
    'X-HubSpot-CSRF-hubspotapi': csrf,
}

headers_token = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

# ============================================================================
# TRY TO LIST PORTALS
# ============================================================================

print("\n[*] Trying to list accessible portals...")

portal_list_endpoints = [
    'https://app.hubspot.com/api/navigation/v3/user/portals',
    'https://app.hubspot.com/api/navigation/v1/user/portals',
    'https://app.hubspot.com/api/users/v1/app/me/portals',
    'https://app.hubspot.com/api/portals/v1/list',
    'https://app.hubspot.com/api/settings/v1/portals',
    'https://app.hubspot.com/api/account/v1/portals',
    'https://api.hubapi.com/account-info/v3/api-usage',
    'https://api.hubapi.com/integrations/v1/me',
]

found_portals = []

for url in portal_list_endpoints:
    try:
        # Try with session
        r = requests.get(url, headers=headers_session, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  *** SUCCESS: {url.split('.com')[1]}")
            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)[:500]}")

                # Look for portal IDs
                data_str = json.dumps(data)
                if TARGET_PORTAL in data_str:
                    print(f"\n  ========================================")
                    print(f"  *** TARGET PORTAL {TARGET_PORTAL} FOUND IN RESPONSE! ***")
                    print(f"  ========================================")

                found_portals.append({
                    'endpoint': url,
                    'data': data
                })

            except:
                print(f"  Response (not JSON): {r.text[:200]}")

        # Also try with token
        r2 = requests.get(url, headers=headers_token, verify=False, timeout=5)
        if r2.status_code == 200 and r.status_code != 200:
            print(f"\n  Works with token: {url.split('.com')[1]}")
            try:
                data = r2.json()
                print(f"  Data: {json.dumps(data, indent=2)[:300]}")

                if TARGET_PORTAL in json.dumps(data):
                    print(f"  *** TARGET PORTAL FOUND! ***")

            except:
                pass

    except:
        pass

# ============================================================================
# GET CURRENT USER INFO
# ============================================================================

print("\n[*] Getting current user info...")

user_endpoints = [
    'https://app.hubspot.com/api/users/v1/app/me',
    'https://app.hubspot.com/api/user/v1/me',
    'https://app.hubspot.com/api/navigation/v3/user/me',
]

for url in user_endpoints:
    try:
        r = requests.get(url, headers=headers_session, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  User info from: {url.split('.com')[1]}")
            try:
                data = r.json()
                print(f"  Data: {json.dumps(data, indent=2)[:1000]}")

                # Check for portal access info
                if 'portal' in str(data).lower() and TARGET_PORTAL in json.dumps(data):
                    print(f"\n  *** TARGET PORTAL IN USER DATA! ***")

            except:
                pass
    except:
        pass

# ============================================================================
# TRY ACCOUNT INFO WITH TOKEN
# ============================================================================

print("\n[*] Checking token account info...")

try:
    r = requests.get(
        'https://api.hubapi.com/account-info/v3/details',
        headers=headers_token,
        verify=False,
        timeout=5
    )

    print(f"\nAccount details: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2))

        portal_id = data.get('portalId')
        print(f"\nToken is associated with portal: {portal_id}")

        if portal_id == TARGET_PORTAL:
            print(f"*** TOKEN IS ALREADY FOR TARGET PORTAL! ***")
        else:
            print(f"Token is for portal {portal_id}, not {TARGET_PORTAL}")

except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("Portal Access Summary")
print("="*80)

if found_portals:
    print(f"\nFound {len(found_portals)} portal listing endpoints")

    for portal in found_portals:
        print(f"\nEndpoint: {portal['endpoint']}")
        print(f"Data: {json.dumps(portal['data'], indent=2)[:300]}")
else:
    print("\nCould not list accessible portals.")
    print("This means either:")
    print("  1. The account only has access to one portal")
    print("  2. Portal listing APIs require different authentication")
    print("  3. We haven't found the right endpoint")

print("\n" + "="*80)
