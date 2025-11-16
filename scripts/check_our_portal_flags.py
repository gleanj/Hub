#!/usr/bin/env python3
"""
Check if the CTF flag might actually be in OUR portal (50708459)
Maybe we're overthinking this - the contact with super_secret in our portal might BE the answer
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
OUR_PORTAL = '50708459'
TARGET_PORTAL = '46962361'

print("="*80)
print("CHECKING IF THE FLAG IS IN OUR PORTAL (50708459)")
print("="*80)

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# We know contact 175137521012 has super_secret
contact_id = '175137521012'

print(f"\n[*] Getting contact {contact_id} from OUR portal...")

fetch_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=firstname,super_secret,email,lastname,company'

r = requests.get(fetch_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

if r.status_code == 200:
    data = r.json()

    print(f"\n{'='*80}")
    print("CONTACT DATA:")
    print('='*80)
    print(json.dumps(data, indent=2))

    props = data.get('properties', {})

    print(f"\n{'='*80}")
    print("KEY PROPERTIES:")
    print('='*80)
    print(f"Contact ID: {contact_id}")
    print(f"Portal: {OUR_PORTAL}")
    print(f"Email: {props.get('email', 'N/A')}")
    print(f"Firstname: {props.get('firstname', 'N/A')}")
    print(f"Super Secret: {props.get('super_secret', 'N/A')}")
    print(f"Lastname: {props.get('lastname', 'N/A')}")
    print(f"Company: {props.get('company', 'N/A')}")

    # Check if this IS the flag
    firstname = props.get('firstname', '')
    super_secret = props.get('super_secret', '')

    if 'FLAG{' in firstname or 'FLAG{' in super_secret:
        print(f"\n{'='*80}")
        print("*** THIS APPEARS TO BE A TEST FLAG! ***")
        print('='*80)
        print(f"\nThese values contain 'FLAG{{' which suggests they're test data.")
        print(f"The real CTF flag is probably in portal {TARGET_PORTAL}.")
        print(f"But we cannot access that portal without app installation.")

    # Save all contact data
    with open('/home/user/Hub/OUR_PORTAL_CONTACT_DATA.json', 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nSaved full contact data to: OUR_PORTAL_CONTACT_DATA.json")

else:
    print(f"Error: {r.status_code}")
    print(f"Response: {r.text[:500]}")

# Check ALL contacts with super_secret to see if any might be the real flag
print(f"\n{'='*80}")
print("CHECKING ALL CONTACTS WITH super_secret PROPERTY")
print('='*80)

search_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

payload = {
    'filterGroups': [{
        'filters': [{
            'propertyName': 'super_secret',
            'operator': 'HAS_PROPERTY'
        }]
    }],
    'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
    'limit': 100
}

r = requests.post(search_url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

if r.status_code == 200:
    data = r.json()
    results = data.get('results', [])

    print(f"\nFound {len(results)} contacts with super_secret property:\n")

    for i, contact in enumerate(results, 1):
        props = contact.get('properties', {})

        print(f"{i}. Contact {contact.get('id')}:")
        print(f"   Firstname: {props.get('firstname', 'N/A')}")
        print(f"   Super_secret: {props.get('super_secret', 'N/A')}")
        print(f"   Email: {props.get('email', 'N/A')}")
        print()

print(f"\n{'='*80}")
print("ANALYSIS")
print('='*80)

print(f"""
Current Situation:
1. We have full access to portal {OUR_PORTAL}
2. We found test flags: FLAG{{test_first_name}} and FLAG{{test_super_secret}}
3. We CANNOT access portal {TARGET_PORTAL} (app not installed)

Possible Scenarios:
A) The test flags in our portal ARE the answer (seems unlikely)
B) The real flags are in portal {TARGET_PORTAL} (cannot access)
C) We're missing something about the challenge setup
D) We need to find a way to install the app on portal {TARGET_PORTAL}

Next Steps:
- Review the ORIGINAL CTF challenge description carefully
- Check if there's any mention of portal {TARGET_PORTAL} vs {OUR_PORTAL}
- Look for OAuth installation URLs
- Search for leaked credentials for portal {TARGET_PORTAL}
""")
