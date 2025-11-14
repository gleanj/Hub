#!/usr/bin/env python3
"""
Investigate associations API 207 responses
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'
CONTACT_ID = '1'

print("="*80)
print("INVESTIGATING ASSOCIATIONS API")
print("="*80)

# Try different association types
association_tests = [
    ('companies', '0-1', '0-2'),
    ('deals', '0-1', '0-3'),
    ('tickets', '0-1', '0-5'),
    ('line_items', '0-1', '0-8'),
    ('notes', '0-1', '0-4'),
    ('tasks', '0-1', '0-27'),
    ('meetings', '0-1', '0-19'),
    ('calls', '0-1', '0-18'),
    ('emails', '0-1', '0-19'),
]

for obj_name, from_type, to_type in association_tests:
    print(f"\n{'='*80}")
    print(f"TESTING {obj_name.upper()} ASSOCIATIONS")
    print('='*80)

    url = f'https://api.hubapi.com/crm/v4/associations/{from_type}/{to_type}/batch/read'

    payload = {'inputs': [{'id': CONTACT_ID}]}

    try:
        r = requests.post(url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"URL: {url}")
        print(f"Status: {r.status_code}")
        print(f"Payload: {json.dumps(payload)}")

        if r.status_code in [200, 207]:
            try:
                data = r.json()
                print(f"\nFull Response:")
                print(json.dumps(data, indent=2))

                # Check for errors or successes
                if 'results' in data:
                    print(f"\nResults: {len(data['results'])} items")

                    for result in data['results']:
                        print(f"\n  Result: {json.dumps(result, indent=2)}")

                if 'errors' in data:
                    print(f"\nErrors: {len(data['errors'])} items")

                    for error in data['errors']:
                        print(f"\n  Error: {json.dumps(error, indent=2)}")

                # If no data, it might just mean contact has no associations of this type
                if not data.get('results') and not data.get('errors'):
                    print(f"\nNo {obj_name} associated with contact {CONTACT_ID}")

            except Exception as e:
                print(f"JSON Parse Error: {e}")
                print(f"Raw response: {r.text[:500]}")

        elif r.status_code == 400:
            try:
                error = r.json()
                print(f"\nError: {json.dumps(error, indent=2)}")
            except:
                print(f"Error text: {r.text[:300]}")

    except Exception as e:
        print(f"Request failed: {e}")

# Also try the search API with different filters
print(f"\n{'='*80}")
print("TRYING SEARCH API WITH CONTACT FILTER")
print('='*80)

search_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

# Try to search for contact 1 specifically
search_payloads = [
    {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'hs_object_id',
                'operator': 'EQ',
                'value': '1'
            }]
        }],
        'properties': ['firstname', 'super_secret', 'email'],
        'portalId': TARGET_PORTAL
    },
    {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'vid',
                'operator': 'EQ',
                'value': '1'
            }]
        }],
        'properties': ['firstname', 'super_secret', 'email'],
        'portalId': TARGET_PORTAL
    },
]

for i, payload in enumerate(search_payloads, 1):
    print(f"\nSearch Payload {i}:")
    print(json.dumps(payload, indent=2))

    try:
        r = requests.post(search_url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"\nResults:")
                print(json.dumps(data, indent=2))

                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n*** CONTAINS super_secret! ***")
            except:
                print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
