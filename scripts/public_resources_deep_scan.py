#!/usr/bin/env python3
"""
Deep scan for publicly accessible HubSpot resources
Forms, landing pages, meetings, knowledge base, etc.
"""

import requests
import json
import os
import re
import urllib3
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()
load_dotenv()

TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("Deep Scan for Public Resources")
print("="*80)
print(f"\nTarget Portal: {TARGET_PORTAL}")
print("Checking for publicly accessible forms, pages, meetings, etc.")
print("="*80)

findings = []

# ============================================================================
# 1. PUBLIC FORMS
# ============================================================================

print("\n[*] Scanning for public forms...")

# Try common form IDs
form_ids = list(range(1, 20)) + [50, 100, 1000]

for form_id in form_ids:
    urls = [
        f'https://forms.hubspot.com/{TARGET_PORTAL}/{form_id}',
        f'https://forms.hubspotqa.com/{TARGET_PORTAL}/{form_id}',
        f'https://share.hsforms.com/{TARGET_PORTAL}/{form_id}',
    ]

    for url in urls:
        try:
            r = requests.get(url, verify=False, timeout=5)

            if r.status_code == 200:
                print(f"  Found form: {url}")

                if 'super_secret' in r.text.lower():
                    print(f"    *** Contains super_secret! ***")
                    findings.append({
                        'type': 'public_form',
                        'url': url,
                        'content': r.text[:1000]
                    })
        except:
            pass

# ============================================================================
# 2. PUBLIC LANDING PAGES / WEBSITES
# ============================================================================

print("\n[*] Scanning for public websites...")

site_urls = [
    f'https://{TARGET_PORTAL}.hs-sites.com',
    f'https://{TARGET_PORTAL}.hubspotpagebuilder.com',
    f'https://www.{TARGET_PORTAL}.com',
    f'https://{TARGET_PORTAL}.com',
]

for url in site_urls:
    try:
        r = requests.get(url, verify=False, timeout=5, allow_redirects=True)

        if r.status_code == 200:
            print(f"  Found site: {url} -> {r.url}")

            if 'super_secret' in r.text.lower():
                print(f"    *** Contains super_secret! ***")
                findings.append({
                    'type': 'public_site',
                    'url': url,
                    'content': r.text[:1000]
                })
    except:
        pass

# ============================================================================
# 3. MEETINGS / BOOKING PAGES
# ============================================================================

print("\n[*] Scanning for meeting/booking pages...")

# Try different meeting link patterns
meeting_ids = list(range(1, 10))

for mid in meeting_ids:
    urls = [
        f'https://meetings.hubspot.com/{TARGET_PORTAL}',
        f'https://meetings.hubspot.com/{TARGET_PORTAL}/{mid}',
        f'https://meetings.hubspot.com/p/{TARGET_PORTAL}',
    ]

    for url in urls:
        try:
            r = requests.get(url, verify=False, timeout=5)

            if r.status_code == 200:
                print(f"  Found meeting page: {url}")

                # Check for contact data
                if any(term in r.text.lower() for term in ['email', 'firstname', 'contact']):
                    print(f"    Contains contact-related data")

                if 'super_secret' in r.text.lower():
                    print(f"    *** Contains super_secret! ***")
                    findings.append({
                        'type': 'meeting_page',
                        'url': url,
                        'content': r.text[:1000]
                    })
        except:
            pass

# ============================================================================
# 4. KNOWLEDGE BASE
# ============================================================================

print("\n[*] Scanning for knowledge base...")

kb_urls = [
    f'https://knowledge.hubspot.com/{TARGET_PORTAL}',
    f'https://knowledge.hubspot.com/portal/{TARGET_PORTAL}',
    f'https://{TARGET_PORTAL}.hubspotknowledge.com',
]

for url in kb_urls:
    try:
        r = requests.get(url, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"  Found KB: {url}")
    except:
        pass

# ============================================================================
# 5. CTA (CALL-TO-ACTION) TRACKING LINKS
# ============================================================================

