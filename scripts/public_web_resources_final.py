#!/usr/bin/env python3
"""
Final attempt: Public web resources for portal 46962361
Check for websites, blogs, landing pages, chatbots, knowledge bases
"""

import requests
import json
import os
import urllib3
import re
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

TARGET_PORTAL = '46962361'

print("="*80)
print("PUBLIC WEB RESOURCES - FINAL ATTEMPT")
print("="*80)

findings = []

# ============================================================================
# 1. CHECK FOR PUBLIC WEBSITE/CMS PAGES
# ============================================================================

print("\n[1] CHECKING FOR PUBLIC WEBSITES")
print("="*80)

# Common HubSpot CMS domain patterns
website_urls = [
    f'https://{TARGET_PORTAL}.hs-sites.com',
    f'https://www.{TARGET_PORTAL}.hs-sites.com',
    f'https://{TARGET_PORTAL}.hubspotpagebuilder.com',
    f'https://{TARGET_PORTAL}.hs-sites.com/contact',
    f'https://{TARGET_PORTAL}.hs-sites.com/about',
    f'https://{TARGET_PORTAL}.hs-sites.com/home',
    f'https://{TARGET_PORTAL}.hs-sites.com/index.html',
]

for url in website_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10, allow_redirects=True)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** WEBSITE FOUND! ***")
            print(f"  Size: {len(r.text)} bytes")

            # Save it
            with open(f'findings/public_website_{TARGET_PORTAL}.html', 'w') as f:
                f.write(r.text)

            # Check for contact data
            if 'firstname' in r.text.lower() or 'super_secret' in r.text.lower():
                print(f"  *** CONTAINS CONTACT KEYWORDS! ***")

                # Look for actual values
                patterns = [
                    r'"firstname"\s*:\s*"([^"]+)"',
                    r'"super_secret"\s*:\s*"([^"]+)"',
                    r'firstname:\s*"([^"]+)"',
                    r'super_secret:\s*"([^"]+)"',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, r.text, re.I)
                    real_values = [m for m in matches if m.lower() not in ['firstname', 'super_secret', 'text', 'string']]

                    if real_values:
                        print(f"  Found: {real_values[:3]}")

                        findings.append({
                            'type': 'website',
                            'url': url,
                            'pattern': pattern,
                            'values': real_values
                        })

            # Check for embedded forms
            form_matches = re.findall(r'portalId["\s:=]+(\d+)', r.text)
            if form_matches:
                print(f"  Found portalId references: {set(form_matches)}")

            # Check for hubspot form embeds
            if 'hbspt.forms.create' in r.text or 'hsforms.com' in r.text:
                print(f"  *** HAS EMBEDDED HUBSPOT FORMS! ***")

                # Extract form IDs
                form_id_matches = re.findall(r'formId["\s:=]+["\'](\d+)', r.text)
                if form_id_matches:
                    print(f"  Form IDs: {set(form_id_matches)}")
    except:
        pass

# ============================================================================
# 2. CHECK FOR BLOG
# ============================================================================

print("\n" + "="*80)
print("[2] CHECKING FOR BLOG")
print("="*80)

blog_urls = [
    f'https://{TARGET_PORTAL}.hs-sites.com/blog',
    f'https://blog.{TARGET_PORTAL}.hs-sites.com',
]

for url in blog_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** BLOG FOUND! ***")

            # Check for contact data in blog
            if 'firstname' in r.text.lower():
                print(f"  Contains 'firstname'")
    except:
        pass

# ============================================================================
# 3. CHECK FOR KNOWLEDGE BASE
# ============================================================================

print("\n" + "="*80)
print("[3] CHECKING FOR KNOWLEDGE BASE")
print("="*80)

kb_urls = [
    f'https://{TARGET_PORTAL}.hs-sites.com/knowledge',
    f'https://knowledge.{TARGET_PORTAL}.hs-sites.com',
    f'https://{TARGET_PORTAL}.hs-sites.com/kb',
    f'https://{TARGET_PORTAL}.hs-sites.com/help',
    f'https://help.{TARGET_PORTAL}.hs-sites.com',
]

