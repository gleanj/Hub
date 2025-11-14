#!/usr/bin/env python3
import requests
import re
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

pages_to_check = {
    'templates': f'https://app.hubspot.com/templates/{TARGET_PORTAL}/list',
    'workflows': f'https://app.hubspot.com/workflows/{TARGET_PORTAL}/flows',
    'integrations': f'https://app.hubspot.com/integrations/{TARGET_PORTAL}',
    'analytics': f'https://app.hubspot.com/analytics/{TARGET_PORTAL}/reports',
}

for name, url in pages_to_check.items():
    print(f"\n{'='*80}")
    print(f"ANALYZING {name.upper()} PAGE")
    print('='*80)

    r = session.get(url, verify=False, timeout=10)

    if r.status_code == 200:
        # Save HTML
        with open(f'findings/{name}_page.html', 'w') as f:
            f.write(r.text)

        print(f"Status: {r.status_code}")
        print(f"Size: {len(r.text)} bytes")

        # Look for API endpoints in the HTML
        api_patterns = [
            r'https://api\.hubapi\.com/[^\s"\'<>]+',
            r'https://app\.hubspot\.com/api/[^\s"\'<>]+',
            r'/api/[^\s"\'<>]+',
        ]

        all_apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, r.text)
            all_apis.update(matches)

        if all_apis:
            print(f"\nFound {len(all_apis)} API endpoints:")
            for api in sorted(all_apis)[:20]:
                print(f"  {api}")

        # Look for contact data or super_secret
        if 'super_secret' in r.text.lower():
            print(f"\n*** CONTAINS 'super_secret'! ***")

            # Find context
            for match in re.finditer(r'.{0,100}super_secret.{0,100}', r.text, re.I):
                print(f"  {match.group()[:150]}")

        if 'firstname' in r.text.lower() and len(r.text) < 300000:
            # Look for actual values, not just labels
            patterns = [
                r'"firstname"\s*:\s*"([^"]+)"',
                r'"firstname"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, r.text, re.I)
                real_values = [m for m in matches if m.lower() not in ['firstname', 'text', 'string']]

                if real_values:
                    print(f"\n*** FIRSTNAME VALUES FOUND! ***")
                    for val in real_values[:5]:
                        print(f"  {val}")