print("\n[*] Scanning for CTA tracking links...")

# CTAs might expose contact data
for cta_id in range(1, 10):
    url = f'https://cta-redirect.hubspot.com/cta/redirect/{TARGET_PORTAL}/{cta_id}'

    try:
        r = requests.get(url, verify=False, timeout=5, allow_redirects=False)

        if r.status_code in [200, 301, 302]:
            print(f"  CTA {cta_id}: {r.status_code}")

            if 'super_secret' in r.text.lower():
                print(f"    *** Contains super_secret! ***")
                findings.append({
                    'type': 'cta',
                    'url': url,
                    'content': r.text
                })
    except:
        pass

# ============================================================================
# 6. EMAIL TRACKING PIXELS / WEB ANALYTICS
# ============================================================================

print("\n[*] Scanning for tracking endpoints...")

tracking_urls = [
    f'https://track.hubspot.com/__ptq.gif?a={TARGET_PORTAL}&k=14&r=https://example.com',
    f'https://forms.hubspot.com/uploads/form/v2/{TARGET_PORTAL}/1',
]

for url in tracking_urls:
    try:
        r = requests.get(url, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"  Tracking endpoint: {url[:60]}...")
    except:
        pass

# ============================================================================
# 7. CONTENT/FILES ENDPOINTS
# ============================================================================

print("\n[*] Scanning for public content...")

content_urls = [
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/contacts.csv',
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/data.json',
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}/export.csv',
    f'https://f.hubspotusercontent00.net/hubfs/{TARGET_PORTAL}/contacts.csv',
]

for url in content_urls:
    try:
        r = requests.get(url, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"  Found content: {url}")

            if 'super_secret' in r.text.lower():
                print(f"    *** Contains super_secret! ***")
                findings.append({
                    'type': 'public_file',
                    'url': url,
                    'content': r.text[:1000]
                })
    except:
        pass

# ============================================================================
# 8. WEBCHAT / LIVE CHAT WIDGET
# ============================================================================

print("\n[*] Scanning for webchat/live chat...")

chat_urls = [
    f'https://api.hubspot.com/livechat-public/v1/message/portal/{TARGET_PORTAL}',
    f'https://api.hubapi.com/conversations/v3/visitor-identification/tokens/create',
]

for url in chat_urls:
    try:
        r = requests.post(url, json={'portalId': TARGET_PORTAL}, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"  Chat endpoint: {url[:60]}...")
            try:
                data = r.json()
                print(f"    Response: {json.dumps(data, indent=2)[:200]}")
            except:
                pass
    except:
        pass

# ============================================================================
# 9. API DOCUMENTATION / DEVELOPER PORTAL
# ============================================================================

print("\n[*] Checking developer resources...")

dev_urls = [
    f'https://developers.hubspot.com/demo-portal/{TARGET_PORTAL}',
    f'https://developers.hubspot.com/docs/api/portal/{TARGET_PORTAL}',
]

for url in dev_urls:
    try:
        r = requests.get(url, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"  Dev resource: {url}")
    except:
        pass

print("\n" + "="*80)
print("Public Resources Scan Complete")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} PUBLIC RESOURCES! ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. {finding['type'].upper()}")
        print(f"   URL: {finding['url']}")

        if 'super_secret' in str(finding).lower():
            print(f"\n   *** CTF FLAG FOUND! ***")
            print(json.dumps(finding, indent=2))

            with open('/home/user/Hub/findings/PUBLIC_CTF_FLAG.json', 'w') as f:
                json.dump(finding, f, indent=2)

    with open('/home/user/Hub/findings/public_resources.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("\n" + "="*80)
    print("SAVED: findings/public_resources.json")
    print("="*80)
else:
    print("\nNo public resources found containing the CTF flag.")
    print("\nNext steps:")
    print("  - The portal may not have public-facing resources")
    print("  - May need legitimate OAuth app installation")
    print("  - May need to contact portal owner for access")
