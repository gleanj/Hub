#!/usr/bin/env python3
"""
Meta-analysis: Look for hints in error messages, cookies, headers
Maybe the challenge contains hints we've been missing
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import base64

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("META-ANALYSIS: LOOKING FOR HIDDEN HINTS")
print("="*80)

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. ANALYZE COOKIES FOR HIDDEN DATA
# ============================================================================

print("\n[1] ANALYZING COOKIES FOR PORTAL HINTS")
print("="*80)

for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)

        # Check if cookie contains portal ID
        if TARGET_PORTAL in value or 'portal' in key.lower():
            print(f"\n  Cookie: {key}")
            print(f"  Contains portal reference!")
            print(f"  Value: {value[:100]}")

        # Try to decode base64 cookies
        if len(value) > 20:
            try:
                decoded = base64.b64decode(value + '==')  # Add padding
                decoded_str = decoded.decode('utf-8', errors='ignore')

                if TARGET_PORTAL in decoded_str or 'portal' in decoded_str.lower():
                    print(f"\n  Cookie {key} (decoded):")
                    print(f"  {decoded_str[:200]}")
            except:
                pass

# ============================================================================
# 2. ANALYZE ERROR MESSAGES FOR CLUES
# ============================================================================

print("\n" + "="*80)
print("[2] COLLECTING ALL ERROR MESSAGES")
print("="*80)

error_messages = []

# Try a contact access to get the error
contact_url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}'

r = requests.get(contact_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

if r.status_code != 200:
    try:
        error = r.json()
        error_messages.append({
            'endpoint': 'contacts/1',
            'error': error
        })

        print(f"\nContact Access Error:")
        print(json.dumps(error, indent=2))
    except:
        pass

# Print all unique error messages
print(f"\n\n{'='*80}")
print("ERROR MESSAGE ANALYSIS")
print('='*80)

for err in error_messages:
    msg = err.get('error', {})

    print(f"\nEndpoint: {err['endpoint']}")
    print(f"Message: {msg.get('message', 'N/A')}")
    print(f"Category: {msg.get('category', 'N/A')}")

    # Look for hints in the message
    message_text = str(msg)

    if 'install' in message_text.lower():
        print(f"  *** Mentions 'install' - might need app installation")

    if 'oauth' in message_text.lower():
        print(f"  *** Mentions 'oauth' - might need OAuth flow")

    if 'scope' in message_text.lower():
        print(f"  *** Mentions 'scope' - might need different scopes")

# ============================================================================
# 3. CHECK RESPONSE HEADERS FOR HINTS
# ============================================================================

print("\n" + "="*80)
print("[3] ANALYZING RESPONSE HEADERS")
print("="*80)

test_url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/views/all/list'

r = session.get(test_url, verify=False, timeout=10)

print(f"\nURL: {test_url}")
print(f"Status: {r.status_code}")
print(f"\nInteresting Headers:")

for header, value in r.headers.items():
    if any(keyword in header.lower() for keyword in ['portal', 'auth', 'access', 'token', 'install', 'app']):
        print(f"  {header}: {value}")

# ============================================================================
# 4. CHECK IF THERE'S A PUBLIC DIRECTORY OR LISTING
# ============================================================================

print("\n" + "="*80)
print("[4] CHECKING FOR PUBLIC PORTAL DIRECTORIES")
print("="*80)

directory_urls = [
    'https://ecosystem.hubspot.com/marketplace/apps',
    'https://developers.hubspot.com/marketplace',
    'https://www.hubspot.com/products/crm',
]

for url in directory_urls:
    print(f"\n{url}")

    try:
        r = requests.get(url, verify=False, timeout=10)

        if r.status_code == 200:
            # Check if portal ID is mentioned
            if TARGET_PORTAL in r.text:
                print(f"  *** Portal {TARGET_PORTAL} mentioned! ***")

                # Find context
                import re

                for match in re.finditer(TARGET_PORTAL, r.text):
                    start = max(0, match.start() - 150)
                    end = min(len(r.text), match.end() + 150)
                    context = r.text[start:end]

                    print(f"  Context: {context[:200]}")
    except:
        pass

# ============================================================================
# 5. CHECK THE TOKEN FOR EMBEDDED INFORMATION
# ============================================================================

print("\n" + "="*80)
print("[5] ANALYZING ACCESS TOKEN")
print("="*80)

token = ACCESS_TOKEN

print(f"Token: {token[:20]}...{token[-10:]}")
print(f"Length: {len(token)}")
print(f"Format: {token.split('-')[0] if '-' in token else 'unknown'}")

# Check if token has any decodable parts
parts = token.split('-')

print(f"\nToken parts: {len(parts)}")

for i, part in enumerate(parts):
    print(f"  Part {i}: {part} ({len(part)} chars)")

    # Try to decode as base64
    if len(part) > 4:
        try:
            decoded = base64.b64decode(part + '==')
            decoded_str = decoded.decode('utf-8', errors='ignore')

            if decoded_str.isprintable() and len(decoded_str) > 3:
                print(f"    Decoded: {decoded_str}")
        except:
            pass

# ============================================================================
# 6. RECONSTRUCT THE CHALLENGE
# ============================================================================

print("\n" + "="*80)
print("[6] CHALLENGE RECONSTRUCTION")
print("="*80)

print("""
Based on all testing, here's what we know:

GIVEN:
- Access token: pat-na1-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
- Token is for portal: 50708459
- Session cookies for: nicksec@wearehackerone.com
- Target portal: 46962361
- Target properties: firstname, super_secret

FOUND:
- Portal 46962361 EXISTS
- Portal 50708459 has test flags
- Error: "Make sure that account has installed your app"
- Zero contacts accessible in portal 46962361

CONCLUSION:
The challenge may be testing whether we can:
A) Recognize we need app installation
B) Find the OAuth installation URL
C) Discover leaked credentials
D) Accept that it's impossible with current access

MISSING INFORMATION:
- Original CTF challenge description
- Setup instructions
- Whether portal 46962361 is correct
- Expected solution path
""")

# ============================================================================
# 7. SEARCH FOR CTF-RELATED KEYWORDS
# ============================================================================

print("\n" + "="*80)
print("[7] SEARCHING FOR CTF KEYWORDS IN ACCESSIBLE PAGES")
print("="*80)

ctf_keywords = ['ctf', 'flag', 'challenge', 'capture', 'bounty', 'h1']

test_urls = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/objects/0-1/views/all/list',
    'https://meetings.hubspot.com/nicksec',
]

for url in test_urls:
    print(f"\n{url[:60]}...")

    try:
        r = session.get(url, verify=False, timeout=10)

        if r.status_code == 200:
            text_lower = r.text.lower()

            found_keywords = [kw for kw in ctf_keywords if kw in text_lower]

            if found_keywords:
                print(f"  Found keywords: {found_keywords}")

                # Get context for first keyword
                import re

                first_kw = found_keywords[0]

                for match in re.finditer(first_kw, r.text, re.I):
                    start = max(0, match.start() - 100)
                    end = min(len(r.text), match.end() + 100)
                    context = r.text[start:end]

                    print(f"  Context: {context[:150]}")
                    break  # Just show first occurrence
    except:
        pass

print("\n" + "="*80)
print("META-ANALYSIS COMPLETE")
print("="*80)
