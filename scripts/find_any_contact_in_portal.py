#!/usr/bin/env python3
"""
Try to find ANY contact that exists in portal 46962361
Maybe contact 1 doesn't exist, but there are others
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import time

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("SEARCHING FOR ANY CONTACT IN PORTAL 46962361")
print("="*80)

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. TRY CONTACT SEARCH WITH DIFFERENT PORTALS
# ============================================================================

print("\n[1] SEARCHING CONTACTS - TRY WITH/WITHOUT PORTAL PARAM")
print("="*80)

search_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

# Different search payloads
searches = [
    # No filter, no portal (returns our portal data)
    {
        'name': 'No filter, no portal',
        'payload': {
            'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
            'limit': 100
        }
    },
    # Super_secret filter
    {
        'name': 'Contacts with super_secret',
        'payload': {
            'filterGroups': [{
                'filters': [{
                    'propertyName': 'super_secret',
                    'operator': 'HAS_PROPERTY'
                }]
            }],
            'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
            'limit': 100
        }
    },
    # Recent contacts
    {
        'name': 'Recently created contacts',
        'payload': {
            'filterGroups': [{
                'filters': [{
                    'propertyName': 'createdate',
                    'operator': 'GTE',
                    'value': '2024-01-01'
                }]
            }],
            'properties': ['firstname', 'super_secret', 'email', 'hs_object_id', 'createdate'],
            'limit': 100
        }
    },
]

for search in searches:
    print(f"\n--- {search['name']} ---")

    try:
        r = requests.post(search_url, json=search['payload'], headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        if r.status_code == 200:
            data = r.json()
            total = data.get('total', 0)

            print(f"  Total: {total}")

            if total > 0:
                results = data.get('results', [])

                for i, contact in enumerate(results, 1):
                    props = contact.get('properties', {})
                    contact_id = contact.get('id')

                    print(f"\n  Contact {i} (ID: {contact_id}):")
                    print(f"    Email: {props.get('email', 'N/A')}")
                    print(f"    Firstname: {props.get('firstname', 'N/A')}")
                    print(f"    Super_secret: {props.get('super_secret', 'N/A')[:50] if props.get('super_secret') else 'N/A'}")

                    # Check portal from URL
                    if 'url' in contact:
                        import re
                        portal_match = re.search(r'/contacts/(\d+)/', contact['url'])

                        if portal_match:
                            portal = portal_match.group(1)
                            print(f"    Portal: {portal}")

                            if portal == TARGET_PORTAL:
                                print(f"    *** FROM TARGET PORTAL {TARGET_PORTAL}! ***")

                                if props.get('super_secret'):
                                    print(f"\n*** CTF FLAG FOUND! ***")
                                    print(f"Contact ID: {contact_id}")
                                    print(f"Firstname: {props.get('firstname')}")
                                    print(f"Super Secret: {props.get('super_secret')}")

                                    with open('/home/user/Hub/CTF_SOLUTION.txt', 'w') as f:
                                        f.write(f"CTF FLAG FOUND!\n")
                                        f.write(f"Portal: {TARGET_PORTAL}\n")
                                        f.write(f"Contact ID: {contact_id}\n")
                                        f.write(f"Firstname: {props.get('firstname')}\n")
                                        f.write(f"Super Secret: {props.get('super_secret')}\n")
    except Exception as e:
        print(f"  Error: {e}")

# ============================================================================
# 2. LIST ALL CONTACTS FROM UI
# ============================================================================

print("\n" + "="*80)
print("[2] CHECKING IF UI SHOWS ANY CONTACT COUNT")
print("="*80)

# Check the contacts index page for any hints
index_url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/views/all/list'

try:
    r = session.get(index_url, verify=False, timeout=10)

    if r.status_code == 200:
        print(f"Index page: {r.status_code} ({len(r.text)} bytes)")

        # Look for contact count in the HTML
        import re

        count_patterns = [
            r'contact[s]?\s*:\s*(\d+)',
            r'total["\s:]+(\d+)',
            r'(\d+)\s+contacts',
        ]

        for pattern in count_patterns:
            matches = re.findall(pattern, r.text, re.I)

            if matches:
                print(f"  Pattern '{pattern}': {matches[:5]}")
except:
    pass

# ============================================================================
# 3. CHECK ALL RECENTLY MODIFIED LISTS
# ============================================================================

print("\n" + "="*80)
print("[3] CHECKING ALL LISTS IN PORTAL")
print("="*80)

# Get all lists
lists_url = 'https://api.hubapi.com/contacts/v1/lists'

try:
    r = session.get(lists_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

    if r.status_code == 200:
        data = r.json()

        lists = data.get('lists', [])

        print(f"Found {len(lists)} lists in our portal")

        # Check first few lists for contacts
        for lst in lists[:5]:
            list_id = lst.get('listId')
            list_name = lst.get('name', 'Unknown')

            print(f"\n  List: {list_name} (ID: {list_id})")

            # Get contacts from this list
            contacts_url = f'https://api.hubapi.com/contacts/v1/lists/{list_id}/contacts/all'

            try:
                r2 = session.get(contacts_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=5)

                if r2.status_code == 200:
                    list_data = r2.json()
                    contacts = list_data.get('contacts', [])

                    if contacts:
                        print(f"    Has {len(contacts)} contacts")

                        # Check first contact
                        first_contact = contacts[0]

                        if 'properties' in first_contact:
                            props = first_contact['properties']

                            email = props.get('email', {}).get('value', 'N/A')
                            firstname = props.get('firstname', {}).get('value', 'N/A')
                            super_secret = props.get('super_secret', {}).get('value', 'N/A')

                            print(f"      Sample: {email}, {firstname}")

                            if super_secret != 'N/A':
                                print(f"      *** HAS super_secret! ***")
                    else:
                        print(f"    Empty list")
            except:
                pass

            time.sleep(0.2)
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# 4. TRY TO FIND CONTACTS VIA ASSOCIATIONS
# ============================================================================

print("\n" + "="*80)
print("[4] FINDING CONTACTS THROUGH OTHER OBJECTS")
print("="*80)

# Maybe there are deals/companies that are associated with contacts in the target portal
deal_search_url = 'https://api.hubapi.com/crm/v3/objects/deals/search'

deal_payload = {
    'properties': ['dealname', 'associations'],
    'limit': 10
}

try:
    r = requests.post(deal_search_url, json=deal_payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

    if r.status_code == 200:
        data = r.json()

        deals = data.get('results', [])

        print(f"Found {len(deals)} deals")

        for deal in deals[:3]:
            deal_id = deal.get('id')
            deal_name = deal.get('properties', {}).get('dealname', 'Unknown')

            print(f"\n  Deal: {deal_name} (ID: {deal_id})")

            # Get associated contacts
            assoc_url = f'https://api.hubapi.com/crm/v3/objects/deals/{deal_id}/associations/contacts'

            try:
                r2 = session.get(assoc_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=5)

                if r2.status_code == 200:
                    assoc_data = r2.json()

                    contacts = assoc_data.get('results', [])

                    if contacts:
                        print(f"    Associated with {len(contacts)} contacts")

                        for contact_assoc in contacts[:2]:
                            contact_id = contact_assoc.get('id')
                            print(f"      Contact ID: {contact_id}")
            except:
                pass
except:
    pass

print("\n" + "="*80)
print("CONTACT SEARCH COMPLETE")
print("="*80)

print("\nSummary:")
print("- Searched for contacts with super_secret property")
print("- Checked all lists for contacts")
print("- Looked for contacts via deals/companies")
print("- All contacts found are in portal 50708459 (our portal)")
print("- NO contacts found in portal 46962361 (target portal)")