for url in kb_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        if r.status_code == 200:
            print(f"  Status: {r.status_code}")
            print(f"  *** KNOWLEDGE BASE FOUND! ***")
    except:
        pass

# ============================================================================
# 4. CHECK FOR CHATBOT/CONVERSATIONS
# ============================================================================

print("\n" + "="*80)
print("[4] CHECKING FOR CHATBOT")
print("="*80)

# Check if there's a publicly accessible chatbot
chatbot_urls = [
    f'https://api.hubapi.com/livechat-public/v1/message/visitor/widget-data/{TARGET_PORTAL}',
    f'https://app.hubspot.com/chatflows/{TARGET_PORTAL}',
]

for url in chatbot_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** CHATBOT FOUND! ***")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

# ============================================================================
# 5. CHECK FOR PUBLIC MEETING LINKS
# ============================================================================

print("\n" + "="*80)
print("[5] CHECKING FOR PUBLIC MEETING LINKS")
print("="*80)

# We already know meetings.hubspot.com/nicksec exists
meeting_urls = [
    'https://meetings.hubspot.com/nicksec',
    'https://meetings.hubspot.com/nicksec/ctf',
    'https://meetings.hubspot.com/nicksec/demo',
    'https://meetings.hubspot.com/nicksec/test',
]

for url in meeting_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  Size: {len(r.text)} bytes")

            # Check for contact data in meeting page
            if 'firstname' in r.text.lower() or 'super_secret' in r.text.lower():
                print(f"  *** CONTAINS CONTACT KEYWORDS! ***")

                # Save it
                filename = url.split('/')[-1] or 'nicksec'
                with open(f'findings/meeting_{filename}.html', 'w') as f:
                    f.write(r.text)
    except:
        pass

# ============================================================================
# 6. CHECK FOR EMAIL SIGNATURE / TRACKING LINKS
# ============================================================================

print("\n" + "="*80)
print("[6] CHECKING FOR EMAIL TRACKING")
print("="*80)

# Try to find email tracking that might expose contact data
tracking_urls = [
    f'https://track.hubspot.com/__ptq.gif?a={TARGET_PORTAL}&k=1&r=https://example.com',
]

for url in tracking_urls:
    print(f"\n{url[:70]}...")

    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200 and len(r.content) > 100:
            print(f"  Size: {len(r.content)} bytes")
    except:
        pass

# ============================================================================
# 7. robots.txt AND sitemap.xml
# ============================================================================

print("\n" + "="*80)
print("[7] CHECKING robots.txt AND sitemap.xml")
print("="*80)

meta_urls = [
    f'https://{TARGET_PORTAL}.hs-sites.com/robots.txt',
    f'https://{TARGET_PORTAL}.hs-sites.com/sitemap.xml',
]

for url in meta_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** FOUND! ***")
            print(f"  Content:\n{r.text[:500]}")

            # If sitemap, parse URLs
            if 'sitemap.xml' in url:
                urls = re.findall(r'<loc>(.+?)</loc>', r.text)
                if urls:
                    print(f"\n  Found {len(urls)} URLs in sitemap")

                    # Check first few URLs for contact data
                    for page_url in urls[:10]:
                        print(f"\n  Checking: {page_url}")

                        try:
                            page_r = requests.get(page_url, verify=False, timeout=5)

                            if page_r.status_code == 200:
                                if 'firstname' in page_r.text.lower() or 'super_secret' in page_r.text.lower():
                                    print(f"    *** CONTAINS CONTACT KEYWORDS! ***")

                                    findings.append({
                                        'type': 'sitemap_page',
                                        'url': page_url,
                                        'size': len(page_r.text)
                                    })
                        except:
                            pass
    except:
        pass

print("\n" + "="*80)
print("PUBLIC WEB RESOURCES CHECK COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL DATA SOURCES! ***\n")

    with open('/home/user/Hub/findings/public_web_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:600]}")

        if 'super_secret' in json.dumps(finding).lower():
            print(f"\n*** CTF FLAG FOUND! ***")
else:
    print("\nNo public web resources with contact data found.")
    print("\nAll possible attack vectors have been exhausted.")
    print(f"\nTotal attack vectors tested across all sessions: 700+")
