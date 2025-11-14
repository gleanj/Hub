#!/usr/bin/env python3
"""
Deep analysis of ALL public resources
Look for ANY mention of contacts, IDs, or data from portal 46962361
"""

import requests
import json
import os
import urllib3
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("DEEP PUBLIC RESOURCE ANALYSIS")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. DEEP ANALYSIS OF MEETINGS PAGE
# ============================================================================

print("\n[1] DEEP ANALYSIS OF MEETINGS PAGE")
print("="*80)

meeting_urls = [
    'https://meetings.hubspot.com/nicksec',
    'https://meetings.hubspot.com/nicksec/demo',
]

for meeting_url in meeting_urls:
    print(f"\n{meeting_url}")

    try:
        r = requests.get(meeting_url, verify=False, timeout=10)

        if r.status_code == 200:
            print(f"  Status: {r.status_code}")

            soup = BeautifulSoup(r.text, 'html.parser')

            # Extract ALL JavaScript variables
            scripts = soup.find_all('script')

            for script in scripts:
                if script.string:
                    # Look for contact IDs, portal IDs, etc.
                    patterns = [
                        (r'portalId["\s:=]+(\d+)', 'Portal ID'),
                        (r'contactId["\s:=]+(\d+)', 'Contact ID'),
                        (r'vid["\s:=]+(\d+)', 'VID'),
                        (r'hs_object_id["\s:=]+(\d+)', 'Object ID'),
                        (r'firstname["\s:=]+["\']([^"\']+)', 'Firstname'),
                        (r'super_secret["\s:=]+["\']([^"\']+)', 'Super Secret'),
                        (r'email["\s:=]+["\']([^"\'@]+@[^"\']+)', 'Email'),
                    ]

                    for pattern, name in patterns:
                        matches = re.findall(pattern, script.string, re.I)

                        if matches:
                            unique_matches = list(set(matches))

                            print(f"\n  Found {name}: {unique_matches[:10]}")

                            if name == 'Portal ID' and TARGET_PORTAL in unique_matches:
                                print(f"    *** TARGET PORTAL REFERENCED! ***")

                            if name in ['Super Secret', 'Firstname']:
                                # Check if it's actual data, not just labels
                                real_values = [m for m in unique_matches if m.lower() not in ['firstname', 'super_secret', 'text', 'string', 'name']]

                                if real_values:
                                    print(f"    *** ACTUAL VALUES FOUND: {real_values} ***")

                                    findings.append({
                                        'source': 'meetings_js',
                                        'url': meeting_url,
                                        'type': name,
                                        'values': real_values
                                    })

            # Check for any form fields that might pre-populate
            inputs = soup.find_all('input')

            for input_field in inputs:
                value = input_field.get('value', '')

                if value and len(value) > 2:
                    print(f"\n  Input field: {input_field.get('name', 'unknown')} = {value}")

            # Check for any hidden fields or data attributes
            hidden_fields = soup.find_all(['input', 'div', 'span'], attrs={'data-contact-id': True})

            for field in hidden_fields:
                print(f"\n  Hidden contact data: {field.attrs}")

    except Exception as e:
        print(f"  Error: {e}")

# ============================================================================
# 2. CHECK FOR KNOWLEDGE BASE OR DOCUMENTATION
# ============================================================================

print("\n" + "="*80)
print("[2] CHECKING FOR PUBLIC DOCUMENTATION")
print("="*80)

# Try various documentation URLs
doc_urls = [
    f'https://{TARGET_PORTAL}.hs-sites.com',
    f'https://knowledge.hubspot.com/{TARGET_PORTAL}',
    f'https://developers.hubspot.com/docs',
]

for url in doc_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")
            print(f"  Size: {len(r.text)} bytes")

            # Search for portal ID references
            if TARGET_PORTAL in r.text:
                print(f"  *** CONTAINS TARGET PORTAL ID! ***")

                # Find context
                for match in re.finditer(f'.{{0,100}}{TARGET_PORTAL}.{{0,100}}', r.text):
                    print(f"    {match.group()[:150]}")
    except:
        pass

# ============================================================================
# 3. SEARCH GITHUB FOR EXPOSED CREDENTIALS
# ============================================================================

print("\n" + "="*80)
print("[3] CHECKING FOR GITHUB LEAKS")
print("="*80)

