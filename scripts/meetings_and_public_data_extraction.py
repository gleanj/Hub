#!/usr/bin/env python3
"""
Deep extraction from meetings page and other public resources
Looking for ANY contact data, especially firstname
"""

import requests
import json
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

TARGET_PORTAL = '46962361'

print("="*80)
print("MEETINGS PAGE & PUBLIC DATA EXTRACTION")
print("="*80)

findings = []

# ============================================================================
# 1. DEEP MEETINGS PAGE ANALYSIS
# ============================================================================

print("\n[1] ANALYZING MEETINGS PAGE")
print("="*80)

meetings_url = f'https://meetings.hubspot.com/p/{TARGET_PORTAL}'

r = requests.get(meetings_url, verify=False, timeout=15)

print(f"URL: {meetings_url}")
print(f"Status: {r.status_code}")
print(f"Size: {len(r.text)} bytes")

if r.status_code == 200:
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')

    # Extract all scripts
    print("\n[*] Analyzing JavaScript bundles...")

    scripts = soup.find_all('script', {'src': True})
    print(f"Found {len(scripts)} external scripts")

    # Download and analyze each script
    for i, script in enumerate(scripts[:10], 1):
        src = script.get('src')
        if not src.startswith('http'):
            src = 'https:' + src if src.startswith('//') else 'https://meetings.hubspot.com' + src

        print(f"\n  [{i}] {src[:80]}...")

        try:
            script_r = requests.get(src, verify=False, timeout=10)
            if script_r.status_code == 200:
                script_text = script_r.text

                # Look for contact data patterns
                patterns = {
                    'firstname': r'firstname["\']?\s*[:=]\s*["\']([^"\']{2,50})["\']',
                    'email': r'email["\']?\s*[:=]\s*["\']([^"\'@]+@[^"\']+)["\']',
                    'name': r'["\']name["\']?\s*[:=]\s*["\']([^"\']{2,50})["\']',
                    'contact': r'contact["\']?\s*[:=]\s*["\']([^"\']{2,100})["\']',
                    'super_secret': r'super_secret["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                }

                for key, pattern in patterns.items():
                    matches = re.findall(pattern, script_text, re.IGNORECASE)
                    if matches:
                        print(f"      Found {key}: {matches[:5]}")

                        for match in matches:
                            # Filter out common false positives
                            if key == 'firstname' and len(match) > 2 and match not in ['text', 'name', 'value', 'string', 'field']:
                                print(f"        *** POTENTIAL FIRSTNAME: {match} ***")
                                findings.append({
                                    'source': 'meetings_js',
                                    'type': 'firstname',
                                    'value': match,
                                    'script': src
                                })

                # Look for API endpoint calls
                api_calls = re.findall(r'(https?://[^\s"\'<>]+api[^\s"\'<>]+)', script_text)
                if api_calls:
                    print(f"      API calls: {len(api_calls)} found")
                    for api in set(api_calls[:5]):
                        print(f"        {api}")

        except Exception as e:
            print(f"      Error: {str(e)[:60]}")

    # Extract inline scripts
    print("\n[*] Analyzing inline scripts...")

    inline_scripts = soup.find_all('script', {'src': False})

    for script in inline_scripts:
        if script.string:
            script_text = script.string

            # Look for firstname
            if 'firstname' in script_text.lower():
                firstname_matches = re.findall(r'firstname["\']?\s*[:=]\s*["\']([^"\']+)["\']', script_text, re.I)
                for match in firstname_matches:
                    if len(match) > 2 and match not in ['text', 'name', 'value']:
                        print(f"    *** FIRSTNAME in inline script: {match} ***")
                        findings.append({
                            'source': 'meetings_inline_js',
                            'type': 'firstname',
                            'value': match
                        })

            # Look for meeting/user data
            if any(term in script_text.lower() for term in ['meeting', 'user', 'owner', 'contact']):
                # Extract JSON objects
                json_pattern = r'\{[^{}]*"(name|firstname|email|owner)"[^{}]*\}'
                json_matches = re.findall(json_pattern, script_text, re.IGNORECASE)
                if json_matches:
                    print(f"    Found data structures: {len(json_matches)}")

# ============================================================================
# 2. CHECK FOR PUBLIC MEETING LINKS
# ============================================================================

print("\n" + "="*80)
print("[2] CHECKING FOR PUBLIC MEETING LINKS")
print("="*80)

# Common meeting link patterns
meeting_slugs = [
    '',  # Root
    'demo',
    'sales',
    'support',
    'consultation',
    'meeting',
    'call',
    'chat',
    'discovery',
    'onboarding',
]

for slug in meeting_slugs:
    url = f'https://meetings.hubspot.com/{slug}' if slug else meetings_url

    try:
        r = requests.get(url, verify=False, timeout=5)

        if r.status_code == 200 and len(r.text) > 1000:
            print(f"\n  Found: {url}")

            # Check for owner/contact information
            if any(term in r.text.lower() for term in ['firstname', 'owner', 'rep', 'agent']):
                print(f"    Contains contact-related data!")

                # Look for names
                name_patterns = [
                    r'owner["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'rep["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'agent["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                ]

                for pattern in name_patterns:
                    matches = re.findall(pattern, r.text, re.IGNORECASE)
                    if matches:
                        print(f"    Matches: {matches[:3]}")
    except:
        pass

# ============================================================================
# 3. CHECK FOR PUBLIC LISTS / SEGMENTS
# ============================================================================

print("\n" + "="*80)
print("[3] CHECKING FOR PUBLIC CONTACT LISTS")
print("="*80)

list_urls = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists/public',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/lists/1',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/list/view/all',
    f'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?portalId={TARGET_PORTAL}',
]

for url in list_urls:
    try:
        r = requests.get(url, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  Accessible: {url}")

            if 'firstname' in r.text.lower() or 'super_secret' in r.text.lower():
                print(f"    *** Contains contact data! ***")
                print(f"    Response: {r.text[:500]}")

                findings.append({
                    'source': 'public_list',
                    'url': url,
                    'response': r.text[:1000]
                })
    except:
        pass

# ============================================================================
# 4. CHECK FOR PUBLIC PAGES / BLOG
# ============================================================================

print("\n" + "="*80)
print("[4] CHECKING FOR PUBLIC PAGES")
print("="*80)

public_page_patterns = [
    f'https://{TARGET_PORTAL}.hubspot.com',
    f'https://www.{TARGET_PORTAL}.com',
    f'https://blog.{TARGET_PORTAL}.com',
    f'https://{TARGET_PORTAL}.hs-sites.com',
    f'https://{TARGET_PORTAL}.hubspotpagebuilder.com',
    f'https://pages.{TARGET_PORTAL}.com',
]

for url in public_page_patterns:
    try:
        r = requests.get(url, verify=False, timeout=5, allow_redirects=True)

        if r.status_code == 200:
            print(f"\n  Found site: {url}")
            print(f"    Redirected to: {r.url}")

            # Check for author/contact info
            soup = BeautifulSoup(r.text, 'html.parser')

            # Look for author meta tags
            author_meta = soup.find('meta', {'name': 'author'})
            if author_meta:
                print(f"    Author: {author_meta.get('content')}")

            # Look for contact information
            if 'contact' in r.text.lower() or 'firstname' in r.text.lower():
                print(f"    Contains contact-related content")

                # Extract email addresses
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
                if emails:
                    print(f"    Emails found: {emails[:3]}")
    except:
        pass

# ============================================================================
# 5. CHECK ROBOTS.TXT AND SITEMAP
# ============================================================================

print("\n" + "="*80)
print("[5] CHECKING ROBOTS.TXT AND SITEMAP")
print("="*80)

robots_urls = [
    f'https://meetings.hubspot.com/robots.txt',
    f'https://{TARGET_PORTAL}.hs-sites.com/robots.txt',
]

for url in robots_urls:
    try:
        r = requests.get(url, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  Robots.txt: {url}")
            print(f"  Content:\n{r.text[:500]}")

            # Look for sitemap
            sitemap_matches = re.findall(r'Sitemap:\s*(.+)', r.text)
            for sitemap_url in sitemap_matches:
                print(f"\n  Sitemap found: {sitemap_url.strip()}")

                try:
                    sitemap_r = requests.get(sitemap_url.strip(), verify=False, timeout=5)
                    if sitemap_r.status_code == 200:
                        print(f"  Sitemap accessible!")

                        # Parse sitemap for URLs
                        urls = re.findall(r'<loc>(.+?)</loc>', sitemap_r.text)
                        print(f"  URLs found: {len(urls)}")

                        for sitemap_url_entry in urls[:10]:
                            print(f"    {sitemap_url_entry}")
                except:
                    pass
    except:
        pass

# ============================================================================
# 6. CHECK FOR CALENDAR/BOOKING API
# ============================================================================

print("\n" + "="*80)
print("[6] CHECKING CALENDAR/BOOKING APIS")
print("="*80)

calendar_urls = [
    f'https://api.hubapi.com/meetings/v1/meetings/public/{TARGET_PORTAL}',
    f'https://api.hubapi.com/calendar/v1/events?portalId={TARGET_PORTAL}',
    f'https://meetings.hubspot.com/api/public/v1/portals/{TARGET_PORTAL}/meetings',
    f'https://meetings.hubspot.com/api/v1/portals/{TARGET_PORTAL}/settings',
]

for url in calendar_urls:
    try:
        r = requests.get(url, verify=False, timeout=5)

        print(f"\n  {url[:70]}")
        print(f"    Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"    Data: {json.dumps(data, indent=2)[:400]}")

                if 'firstname' in json.dumps(data).lower() or 'owner' in json.dumps(data).lower():
                    print(f"    *** Contains contact data! ***")
                    findings.append({
                        'source': 'calendar_api',
                        'url': url,
                        'data': data
                    })
            except:
                print(f"    Response: {r.text[:200]}")
    except:
        pass

print("\n" + "="*80)
print("PUBLIC DATA EXTRACTION COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL DATA POINTS! ***\n")

    for finding in findings:
        print(f"\n{finding.get('source')}:")
        print(f"  {json.dumps(finding, indent=2)[:500]}")

        # Check if we found the firstname
        if finding.get('type') == 'firstname':
            print("\n" + "="*80)
            print("*** POTENTIAL CTF FLAG - FIRSTNAME FOUND! ***")
            print("="*80)
            print(f"Source: {finding.get('source')}")
            print(f"Value: {finding.get('value')}")

            with open('/home/user/Hub/findings/POTENTIAL_CTF_FLAG.json', 'w') as f:
                json.dump(finding, f, indent=2)

    with open('/home/user/Hub/findings/public_data_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("\nSaved: findings/public_data_findings.json")
else:
    print("\nNo contact data found in public resources.")
