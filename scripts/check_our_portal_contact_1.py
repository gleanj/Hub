#!/usr/bin/env python3
"""
Check if contact 1 exists in OUR portal (50708459) instead of target portal
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
OUR_PORTAL = '50708459'

print("="*80)
print("CHECKING CONTACT 1 IN OUR PORTAL")
print("="*80)

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# Try to get contact 1 from OUR portal
contact_urls = [
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={OUR_PORTAL}&properties=firstname,super_secret,email',
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?properties=firstname,super_secret,email',  # No portalId (should use token's portal)
    f'https://app.hubspot.com/contacts/{OUR_PORTAL}/contact/1',
]

for url in contact_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"\n  *** CONTACT 1 FOUND IN OUR PORTAL! ***")

            try:
                data = r.json()
                print(f"  Response:")
                print(json.dumps(data, indent=2))

                # Check for super_secret
                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n  *** CONTAINS super_secret! ***")

                    # Extract the value
                    props = data.get('properties', {})
                    if 'super_secret' in props:
                        print(f"\n  Firstname: {props.get('firstname', 'N/A')}")
                        print(f"  Super Secret: {props.get('super_secret', 'N/A')}")

                        # Save it
                        with open('/home/user/Hub/findings/CONTACT_1_OUR_PORTAL.json', 'w') as f:
                            json.dump(data, f, indent=2)

                        print(f"\n  Saved to findings/CONTACT_1_OUR_PORTAL.json")
            except:
                # HTML response
                if len(r.text) > 1000 and ('firstname' in r.text.lower() or 'super_secret' in r.text.lower()):
                    print(f"  Size: {len(r.text)} bytes")
                    print(f"  Contains contact keywords")
    except:
        pass

# Try batch read with just contact 1
print(f"\n{'='*80}")
print("BATCH READ FOR CONTACT 1 IN OUR PORTAL")
print('='*80)

batch_url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/read'

payload = {
    'inputs': [{'id': '1'}],
    'properties': ['firstname', 'super_secret', 'email']
}

try:
    r = requests.post(batch_url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

    print(f"Status: {r.status_code}")

    if r.status_code in [200, 207]:
        data = r.json()
        print(f"\nResponse:")
        print(json.dumps(data, indent=2))

        if 'results' in data and data['results']:
            print(f"\n*** GOT RESULTS! ***")

            for result in data['results']:
                if 'properties' in result:
                    props = result['properties']

                    if 'super_secret' in props:
                        print(f"\nFirstname: {props.get('firstname', 'N/A')}")
                        print(f"Super Secret: {props.get('super_secret', 'N/A')}")

                        print(f"\n{'='*80}")
                        print("*** CONTACT 1 WITH super_secret FOUND IN OUR PORTAL! ***")
                        print('='*80)

                        # Check the URL in the result
                        if 'url' in result:
                            print(f"URL: {result['url']}")
except:
    pass

# Try search for contact with ID 1 in our portal
print(f"\n{'='*80}")
print("SEARCH FOR CONTACT ID 1")
print('='*80)

search_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

search_payload = {
    'filterGroups': [{
        'filters': [{
            'propertyName': 'hs_object_id',
            'operator': 'EQ',
            'value': '1'
        }]
    }],
    'properties': ['firstname', 'super_secret', 'email']
}

try:
    r = requests.post(search_url, json=search_payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

    print(f"Status: {r.status_code}")

    if r.status_code == 200:
        data = r.json()
        print(f"\nResponse:")
        print(json.dumps(data, indent=2))

        if data.get('total', 0) > 0:
            print(f"\n*** FOUND {data['total']} CONTACTS! ***")
except:
    pass