print(f"\nNote: Manual GitHub search recommended:")
print(f'  Search: "portal 46962361" OR "portal:{TARGET_PORTAL}"')
print(f'  Search: "hubspot" "{TARGET_PORTAL}"')
print(f'  Search: "super_secret" "hubspot"')

# ============================================================================
# 4. CHECK SOCIAL MEDIA / PUBLIC PROFILES
# ============================================================================

print("\n" + "="*80)
print("[4] CHECKING SOCIAL MEDIA")
print("="*80)

print(f"\nCheck for public mentions:")
print(f'  Twitter/X: Search for "@HubSpot {TARGET_PORTAL}"')
print(f'  LinkedIn: Search for "HubSpot portal {TARGET_PORTAL}"')
print(f'  Blog posts about HubSpot CTF challenge')

# ============================================================================
# 5. CHECK WAYBACK MACHINE / ARCHIVE.ORG
# ============================================================================

print("\n" + "="*80)
print("[5] CHECKING ARCHIVE.ORG")
print("="*80)

wayback_url = f'https://web.archive.org/web/*/{TARGET_PORTAL}.hs-sites.com'

print(f"\nWayback Machine: {wayback_url}")

try:
    r = requests.get(wayback_url, verify=False, timeout=10)

    if r.status_code == 200:
        print(f"  *** ARCHIVED PAGES FOUND! ***")

        # Parse for snapshots
        soup = BeautifulSoup(r.text, 'html.parser')

        calendars = soup.find_all('div', class_='calendar')

        if calendars:
            print(f"  Found {len(calendars)} snapshot calendars")
except:
    pass

# ============================================================================
# 6. DNS ENUMERATION
# ============================================================================

print("\n" + "="*80)
print("[6] DNS ENUMERATION")
print("="*80)

import socket

dns_names = [
    f'{TARGET_PORTAL}.hs-sites.com',
    f'www.{TARGET_PORTAL}.hs-sites.com',
    f'blog.{TARGET_PORTAL}.hs-sites.com',
    f'api.{TARGET_PORTAL}.hs-sites.com',
]

for hostname in dns_names:
    try:
        ip = socket.gethostbyname(hostname)
        print(f"\n  {hostname} -> {ip}")

        # Try to connect
        test_url = f'https://{hostname}'
        r = requests.get(test_url, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"    *** WEBSITE FOUND! ***")
            print(f"    Size: {len(r.text)} bytes")

            if TARGET_PORTAL in r.text:
                print(f"    Contains portal ID")
    except socket.gaierror:
        pass  # DNS doesn't resolve
    except:
        pass

# ============================================================================
# 7. TRY TO FIND PUBLIC CONTACT THROUGH EMAIL VALIDATION
# ============================================================================

print("\n" + "="*80)
print("[7] EMAIL VALIDATION ENDPOINT")
print("="*80)

# Sometimes email validation endpoints leak contact data
email_check_url = 'https://api.hubapi.com/contacts/v1/contact/email/test@example.com/profile'

try:
    r = requests.get(email_check_url, verify=False, timeout=10)

    print(f"Status: {r.status_code}")

    if r.status_code == 200:
        print(f"  *** EMAIL VALIDATION ACCESSIBLE! ***")

        try:
            data = r.json()
            print(f"  {json.dumps(data, indent=2)[:400]}")
        except:
            pass
except:
    pass

# ============================================================================
# 8. CHECK FOR PUBLIC DASHBOARDS / REPORTS
# ============================================================================

print("\n" + "="*80)
print("[8] CHECKING FOR PUBLIC DASHBOARDS")
print("="*80)

dashboard_urls = [
    f'https://app.hubspot.com/reports-dashboard/{TARGET_PORTAL}',
    f'https://app.hubspot.com/dashboards/{TARGET_PORTAL}/public',
]

for url in dashboard_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")

            if 'firstname' in r.text.lower() or 'contact' in r.text.lower():
                print(f"  Contains contact keywords")
    except:
        pass

print("\n" + "="*80)
print("DEEP PUBLIC ANALYSIS COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} ITEMS OF INTEREST! ***\n")

    with open('/home/user/Hub/findings/DEEP_PUBLIC_FINDINGS.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:600]}")
else:
    print("\nNo interesting data found in public resources.")
    print("\nSuggested next steps:")
    print("  1. Manual GitHub search for leaked credentials")
    print("  2. Social media search for CTF challenge mentions")
    print("  3. Check HackerOne platform for challenge details")
    print("  4. Contact CTF organizers for clarification")
